Title: Using off-cpu flame graphs on Linux
Date: 2015-12-20
Tags: Linux, perf_events, flamegraph
Summary: I use off-cpu flame graphs to identify that repeated mmap calls are slowing my database.

## The setup

I recently got to debug a pretty strange performance issue in a test build
of our product. It was running under a synthetic workload where we had 16
threads (one for each CPU core) each running a very simple query
(`select count(*) from t where i > 5`) that would have to visit almost all of
the table's 1 million rows. In theory, this would be a CPU bound operation
since it would be reading from a file that was already in disk buffer cache.
In practice, our cores were spending about 50% of their time idle:

![Each core is spending about half it's time idle.](|filename|/images/low_cpu_usage.png "Each core is spending about half it's time idle.")

## What were our threads doing?

After confirming that our workload was indeed using 16 threads, etc, I took a
look what state our various threads were in. In every refresh of my
[`htop`](http://hisham.hm/htop/) window, I saw that a handful of our threads
were in the
[`D`](http://blog.kevac.org/2013/02/uninterruptible-sleep-d-state.html)
state corresponding to "Uninterruptible sleep":

    :::console
      PID USER      PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command
    55308 neil       21   1 11.6G 3825M 36804 S 530.  3.4 21h44:11 ./memsqld
    55969 neil       20   0 11.5G 3825M 36804 R 35.8  3.4 30:31.52 ./memsqld
    56121 neil       20   0 11.6G 3825M 36804 D 35.8  3.4 34:55.03 ./memsqld
    56120 neil       20   0 11.6G 3825M 36804 D 34.4  3.4 36:27.53 ./memsqld
    56109 neil       20   0 11.6G 3825M 36804 R 33.7  3.4 31:57.14 ./memsqld
    56088 neil       20   0 11.6G 3825M 36804 D 33.7  3.4 50:08.92 ./memsqld
    56099 neil       20   0 11.6G 3825M 36804 D 33.7  3.4 31:58.06 ./memsqld
    56069 neil       20   0 11.6G 3825M 36804 R 33.1  3.4 31:01.54 ./memsqld
    56101 neil       20   0 11.6G 3825M 36804 D 32.4  3.4 28:41.27 ./memsqld
    56104 neil       20   0 11.6G 3825M 36804 D 32.4  3.4 31:54.41 ./memsqld
    55976 neil       20   0 11.5G 3825M 36804 D 32.4  3.4 30:18.72 ./memsqld
    55518 neil       20   0 11.5G 3825M 36804 D 32.4  3.4 29:48.51 ./memsqld
    55966 neil       20   0 11.5G 3825M 36804 D 32.4  3.4 36:51.50 ./memsqld
    55971 neil       20   0 11.5G 3825M 36804 R 32.4  3.4 27:22.96 ./memsqld
    55959 neil       20   0 11.5G 3825M 36804 D 32.4  3.4 38:13.50 ./memsqld
    55975 neil       20   0 11.5G 3825M 36804 R 31.7  3.4 30:18.38 ./memsqld

## Why were we going off CPU?

At this point, I generated an
[off-cpu flamegraph](http://www.brendangregg.com/blog/2015-02-26/linux-perf-off-cpu-flame-graph.html)
using Linux `perf_events`, to see why were entering this state. The machine I
was testing on was old enough that it didn't have `perf inject`, so I had to 
use an
[`awk` script](https://github.com/awreece/FlameGraph/blob/6f3e75f10923d1f97e4b2b0a40d8ec3c9d063974/stackcollapse-perf-sched.awk)
I'd previously written:

    ::console
    $ sudo perf record --call-graph=fp -e 'sched:sched_switch' -e 'sched:sched_stat_sleep' -e 'sched:sched_stat_blocked' --pid $(pgrep memsqld | head -n 1) -- sleep 1
    [ perf record: Woken up 1 times to write data ]
    [ perf record: Captured and wrote 1.343 MB perf.data (~58684 samples) ]
    $ sudo perf script -f time,comm,pid,tid,event,ip,sym,dso,trace -i sched.data | ~/FlameGraph/stackcollapse-perf-sched.awk | ~/FlameGraph/flamegraph.pl --color=io --countname=us >off-cpu.svg

The culprit was that `mmap` was contending in the kernel on the `mm->mmap_sem` lock:

![We see a lot of time is spent in rwsem_down_write_failed.](|filename|/images/mmap_off_cpu.svg "In an off-cpu flamgraph, the width of a bar is proportional to the total time spent off cpu. Here we see a lot of time is spent in rwsem_down_write_failed.")

Fortunately, the fix was simple -- we switched to using the traditional file
`read` interface. After this change, we nearly doubled our throughput
and became CPU bound as we expected:

![Almost 100% CPU utilization](|filename|/images/high_cpu_usage.png "Almost 100% CPU utilization")

## Open questions

I'll buy a {root,}beer/beverage of choice for anyone who can help me with these
questions:

  - Is there a good tool in Linux to see (in periodic updates) what % of time a thread spends in each of the various possible thread states?
  - Why do the time spent sleeping / executing mmap as recorded by by the sched probes not align with the latency of mmap calls if the mmap calls don't show in cpu stack traces? (I suspect that `mm_populate` or `rwsem_down_read_failed` does an alarming amount of work while having disabled bottom half interrupts, which is interfering with `perf`)
Title: Dtrace isn't just a tool; its a philosophy
Date: 2016-01-03
Tags: Linux, perf_events
Summary: I document some pain points from a recent performance investigation and then speculate that such issues are endemic to Linux.

My most recent [post]({filename}off_cpu_mmap.md) was a story about a successful performance investigation. Unfortunately, this happy post was intentionally simplified for the audience of my company's blog. The reality is that I find doing performance investigations on Linux is a frustrating process due to the lack of adequate tooling. In this blog post, I document some of my particular pain points and then speculate that such issues are endemic to Linux.

## Some pain points

Compare how we answer the following questions[^1] (in production) in Linux and FreeBSD/Solaris: 

[^1]: I acknowledge that these questions are particularly painful to answer with `perf`, but I am not nearly as frustrated at the awkwardness of doing so with `perf` than I am scared of the instability in `perf` when answering them. I want my system introspection tool to feel rock solid and I don't quite have that confidence with `perf`.

### Why am I going off CPU?

  - FreeBSD/Solaris: 

        :::console
        # dtrace -n 'sched:::off-cpu /pid==$target/ { self->ts = timestamp; } sched::on-cpu /self->ts/ { @[stack(), ustack()] = quantize(timestamp - self->ts); self->ts = 0}' -p $PID

  - Linux: 

        :::console
        # perf record -g -e 'sched:sched_switch' -e 'sched:sched_stat_sleep' -e 'sched:sched_stat_blocked' -p $PID

    then post process with `perf inject -s` (if you have it) or my 200 line `stackcollapse-perf-sched.awk` script. Unfortunately, tracing all scheduler events is very high overhead in perf and the lack of in-kernel aggregation means that events probably will be dropped if load is high. Even more alarmingly, there appear to be bugs in perf that prevent it from reliably getting consistent traces (even with large trace buffers), causing it to produce empty perf.data files with error messages of the form: 
    
        0x952790 [0x736d]: failed to process type: 3410

    Since this failure is not determinisitic, re-executing `perf record` will eventually succeed; however, it then can sometimes be hard to catch the pathology.

### Why am I calling `malloc`?

  - FreeBSD/Solaris: 

        ::console 
        # dtrace -n 'pid$target::malloc:entry { @[ustack()] = count(arg0); } -p $PID'

  - Linux: It is possible you could write a `gdb` script, although I'd be scared to do this in production. Another alternative is use the `uprobe` interface:

        :::console
        # perf probe /lib/x86_64-linux-gnu/libc.so.6 malloc 'size=%di'
        # perf record -e probe_libc:malloc -g --pid $PID`

    Aside from the common message about the overhead of not having in kernel aggregates, I've found this interface to be particularly brittle. Even scarier, [Brendan Gregg](http://www.brendangregg.com/blog/2015-06-28/linux-ftrace-uprobe.html) also warns about issues that would make it unsuitable for production environments (I haven't personally seen this when using `perf` yet):
    > frequently hit issues where the target process either crashes or enters an endless spin loop

### What files am I reading?

   - FreeBSD/Solaris: 

        :::console
        # dtrace -n 'syscall::read:entry { @[fds[arg0].fi_pathname] = sum(arg2); }' -p $PID

   - Linux: `strace` used to be a traditional solution, although it has high overhead. With 

        :::console
        # perf trace -eread -p $PID

     you can now save the data and post process (although I must repeat the message about the overhead of not having in kernel aggregates).

### The problem with stack traces.

Most all of the questions I have are of the form "Why is my application X" and are answered by looking at userspace stack traces. Unfortunately, this is almost impossible to do in my Linux distribution. Ubuntu compiles `libc` with `-fomit-frame-pointer` (the `gcc` default for `-O2` and above), which stymies `perf`s ability to walk stacks that go through the most commonly used system library. Worse, it is [not clear](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1248289) that the `perf` on Ubuntu properly supports walking `dwarf` unwind information (I've used `--call-graph=dwarf` only moderately successfully, as it appears to lose frames compared to the stacks in `gdb`, etc.).

## Introspection in Linux

It seems to me that the Linux community does not support the same level of kernel/system introspection as Solaris. The lack of frame pointers in Linux is a pretty big example of this, but I think this issue is cultural, not technical. Take a look at a famous quote[^2] from [Linus himself](https://lwn.net/2000/0914/a/lt-debugger.php3) in 2000 on why he eschews the use of a kernel debugger:

> I don't think kernel development should be "easy". ... I do not think that extra visibility into the system is necessarily a good thing.

In Linux, the kernel is a complicated, mysterious system that is only intended to be fully understood by the authors, so tools like kernel debuggers are not necessary. 

Compare to a recent quote from an equally opinionated former Solaris kernel engineer, [Bryan Cantril](https://www.youtube.com/watch?v=sYQ8j02wbCY), on why it is important to have observability into Docker containers:

> Don't just reboot your pc, goddammnit, debug it! Come on, you're an educated person, right? Or at least you want to act like one around other educated people!

In that talk, Bryan emphatically calls for bigger observability into a Linux subsystem so that complicated problems in production can be diagnosed and fixed. He condemns the engineering anti-pattern of only adding observability when something has gone wrong, pointing out that this puts the engineer in the position of trying to reproduce a potentially transient issue.

I think these quotes indicate a remarkable difference: in Solaris, the kernel is a fundamental part of a larger system that must be understood as part of the larger system, so tools like `dtrace` are necessary.

[^2]: I acknowlege both quotes are taken _only slightly_ out of context to get the most exciting blurb, but I believe I honestly captured the sentiment of their authors in my analysis.

## A question driven methodology

The thing about `dtrace` is that it is so powerful and so flexible that it encourages a _question_ driven methodology rather than _tool_ driven methodology. Rather than merely trying to infer problems from some `sar` utility, we ask simple and specific questions to root cause an issue. The common tools (`iostat`, `top`, `sar`) are useful as a means to prompt these questions but are rarely useful on their own. When Brendan Gregg advocates for the [USE method](http://www.brendangregg.com/usemethod.html) or the [TSA method](http://www.brendangregg.com/tsamethod.html), he is providing frameworks for convert these `sar` metrics into useful questions.

I have a story that illustrates this point quite well. A couple of years ago, I did a mock technical interview with Adam Leventhal where he walked me through a real performance investigation he had previously done. For the interview, he described a faulty server to me and asked me to debug it using only a "magical oracle" that could answer any question about the system -- over the course of the interview, he explained how he used `dtrace` to answer any question we put to the "oracle".

This question driven methodology that I've learned from my mentors from the Solaris community has proven challenging for me as I start working more with Linux. I'm slowly learning to use `perf` to answer my questions and I'm slowly improving the culture at my current company. Some highlights:

 - Our database is always compiled with `-fno-omit-frame-pointer`, which increases the fidelity of our CPU stacks collected from `perf`.
 - We have hooks to increase debuggability (via recording JIT-ed symbols for `perf`, etc) that can be dynamically enabled at run time for ad-hoc investigations.
 - Almost all engineers at the company use flame graphs to do performance investigations. They quickly answer the first question of "where is my cpu time being spent" and it has become uncommon to see a performance regression bug filed without an attached flame graph.
 - The most recent iteration of performance tests were [actively benchmarked](http://www.brendangregg.com/activebenchmarking.html) with flame graphs as they were written. Through this process, we caught and corrected several tests that were testing the wrong path.
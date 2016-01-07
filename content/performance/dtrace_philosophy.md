Title: Dtrace isn't just a tool; it's a philosophy
Date: 2016-01-03
Tags: Linux, perf_events, opinion
Summary: I document some pain points from recent performance investigations and then speculate that such issues are endemic to the Linux community.

My most recent [post]({filename}off_cpu_mmap.md) was a story about a successful performance investigation. Unfortunately, this happy post was intentionally simplified for the audience of my company's blog. The reality is that I frequently find doing performance investigations on Linux a frustrating process due to the lack of adequate tooling. In this blog post, I document some recent pain points and then speculate that such issues are endemic to Linux.

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

    Then post process with `perf inject -s` (if you have it) or my 200 line `stackcollapse-perf-sched.awk` script. Unfortunately, tracing all scheduler events is very high overhead in perf and the lack of in-kernel aggregation means that events probably will be dropped if load is high. Even more alarmingly, there appear to be bugs in perf that prevent it from reliably getting consistent traces (even with large trace buffers), causing it to produce empty perf.data files with error messages of the form: 
    
        0x952790 [0x736d]: failed to process type: 3410

    Since this failure is not deterministic, re-executing `perf record` will eventually succeed; however, it then can sometimes be hard to catch the pathology.

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

     You can now save the data and post process (although I must repeat the message about the overhead of not having in kernel aggregates).

### The problem with stack traces.

Almost all of the questions I have are of the form: "Why is my application X", and are answered by looking at userspace stack traces. Unfortunately, this is almost impossible to do in my Linux distribution. Ubuntu compiles `libc` with `-fomit-frame-pointer` (the `gcc` default for `-O2` and above), which stymies `perf`s ability to walk stacks that go through the most commonly used system library. Worse, it is [not clear](https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1248289) that the `perf` on Ubuntu properly supports walking `dwarf` unwind information. I've used `--call-graph=dwarf` only moderately successfully, as it appears to lose frames compared to the stacks in `gdb`, etc.

When Linux applications omit frame pointers, they are eschewing future visibility for the sake of an immediate micro-optimization. Some applications choose a compromise of merely omitting frame pointers for leaf functions (causing the _second to last_ frame of every stack to be omitted). In either, aggressive function inlining causes the resulting stack trace to be an approximation of the logical stack trace. As a stark contrast, the Illumos kernel forces frame pointers and prohibits small functions from being [automatically inlined](https://github.com/illumos/illumos-gate/blob/6249f9725f411468c70516176806c553ac983270/usr/src/uts/Makefile.uts#L237) to guarantee precise stack traces. Since the most convenient place to add dynamic tracepoints via `dtrace` is at function call boundaries, this also ensures that there will be a plethora of options if it ever become necessary to debug some new component.

## Introspection in Linux

It seems to me that the Linux community does not support the same level of kernel/system introspection as Solaris and I think this issue is cultural, not technical. Take a look at a famous quote[^2] from [Linus himself](https://lwn.net/2000/0914/a/lt-debugger.php3) in 2000 on why he eschews the use of a kernel debugger:

> I don't think kernel development should be "easy". ... I do not think that extra visibility into the system is necessarily a good thing.

In Linux, the kernel is a complicated, mysterious system that is only intended to be fully understood by the authors, so tools like kernel debuggers are not necessary. 

Compare to a recent quote from an equally opinionated former Solaris kernel engineer, [Bryan Cantrill](https://www.youtube.com/watch?v=sYQ8j02wbCY), on why it is important to have observability into Docker containers:

> Don't just reboot your pc, goddammnit, debug it! Come on, you're an educated person, right? Or at least you want to act like one around other educated people!

In that talk, Bryan emphatically calls for bigger observability into a Linux subsystem so that complicated problems in production can be diagnosed and fixed. He condemns the engineering anti-pattern of only adding observability when something has gone wrong, pointing out that this puts the engineer in the position of trying to reproduce a potentially transient issue. Flexible dynamic tracing tools with the power to deeply introspect the kernel, like `dtrace`, are necessary to observe and debug such issues in production.

[^2]: I acknowledge both quotes are taken _only slightly_ out of context to get the most exciting blurb, but I believe I honestly captured the sentiment of their authors in my analysis.

## A question driven methodology

The thing about `dtrace` is that it is so powerful and so flexible that it encourages a _question_ driven methodology rather than _tool_ driven methodology. Rather than merely trying to infer problems from some `sar` utility, we ask simple and specific questions to root cause an issue. The common tools (`iostat`, `top`, `sar`, etc.) are useful as a means to prompt these questions but are rarely useful on their own. When Brendan Gregg advocates for the [USE method](http://www.brendangregg.com/usemethod.html) or the [TSA method](http://www.brendangregg.com/tsamethod.html), he is providing frameworks for converting these `sar` metrics into useful questions.

I have a story that illustrates this point quite well. A couple of years ago, I did a mock technical interview with Adam Leventhal where he walked me through a real performance investigation he had previously done. For the interview, he described a faulty server to me and asked me to debug it using only a "magical oracle" that could answer any question about the system -- over the course of the interview, he explained how he had used `dtrace` to answer every question we had put to the "oracle". By looking beyound the simple `sar` metrics and asking focused questions, we were able to "resolve" in an hour an issue that would be nigh impossible to understand otherwise.

Linux supports some dynamic tracing tools that enable these types of investigations, but (at least until recently) they remain second class citizens. `perf` and `ftrace` feel  brittle and limited compared to the deep visibility of `dtrace`. In contrast, dynamic tracing is so valuable to Solaris that the kernel is built specifically with `dtrace` in mind. High fidelity dynamic tracing of production is too important to be approximated by separate tools; it is baked into every layer of the system.

## What can we do about this?

The question driven methodology that I've learned from my mentors from the Solaris community has proven challenging for me as I start working more within my Linux-based company. I'm slowly learning to use `perf` to answer my questions and I'm slowly changing the culture at my current company. Some highlights:

 - We compile with `-fno-omit-frame-pointer`, which increases the fidelity of our CPU stacks collected from `perf`.
 - We're slowly cutting back on the amount of unnecessary function inlining and have simple tools in place to detect eggregious examples of this.
 - We have hooks to increase debuggability (via recording JIT-ed symbols for `perf`, etc) that can be dynamically enabled at run time for ad-hoc investigations. Previously, they required a server restart.
 - Almost all engineers at the company use flame graphs to do performance investigations. They quickly answer the first question of "where is my cpu time being spent" and it has become uncommon to see a performance regression bug filed without an attached flame graph.
 - The most recent iteration of performance tests were [actively benchmarked](http://www.brendangregg.com/activebenchmarking.html) with flame graphs as they were written. Through this process, we caught and corrected several tests that were testing the wrong path.

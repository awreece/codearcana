Title: An informal survey of Linux dynamic tracers
Date: 2016-01-09
Tags: Linux, tracing, perf_events
Summary: I survey some dynamic tracers (e.g. perf, sysdig) available on Linux.

I've gotten some questions about the choice of `perf` over all the other
available Linux tracers. This blog post is a quick overview of my personal
experiencing trying several tracers; it is not intended to be authoritative.

## My requirements

Since I use dynamic tracers to iteratively answer
[questions]({filename}dtrace_philosophy.md) about production systems, I have
several requirements. I'll order them here based on their priority to me:

  1. A good tracing tool is stable. I do not want my production systems crashing.
  2. A good tracing tool is low overhead. I want to use it in production
     environments, so it cannot substantially affect system performance.
     This usually means I want some sort of selective filtering or early
     output aggregation.
  3. A good tracing tool can collect userspace stacks. The most frequent
     question I ask is "Why is my application X", and userspace stacks are the
   	 number one way I answer this question.
  4. A good tracing tool has visibility into the kernel. I am frequently asking
     questions about the system (e.g. "Why am I descheduled?" or "Why am I doing
	 disk IO?") that can only be answered effectively with kernel support.
  5. A good tracing tool is easily usable on old (e.g. pre-3.2 kernel)
     systems. For many of my customers, upgrading (especially to mainline
	 kernel) is a frightening proposition.
  6. A good tracing tool already exists on the system. A great tracing tool
     doesn't require special packages to be installed. For many of my customers,
	 installing new software (especially on a production server) is a
	 challenging or painful process.

## Tracers I have tried

  - [`ftrace`](http://elinux.org/Ftrace): Powerful building block that doesn't
    have a satisfactory front
    end yet. Brendan Gregg has some good tools in his
	[perf-tools](https://github.com/brendangregg/perf-tools) package.
	Enabled by default even on old kernels and usable with no external packages,
	but requires root.
	Has some quirks: for example, I had difficulty getting userspace stacks to
	work reliably across all events when I tried it.
  - [`perf`](https://perf.wiki.kernel.org/index.php/Main_Page): Rapidly growing
    frontend for many other kernel tracing subsystems,
    including parts of `ftrace`. Has a huge surface area in the kernel and
	in userspace. Kernel support for `perf` is very common, although the
	userspace frontent requires a package to be installed. Provides little
	to no support[^1] for in-kernel aggregation (some support for event filtering)
	so all data must be post-processed in userspace -- this can have a large
	performance effect for very frequent events (e.g. scheduler events).
	For this reason, I find the interface pretty clunky.
	
	`perf` is my current favorite tracer because of the support, surface area, and
	because it can be used in production environments without custom kernel
	modules.	

[^1]: `perf stat` can do some aggregation, but unfortunately cannot aggregate on
very complicated things (e.g. stacks).

  - [`systemtap`](https://sourceware.org/systemtap/): I can't really find
    evidence of people using this legitimately
    except to do kernel development. Was hard to install (required massive
	download of debug symbols and a custom kernel??). I have concerns about its
	viability for production environments.
  - [`sysdig`](http://www.sysdig.org/): A glorious user interface and easy to
    install, but definitely the
    new kid on the block. Requires a custom kernel module to be installed.
	Only traces at the syscall boundary, which is good enough for some use
	cases, but I generally prefer more visibility into the kernel (for example,
	to see that we're getting descheduled due to page faults, etc).
	Doesn't have a way to filter or aggregate in-kernel events (by design) and
	cannot collect stack traces. These developers seemed very open
	to outside contributors and upstream their work pretty quickly, so maybe
	contributions here could actually be used customers in my lifetime.
	
## Tracers I have investigated

  - [`lttng`](https://lttng.org/): Incredible docs, but requires a kernel module
    to trace kernel events. Appears to have strong support for a variety of
	userspace applications. Does not appear to do in-kernel aggregation. 
	Can this collect stack traces?
  - [`ktap`](http://www.ktap.org/): Haven't played around with this but the
    interface is really pretty. I have some concerns about its
	[stability](https://github.com/ktap/ktap/issues).
  - [`eBPF`](https://lwn.net/Articles/603983/): Looks flexible and will be
    mainline in the kernel, but isn't there on old kernels and doesn't have a
	good frontend yet. I'm watching [iovisor](https://github.com/iovisor/bcc)
	for that.

Feel free to chime in with any other tracers or commentary.

Title: A cross-platform monotonic timer
Date: 2013-05-15
Tags: profiling
Summary: I've been working on writing a memory bandwidth benchmark for a while and needed to use a monotonic timer to compute accurate timings. I have since learned that this is more challenging to do that I initially expected and each platform has a different way of doing it.

I've been working on writing a memory bandwidth benchmark for a while and
needed to use a monotonic timer to compute accurate timings. I have since
learned that this is more challenging to do that I initially expected and each
platform has a different way of doing it.

# The problem #

First, I started by using `gettimeofday`:

~~~
:::c
struct timeval before, after;

gettimeofday(&before, NULL);
function();
gettimeofday(&after, NULL);
~~~

Unfortunately, this will not always work since it is dependent on the system clock. If some other process changes the system time between the two calls to `gettimeofday`, it could report inaccurate results. We need a function that returns a monotonically increasing value.

# A solution? #

Luckily, such a function exists on Linux. We can use `clock_gettime` with `CLOCK_MONOTONIC`:

~~~
:::c
struct timespec before, after, total;

clock_gettime(CLOCK_MONOTONIC, &before);
function();
clock_gettime(CLOCK_MONOTONIC, &after);
~~~
# Other platforms #

Unfortunately, this doesn't work everywhere! Each platform has its own way
accessing a high resolution monotonic counter. On Mac OS X we use
[`mach_absolute_time`](https://developer.apple.com/library/mac/#qa/qa1398/_index.html)
and on Windows we use
[`QueryPerformanceCounter`](http://msdn.microsoft.com/en-us/library/windows/desktop/ms644904(v=vs.85).aspx). 

## `rdtsc` ##
On x86 machines where none of these are available, we can resort directly to `rdtsc`. This is a special instruction that returns the [Time Stamp Counter](https://en.wikipedia.org/wiki/Time_Stamp_Counter), the number of cycles since reset. Unfortunately, we have to be *very* careful when using this instruction. [This white paper](http://download.intel.com/embedded/software/IA/324264.pdf) offers a lot of good advice on how to use it, but in short we have to take care to prevent instruction reordering. In the following code, the reordering of the `fdiv` after the `rdtsc` would lead to inaccurate timing results:

~~~
:::gas
rdtsc
fdiv # Or another slow instruction
rdtsc
~~~

The instruction `rdtscp` prevents instructions that occur before the `rdtsc` from being reordered afterwards. Unfortunately, instructions that occur after the `rdtscp` can still be reordered before it. The following code could have `fdiv` reordered before the `rdtscp`, leading to inaccurate results:

~~~
:::gas
rdtscp
call function
rdtscp
fdiv
~~~

The suggested way to avoid the reordering is to use the `cpuid` instruction, which has the effect of preventing all instruction reordering around it. While this is a slow instruction, we can be a bit clever and ensure that we never have to execute it while between the times when we query the counter.  
The ideal timing code looks something like this:

~~~
:::gas
cpuid
rtdsc
# Save %edx and %eax (the output of rtdsc).
call function
rdtscp
# Save %edx and %eax.
cpuid
~~~

# A cross platform timer #
Assembling all this information, I attempted to write a cross-platform utility for fine grained timing. A few late nights and a file full of `#ifdef`s later, I have the start of such a utility. Currently, it supports the function `monotonic_seconds` which returns the seconds from some unspecified start point as a double precision floating point number. In the future, I'll add support for `monotonic_cycles` as a static inline function in the header and `cycles_to_seconds` as a way to convert cycles to seconds. Check it out [here](https://github.com/awreece/monotonic_timer/blob/master/monotonic_timer.c)!

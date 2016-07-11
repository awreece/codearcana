Title: Arena "leak" in glibc
Tags: glibc, perf_events, malloc, Linux
Date: 2016-07-11
Summary: I diagnose an unexpected behavior in the glibc malloc implementation manifesting as a slow memory "leak".


I was recently working on really strange memory issue. Over the course of 1-2 weeks, memory usage of `memsqld` increased despite no change in the amount of data stored. To make matters even more interesting, `memsqld` keeps extremely detailed accounting of memory usage (by tracking calls to `mmap`, `malloc`, etc). `memsqld`'s accounting was off, reporting that we were only use ~2-3G of memory despite actually consuming ~15G of memory. What was going on?

The first thing I did was capture the output of `/proc/$PID/maps` in the offending process and then generated a core dump so I could get `memsqld` running again and do analysis offline. 

I summed up all the different types of memory using awk and noticed that the 12GB difference appeared to be coming from ~64MB regions that were mapped `rwxp`:

```
:::console
$ cat proc_pid_maps | gawk '{ split($1, a, "-"); b=strtonum("0x" a[1]); e=strtonum("0x" a[2]) } /stack/ { t="stack"; } /heap/ { t="heap"; } /\.so/ { t="so" } /\.mu/ { t="mu" } /\.mo/ { t="mo"; }  (!t) { $1 = ""; t=$0} { print e-b " " t ; t=""}' | awk '{ s=$1; $1=""; b[$0] += s; c[$0] += 1 } END { print "bytes count type"; for (t in b) { print b[t] " " c[t] " " t } }' | sort -nk 1

bytes count type
4096 1  r-xp 00000000 00:00 0 [vsyscall]
8192 1  r--p 00000000 00:00 0 [vvar]
8192 1  r-xp 00000000 00:00 0 [vdso]
8192 1  r-xp 00000000 ca:3400 262148 /data/logs/sharding_log_0
20480 1  r-xp 00000000 ca:3400 262166 /data/logs/app_old_log_0
73728 1  r-xp 00000000 ca:3400 262157 /data/logs/app_log_0
499712 1  r-xp 00000000 00:42 86 /memsqlbin/lib/interp_ops.bc
4460544 125  mo
4796416 1  rwxp 02085000 00:42 51 /memsqlbin/memsqld
6656000 242  r-xp 00000000 00:00 0
8245248 89  mu
34103296 1  r-xp 00000000 00:42 51 /memsqlbin/memsqld
55984128 81  so
375599104 1  heap
1515778048 1037  ---p 00000000 00:00 0
2380578816 871  stack
12578443264 359  rwxp 00000000 00:00 0
```

## Using `perf` to trace `mmap`s

I wanted to see who was allocating these large regions, so I used `perf` to record a stack trace any time the `memsqld` process `mmap`ed a region of memory greater than 60MB in length[^1]:

[^1]: I found the name of the filter arguments via `cat /sys/kernel/debug/tracing/events/syscalls/sys_enter_mmap/format`.

```
:::console
$ sudo perf record -g -e syscalls:sys_enter_mmap --filter 'len > 60000000' --pid $PID_OF_MEMSQL -o /path/to/storage -- sleep $2_DAYS_IN_SECONDS
```

Unfortunately, this proved to be useless -- since `libc` on Linux is typically compiled without frame pointers, the stack traces we got were *very* short:

```
memsqld   531 [003] 3033773.536620: syscalls:sys_enter_mmap: addr: 0x00000000, len: 0x08000000, prot: 0x00000000, flags: 0x00004022, fd: 0xffffffff, off: 0x00000000
	    7fb0a4d6297a mmap64 (/lib/x86_64-linux-gnu/libc-2.19.so)
```

I figured I'd use `perf probe` to trace the `mmap64` library call boundary so I could see the stacks, but unfortunately, this didn't work inside docker[^2]:

[^2]: I suspect that `perf probe` interacts poorly with Linux filesystem namespaces; has anyone played around here before?

```
:::console
root@memsql-leaf-1-2649458094-nz33q:/data/areece# perf probe /lib/x86_64-linux-gnu/libc-2.19.so mmap64 'len=%si'
Probe point 'mmap64' not found.
  Error: Failed to add events.
```

## A lucky guess
Going back to the drawing board, I looked at the data in the core dump. When I looked at the memory near those 64MB sections, I noticed that the contents looked heap-ish:

```
(gdb) x/100a 0x7f8f98000000
0x7f8f98000000:	0x7f8f98000020	0x0
0x7f8f98000010:	0x3e27000	0x4000000
0x7f8f98000020:	0x200000000	0x7f8f980fa580
0x7f8f98000030:	0x0	0x7f8f9a6646e0
0x7f8f98000040:	0x7f8f9ab025f0	0x0
0x7f8f98000050:	0x0	0x0
0x7f8f98000060:	0x0	0x0
0x7f8f98000070:	0x0	0x7f8f9be069e0
0x7f8f98000080:	0x7f8f9bdda2a0	0x7f8f9bdd9fb0
0x7f8f98000090:	0x7f8f9bdc3210	0x7f8f980910f0
0x7f8f980000a0:	0x7f8f980a4cb0	0x7f8f99678920
0x7f8f980000b0:	0x7f8f9aad0b90	0x7f8f98104070
0x7f8f980000c0:	0x7f8f98057370	0x7f8f9a649470
0x7f8f980000d0:	0x7f8f9aac2df0	0x7f8f9808e630
0x7f8f980000e0:	0x7f8f9a66e920	0x7f8f996222a0
0x7f8f980000f0:	0x7f8f9bce28e0	0x7f8f9ab89030
```

Furthermore, the permissions on these pages matched the permissions on our heap:

```
0345b000-098c0000 rwxp 00000000 00:00 0                                  [heap]
```

I looked for ways to introspect the `glibc` heap and found `malloc_stats(3)`. Sure enough, this revealed the issue:

```
:::console
$ gdb --batch --pid 6 --ex 'call malloc_stats()'
Arena 0:
system bytes     =  157237248
in use bytes     =   82474432
Arena 1:
system bytes     =  245886976
in use bytes     =    4931712
Arena 2:
system bytes     =  191258624
in use bytes     =    3757776
Arena 3:
system bytes     =  187617280
in use bytes     =    1905632
... <snip> 
Arena 63:
system bytes     =  274530304
in use bytes     =    1173504
Total (incl. mmap):
system bytes     = 3299606528
in use bytes     =  645742704
max mmap regions =       1086
max mmap bytes   =  456876032
```

(ignore the total – `glibc` uses a 32bit counter for total bytes which overflowed. The correct sum of each arena `system_bytes` is 14GB)

Turns out these regions are the product of a `glibc` `malloc` feature: [per thread arenas](https://siddhesh.in/posts/malloc-per-thread-arenas-in-glibc.html). An arena is a self contained portion of the heap
from which memory can be allocated; each arena is completely independent of the other arenas. The `glibc` `malloc` implementation attempted to improve performance by allowing all threads to use their own arena (up to a default cap `MALLOC_ARENA_MAX` of 8 arenas per CPU core). When a thread goes to allocate memory, it tries to exclusively lock the arena it allocated from most recently; however, upon failing, the thread will switch to another arena or create a new arena if all arenas are busy. 

For applications with a small number of threads that use `malloc` heavily, this approach works well. Unfortunately, `memsqld` uses `malloc` very sparingly but uses a large number of threads; in this workload, we had managed to induce a pathology where we had 64 malloc arenas that were using only ~1% of about ~200MB of system memory for user data, a huge waste of memory. Fortunately, the "fix" is simple –- we set the maximum number of arenas back down to one per core by setting the `MALLOC_ARENA_MAX` environment variable appropriately.



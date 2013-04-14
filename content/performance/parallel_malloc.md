Title: Analysis of a Parallel Memory Allocator
Date: 2012-05-11
Summary: I implemented and tested different configurations of a modern parallel memory allocator.

# Background #
## Problem ##
Many modern programs frequently use dynamic memory allocation. However, modern
programs increasingly are multithreaded and parallel to take advantage of
increasingly parallel processors. Unfortunately, this trend conflicts with the
fact that there is a single heap in most current programs. Consequently,
research into parallel memory allocators is topical and important.

## Solution? ##
The simplest solution to ensuring correctness in a multithread memory allocator
is to use a global lock around the heap. Unfortunately, this has
<em>extremely</em> negative performance consequences and is almost never 
adopted by modern memory allocators. Modern memory allocators tend to adopt 
some form of the following 3 solutions:
<ul>
<li>
They partition the heap into logical arenas or chunks that handle large 
portions of the heap. This reduces contention on the global heap and 
heap data structures.
</li>
<li>
They use fine grained locking on individual slabs or slab classes.
</li>
<li>
They use thread local caches to provide a fast path that requires no locks.
</li>
</ul>

## Modern memory allocators ###
<p>As I understand, the most popular modern parallel mallocs are 
<a href="https://www.facebook.com/notes/facebook-engineering/scalable-memory-allocation-using-jemalloc/480222803919"><tt>jemalloc</tt></a>, 
<a href="http://goog-perftools.sourceforge.net/doc/tcmalloc.html"><tt>tcmalloc</tt></a>, 
<a href="http://www.malloc.de/en/"><tt>ptmalloc</tt></a>, 
<a href="https://doors.gracenote.com/developer/open.html"><tt>concur</tt></a>, 
<a href="http://www.nedprod.com/programs/portable/nedmalloc/"><tt>nedmalloc</tt></a>
and <a href="http://www.cs.umass.edu/~emery/pubs/berger-asplos2000.pdf"><tt>hoard</tt></a>. 
Oracle did some 
<a href="http://developers.sun.com/solaris/articles/multiproc/multiproc.html">investigation</a> 
and I have taken a look at the internals of jemalloc, tcmalloc, concur, and hoard. 
As I understand:

<ul><li><tt>tcmalloc</tt> uses a global slab allocator with thread local caches to avoid contention</li>
	<li><tt>hoard</tt> uses different arenas and assigns superblocks to threads to avoid contention</li>
	<li><tt>jemalloc</tt> uses different arenas and thread local caches to avoid contention
and uses red black trees and an optimized slab allocator to avoid fragmentation</li>
<li><tt>concur</tt> uses different arenas and fine grained locking on size classes to avoid contention</li>
</ul>
</p>
<p>
One interesting characteristic of many of these memory allocators is that they
all tend to allocate memory from the system in chunks of about 1 to 4MB.
Consequently, they tend to have an overhead of up to 2 to 4MB per arena. Most
of them justify this overhead by pointing out that 2MB of overhead is minimal
when the total application footprint can exceed 1GB (in an application such as
firefox) and it is acceptable for an application to use 2MB of heap when
modern computers routinely have several GB of RAM.
</p>

<p>
Another interesting characteristic of these memory allocators is they almost
never coallesce individual blocks (some do coallesce individual blocks). 
Instead, they use slab allocators and assume
allocation requests tend be of very similar sizes. In general, this follows
the general pattern of tolerating a moderate amount of memory overhead to
increase performance.
</p>

# Approach #
## A simple modern memory allocator ##
<p>
In order to investigate and analyze the performance of a modern memory
allocator, I wrote a simplified memory allocator, <tt>ar_malloc</tt>, that 
uses many of the modern optimizations. <tt>ar_malloc</tt> is based quite
heavily on <tt>jemalloc</tt> but makes some simplifications. In order to keep 
the work manageable, <tt>ar_malloc</tt> makes the assumption that allocation 
requests are smaller than 1024 bytes. In addition, it uses slabs of a fixed 
size and never frees memory to the system (<tt>jemalloc</tt> uses variable sized
slabs to reduce memory overhead).
</p>
## Testing a memory allocator ## 
<p>
In order to test <tt>ar_malloc</tt>, I constructed a test framework (based off a
test in the <tt>tcmalloc</tt> codebase) that spawns 
several threads that each randomly decide to allocate a random sized block or 
free a random block. This does not simulate the effect of actually using the blocks
and does not simulate a realistic workload, but it is still a useful
basis for investigation. I ran this test on a 16 core shared memory system and used
new initialization of malloc for each run to reduce the variance in run time.
</p>

# Results #
## Comparision of <tt>ar_malloc</tt> to other solutions ##
<p>
We compared the performance of <tt>ar_malloc</tt>, <tt>ar_malloc</tt> with a global lock, 
and the libc malloc on the test described in the previous section.
</p>
<figure>
![Run time vs Number of threads](https://docs.google.com/spreadsheet/oimg?key=0AjzaNgu-PE5_dDJJUnRCaXZueks1UTlQVXBxYlFsSXc&oid=4&zx=1aneio5en2km)
<figcaption>This is chart of test run time vs number of threads for a global locked malloc, <tt>ar_malloc</tt>, and libc malloc. As 
	you can see, the global lock solution is really bad.</figcaption>
</figure>

<figure>
	<img src="https://docs.google.com/spreadsheet/oimg?key=0AjzaNgu-PE5_dDJJUnRCaXZueks1UTlQVXBxYlFsSXc&oid=14&zx=rgpgcr33f1ax" />
	<figcaption>This is chart of test run time vs number of threads for <tt>ar_malloc</tt> and libc malloc. As 
	you can see, <tt>ar_malloc</tt> is about 3 times faster than libc for even
	single threaded execution. </figcaption>
</figure>
<figure>
	<img src="https://docs.google.com/spreadsheet/oimg?key=0AjzaNgu-PE5_dDJJUnRCaXZueks1UTlQVXBxYlFsSXc&oid=8&zx=ttz2qtfnzo60" />
	<figcaption>This is chart of test speedup vs number of threads for <tt>ar_malloc</tt> and libc malloc. As 
	you can see, <tt>ar_malloc</tt> exhibits linear speedup that scales cleanly with
	the number of threads, whereas libc scales only to about 8 threads. 
	</figcaption>
</figure>

## Comparison of different configuration ##
<p>
I examined several different configurations of <tt>ar_malloc</tt>, specifically 
focusing on the number of arenas. We attempted to figure out the effect of and 
analyze the behavior of using different number of arenas.
</p>

<figure>
	<img src="https://docs.google.com/spreadsheet/oimg?key=0AjzaNgu-PE5_dDJJUnRCaXZueks1UTlQVXBxYlFsSXc&oid=11&zx=fwaahh94nhlg" />
<figcaption>This is a chart of run time vs number of threads for different configurations of <tt>ar_malloc</tt>.
	As you can see, there appear to be two curves. We will call the lower one the &quot;no contention&quot; curve and the
	upper one the &quot;contention&quot; curve. You can see that the performance of a memory allocator moves from the &quot;no contention&quot;
	curve to the &quot;contention&quot; curve when the number of threads exceeds the number of arenas.
	</figcaption>
</figure>

<figure>
	<img src="https://docs.google.com/spreadsheet/oimg?key=0AjzaNgu-PE5_dDJJUnRCaXZueks1UTlQVXBxYlFsSXc&oid=13&zx=fhdbihufrx4u" />
	<figcaption>
	This is a chart of speedup vs number of threads for different configurations of <tt>ar_malloc</tt>. As you before, there are 
	two curves: the &quot;no contention&quot; line and the &quot;contention&quot; line. Again, the speedup of a memory allocator
	moves from the &quot;no contention&quot; line to the &quot;contention&quot; line when the number of threads exceeds the 
	number of arenas. It is important to note that the speedup is still mostly linear even when the number of arenas is far less
	than number of threads.
	</figcaption>
</figure>

# Conclusion #
Over the course of this project, I have demonstrated that it is feasible to 
write a modern parallel memory allocator that performs quite favorably 
on random workloads. <tt>ar_malloc</tt> makes many simplifying assumptions,
but is just over 2000 lines of code, outperforms libc malloc by a factor
of 3, and demonstrates linear speedup that seems to scale very well with
the number of threads.

# Further Investigation #
<p>
There are several routes for further investigation in parallel memory
allocators.</p>
<p>The exisiting test framework allocates random sizes distributed
uniformly in the range 8, 1024. This almost certainly does not simulate 
realistic memory allocation patterns. An interesting further exploration could
use <tt>ar_malloc</tt> with real programs (either via static linking or LD_PRELOAD) 
or to investigate the actual memory distribution of a general program. 
</p>
<p>This investigation only examined the effect of different number of arenas.
A further exploration could examine the effect of thread local caches and fine
grained locking on the performance of <tt>ar_malloc</tt>.
</p>

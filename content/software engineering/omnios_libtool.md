Title: Compiling with libtool on OmniOS
Date: 2014-04-30
Tags: libtool, omnios

I'm having issues compiling glib2.40.0 (a libtool compiled shared library) on Omnios.

In particular, my shared library has a static initializer that does not get executed by the libtool linked library. I've reduced this to the test case below:

    :::c
    #include <stdio.h>
    
    void __attribute__((constructor)) myctor() {
        printf("in myctor\n");
    }

I can compile with libtool and link with gcc, and get the expected behavior on LD_PRELOAD:

    :::console
    $ libtool --mode=compile gcc -c myctor.c
    libtool: compile:  gcc -c myctor.c  -fPIC -DPIC -o .libs/myctor.o
    $ gcc -shared .libs/myctor.o -o libmyctor.so
    $ LD_PRELOAD=$(pwd)/libmyctor.so ls
    in myctor
    libmyctor.so  myctor.c      myctor.lo

If I link with libtool, I do not get the expected behavior:

    :::console
    $ libtool --mode=link gcc -o libmyctor.la  -rpath /usr/lib myctor.lo
    libtool: link: gcc -shared  -fPIC -DPIC -Wl,-z -Wl,text -Wl,-h -Wl,libmyctor.so.0 -o .libs/libmyctor.so.0.0.0  .libs/myctor.o      -nostdlib -lc
    libtool: link: (cd ".libs" && rm -f "libmyctor.so.0" && ln -s "libmyctor.so.0.0.0" "libmyctor.so.0")
    libtool: link: (cd ".libs" && rm -f "libmyctor.so" && ln -s "libmyctor.so.0.0.0" "libmyctor.so")
    libtool: link: ( cd ".libs" && rm -f "libmyctor.la" && ln -s "../libmyctor.la" "libmyctor.la" )
    $ LD_PRELOAD=$(pwd)/.libs/libmyctor.so.0.0.0 ls
    libmyctor.la  libmyctor.so  myctor.c      myctor.lo

I performed some trial and error experiments with the displayed gcc command invocation, and determined that "-nostdlib" is the flag that causes the constructor to no longer be called:

    :::console
    $ gcc -shared  -fPIC -DPIC -Wl,-z -Wl,text -Wl,-h -Wl,libmyctor.so.0 -o .libs/libmyctor.so.0.0.0  .libs/myctor.o
    $ LD_PRELOAD=$(pwd)/.libs/libmyctor.so.0.0.0 ls
    in myctor
    libmyctor.la  libmyctor.so  myctor.c      myctor.lo
    
    $ gcc -shared  -fPIC -DPIC -Wl,-z -Wl,text -Wl,-h -Wl,libmyctor.so.0 -o .libs/libmyctor.so.0.0.0  .libs/myctor.o      -nostdlib -lc
    $ LD_PRELOAD=$(pwd)/.libs/libmyctor.so.0.0.0
    libmyctor.la  libmyctor.so  myctor.c      myctor.lo

Illumos / Solaris has its own peculiarities for static initializers (<https://blogs.oracle.com/ahl/entry/the_mysteries_of_init> was a helpful blogpost). The ".init" section for the gcc linked library has the expected contents:

    :::console
    $ dis -t .init libmyctor.so
    disassembly for libmyctor.so
    
    
    section .init
    _init()
        _init:      55                 pushl  %ebp
        _init+0x1:  89 e5              movl   %esp,%ebp
        _init+0x3:  83 e4 f0           andl   $0xfffffff0,%esp
        _init+0x6:  83 ec 0c           subl   $0xc,%esp
        _init+0x9:  53                 pushl  %ebx
        _init+0xa:  e8 00 00 00 00     call   +0x0  <_init+0xf>
        _init+0xf:  5b                 popl   %ebx
        _init+0x10: 81 c3 49 00 01 00  addl   $0x10049,%ebx
        _init+0x16: e8 35 ff ff ff     call   -0xcb <frame_dummy>
        _init+0x1b: e8 a0 ff ff ff     call   -0x60 <__do_global_ctors_aux>
        _init+0x20: 5b                 popl   %ebx
        _init+0x21: c9                 leave  
        _init+0x22: c3                 ret   

But the ".init" section for the libtool linked library doesn't exist

    :::console
    $ dis -t .init .libs/libmyctor.so
    disassembly for .libs/libmyctor.so
    
    dis: warning: failed to find section '.init' in '.libs/libmyctor.so'

Digging a bit deeper (and reading that blog post), I see that I need to add `/usr/lib/crti.o` and `/usr/lib/crtn.o`. If I add these to the command line, I get an ".init" section that seems to be only partially complete:

    :::console
    section .init
    _init()
        _init:      55                 pushl  %ebp
        _init+0x1:  89 e5              movl   %esp,%ebp
        _init+0x3:  83 e4 f0           andl   $0xfffffff0,%esp
        _init+0x6:  83 ec 0c           subl   $0xc,%esp
        _init+0x9:  53                 pushl  %ebx
        _init+0xa:  e8 00 00 00 00     call   +0x0  <_init+0xf>
        _init+0xf:  5b                 popl   %ebx
        _init+0x10: 81 c3 31 00 01 00  addl   $0x10031,%ebx
        _init+0x16: 5b                 popl   %ebx
        _init+0x17: c9                 leave  
        _init+0x18: c3                 ret

The problem is that we also need to pass some gcc artifacts (`/opt/gcc-4.8.1/lib/gcc/i386-pc-solaris2.11/4.8.1/crt{begin,end}.o`) to get this to work. If I add all the relevant artifacts, I can get the constructor to behave correctly with `-nostdlib`:

	:::console
	$ gcc -shared -nostdlib -lc -lgcc -lgcc_s /usr/lib/crti.o  /opt/gcc-4.8.1/lib/gcc/i386-pc-solaris2.11/4.8.1/crtbegin.o .libs/myctor.o /opt/gcc-4.8.1/lib/gcc/i386-pc-solaris2.11/4.8.1/crtend.o /usr/lib/crtn.o -o libmyctor.so
	$ LD_PRELOAD=$(pwd)/libmyctor.so ls
	in myctor
	libmyctor.so  myctor.c      myctor.lo
	
Fortunately, this all turns out to be unnecessary - a good spot by Rich Lowe turned up some voodoo in the omnios build infrastructure: the `-nostdlib` was inexplicably added to the libtool options ["glib2 -nostdlib"](https://github.com/omniti-labs/omnios-build/commit/16fdea8b57a52d74876606d6b118b50753603395) (For more fun, check out ["generic libtool unfucking support"](https://github.com/omniti-labs/omnios-build/commit/18800320ec1119aab568efc72f50c3689e30c687)). Removing this allows us to compile our library with the expected behavior.

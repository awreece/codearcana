Title: Statically linking libstdc++
Date: 2015-12-09
Tags: linking, gcc
Summary: In this post, I statically link <code>libstdc++</code> into a <code>configure</code>d library.

I recently found myself wanting to statically link `libstdc++` into a 
library I was compiling and found it to be a surprising challenging process.

## Small example library ##

I first started playing with a small example library:

```
:::c
#include <iostream>

__attribute__((noinline))
void bar()
{
  std::cout << __FILE__ <<  " " << __func__ << std::endl;
}

void foo()
{
  bar();
  std::cout << "Hello" << std::endl;
}
```

Before I even got to statically compiling `libstdc++`, I noticed something
strange: The symbol `bar` was getting resolved through the PLT!

```
:::console
$ gcc -O3 -shared -fPIC foo.cpp -o foo.so
$ gdb foo.so --batch --ex "disas foo"
Dump of assembler code for function _Z3foov:
   0x0000000000000b70 <+0>: push   %rbp
   0x0000000000000b71 <+1>: push   %rbx
   0x0000000000000b72 <+2>: sub    $0x8,%rsp
   0x0000000000000b76 <+6>: callq  0x960 <_Z3barv@plt>
... <snip> ...
```

I played around with a couple of things, and eventualy figured out I could
mark `bar` as having hidden visibility and then it wouldn't use this PLT.

## Static `libstdc++`? ##

`g++` has a command line option `-static-libstdc++` which appears to do
exactly what I want. Unfortunately, the calls to the `libstdc++` symbols 
are resolved via the PLT, as above with `bar`:

```
:::console
$ gcc -static-libstdc++ -O3 -shared -fPIC foo.cpp -o foo.so
$ /tmp% gdb foo.so --batch --ex "disas foo"
   0x0000000000000b21 <+1>: push   %rbx
   0x0000000000000b22 <+2>: sub    $0x8,%rsp
   0x0000000000000b26 <+6>: callq  0xa80 <_Z3barv>
   0x0000000000000b2b <+11>:  mov    0x20049e(%rip),%rbx        # 0x200fd0
   0x0000000000000b32 <+18>:  lea    0x7a(%rip),%rsi        # 0xbb3
   0x0000000000000b39 <+25>:  mov    $0x5,%edx
   0x0000000000000b3e <+30>:  mov    %rbx,%rdi
   0x0000000000000b41 <+33>:  callq  0x930 <_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l@plt>
... <snip> ...
```

I tried to do a cute trick to make all the C++ functions have hidden
visibility:

```
:::c
#pragma GCC visibility push(hidden)
#include <iostream>
#pragme GCC visibility pop
```

Unfortunately, the symbols were *still* resolved via the PLT. What was going on?
Could I force `g++` to just use the symbols in the binary it had a copy of rather
than using the PLT?

## `Bsymbolic-functions` ##

Some deep soul searching lead me to
[a stack overflow post](http://stackoverflow.com/q/7216973) where someone else
had the same questions and talked about a flag that solved this exact problem.
This allowed me to get rid of the visiblity annotation on `bar`, but it still didn't
solve my libstdc++ problem.

```
:::console
$ gcc -static-libstdc++ -Wl,-Bsymbolic-functions -O3 -shared -fPIC foo.cpp -o foo.so
```

I eventually found the real issue: library order during linking. If I manually
specified the `libstc++.a` library as the last library, the symbols would not
be resolved via the plt:

```
:::console
$ gcc -static-libstdc++ -Wl,-Bsymbolic-functions -O3 -shared -fPIC foo.cpp -o foo.so $(g++ $CXXFLAGS -print-file-name=libstdc++.a)
$ gdb foo.so --batch --ex "disas foo"
Dump of assembler code for function _Z3foov:
   0x00000000000422e0 <+0>: push   %rbp
   0x00000000000422e1 <+1>: push   %rbx
   0x00000000000422e2 <+2>: sub    $0x8,%rsp
   0x00000000000422e6 <+6>: callq  0x42240 <_Z3barv>
   0x00000000000422eb <+11>:  mov    0x2756ae(%rip),%rbx        # 0x2b79a0
   0x00000000000422f2 <+18>:  lea    0x518ef(%rip),%rsi        # 0x93be8
   0x00000000000422f9 <+25>:  mov    $0x5,%edx
   0x00000000000422fe <+30>:  mov    %rbx,%rdi
   0x0000000000042301 <+33>:  callq  0x45670 <_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l>
... <snip> ...
```

Specifing this static `libstdc++.a` as a final arg worked with both the
`#pragma GCC visibility push(hidden)` trick and with `-Bsymbolic-functions`.

## In `./configure` ##

I had a `./configure` library that I wanted to build with a static `libstdc++`. Using
what I learned above, this seemed relatively straightforward:

```
:::console
./configure CXXFLAGS="-static-libstc++" LDFLAGS="-Bsymbolic-functions" LIBS="$(g++ -print-file-name=libstdc++.a)"
```

Unfortunately, this didn't work. Using `make VERBOSE=1`, I looked at the
command used to link my library and saw the issue: `make` was calling
`gcc` to link the library rather than `ld` but wasn't wrapping `LDFLAGS`.
I did so manually and got my expected results, a static `libstdc++` where 
none of the symbols were resolved using the PLT. My final `configure`
invocation was:

```
:::console
./configure CXXFLAGS="-static-libstc++" LDFLAGS="-Wl,-Bsymbolic-functions" LIBS="$(g++ -print-file-name=libstdc++.a)"
```

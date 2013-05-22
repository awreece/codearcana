Title: A brief introduction to x86 calling conventions
Date: 2013-05-22
Tags: tutorial
Summary: To support some of my other tutorials, I prepared a brief introduction to x86 calling conventions. 

To support some of my other tutorials, I will provide a brief introduction to x86 calling conventions. This should be considered an *introduction*, not a thorough resource. I encourage you to check out the "Machine Prog" lectures from [the CMU 15-213 course](https://www.cs.cmu.edu/afs/cs/academic/class/15213-s13/www/schedule.html) or an alternative resource. In particular, pages 11-14 of [this lecture](https://www.cs.cmu.edu/afs/cs/academic/class/15213-s13/www/lectures/07-machine-procedures.pdf) are useful. [The wikipedia page](https://en.wikipedia.org/wiki/X86_calling_conventions) is also a useful reference.

# Calling a function #

A computer program[^3] keeps track of two important pointers as it runs: the instruction pointer, which points to the next instruction it will execute, and the stack pointer, which points to the last value pushed onto the stack. In x86, the instruction pointer is the register `%eip` and the stack pointer is in the register `%esp`[^4]. The stack grows down (as values are pushed onto the stack, the stack pointer decreases) and is logically divided into regions, one for each function, called stack frames. 

[^3]: While I hope to stay close the spirit of the truth, I'm about to lie to simplify things. Please forgive me.

[^4]: In x86-64, the instruction pointer and the stack pointer are in the registers `%rip` and `%rsp`, respectively.

When a function is called, the instruction pointer is pushed onto the stack to allow the program to return to the site of the `call` later. Before the `call`, the instruction pointer points to the `call` instruction and the stack pointer points to the last thing pushed (in this case, some garbage value):

~~~
:::objdump
                    code                          |          stack
--------------------------------------------------+----------------------------
%eip => 0x00001f66: call   0x1ef0 <nop_ret>       |      | 0xdeadbeef | <= %esp
        0x00001f6b: movl   $0x0,-0x8(%ebp)        |      |            |
~~~

After the `call`, the instruction pointer points to the first instruction in our function and the stack pointer points to the last thing pushed, the return address from our function:

~~~
:::objdump
                    code                          |          stack
--------------------------------------------------+----------------------------
%eip => 0x00001ef0:	ret                           |      | 0xdeadbeef |
                                                  |      | 0x00001f6b | <= %esp
~~~

In this case, the function does nothing and merely returns. The `ret` instruction pops a value off the stack and into `%eip`. This both increments the stack pointer and returns control flow to the calling function:

~~~
:::objdump
                    code                          |          stack
--------------------------------------------------+----------------------------
        0x00001f66: call   0x1ef0 <nop_ret>       |      | 0xdeadbeef | <= %esp
%eip => 0x00001f6b: movl   $0x0,-0x8(%ebp)        |      |            |
~~~

# Arguments #

When a function needing arguments is called, they pushed onto the stack immediately before the call[^5]. If there is more than one argument, the first argument is pushed on last. The following sequence of operations corresponds to the function call `proj_1(0x5, 0x10)`:

[^5]: In x86-64, the first 6 integer arguments are passed in the registers `%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r9`, and `%r8`. The first 8 floating point arguments are passed in via `%xmm0` through `%xmm7`. Any additional arguments are pushed onto the stack.

~~~
:::objdump
                    code                          |          stack
--------------------------------------------------+----------------------------
%eip => 0x00001f78: pushl  $0x10                  |      | 0xdeadbeef | <= %esp
        0x00001f7a: pushl  $0x5                   |      |            |
        0x00001f7c: call   0x1f90 <proj_1>        |      |            |
        0x00001f81: movl   $0x0,-0x8(%ebp)        |      |            |      
~~~
~~~
:::objdump
        0x00001f78: pushl  $0x10                  |      | 0xdeadbeef |
%eip => 0x00001f7a: pushl  $0x5                   |      | 0x10       | <= %esp
        0x00001f7c: call   0x1f90 <proj_1>        |      |            |
        0x00001f81: movl   $0x0,-0x8(%ebp)        |      |            |      
~~~

~~~
:::objdump
        0x00001f78: pushl  $0x10                  |      | 0xdeadbeef |
        0x00001f7a: pushl  $0x5                   |      | 0x10       |
%eip => 0x00001f7c: call   0x1f90 <proj_1>        |      | 0x5        | <= %esp
        0x00001f81: movl   $0x0,-0x8(%ebp)        |      |            |      
~~~

# Return values #

As you can see, the arguments are above the return address on the stack immediately after the function call. In this case, our simple function returns merely the first argument. The `mov 0x4(%esp), %eax` moves the value 4 above `%esp` into `%eax`. By convention, the return value of a function is in `%eax`.

~~~
:::objdump
                    code                          |          stack
--------------------------------------------------+----------------------------
%eip => 0x00001f90: mov    0x4(%esp),%eax         |      | 0xdeadbeef | 
        0x00001f94: ret                           |      | 0x10       |
                                                  |      | 0x5        |
                                                  |      | 0x00001f81 | <= %esp
~~~
~~~
:::objdump
        0x00001f90: mov    0x4(%esp),%eax         |      | 0xdeadbeef | 
%eip => 0x00001f94: ret                           |      | 0x10       |
                                                  |      | 0x5        |
                                                  |      | 0x00001f81 | <= %esp
~~~
~~~
:::objdump
        0x00001f78: pushl  $0x10                  |      | 0xdeadbeef |
        0x00001f7a: pushl  $0x5                   |      | 0x10       |
        0x00001f7c: call   0x1f90 <proj_1>        |      | 0x5        | <= %esp
%eip => 0x00001f81: movl   $0x0,-0x8(%ebp)        |      |            |   
~~~

# Base pointer #

The base pointer is conventionally used to mark the start of a function's stack frame, or the area of the stack managed by that function. The start of each function has a preamble saves the old base pointer and initializes a new one and the end of each function has epilogue that restores the old base pointer:

~~~
:::gas
my_function:
  push %ebp        # Save the old %ebp.
  movl %esp, %ebp  # Point %ebp to the saved %ebp and the new stack frame.
  
  # Function body.
  
  pop %ebp         # Restore the old ebp.
  ret
~~~

Inside a function, the stack would look like this:

~~~
:::text
| <argument 2>       |
| <argument 1>       |
| <return address>   |
| <old ebp>          | <= %ebp
| <local var>        |
| <local var>        | <= %esp
~~~

# Saving registers #

Inside a function, you can freely use `%eax`, `%ecx`, and `%edx`. However, they are not guaranteed to be persistent across function calls (other functions can use them freely) so you must save them before calling other functions. If you use any other register, you _must_ make sure to save them before you use them and restore them to the original values before you return. Registers you must save before you call a function are called _caller save_ registers. Registers you must save before you can use them in a function are called _callee save_ registers.

# To recap: #

-    `%esp` points to the last thing pushed on the stack.
-    `%eip` points to the next thing to execute.
-    `call <addr>` pushes the current value of `%eip` and changes `%eip` to `<addr>`.
-    `ret` pops the next value off the stack into `%eip`.
-    Arguments are pushed onto the stack before a function call.
-    Immediately after function call, the stack looks like this:

        :::objdump
        | <argument 2>     |
        | <argument 1>     |
        | <return address> | <= %esp

-    The return value of a function is in `%eax`.
-    `%eax`, `%ecx`, and `%edx` are caller save registers. `%ebp`, `%ebx`, `%edi`, and `%esi` are callee save registers.
-    Please read more to learn more!
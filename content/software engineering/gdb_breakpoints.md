Title: gdb breakpoint commands and conditional breakpoints
Keywords: gdb, conditional breakpoint, breakpoint commands
Date: 2015-05-16
 
During my first week at my new job, I had the opportunity to teach some of my new coworkers about `gdb` breakpoint commands and conditional breakpoints. I had a lot of fun teaching these techniques my friends here and thought others might find the story enjoyable as well.
 
## Breakpoint commands
 
The first question I had was: _where is our server doing reads_? To answer this question, I used an often overlooked feature of `gdb`: breakpoint commands. At a high level, these allowed us to run an arbitrary set of `gdb` command automatically when a break point is hit. In my case, I wanted to see what stack trace was causing the reads:
 
```
(gdb) break read
Breakpoint 2 at 0x7ffff7382960: file ../sysdeps/unix/syscall-template.S, line 82.
(gdb) commands
End with a line saying just "end".
>backtrace
>continue
>end
(gdb)
```
 
I put a breakpoint on the `libc` `read` function call and automatically do two things: print the backtrace of the thread that hit the read and then continue execution. The overall effect of this is that `gdb` runs the program as normal but prints a backtrace every time the program reads:
 
```
Breakpoint 1, read () at ../sysdeps/unix/syscall-template.S:82
82 ../sysdeps/unix/syscall-template.S: No such file or directory.
#0  read () at ../sysdeps/unix/syscall-template.S:82
#1  0x00007ffff7324ed8 in _IO_new_file_underflow (fp=0x7ffff76386c0)
    at fileops.c:606
#2  0x00007ffff73265be in _IO_default_uflow (fp=0x0) at genops.c:440
#3  0x00007ffff731da9b in _IO_getc (fp=0x7ffff76386c0) at getc.c:41
#4  0x00007ffff7b6e63d in __gnu_cxx::stdio_sync_filebuf<char, std::char_traits<char> >::underflow() () from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
#5  0x00007ffff7b58c17 in std::istream::sentry::sentry(std::istream&, bool) ()
   from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
#6  0x00007ffff7b59b4b in std::istream::operator>>(int&) ()
   from /usr/lib/x86_64-linux-gnu/libstdc++.so.6
#7  0x0000000000400905 in main ()
```
 
## Conditional breakpoints
 
I also noticed it was opening an interesting file, so I wanted break into a debugger to inspect the program to figure out why. Unfortunately, it opens a _lot_ of files (logs, etc), so I needed a way to filter out only the interesting calls to `open`. To do this, I used `gdb` conditional breakpoints. The example below creates a breakpoint on `open` that only triggers if `/home/alex` is a substring in the filename:
 
```
(gdb) break open if strstr($rdi, "/home/alex")
Breakpoint 1 at 0x7ffff7382770: file ../sysdeps/unix/syscall-template.S, line 82.
(gdb) continue
Breakpoint 1, open64 () at ../sysdeps/unix/syscall-template.S:82
82 ../sysdeps/unix/syscall-template.S: No such file or directory.
(gdb) x/s $rdi
0x400b7c:  "/home/alex/a.out"
```
 
This example takes advantage of two more pieces of `gdb` functionality:

 - `gdb` can call an arbitrary function (in this case, we call the `libc` `strstr` function to compute substring).
 - `gdb` can directly access the values of register and then cast them to common C types (in this case, `$rdi` is the first argument, which we know is a `char *`)
 
## Putting it all together
 
We can use these tricks together to get ad-hoc dynamic tracing of our server!
 
This logs the filename and the stack trace from any open call that isn't to our log directory, but otherwise runs the server as normal:
 
```
(gdb) break open if !strstr($rdi, "/var/log")
(gdb) commands
End with a line saying just "end".
>print/s $rdi
>backtrace
>continue
>end
(gdb) continue
```
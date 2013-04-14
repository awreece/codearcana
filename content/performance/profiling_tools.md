Title: Introduction to Using Profiling Tools
Date: 2013-02-26
Tags: performance, profiling
Summary: In this article, you will see several performance tools used to identify bottlenecks in a simple program.

## Performance tools ##

Frequently, we need to identify slow portions of our programs so we can improve performance. There are a number of tools available to profile programs and identify how much time is spent where. The most common of these tools sample the program periodically, recording information to be later analyzed. Typically, they involve a phase spent recording data and a later phase for analyzing it. We will use two common tools to analyze a simple program: Google `pprof` and Linux `perf`.

### Google `pprof` ###

Google `pprof` is a tool available as part of the Google [`perftools`](https://code.google.com/p/gperftools/) package. It is is used with
`libprofiler`, a sampling based profiler that is linked into your binary. There are 3 steps for using `pprof`: linking it into the binary, generating profile output, and analyzing the output. The following links a binary with `libprofiler`:

    :::console
    % gcc main.c -lprofiler
 
 For any profile linked with `libprofiler`, setting the environment variable `CPUPROFILE` enables profiling and specifies the output file. The following command runs `./a.out` and prints profiling data to `out.prof`:
 
    :::console
    % CPUPROFILE=out.prof ./a.out

We can now analyze this file using `pprof`. Below, we output the sample counts for all the functions in `a.out`:

    :::console
    % pprof --text ./a.out out.prof
    ... <snip> ...
    Total: 311 samples
      144  46.3%  46.3%      144  46.3% bar
       95  30.5%  76.8%       95  30.5% foo
       72  23.2% 100.0%      311 100.0% baz
        0   0.0% 100.0%      311 100.0% __libc_start_main
        0   0.0% 100.0%      311 100.0% _start
        0   0.0% 100.0%      311 100.0% main
         
See full documentation [here](https://google-perftools.googlecode.com/svn/trunk/doc/cpuprofile.html).

### Linux `perf` ###

On Linux, the `perf` system is a powerful tool for analyzing program / system performance. It provides some nice abstractions over tracking hardware counters on different CPUs. It defines a number of events to be tracked and recorded. Run `perf list` to see a list of the events allowed on your system. 

To use `perf`, you run: 
 
    :::console
    % perf stat ./a.out
     Performance counter stats for './a.out':

        3121.725439 task-clock                #    0.997 CPUs utilized          
                 11 context-switches          #    0.000 M/sec                  
                  7 CPU-migrations            #    0.000 M/sec                  
                308 page-faults               #    0.000 M/sec                  
      9,121,960,506 cycles                    #    2.922 GHz                     [83.32%]
      5,213,187,548 stalled-cycles-frontend   #   57.15% frontend cycles idle    [83.32%]
        292,952,401 stalled-cycles-backend    #    3.21% backend  cycles idle    [66.68%]
      5,215,556,086 instructions              #    0.57  insns per cycle        
                                              #    1.00  stalled cycles per insn [83.35%]
      1,303,060,483 branches                  #  417.417 M/sec                   [83.35%]
             66,559 branch-misses             #    0.01% of all branches         [83.33%]

        3.132028707 seconds time elapsed
  
In addition to `perf stat`, there quite a few other ways to use perf. Run 

    :::console
    % perf 

to see a list of the commands (you might want to look into `perf record` and `perf annotate`). 
 
For an example of this being used in real life, see this excellent analysis of  [this analysis of a string comparison bottleneck in `git gc`](http://thread.gmane.org/gmane.comp.version-control.git/172286)
 
## Our Investigation ##
We compile the program with `-lprofiler` so we can generate output to examine. `try_perf.c` is a C program that counts the number of even values
in an array of random numbers. We run with 8 threads that all increment a global
counter every time they see an even number.
 
    :::console
    % gcc try_perf.c -g -lprofiler -lpthread
    % CPUPROFILE=a.out.prof ./a.out --num_threads=8
 
We run pprof and get the source code annotated with the number of probes that 
hit that instruction during the trace (result below trimmed for brevity).

    :::console
    % pprof --list=thread_scan a.out a.out.prof
     ... <snip> ...
       .      .   60: void* thread_scan(void* void_arg) {
       .      .   61:    // TODO(awreece) Copy locally so dont interfere with each other.
       .      .   62:  thread_arg_t* args = (thread_arg_t*) void_arg;
       .      .   63:  size_t i;
       .      .   64: 
     303    323   65:  for (i = 0; i < arg->size; i++) {
       6     10   66:     uint32_t val = arg->input[i];
       6     15   67:   if (val % 2 == 0) {
       9    300   68:     __sync_fetch_and_add(args->evens, 1);
       .      .   69:   }
       .      .   70:  }
       .      .   71: }

The output above is actually misleading: if you look at the assembly (shown below), the instruction immediately after the atomic instruction (the `addq   $0x1,-0x8(%rbp)` after the `lock addq $0x1,(%rax)`) gets excess hits that count towards the for loop when they should probably count towards the atomic instruction.
 
    :::console
    % pprof --disas=thread_scan a.out a.out.prof
     ... <snip> ...
      9    300    68: __sync_fetch_and_add(arg->num_evens, 1);
      4      5      4008a4: mov    -0x10(%rbp),%rax
      1      5      4008a8: mov    0x10(%rax),%rax
      4    290      4008ac: lock addq $0x1,(%rax)
    303    320    65: for (i = 0; i < arg->size; i++) {
    286    287      4008b1: addq   $0x1,-0x8(%rbp)
      1      2      4008b6: mov    -0x10(%rbp),%rax

  
Hrm. Why are we spending a lot of time in `lock addq $0x1,(%rax)`?

To understand this, we will use `perf`. Run: 

    :::console
    % perf stat ./a.out
     Performance counter stats for './a.out':

        5793.307952 task-clock                #    2.157 CPUs utilized          
                589 context-switches          #    0.000 M/sec                  
                 11 CPU-migrations            #    0.000 M/sec                  
              1,974 page-faults               #    0.000 M/sec                  
     16,378,904,731 cycles                    #    2.827 GHz                     [83.37%]
     10,407,719,950 stalled-cycles-frontend   #   63.54% frontend cycles idle    [83.38%]
      8,213,634,448 stalled-cycles-backend    #   50.15% backend  cycles idle    [66.65%]
     12,070,323,273 instructions              #    0.74  insns per cycle        
                                              #    0.86  stalled cycles per insn [83.32%]
      2,428,236,441 branches                  #  419.145 M/sec                   [83.31%]
         67,558,697 branch-misses             #    2.78% of all branches         [83.35%]

        2.685598183 seconds time elapsed

Wow, thats a lot of stalled instructions! The 8 threads are sharing the same counter, generating a lot of memory traffic. We modify the program so they all use their own counter, and then we aggregate at the end (if we do this, we don't need to use the atomic instruction).

    :::c
    size_t counts[nthreads];
    size_t num_evens = 0;

    for (i = 0; i < nthreads; i++) {
         counts[i] = 0;
         args[i].num_evens = &counts[i];
         args[i].input = &inarray[i * (size / nthreads)];
         args[i].size = size / nthreads;
         pthread_create(&threads[i], NULL, thread_scan, &args[i]);
     }   
     for (i = 0; i < nthreads; i++) {
         pthread_join(threads[i], NULL);
         num_evens += counts[i];
     }   

But that didn't seem to help at all! We still spend most of our time on the increment, even though we aren't using an atomic instruction: 

    :::console
    % pprof --list=thread_scan a.out out.prof
    ... <snip> ...
      .      .   60: void* thread_scan(void* void_arg) {
      .      .   61:    // TODO(awreece) Copy locally so dont interfere with each other.
      .      .   62:  thread_arg_t* args = (thread_arg_t*) void_arg;
      .      .   63:  size_t i;
      .      .   64: 
     22     44   65:  for (i = 0; i < args->size; i++) {
     14     25   66:     uint32_t val = args->input[i];
     12     33   67:   if (val % 2 == 0) {
    157    308   68:    *(args->num_evens) += 1;
      .      .   69:   }
      .      .   70:  }
      .      .   71: }

Why could this be? Lets run `perf stat` again and see:

    :::console
    % perf stat ./a.out
     Performance counter stats for './a.out':

          4372.474270 task-clock                #    1.882 CPUs utilized          
                  385 context-switches          #    0.000 M/sec                  
                    9 CPU-migrations            #    0.000 M/sec                  
                1,135 page-faults               #    0.000 M/sec                  
       12,411,517,583 cycles                    #    2.839 GHz                     [83.26%]
        6,270,257,100 stalled-cycles-frontend   #   50.52% frontend cycles idle    [83.33%]
        4,291,405,838 stalled-cycles-backend    #   34.58% backend  cycles idle    [66.78%]
       12,306,996,386 instructions              #    0.99  insns per cycle        
                                                #    0.51  stalled cycles per insn [83.39%]
        2,420,224,187 branches                  #  553.514 M/sec                   [83.40%]
           69,182,448 branch-misses             #    2.86% of all branches         [83.30%]

          2.323372370 seconds time elapsed
         
What is going on now? We *still* have a lot of stalled instructions, but all those counters are different. See?

    :::c
    size_t counts[nthreads];

Oh, they are all on the same cache line - we're experiencing false sharing. Let us use a thread local counter thats on a different cache line for each thread:

    :::c
    void* thread_scan(void* void_arg) {
      thread_arg_t* args = (thread_arg_t*) void_arg;
      size_t i;
      size_t num_evens = 0;

      for (i = 0; i < args->size; i++) {
        uint32_t val = args->input[i];
        if (val % 2 == 0) {
          num_evens++;
        }
      }
      return num_evens;
    }
 
    ... <snip> ...
 
    for (i = 0; i < nthreads; i++) {
      size_t count;
      pthread_join(threads[i], &count);
      num_evens += count;
    }

And then look at the profile:

    :::console
    % pprof --list=thread_scan a.out out.prof
    ... <snip> ...
      .      .   60: void* thread_scan(void* void_arg) {
      .      .   61:    // TODO(awreece) Copy locally so dont interfere with each other.
      .      .   62:  thread_arg_t* args = (thread_arg_t*) void_arg;
      .      .   63:  size_t i;
      .      .   64:  size_t num_evens;
      .      .   65: 
    144    292   66:  for (i = 0; i < args->size; i++) {
     14     25   67:     uint32_t val = args->input[i];
     12     33   68:   if (val % 2 == 0) {
     13     16   69:    num_evens++;
      .      .   70:   }
      .      .   71:  }
      4      8   72:  return num_evens;
      .      .   73: }

Good, our increment doesn't dominate the function anymore. We look at `perf stat` and see:

    :::console
    % perf stat ./a.out
     Performance counter stats for './a.out':

        2977.781539 task-clock                #    1.472 CPUs utilized          
                177 context-switches          #    0.000 M/sec                  
                 12 CPU-migrations            #    0.000 M/sec                  
              3,506 page-faults               #    0.001 M/sec                  
      8,523,367,658 cycles                    #    2.862 GHz                     [83.32%]
      2,057,253,537 stalled-cycles-frontend   #   24.14% frontend cycles idle    [83.26%]
        919,272,160 stalled-cycles-backend    #   10.79% backend  cycles idle    [66.70%]
     12,067,358,492 instructions              #    1.42  insns per cycle        
                                              #    0.17  stalled cycles per insn [83.42%]
      2,454,951,795 branches                  #  824.423 M/sec                   [83.42%]
         67,544,262 branch-misses             #    2.75% of all branches         [83.42%]

        2.022988074 seconds time elapsed
     
Ah, perfect! 30% faster than our original solution and significantly fewer stalled instructions.


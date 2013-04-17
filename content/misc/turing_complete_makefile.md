Title: CS Theory with Make
Date: 2012-03-05
Tags: make, theory
In this post, I play around with some make functions and eventually provide a constructive proof that the make syntax is turing complete via reduction to μ-recursion.

First, we have to construct numbers. I used the representation of numbers as
unary strings of the character `0`: ie, the number 4 is represented by `0000`
(zero being the empty string). We can also compute the successor of a number:

~~~~
:::make
# If this is called as a make function, $(1) will be replaced with the first
# function argument.
successor = O$(1)

$(info $(call successor,O))  # Outputs 'OO'
~~~~

Life is a lot easier if we can compute predecesser. Luckily, this is pretty
easy for us too:

~~~~
:::make
monus_one = $(patsubst O%,%,$(1))

$(info $(call monus_one,OO))  # Outputs '0'
~~~~

Now lets actually do computation with this. It is hideous, but we can actually
compute fibonacci numbers in make:

~~~
:::make
fib = $(if $(1),$(if $(call monus_one,$(1)),$(call fib,$(call \
  monus_one,$(1)))$(call fib,$(call monus_one,$(call monus_one,$(1)))),O),O)
~~~

Let me try to break this up a bit. I'll add comments but it will no longer be
valid make.
~~~
:::make
# fib (n):
fib = $(if $(1), # If n > 0:
          $(if $(call monus_one,$(1)), # if n - 1 > 0:
              # return fib(n-1) + fib(n-2)
              $(call fib,$(call monus_one,$(1)))$(call fib,$(call monus_one,$(call monus_one, $(1))))
          ,O) # else: return 1
      ,O) # else: return 1
~~~

This is pretty fun and all, but we haven't actually done anything that we
couldn't do with a primitive recursive function. We can easily show that make
is more powerful than primitive recusion by encoding the [Ackerman
function](https://en.wikipedia.org/wiki/Ackermann_function).

~~~
:::make
ack = $(if $(1),$(if $(2),$(call ack,$(call monus_one,$(1)),$(call \
  ack,$(1),$(call monus_one,$(2)))),$(call ack,$(call monus_one,$(1)),O)),$(2)O)
~~~

All right, so how far can we take this? As it turns out, there is a class of
functions that are computable only by a turing complete language:
[µ-recursive 
functions](https://en.wikipedia.org/wiki/%CE%9C-recursive_function). They are
the primitive recursive functions with the addition of the minimization (µ)
operator: µ of f(x) is the minimum x such that f(x)=0. As it turns out, we can
encode this operator in make:

~~~~~
:::make
# muh f x returns the first number greater than or equal to x such
# that f(x) is true.
muh = $(if $(call $(1),$(2)),$(2),$(call muh,$(1),O$(2)))

# mu f returns the first number greater than or equal to 0 such
# that f(x) is true.
mu = $(call muh,$(1),)
~~~~~

Wow! There we have it, make is turing complete. As a final piece of fun, here
is the inverse ackerman function:

~~~~~
:::make
not = $(if $(1),,O)

# lesseq_template n creates a function lesseq_y that returns y < x
define lesseq_template
  lesseq_$(1) = $$(findstring $$(1),$(1))
endef

# geack_template y creates a function geack_y that returns ack(x) > y
define geack_template
  geack_$(1) = $(eval $(call lesseq_template,$(1)))\
	$$(call not,$$(call lesseq_$(1),$$(call ack,$$(1),$$(1))))
endef

# invack n: Find the first value x such that ack(x) > n.
invack = $(eval $(call geack_template,$(1)))$(call mu,geack_$(1))
~~~~~

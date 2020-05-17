Title: TCP Keepalive is a lie
Date: 2015-08-28
Tags: tcp, linux, networking, perf_events

In the past few months, I’ve had to debug some gnarly issues related to TCP_KEEPALIVE. Through these issues, I’ve learned that it is harder than one might think to ensure that your sockets fail after a short time when the network is disconnected. This blog post is intended to serve as a cautionary tale.

## What is TCP_KEEPALIVE and how are we using it?

TCP_KEEPALIVE is an optional TCP socket option (disabled by default) intended to prevent servers from (RFC1122, p102):

> [hanging] indefinitely and [consuming] resources unnecessarily if a client crashes or aborts a connection during a network failures

When a socket has the option enabled, it will send an empty TCP packet with the ACK bit set after it has been idle for a time period to probe the connection. If that probe is not acknowledged in a short amount of time, additional probes will be sent until one is acknowledged or the connection is determined to be disconnected. TCP_KEEPALIVE is disabled by default and configured with [3 parameters in Linux](http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/usingkeepalive.html):

 - `tcp_keepalive_time`, the time in before the first probe is sent (default 2 hours)
 - `tcp_keepalive_intvl`, the time between probes / how long to wait for a response (default 75 seconds)
 - `tcp_keepalive_probes`, the number of additional probes to send before failing the connection (default 9)

We enable TCP_KEEPALIVE on our replication sockets because we want to stop replicating when a leaf is unresponsive. Our replication sockets are bi-directional: the master sends the slave new log records every time a transaction is committed and the slave tells the master when it has also committed them. It is important to quickly detect a failed node because we delay transactions on the master if the slave is too far behind. Elsewhere in memsql, we detect failed leaves with a heartbeat that pings every leaf every 10s and fails them if they have not responded after 3 attempts (i.e. after 30 seconds). We configured replication sockets to behave similarly by setting `tcp_keepalive_time` and `tcp_keepalive_intvl` to 10 seconds `tcp_keepalive_probes` to 2 probes (i.e. disconnect after 30 seconds)

## Why isn't TCP_KEEPALIVE working?

The first issue I investigated was that our replication sockets were not disconnecting properly during network failures. I induced a network failure using an `iptables` firewall that dropped all packets between the master and a slave. Surprisingly, the master did not fail the slave, even after several minutes had passed. The reason for this was confusing -- the replication socket was still active!

This behavior was very strange to me, as I would have expected TCP_KEEPALIVE to have disconnected the socket. I dug a little deeper using netstat and saw that the sockets weren't even in the keepalive state.

At this point, I suspected a programmer bug and installed a [custom kernel module](https://github.com/veithen/knetstat) to check the socket options on the socket. Sure enough, TCP_KEEPALIVE was enabled.

I decided to monitor the state of the the socket immediately after I triggered the network failure and I noticed something peculiar: it actually entered the keepalive state after 10 seconds but switched back to the "on" state shortly after.

What could cause a socket to leave keepalive? Some despondent googling eventually lead me to an an answer: a socket can only be in the keepalive state if it is idle. If there is outstanding data, the socket will be in the on state as it transmits/retransmits the data. A thread on the master was managing to commit a transaction and send a log record to the replication socket, knocking it out of the state keepalive as it tried (unsuccessfully) to retransmit the data to the slave. How long will the socket remain open as we send our packets into the void? Thats controlled by the `tcp_retries2` tunable in Linux:

	tcp_retries2 (integer; default: 15; since Linux 2.2)
		      The maximum number of times a TCP packet is retransmitted in
		      established state before giving up. The default value is 15,
		      which corresponds to a duration of approximately between 13 to
		      30 minutes, depending on the retransmission timeout. The
		      RFC 1122 specified minimum limit of 100 seconds is typically
		      deemed too short.

So our socket was stuck uselessly retransmitting packets and wasn't getting disconnected for half an hour! Unfortunately it [appears](http://stackoverflow.com/a/5907951/447288) that it is not possible to set `tcp_retries2` on a per socket basis, but we can use a different socket option. If the TCP_USERTIMEOUT option is set on a socket, the socket will automatically disconnect if transmitted data is not acknowledged within that many seconds. We set it to 30 seconds to match the our heartbeat logic.

## TCP_KEEPALIVE is super effective!

Now that our sockets were properly terminating during network failures, we started noticing another perplexing issue. In some environments, we saw connections time out after -1 seconds (i.e. with an infinite timeout set). 

> Leaf error: timed out from socket after -1 seconds

We managed to set up a cluster on EC2 that could reproduce the issue by performing 100 simultaneous full table scans, each of which took over a minute to iterate over a many gigabyte linked list. Our logs showed that a non-blocking `recv` syscall was failing with ETIMEDOUT. This type of failure can only occur if a socket fails due to a timeout (e.g. TCP_KEEPALIVE or a retransmission timeout).

I took a quick stock of our system, following Brendan Gregg’s [USE method](http://www.brendangregg.com/usemethod.html). Each leaf had many gigabytes of free memory and there was no disk activity. The CPUs on the leaves were 100% utilized running the full table scans and the load average was quite high (~2400) because each table scan used many CPU-bound threads. The network was very under-utilized (~5KB/s and ~10 packets/s according `nicstat`) and there were no TCP retransmissions during the connection failures.

Since CPU was the only interesting resource, I focused on it. Could user processes somehow be starving the kernel of CPU and preventing it from responding to keepalive packets? I spent some time reading about how Linux handles interrupts after I saw the `ksoftirqd` process executing. Linux splits interrupts[^1]into two parts: the hardware interrupt that does very little work and a “soft” interrupt that handles the interesting logic. Most of the time these “soft” interrupts are handled immediately before returning from the kernel after the hardware interrupt; however, Linux restricts the number of “soft” interrupts that can be processed at a time to prevent interrupts from starving user traffic. Remaining “soft” interrupts can be processed by the `ksoftirqd` process which runs at the same priority as the default user processes. Could user threads (e.g. `memsqld`) be starving `ksoftirqd`?

[^1]: For more information on the networking stack, see the excellent packagecloud.io blog posts on the Linux networking stack for [`send`](https://blog.packagecloud.io/eng/2017/02/06/monitoring-tuning-linux-networking-stack-sending-data/) and [`receive`](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/).

The theory went like this: since the Linux scheduler[^2] executes processes of the same priority in round robin fashion and uses a default time slice of 100ms, a run queue of 2400 constitutes a 10 second scheduler latency! If the ksoftirqd processes were only getting scheduled every 10s, then we wouldn’t be responding to the TCP keepalive requests in time. To confirm or deny this theory, I measured the scheduler latency of the `ksoftirqd` processes using `perf sched`. Unfortunately, their maximum scheduler latency was measured in _milliseconds_, firmly disproving the theory.

[^2]: For more information on the internals of the Linux scheduler, see [this fantastic survey paper](https://tampub.uta.fi/bitstream/handle/10024/96864/GRADU-1428493916.pdf) by Nikita Ishkov.

I started using wireshark to examine the network traffic and noticed something fishy: _all_ of the keepalive packet’s were getting sent at the same time. I had an eureka moment: enabling TCP_KEEPALIVE with static timers on all connections meant that all connections fired their keepalive timers at the same time, leading to momentary network congestion and packet drops. Once I understood the issue, it was easy to suggest some fixes: add some jitter to the timers and make sure the `tcp_keepalive_intvl` was relatively prime to `tcp_keepalive_time`. Both of these ensure that keep alive probes on multiple connections won't fire in lockstep.

## Takeaways

TCP is a protocol that has a lot of features built into it, but resiliency to network partitions is not one of them. Properly tuning TCP to close connections in the face of network partitions is challenging and understanding what is going on is even harder.  Despite these challenges, TCP_KEEPALIVE can be configured to live up to its goal of aborting connections during network failures.

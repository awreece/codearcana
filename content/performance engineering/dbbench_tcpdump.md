Title: Fast query log with tcpdump and tshark
Date: 2016-07-21
Tags: Linux, tcpdump, wireshark, dbbench

[`dbbench`](http://blog.memsql.com/dbbench-active-benchmarking/) is a tool I've been working on for a while at MemSQL. It is an open source database workload driver engineers at MemSQL and I use for performance testing. One often-overlooked feature in `dbbench` is the ability to replay query log files. Previously, this was a somewhat manual process; however, I recently figured out how to generate a `dbbench` compatible query log file from a `tcpdump` packet capture.

Make sure to filter for only packets *to* this host and only packets *to* `memsql`:

```
:::console
$ sudo tcpdump -w - 'dst net 172.16.134.129 and tcp port 3306' | \
    tshark -Y 'mysql.command == query' -Tfields -e 'frame.time_epoch' -e'mysql.query' -r - -Eseparator=, | \
    awk -F, -v OFS=, '{ $1=int($1 * 1000000); print}'
```

This generates a `dbbench` compatible query log file:

```
:::csv
1469147706082709,select @@version_comment limit 1
1469147706083398,SELECT DATABASE()
1469147706084257,select database()
1469147706084701,select 1+1
1469147706085110,select 'alex'
```

If you see packet drops, you can try to filter mysql queries in the kernel:

```
:::console 
$ sudo tcpdump -w - 'dst net 172.16.134.129 and tcp port 3306 and tcp[36] == 3' | \
    tshark -Tfields -e 'frame.time_epoch' -e'mysql.query' -r - -Eseparator=, | \
    awk -F, -v OFS=, '{ $1=int($1 * 1000000); print}'
```

This is a bit spooky, because the tcp header length can actually change a bit (e.g. if special tcp options are used).[^1]

[^1]: Is it possible to filter on `tcp.data[]` in the `tcpdump` syntax? I'll buy a (root)beer for anyone who shows me how.

You can also capture the packets into a pcap file and process them elsewhere if you want:

```
:::console
$ cat out.pcap | tshark -Y 'mysql.command == query' -Tfields -e 'frame.time_epoch' -e'mysql.query' -r - -Eseparator=, | \
    awk -F, -v OFS=, '{ $1=int($1 * 1000000); print}'
```

Note you can use `frame.time_relative` if you want; then the timestamps for each query will be relative to the start of the file. 
Title: Why are builds on HGFS so slow?
Date: 2015-12-04
Tags: profiling, vmware, make
Summary: We use flame graphs to identify that hgfs is the bottleneck in my build.

## My configuration ##

I work at a company whose product builds and runs exclusively on Linux.
Like most sane people, I prefer to live in a more user-friendly operating
system and my laptop runs Mac OSX. To build my company's product, I use
VMWare Fusion to run an Ubuntu 14.04 virtual machine. I use a local GUI to
edit and search source code, only using the virtual machine to compile
and test the built product. 

Until recently, I kept the files on my virtual machine in sync
with the files on the host machine by using VMWares hgfs kernel module,
which allows a guest to access files on the host (and vice versa).
This configuration causes me no end of grief -- the open-vm-tools ubuntu
package does not include hgfs so I have to manually compile and install
VMWare's tools. This sometimes
[breaks](https://github.com/rasa/vmware-tools-patches/issues/29) and needs
to be recompiled every time I update my kernel.

## HGFS performance issues ##

On top of this, the VMWare HGFS has some serious performance issues.
Yesterday, I got fed up with the fact that my incremental builds were
slower than my colleagues and started doing a performance investigation.
An incremental build in which _no_ files were changed after a successful
build took almost 10 seconds. I noticed my system had incredibly high
CPU utilization and generated a
[Flame Graph](http://www.brendangregg.com/flamegraphs.html):

![make using hgfs](|filename|/images/make_using_hgfs.svg "`mutex_spin_owner` is at the top of every filesystem access")

I was amazed -- all the HGFS stacks were spending time blocked in
`mutex_spin_on_owner`. It looks like all file accesses have
to go through a filesystem-wide global lock!

    :::c
    int
    HgfsTransportSendRequest(HgfsReq *req)   // IN: Request to send
    {
        HgfsReq *origReq = req;
        int ret = -EIO;
                                                                                        
        ASSERT(req);                                                                    
        ASSERT(req->state == HGFS_REQ_STATE_UNSENT);                                    
        ASSERT(req->payloadSize <= req->bufferSize);                                    
                                                                                        
        compat_mutex_lock(&hgfsChannelLock); 


Once I realized this horrible performance pathology, I knew I couldn't use
VMWare HGFS anymore. I set up Mac OSX to share the directory over nfs:

    :::console
    $ # Only share on the vmnet8 subnet and map all accesses to be my user.
    $ echo "/Volumes/Developer -network 172.16.134.0 -mask 255.255.255.0 -mapall=areece" | sudo tee -a /etc/exports
    $ sudo nfsd update

and mounted the directory on Linux:

    :::console
    $ echo "172.16.134.1:/Volumes/Developer /mnt/Developer nfs" | sudo tee -a /etd/fstab
    $ sudo mount 172.16.134.1:/Volumes/Developer

This cut my build times down to 1s, almost 10x faster. Here is the revised Flame Graph:

![make using nfs](|filename|/images/make_using_nfs.svg "Much less time is spent when using NFS")

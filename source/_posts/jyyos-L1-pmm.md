---
title: jyyos-L1-pmm
date: 2024-07-21 15:44:49
tags:
---

# L1-pmm 实验报告

## 设计

考察来自真实操作系统的workload的三个性质：

大量、频繁的小内存分配/释放；其中绝大部分不超过 128 字节；

较为频繁的，以物理页面大小为单位的分配/释放 (4 KiB)；

非常罕见的大内存分配。

所以，我们的内存分配器需要既能满足分配大内存的要求（减少碎片），又能快速分配小内存。参考linux内核，采用buddy system+slab的实现。

buddy system管理一系列连续$2^i$个页的空间。slab管理一系列固定大小的小内存缓存池。

### kalloc

`kalloc`依据要分配的大小选择从buddy system中分配还是从slab中分配。当分配的大小比较大，`kalloc`调用buddy system的分配页接口直接分配相应的页。

否则，`kalloc`获取要分配的小内存大小对应的slab cache，并尝试从中直接分配小内存。

### buddy system

参考linux的页表项，在heap中预留了一小块空间，专门用来存放每页的meta data。然后将剩下的heap分为一系列$2^i$页的块，并保证对齐。

### slab

使用`kmem_cache_t`类型的结构来管理小的`slab`。每个小内存大小(32B, 64B, 128B, ...)都有自己的`kmem_cache_t`对象。`kmem_cache_t`可以从buddy system获得和删除页来构建`slab`。一个`slab`中存储了元数据和一系列大小相同的可用内存块。在每个可用内存块中都存储下一个可用内存块的地址。即`slab`中可用内存块构成链表结构。`kmem_cache_t`还为每个cpu都准备了`cpu_cache`。小内存的分配和释放优先从`cpu_cache`中进行，无需加锁。`cpu_cache`的内存块过多时再加锁向`kmem_cache_t`调整。

## 印象深刻的bug

### buddy system的初始化

教科书上的资料只介绍了buddy system应用于$2^i$大小内存时的原理。但是，heap的大小并不刚好是$2^i$。如果只考虑$2^i$大小，会造成极大的浪费。问题在于如何将heap分成一系列大小为$2^i$页的块并同时保证对齐。

一开始想利用heap大小的二进制表示来直接划分heap，但是难以满足对齐要求。后来参考linux kernel的实现，`addr`从页对齐的第一个地址开始，不断将heap按照`addr`划分出最大能对齐的连续页( $order=\log_2(addr/PAGE\_SIZE)$ )，然后释放这些连续页，让buddy system的释放逻辑来完成合并（这在释放逻辑实现正确的前提下是可行且一定正确的）。从而实现尽可能少浪费空间的对齐。

---
title: jyyos-L2-kmt
date: 2024-07-21 15:45:34
tags:
---

# L2-kmt 实验报告

## 设计

### spinlock

基本参考xv6的实现。最大的收获是关中断需要考虑锁的嵌套，只有当当前cpu不持有任何自旋锁时才能将中断恢复。

### semaphore

信号量实际上可以视为互斥锁的泛化。根据OSTEP对信号量的定义：

- P操作：将值减一，如果减少后值小于0，阻塞当前线程

- V操作：将值加一，如果有线程在等待当前信号量，唤醒其中一个

实现的信号量有四个成员：`value`,`name`,自旋锁`lock`和链表头`wait_list`。

使用自旋锁保护对信号量内部的访问，用链表保存正在等待当前信号量的线程。阻塞线程通过修改线程结构体的状态实现。

### task_t相关操作实现

操作系统是状态机的管理器。一个task在kernel内就只是一个数据结构。因此，`kmt_create`和`kmt_teardown`唯一的工作是构造和析构作为数据结构的`task_t`，

不涉及调度和运行，实现难度较低。`os_trap`和`os_on_irq`基本按照实验指南实现。L2中，个人认为实现难度最大的是调度程序`kmt_schedule`。

## 印象深刻的bug

### 对线程状态的错误assertion

最开始假设cpu当前执行流的状态一定是`running`。导致了错误的assertion:`assert(current->state==running)`。但是后来发现，当一个线程调用`sem_wait`并被阻塞但没有执行到`yield`前，当前执行流确实处于`blocked`状态。

### idle线程导致thread starvation

最开始的idle线程是一个简单的死循环：`iset(true) while(1);`。生产者-消费者测试也能正常工作，但oj上显示thread starvation。后来将`while(1);`改为`while(1){yield();}`后顺利通过。原因应该是最开始的idle线程没有进行主动`yield`，只能依靠时钟中断切换线程，导致生产者-消费者线程需要等待较长时间才能被调度执行。

### 隐蔽的栈数据竞争

第一次实现完成后，在1 cpu下工作完全正常，但在多cpu下总是触发大量assertion，检查实现和debug都无法找到原因。后来查阅AM文档对CTE的说明，发现trap会借用当前执行流的栈。

在trap时，当前执行流的栈会依次压入`context`->`...`->`os_trap`的栈帧。当`os_trap`返回`Context*`后，cpu会在`...`的栈帧内进行换栈等一系列操作。假设这样一个情况：CPU0运行task A，CPU 1运行task B。随后的调度决定让CPU0和CPU1交换它们的task，即让CPU0运行task B，让CPU1运行task A（这是很有可能发生的）。假设CPU1率先借用task B的栈切换到了task A，但CPU0还没有完成切换到task B的工作，即CPU0还在task A的栈上执行。此时CPU0和CPU1同时运行在task A的栈上。CPU1很有可能破坏CPU0在栈上存储的用于换栈的信息，导致CPU0产生未知行为。即CPU0和CPU1在task A的栈上发生了数据竞争。这个数据竞争极其隐蔽，如果不是RTFM和依靠一点运气很难发现。

栈数据竞争引出了重要的一条实现要求：永远不要调度一个cpu的当前执行流。可以通过禁止调度程序调度所有cpu的当前task实现。即为task增加一个`disabled`标志位，标志是否禁止调度。在`kmt_context_save`被调用时，（`kmt_context_save`在trap中总是第一个被调用），就设置当前task的`disabled`位为`true`。在调度程序`kmt_schedule`中，会忽略所有设置了`disabled`位的task。只有在确保已经从task A切换到task B后，才能将task A的`disabled`位清空，重新允许调度。而我们知道，当task B陷入trap后，一定代表已经切换到了task B。通过在`task_t`中增加`prev`成员追踪此task是从哪个task调度来的，并在`kmt_context_save`中将`prev`的`disabled`位清空，就可以实现`disabled`位的还原。

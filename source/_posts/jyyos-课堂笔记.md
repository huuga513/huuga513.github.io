---
title: jyyos-课堂笔记
date: 2024-07-21 16:29:15
tags:
---
# 并发
## 互斥
### 宽松内存模型 
在计算机体系结构中，宽松内存模型（Relaxed Memory Consistency Model）是一种允许对内存操作进行更多重排序的内存模型，以提高处理器执行指令的性能。这种模型相对于严格的内存模型（如顺序一致性模型）提供了更大的灵活性，允许处理器和编译器对读写操作进行更多的优化，但同时也增加了编程的复杂性，因为程序员需要额外的同步机制来保证内存操作的可见性和顺序性。

对于X86_64架构，其内存模型通常被认为是TSO（Total Store Ordering），这是一种允许STORE和LOAD操作重排序的模型，但所有的STORE操作在到达内存时保持了程序中的顺序。这意味着，尽管LOAD操作可能会在STORE操作之前执行，但任何处理器上的未来的读操作都会看到STORE操作的效果，直到它被后续的STORE操作覆盖。

ARM架构的内存模型则更加灵活，它允许更广泛的内存操作重排序。在ARMv7及以前的版本中，内存模型包括了Strongly Ordered、Device和Normal类型，而在ARMv8中，内存模型主要分为Normal memory和Device memory。Normal memory允许对内存访问进行重排序，而Device memory则不允许对访问进行重排序。ARMv8引入了更复杂的内存顺序和屏障指令，以支持更高效的多处理器同步。

总的来说，X86_64的内存模型相对严格但仍允许一定程度的重排序，而ARM的内存模型则提供了更宽松的内存访问顺序和更丰富的内存屏障指令，以适应不同的硬件和软件需求。
### C语言知识
`__attribute__((constructor))` 是 GCC 编译器的一个特性，用于在 C 或 C++ 程序中定义特殊的函数，这些函数会在程序的 `main()` 函数执行之前被自动调用，即在程序的启动阶段。它通常用于执行一些程序初始化操作，比如资源分配、设置全局状态、初始化静态变量等。

这个属性可以用来修饰任何函数，使其成为构造函数（constructor）。构造函数会在程序开始运行时，且在调用 `main()` 函数之前执行。这确保了在程序的主体部分开始执行之前，所有必要的初始化工作都已完成。

下面是一个简单的示例，展示了如何使用 `__attribute__((constructor))`：

```c
#include <stdio.h>

__attribute__((constructor)) void init(void) {
    printf("Initialization function called before main.\n");
}

int main() {
    printf("Program is running.\n");
    return 0;
}
```

在这个例子中，`init` 函数被定义为一个构造函数。当你编译并运行这段代码时，输出将会是：

```
Initialization function called before main.
Program is running.
```

这表明 `init` 函数在 `main()` 函数之前被调用。

值得注意的是，构造函数的调用顺序是按照它们在程序中出现的顺序，从上到下进行的。如果有多个构造函数，它们将按照在源代码中定义的顺序依次执行。

此外，与构造函数相对的概念是析构函数（destructor），在 C++ 中使用 `__declspec(dllexport)` 或者在 C++11 及以后版本中使用 `atexit()` 函数来注册，而在 C 中通常不使用析构函数，因为 C 语言本身不支持析构函数的概念。不过，可以通过 `__attribute__((destructor))` 实现类似的功能，但这种用法不是标准 C 语言的一部分，而是 GCC 编译器的扩展。

### 自旋锁
自旋锁的实现：

以原子交换int xchg_atomic(int* addr, int val)为基本操作，该函数原子地用val替换addr中的值，并返回addr中的原值。
```C
// 假设这是提供的原子交换函数
int xchg_atomic(int* addr, int val) {
    // 原子交换操作的实现会依赖于具体的硬件指令
    // 这里只是一个示例，实际实现需要根据平台进行优化
    int old_val = *addr;
    __asm__ volatile (
        "xchg %0, %1"
        : "+r"(val) // 约束：输入和输出
        : "m"(*addr) // 约束：内存操作数
        : "memory" // 效果：内存屏障
    );
    return old_val;
}

// 自旋锁结构体
typedef struct spinlock {
    volatile int locked; // 使用volatile关键字以避免编译器优化
} spinlock_t;

// 初始化自旋锁
void spinlock_init(spinlock_t* lock) {
    lock->locked = 0;
}

// 锁定自旋锁
void spinlock_lock(spinlock_t* lock) {
    while (xchg_atomic(&(lock->locked), 1)) {
        // 如果xchg返回1，说明锁已被其他线程持有，当前线程需要自旋等待
    }
}

// 解锁自旋锁
void spinlock_unlock(spinlock_t* lock) {
    xchg_atomic(&(lock->locked), 0);
}
```
#### OS kernel中的自旋锁
在操作系统内核中，自旋锁+中断可能导致死锁：

刚上锁就中断

自旋锁一个线程获取自己已经持有的锁会导致死锁

应用程序只需要自旋就可以实现自旋锁（中断处理程序不可能试图获取这把锁，试图获取的都是内核里的锁）

内核中需要自旋和关中断才能正确实现自旋锁

RCU！！

### 互斥锁

程序代码分两类：计算和syscall

锁放到kernel中：acquire锁失败就直接切换线程，避免浪费。并把此线程标记为等待，直到锁unlock解除标记。实现仍是spin lock
->mutex lock

- 互斥锁：当一个线程尝试获取一个已经被其他线程持有的互斥锁时，该线程会被阻塞（即进入睡眠状态），直到锁被释放。这意味着线程会放弃CPU，直到它能够获取到锁。

- 自旋锁：当一个线程尝试获取一个已经被其他线程持有的自旋锁时，该线程会进入一个忙等待（自旋）状态，不断检查锁的状态，直到锁被释放。这意味着线程不会放弃CPU，而是在循环中消耗CPU时间。

性能优化：不用每次都陷入kernel， 尽量在用户态。成功直接交换不进入kernel，失败syscall `system_await`请求暂停自己（让os帮自己实现自旋）。

**任何时候希望访问共享内存都要上锁**，并不是必要的，但是无锁并发正确性是很微妙的。

# 同步
协调线程的行为

## 最简单的例子
所有人在演奏音乐，指挥每打一个拍子演奏一个音符。如何同步所有人的行为？

> 并发控制：控制流聚拢-发散-聚拢

所有人演奏完第$n$拍-任意混乱演奏第$n+1$拍-所有人演奏完第$n+1$拍。

### 怎么做？
1. 先到先等
   自旋等待同步条件达成。

2. Producer-Consumer
   Producer: buffer有空位，则放入，否则等待

   Consumer：buffer有数据，则取走，否则等待

   注意：生产者和消费者应用不同的条件变量：生产者要能唤醒至少一个消费者，消费者要能唤醒至少一个生产者

   例题：并发实现两个线程$T_1, T_2$，$T_1$打印左括号，$T_2$打印右括号，任何时候打印都是合法括号序列前缀，且括号嵌套深度不超过$n$

   我们还是可以用自旋不断访问条件变量判断是否成立，这是正确的。但是在条件不满足时cpu会空转，浪费性能。

   条件变量法：任何问题只要能找到条件变量，都可以用条件变量法解决。
    - 总是在检查变量时获得锁
    - 总是在唤醒后再次检查同步条件：always use while
    - 可以唤醒所有潜在可能被唤醒的人 : broadcast

    满足时执行，不满足等待

    万能同步法：条件变量
   ```C
   mutex_lock(&lk);
   while (!condition){ //while 很重要，不能if
    cond_wait(&cv, &lk); //条件不满足释放互斥锁并进入等待状态，唤醒直接返回，条件满足获得互斥锁。
   }
   cond_broadcast(&cv); //试图唤醒所有用这个条件变量的。（任何改变共享世界的行为都会让所有人检查自己的条件）
   ```

   例题：打印小鱼$T_1,T_2,T_3$，每个线程能做的事只有死循环打印"<",">","_"。要求同步线程打印"<><\_"或"\_><>"

   打印"<",">","_"的条件是什么？

   状态机！

## 信号量
仍是演奏音乐的例子。能否如此实现？为每个线程创建一个锁，初始时都锁上。指挥家在每个节拍结束时释放所有锁，演奏家只有获得自己的锁才能演奏。这样是否就实现了同步？

另一个例子：计算lcs：每个节点只有获得了所有入边的锁才能执行计算。

很自然的就能实现计算图的同步。

信号量是一小球数，V往口袋里放一个球，P往口袋里拿一个球，线程同步条件是球到达某个数目。（注意可以有很多个口袋）

我们可以用一个整数来表达同步条件时，就可以使用信号量。

哲♂学家吃饭：

方案一：左右手叉子能用直接拿，吃完放下。（信号量）

问题：所有哲♂学家同时拿走左手边叉子，卡住了

方案二：先上锁，只有自己能访问所有叉子。吃完饭放下。（条件变量）

正确！

# 前端并行
ajax：callback hell

解决：
Promise：描述计算图

## HPC并行
OpenMP


# 现实中的并发bug

## 死锁

### AA-Deadlock
lock&lock, 尤其容易出现在系统内核的中断中。

### ABBA-Deadlock
X thread: lock A-> lock B, Y thread: lock B-> lock A

最后X，Y都无法工作。

两个人的哲♂学家吃饭问题，两个人都同时拿起左手边的叉子。永远无法吃饭

gpt says：

ABBA-Deadlock是指一种特定的死锁情况，其中“ABBA”可能代表了两个或多个进程或事务在争夺资源时的一种特定顺序或模式，导致它们互相等待对方释放资源，从而陷入死锁状态。

死锁是指两个或两个以上的进程或事务在执行过程中，因争夺资源而造成的一种互相等待的现象。具体来说，当一组进程中的每一个进程都在等待仅由该组进程中的其他进程才能引发的事件时，这组进程就陷入了死锁状态。在这种情况下，系统无法继续执行任何进程，因为每个进程都在等待其他进程释放资源，从而形成了一个循环等待的条件。

ABBA-Deadlock是一个具体例子或模式，用于说明这种死锁情况。它可能涉及两个进程A和B，每个进程都按照一定的顺序（如A先获取资源1然后请求资源2，B先获取资源2然后请求资源1）尝试获取资源，但由于资源的分配和请求顺序不当，导致两个进程都无法继续执行，从而陷入死锁。

为了预防和处理死锁，可以采取一系列措施，如破坏死锁的必要条件（请求和保持条件、不剥夺条件、环路等待条件等）、使用资源分级法、避免循环等待等。

### 死锁的必要条件

System deadlocks (1971): 把锁看成袋子里的球
1. Mutual-exclusion - 一个口袋一个球，得到球才能继续
2. Wait-for - 得到球的人想要更多的球
3. No-preemption - 不能抢别人的持有的球
4. Circular-chain - 形成循环等待球的关系

## Data-race

数据竞争（Data Race）是指多个线程并发访问共享数据，并且至少有一个线程对共享数据进行**写**操作，而这些访问没有进行适当的同步。（跑赢的人先执行，完全不保证线程执行顺序）

由于线程的执行顺序是不确定的，因此多线程并发程序的运行结果往往也是不确定的。这种不确定性严重影响了程序的可靠性和稳定性。

### Order Violation
"BA"：事件未按预定顺序发生

#### concurrent use-after-free
在并发环境中，这个问题尤为严重，因为多个线程可能同时访问和修改共享数据。一旦一个线程释放了资源，其他线程就不应该再访问它。但是，由于线程之间的调度是不确定的，以及可能存在数据竞争和同步问题，因此很难确保不会发生并发use-after-free错误。

# 虚拟化
## 进程
### 系统的启动
CPU Reset-> firmware --启动os--> os init --加载第一个进程--> init(1)

### 进程的创建
- fork()
  立即复制状态机，包括所有信息的完整拷贝
  - PC
  - Memory
  - ...
  
习题：写出运行结果，到底创建了几个状态机
```C
pid_t x = fork();
pid_t y = fork();
printf("%d %d", x, y);
```

ans: 3

#### execve
将当前进程**重置**为一个可执行文件描述状态机的初始状态。执行名为filename的程序，填入argc和argv，环境变量envp。（把自己换成另外一个人）

所以，要执行一个程序g，fork()->execve(g,...)

### 进程的结束
- exit
  会进行清理（调用atexit函数，关闭文件描述符等）。调用`SYS_exit_group`（行为是终止进程和所有的线程）
- _exit
  不会进行清理，直接调用`SYS_exit_group`
- syscall(SYS_exit,)
  不会进行清理，直接调用`SYS_exit`(行为是只终止该线程，子线程交给init(1))继承

### 进程的地址空间
查看进程地址空间：
在Linux中，有多种方法可以查看进程的地址空间。以下是一些常用的方法：

使用/proc文件系统
Linux的/proc文件系统为内核和进程提供了一个接口。每个运行的进程在/proc下都有一个以进程ID命名的目录。例如，要查看进程ID为1234的进程的地址空间信息，可以查看/proc/1234/maps文件。

```bash
cat /proc/1234/maps
```
这将显示该进程的内存映射，包括代码段、数据段、共享库、堆、栈等。
2. 使用pmap命令

pmap命令可以显示一个进程的内存映射。例如：

```bash
pmap -x 1234
```
这里，-x选项表示以更详细的格式显示信息。
3. 使用gdb

如果你安装了GNU调试器(gdb)，你也可以使用它来查看进程的地址空间。首先，你需要附加到目标进程：

```bash
gdb -p 1234
```
然后，在gdb的命令行中，你可以使用info proc mappings命令来查看进程的内存映射。

请注意，为了查看其他用户的进程信息，你可能需要root权限。而且，使用gdb附加到正在运行的进程可能会对该进程的行为产生影响，因此请谨慎操作。

这些工具和方法提供了关于进程地址空间的详细信息，包括每个段的起始和结束地址、权限（读、写、执行）以及可能的文件名（如果适用）。这些信息对于调试和性能分析非常有用。

查询pid
```bash
pidof [name]
```

#### 无需陷入kernel的“系统调用”
特殊地址空间段：
```
7ffcf25f2000-7ffcf25f6000 r--p 00000000 00:00 0                          [vvar]
7ffcf25f6000-7ffcf25f8000 r-xp 00000000 00:00 0                          [vdso]
```

在Linux系统中，系统调用是用户空间程序与内核空间进行交互的重要机制。传统的系统调用需要从用户态切换到内核态，这种切换涉及到上下文的保存和恢复，以及可能的模式切换，这些操作相对较为耗时。为了提高系统调用的效率，Linux内核引入了两种特殊的机制：`vdso`（Virtual Dynamic Shared Object）和`vvar`（Virtual Variable），即直接把系统代码和数据共享给进程。

以`gettimeofday`系统调用为例，这个调用通常用于获取当前的时间信息。在没有`vdso`和`vvar`的情况下，用户空间的程序需要通过陷入（trap）到内核态来获取时间，这会导致较大的性能开销。但是，通过使用`vdso`和`vvar`，Linux可以使得某些系统调用几乎不需要从用户态切换到内核态，从而显著提高效率。

1. **vdso（Virtual Dynamic Shared Object）**：
   `vdso`是一种特殊的共享对象，它提供了一种机制，允许用户空间程序直接调用一些特定的内核服务，而无需进行上下文切换。`vdso`的实现通常是通过将内核中的某些代码片段映射到用户空间，这样用户空间的程序就可以直接调用这些代码。对于`gettimeofday`这样的系统调用，`vdso`提供了一个名为`__vdso_gettimeofday`的函数，用户空间的程序可以通过动态链接器（dynamic linker）调用这个函数，而这个函数实际上会直接调用内核中的相应代码。

2. **vvar（Virtual Variable）**：
   `vvar`是一种特殊的全局变量，它允许用户空间程序直接读取或写入内核空间中的某些数据，而无需进行系统调用。对于`gettimeofday`，内核维护了一个名为`__vdso_timehands`的`vvar`，它包含了与时间相关的各种信息。用户空间的程序可以通过读取这个`vvar`来获取当前的时间信息，而无需进行系统调用。

结合`vdso`和`vvar`，`gettimeofday`的实现可以非常高效。用户空间的程序首先通过动态链接器找到`__vdso_gettimeofday`函数的地址，然后直接调用这个函数。这个函数会读取`__vdso_timehands``vvar`中的信息，并将结果返回给用户空间的程序。整个过程不需要陷入内核态，因此大大提高了系统调用的性能。

总结来说，`vdso`和`vvar`通过将内核代码和数据映射到用户空间，使得某些系统调用可以直接在用户态执行，从而避免了频繁的内核态与用户态之间的切换，提高了系统的效率。对于`gettimeofday`这样的常用系统调用，这种优化尤其重要，因为它可以显著减少系统调用的开销。

我们不需要syscall！

#### 增删改地址空间
什么指令可以修改地址空间？syscall！具体来说，是mmap系统调用。

#### 入侵地址空间
在Linux系统中，`/proc/[pid]/mem`是一个特殊的文件，它代表了指定进程的整个内存映射。这个文件在常规权限下是只读的。

以下是`/proc/[pid]/mem`的一些常见用途：

1. **调试**：调试器如`gdb`可能会使用`ptrace`系统调用，通过`/proc/[pid]/mem`来读取或写入进程的内存，以便进行调试。这可以用于检查变量的值、修改程序的执行流程等。

2. **内存修改**：通过`ptrace`，某些特殊的程序或脚本可以修改正在运行的进程的内存。这种技术有时被用于游戏作弊、逆向工程或系统调试。

3. **内存检查**：可以扫描或检查进程的内存，以寻找特定的值或模式。这在一些特殊的应用场景中可能会有用，比如在游戏黑客攻击中改变游戏状态。

4. **进程内存监控**：虽然不能直接读取，但可以通过`ptrace`来监控进程的内存使用情况，这对于性能分析和内存泄漏检测可能有帮助。

使用`/proc/[pid]/mem`通常需要具备相应的权限，特别是当涉及到读取或写入其他用户进程的内存时。此外，这种操作通常与安全和隐私问题相关，因此应该谨慎使用，并且只在合法和必要时进行。

需要注意的是，直接通过`/proc/[pid]/mem`操作进程内存是高级且危险的操作，它可能会导致程序崩溃或其他不可预测的行为。因此，这种技术通常只由经验丰富的系统管理员或专业开发者在特定情况下使用。

- Search+Filter
  可以找到某个感兴趣的变量对应的内存地址。（CE的实现）



### linux shell
进程的“视觉”和“触觉”：syscall

ps:什么时候可以优化？只要系统调用的参数不变就可以优化成任何东西！
#### 访问操作系统中的对象
Everything is a file.

在Linux系统中，"everything is a file" 这句话中的 "everything" 指的是**系统中几乎所有的对象和资源**。具体来说，它包括：

1. **普通文件**：包含文本数据、二进制数据等的文件。

2. **目录**：包含文件和子目录的文件。

3. **设备文件**：代表硬件设备，如硬盘、键盘、鼠标等。

4. **管道**：允许进程间通信的文件。

5. **套接字**：用于网络通信的文件。

6. **符号链接**：指向另一个文件或目录的文件。

7. **FIFO（先进先出队列）**：一种进程间通信机制。

8. **文件系统**：包括整个文件系统的层次结构。

9. **内存对象**：如共享内存段。

10. **进程控制块**：代表系统中的进程。

11. **信号量**：用于进程同步的机制。

12. **消息队列**：用于进程间通信的队列。

13. **内存映射文件**：将文件内容映射到内存中，以便进行高效访问。

14. **伪终端**：用于模拟终端的文件。

15. **文件描述符**：用于文件操作的整数。

通过将所有这些不同的对象和资源都视为文件，Linux提供了一个统一的接口来访问和管理它们。这使得文件操作的命令和工具（如cat、chmod、chown、ls等）可以应用于各种类型的资源，从而简化了系统编程和文件管理。

这种哲学反映了Unix的设计原则，即"一切皆文件"，它强调简洁、一致和模块化。通过将一切都抽象为文件，Linux系统能够以一种简单、一致和可预测的方式处理各种资源。这使得Linux成为一个强大、灵活和可扩展的操作系统。

##### 文件描述符fd
fd是指向操作系统对象的指针

#### 命名管道(named pipe)
在Linux系统中，命名管道（也称为FIFO，即“先进先出”队列）是一种特殊的文件类型，允许不相关的进程之间进行通信。命名管道的同步机制确保了数据的一致性和完整性，以下是关于命名管道的`read`、`write`操作和同步机制的解释：

##### 命名管道的创建

命名管道通过`mkfifo`命令创建，例如：

```bash
mkfifo mypipe
```

这将在当前目录下创建一个名为`mypipe`的命名管道。

##### read和write操作

1. **write操作**：当一个进程向命名管道写入数据时，它被阻塞，直到另一个进程从该管道中读取数据。这确保了写入的数据被读取，防止了数据的丢失。（放完球手不拿出来直到球被拿走）
```C
int fd = open("pipe",WRITE);
write(fd,buf); // blocked until data be read
```

2. **read操作**：当一个进程从命名管道读取数据时，它将接收到写入进程写入的数据。如果管道中没有数据，读取操作将被阻塞，直到有数据可读。（手伸进管道里直到拿到球）
```C
int fd = open("pipe",READ);
read(fd,buf); // blocked until read something
```
命名管道是进程间通信（IPC）的一种简单而有效的方式，特别是在需要单向通信或不需要建立复杂的共享内存和信号量机制的情况下。通过上述的read、write操作和同步机制，命名管道提供了一种可靠的方式来在进程之间传输数据。

#### 匿名管道
在Linux中，匿名管道（也称为无名管道）是一种进程间通信（IPC）机制，允许具有共同祖先的进程之间进行通信。匿名管道通常用于父子进程或兄弟进程之间的通信。以下是匿名管道的`read`、`write`操作和同步机制的解释：

##### 创建匿名管道

匿名管道是通过`pipe`系统调用创建的，它创建一对文件描述符（fd），分别用于读和写：

```c
int pipe(int fd[2]);
```

- `fd[0]`：用于读取的文件描述符。
- `fd[1]`：用于写入的文件描述符。

##### read和write操作

1. **write操作**：写入进程使用`write`系统调用来向管道写入数据。

- 写操作阻塞：

缓冲区满时：当管道的缓冲区已满，且仍有数据需要写入时，写操作会被阻塞，直到读取进程从管道中读取一些数据，从而释放缓冲区空间。

读端全部关闭时：如果所有指向管道读端的文件描述符都关闭了，而仍有进程尝试向管道的写端写入数据，那么该进程会收到一个SIGPIPE信号，这通常会导致进程异常终止。

2. **read操作**：读取进程使用`read`系统调用来从管道读取数据。如果管道中没有数据，读取操作将被阻塞，直到有数据可读。

- 读操作阻塞：

无数据时：当管道中没有数据可供读取，且所有指向管道写端的文件描述符都未关闭时，读操作会被阻塞，直到写入进程向管道中写入数据。

写端全部关闭时：如果所有指向管道写端的文件描述符都关闭了（即管道写端的引用计数为0），而读取进程仍尝试从管道中读取数据，那么在读取完管道中剩余的所有数据后，再次调用read()会返回0，就像读到了文件末尾一样。

```C
if (fork() == 0) {
   // child
   read(fd[0]);
}else {
   write(fd[1],buf,len);
}
```

匿名管道是一种简单而高效的进程间通信方式，特别适用于需要单向通信或不需要建立复杂的共享内存和信号量机制的场景。通过上述的`read`、`write`操作和同步机制，匿名管道提供了一种可靠的方式来在具有共同祖先的进程之间传输数据。

匿名管道和命名管道在Linux中都是用于进程间通信（IPC）的机制，但它们之间存在几个重要的区别。以下是两者之间的主要差异：

- 命名与识别：
   匿名管道：由于它没有名称，所以称为“匿名”。这种管道在内存中创建，没有持久性，并且只能通过文件描述符在相关进程之间进行识别和使用。一旦相关的进程终止，管道就会被销毁。
   命名管道：也称为FIFO（First In, First Out），它在文件系统中具有唯一的名称。这使得任何进程都可以通过该名称来引用和使用管道。命名管道具有持久性，存在于文件系统中，直到被显式删除。
- 通信范围：
   匿名管道：其通信范围局限于具有亲属关系的进程之间，如父子进程或兄弟进程。它们不能用于不同计算机或不同会话之间的通信。
   命名管道：由于其在文件系统中的可见性，命名管道可以实现任意两个进程之间的通信，无论它们是否具有亲属关系。这使得命名管道在更广泛的场景中具有更高的灵活性。
- 通信模式：
   匿名管道：它是半双工的，这意味着在任一时间点，数据只能在一个方向上流动。要实现双向通信，需要创建两个匿名管道。
   命名管道：它是全双工的，允许数据在同一管道中双向流动。这意味着一个进程可以同时在同一命名管道上进行读写操作。
- 使用场景：
   匿名管道：由于其简单性和局限性，匿名管道通常用于亲属进程之间的单向通信。
   命名管道：命名管道因其灵活性和可见性而适用于各种复杂的IPC场景，如生产者-消费者模型等。

总的来说，匿名管道和命名管道都是Linux中用于进程间通信的有效工具，但它们在命名、通信范围、通信模式和使用场景等方面存在显著的差异。根据具体的需求和场景，可以选择适合的管道类型来实现进程间的通信。

### shell：OS的外壳
用户看不到操作系统，看到的是使用系统调用的应用程序。

Shell是一种特殊的应用程序，将系统调用的功能暴露给用户。
#### shell 连接符
在Linux shell中，||、;、&& 和 | 是用于控制命令执行流程的连接符。以下是它们的解释：

|| (逻辑或)
|| 用于连接两个命令。当第一个命令执行失败（返回非零退出状态）时，才会执行第二个命令。

示例：

```bash
command1 || command2
```
如果 command1 执行成功，则不会执行 command2。但如果 command1 失败，则会执行 command2。
2. ; (分号)

; 用于分隔两个命令，无论第一个命令执行成功还是失败，第二个命令都会执行。

示例：

```bash
command1; command2
```
无论 command1 的执行结果如何，command2 都会执行。
3. && (逻辑与)

&& 用于连接两个命令。当第一个命令执行成功（返回零退出状态）时，才会执行第二个命令。

示例：

```bash
command1 && command2
```
如果 command1 执行成功，则会执行 command2。但如果 command1 失败，则不会执行 command2。
4. | (管道)

| 用于将一个命令的输出作为另一个命令的输入。

示例：

```bash
command1 | command2
```
这将 command1 的输出传递给 command2 作为其输入。例如，你可以使用 cat file.txt | grep "pattern" 来搜索 file.txt 中的 "pattern"。

这些连接符可以组合使用，以创建更复杂的命令序列。例如：

```bash
command1 && command2 || command3
```
这表示：如果 command1 成功，则执行 command2；如果 command1 失败，则执行 command3（并且不执行 command2）。

### shell 前后台
在Linux shell中，前后台管理命令允许用户控制进程的执行方式，即进程是在前台运行还是在后台运行。这对于需要长时间运行的任务或者需要同时执行多个任务的情况非常有用。

前台运行：默认情况下，当你在shell中输入一个命令并执行时，该命令通常在前台运行。这意味着它会占用你的终端，直到命令完成。在此期间，你通常不能执行其他命令，除非该命令产生了一个子shell或允许交互。

后台运行：将命令放到后台运行意味着该命令将在独立的进程中执行，而你的shell（或终端）将立即返回提示符，允许你执行其他命令。这对于需要长时间运行的任务（如文件复制、大型计算任务等）特别有用。
以下是一些常用的前后台管理命令和技巧：

&：在命令的末尾添加&符号，可以将命令放到后台执行。例如：command &。

Ctrl+Z：当你在前台运行一个命令时，按下Ctrl+Z组合键可以暂停该命令的执行，并将其放到后台的挂起状态。

bg：该命令用于将最近暂停的作业（即使用Ctrl+Z暂停的作业）放到后台继续执行。

fg：该命令用于将最近暂停的作业或后台运行的作业带到前台执行。

jobs：此命令列出当前shell会话中所有后台作业的状态。

kill：虽然这不是一个直接的前后台管理命令，但kill命令允许你发送信号给进程，包括终止后台运行的进程。例如，kill %job_number可以终止特定的后台作业。

请注意，前台和后台作业的状态以及它们与shell的关联通常只存在于单个shell会话中。如果你关闭了shell或开启了新的shell会话，这些状态通常不会保留。

### 实现shell
`-ffreestanding`，`-nostdlib`

```C
void _start() {
   main();
   syscall(SYS_EXIT,0);
}
```
参考jyy的shell
#### shell 管道实现
`SYS_DUP`拷贝管道写口到标准输出，管道读口到标准输入

### 进程的加载
#### Shebang
linux脚本如果以`#!`开头且可执行，shell会默认`#!`后面的是解释器

#### execve
进程加载是通过execve syscall执行的。当然，我们可以实现自己的execve（而不直接调用syscall！）。FLE的加载就是这么进行的。只要复制数据到memory，设置PC，程序就完成加载了！

### 静态链接
TODO

### 动态链接

#### 代码的动态链接
动态链接的基本思想：查表

```ASM
call *TABLE[printf@symtab]
```

加载器在加载时填入`TABLE`的相应表项，即**GOT**

- 如何确定是直接跳转还是查表？
1. 所有函数调用都查表
   性能无法接受
2. 所有函数都直接跳转
   call 只能有32位偏移量，跳不过去。（call 只能call 在同一模块内的函数）

从性能上考虑，只能全部直接跳转。链接器在链接时，如果发现符号是动态链接的，会合成一小段代码，即**PLT**。

```C
printf();
```
```ASM
call printf@PLT

printf@PLT:
    jmp *GOT[printf@symtab] # 为了实现位置无关代码（PIC），为*offset(%rip)
```

> 是否一定需要PLT？
如果已知call 对象在同一个链接单元内，可以不用PLT，直接call。但是先编译后链接的历史包袱限制了这一点。编译器只能保守编译。


#### 数据的动态链接

对于数据，我们不能 “间接跳转”！
> 动态链接代码和数据的区别：代码可以两级跳转，先跳一小步到本模块内的一串代码再跳一大步到本模块外的代码来动态链接。数据无法两级跳转，因为mov一定要mov某个地址。

理论上，
x = 1, 在同一个 .so (或 executable)内，我们可以这么操作：
```C
mov $1, offset_of_x(%rip)
```

x = 1, 而在另一个 .so内，我们应该如此操作
```C
mov GOT[x], %rdi
mov $1, (%rdi)
```

但是，编译器不知道x的定义到底是不是在同一个链接单元内。如
```
a1.c -> int x;
a2.c -> extern int x; x=1;
b.c  -> extern int x; x=1;

gcc -fPIC -shared a1.c a2.c -o a.so
gcc -fPIC -shared b.c -o b.so
```
即使我们知道a2.c引用的x在同一个链接单元内，可以直接得到地址，编译器却只能保守编译a2.c（先编译后链接的历史包袱）。
得到不优雅的编译：
-fPIC 默认会为所有 extern 数据增加一层间接访问。

如果想要人为为编译器提供信息x一定在同一个链接单元内，可以这么写(a2.c)：
```C
extern int __attribute__((visibility("hidden"))) x;
```

#### -fPIE 和 -fPIC
PIE表示位置无关可执行程序，在链接时如果发现extern的数据符号可以在当前链接的文件里面找到，会直接翻译成相对rip寻址（一个优化）

### 加载
复制各段代码到内存指定位置。赋予可读/可写/可执行权限，跳转执行。

## 应用程序视角的OS
应用程序眼里，OS就是对象+API

### syscall
跳转并获得无限权力

#### 启动和结束
`trap`启动，`return-from-trap`结束。

`trap`时，
保存寄存器状态(push)到kernel stack, 进入内核态。

`return-from-trap`时，
恢复寄存器状态(pop from kernel stack)，进入内核态

### 中断
可以理解为被强制插入的yield的syscall指令。

封存状态机状态。

在处理器处理中断时，保存现场是一个关键的步骤，以确保在中断处理完成后能够恢复到中断发生时的现场并继续执行原程序。以下是处理器保存现场的详细过程以及可能使用的寄存器：

- 中断发生：当外部设备发生故障或者需要响应处理器的请求时，会触发一个中断信号，将处理器从当前执行的指令转移到中断处理程序的入口地址。
- 保存现场：
- 保存断点：处理器首先会将断点处的PC值（即下一条应执行指令的地址）推入堆栈保存下来，这称为保护断点。这一步通常由硬件自动执行。
- 保存寄存器内容：处理器还会将当前执行任务的寄存器及其他必要的状态信息保存到中断栈或堆栈中。这些寄存器可能包括通用寄存器（如数据寄存器、地址寄存器、索引寄存器等）、特殊寄存器（如状态寄存器、控制寄存器等）以及系统寄存器（如CR3寄存器，用于存储页目录表的物理地址）。
- 保存标志位状态：处理器还会将当前的标志位状态（如追踪标志TF、中断允许标志IF、方向标志DF等）保存到堆栈中。这些标志位用于控制处理器的行为，如是否响应中断、是否进入单步执行模式等。
- 保存方式：保存现场的方式可以是集中式或分散式的。集中式保存通常是在内存的系统区中设置一个中断现场保存栈，所有中断的现场信息都统一保存在这个栈中。分散式保存则是在每个进程的PCB（进程控制块）中设置一个核心栈，一旦程序被中断，它的中断现场信息就保存在自己的核心栈中。
- 中断处理：保存现场完成后，处理器会跳转到中断处理程序的入口地址，开始执行中断处理程序。中断处理程序会根据具体的中断事件执行相应的处理逻辑，完成所需的操作。
- 恢复现场：中断处理程序执行完成后，处理器会从中断栈或堆栈中恢复之前保存的现场。这包括恢复寄存器的值、标志位的状态以及PC值等。恢复现场后，处理器会继续执行原程序。

### 进程调度
进程调度需要有优先级

#### UNIX Nicenes
好人总会吃亏，越nice的人越愿意把资源让给别人。

RTOS：坏人躺下好人才能上

linux：10 Nices $\approx$ 10x CPU using rate

Unix niceness is a system attribute that determines the priority of a process in terms of CPU scheduling. It is a way to influence the amount of CPU time allocated to processes by the kernel. The niceness value ranges from -20 to 19:

- **Lower niceness values** (e.g., -20) correspond to higher priority. These processes will be more favored by the scheduler and receive more CPU time.
- **Higher niceness values** (e.g., 19) correspond to lower priority. These processes will receive less CPU time as the scheduler will favor other processes with lower (more negative) niceness values.

The default niceness value for a process is usually 0. Users can adjust the niceness value of their processes using the `nice` command when starting a process or the `renice` command to change the niceness of an already running process. For example, to start a process with a niceness value of 10, you can use:

```sh
nice -n 10 my_program
```

To change the niceness of a running process with process ID 1234 to 5, you can use:

```sh
renice 5 -p 1234
```

Higher niceness values are useful for background processes or less critical tasks, ensuring they do not take away CPU time from more important processes. Conversely, processes that require more CPU time can be assigned lower niceness values to increase their priority.

##### 如果Nice值相同？
公平分享CPU（Round-Robin）

Round-Robin (RR) is a scheduling algorithm used in operating systems for process and task management. It is one of the simplest and most widely used scheduling techniques, especially in time-sharing systems. Here are the key characteristics and principles of Round-Robin scheduling:

1. **Time Slices (Quanta)**: Each process is assigned a fixed time slice or quantum during which it can execute. The length of the time slice is a crucial parameter and can significantly affect system performance.

2. **Circular Queue**: Processes are maintained in a circular queue. When a process’s time slice expires, it is moved to the back of the queue, and the next process in line is given the CPU.

3. **Fairness**: RR aims to be fair by giving each process an equal share of the CPU. Each process gets an equal opportunity to execute in turn, preventing any single process from monopolizing the CPU.

4. **Preemption**: If a process does not complete within its allocated time slice, it is preempted and placed at the end of the queue. The CPU is then allocated to the next process in the queue.

5. **Performance**: The performance of RR scheduling depends heavily on the length of the time slice. If the time slice is too long, RR can behave like First-Come, First-Served (FCFS) scheduling, leading to poor response times for short tasks. If the time slice is too short, it can lead to excessive context switching, which may reduce CPU efficiency.

6. **Starvation-Free**: Because each process gets its turn, RR scheduling prevents starvation, ensuring that all processes will eventually be executed.

### Example

Consider three processes, P1, P2, and P3, with time slices of 4 units each:

- At time 0, P1 starts execution.
- At time 4, if P1 has not finished, it is moved to the back of the queue, and P2 starts execution.
- At time 8, if P2 has not finished, it is moved to the back of the queue, and P3 starts execution.
- The cycle repeats until all processes are completed.

Round-Robin scheduling is particularly effective in environments where a large number of short tasks need to be processed quickly, making it a popular choice for interactive systems and time-sharing environments.

# persist
## IO 设备实现
### GPIO
极简内存模型：memory-mapped I/O 直接读取/写入电平信号。

xxx-yyy 地址连接到内存控制器，aaa-zzz地址连接到IO设备线

这意味着外设的寄存器看起来就像是内存的一部分，CPU可以直接通过加载和存储指令来访问这些寄存器，就像访问普通RAM一样，而不需要专门的I/O指令或端口操作。

### DMA
如果让CPU移动1GiB的数据，太过浪费。为了节约CPU资源：

DMA: 只能执行 memcpy(ATA0, buf, length); 的处理器

支持的几种类型的 memcpy

memory → memory

memory → device (register)

device (register) → memory

实际实现：直接把 DMA 控制器连接在总线和内存上

## 文件系统的细节
### fd
fd（文件描述符）：指向操作系统内对象的指针。

对象的访问都需要指针：open, close, read/write (解引用), lseek (指针内赋值/运算), dup (指针间赋值)

### open
openat：相对某个目录打开

### mmap
mmap比文件大小小的大小没有问题，但如果mmap比文件大的大小呢？
```C
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <errno.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *filename = argv[1];
    int fd = open(filename, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return EXIT_FAILURE;
    }

    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        perror("fstat");
        close(fd);
        return EXIT_FAILURE;
    }

    // 故意多映射4KB
    size_t map_size = sb.st_size + 4096;

    void *mapped_region = mmap(NULL, map_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (mapped_region == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return EXIT_FAILURE;
    }

    // 遍历映射的内存空间
    char *ptr = (char *)mapped_region;
    for (size_t i = 0; i < map_size; ++i) {
            // 打印文件内容或执行其他操作
        printf("%c", *ptr);
        ++ptr;
    }

    if (munmap(mapped_region, map_size) == -1) {
        perror("munmap");
        close(fd);
        return EXIT_FAILURE;
    }

    close(fd);
    return EXIT_SUCCESS;
}
```
### 超出边界写入
在Linux中，如果你有一个1MiB（即1024KiB）大小的文件，并尝试使用`lseek`函数将文件指针移动到3MiB处，然后写入数据，这里会发生几个关键操作：

1. **文件指针移动**：首先，`lseek`调用会成功将文件指针移动到你指定的3MiB位置，即使该位置超出了当前文件的实际大小。`lseek`并不检查文件指针是否超过文件末尾，它只是简单地设置内部记录的偏移量。

2. **写入数据**：当你在3MiB的位置开始写入数据时，Linux会执行以下操作：
   - **文件扩展**：如果文件原先大小不足3MiB，操作系统会自动扩展文件大小以适应你的写入操作。这意味着文件将从1MiB扩展到至少3MiB。
   - **分配磁盘空间**：根据文件系统的具体配置和可用空间情况，可能需要分配额外的磁盘空间来满足文件扩展的需求。如果磁盘空间不足，写入操作可能会失败，并可能产生错误（比如ENOSPC，表示没有空间可用了）。
   - **填充空洞**：从原文件的1MiB末尾到你开始写入的3MiB之间，如果没有显式写入数据，这段区间将会被填充零字节（或者在某些文件系统上可能是未定义内容），这被称为“稀疏文件”中的“空洞”。

3. **实际写入**：你写入的数据将从3MiB的位置开始存储。如果写入的数据量使得文件大小超过了最初设定的3MiB位置，文件会进一步扩展以容纳所有写入的数据。

综上所述，通过这样的操作，你可以有效地在文件中创建一个“空洞”，并在该“空洞”之后写入数据，导致文件中出现未初始化的区域（通常是零填充）。这种方式在某些场景下非常有用，例如预先分配大文件的空间或创建稀疏文件。但请注意，这种做法可能会导致文件占用的磁盘空间与逻辑上的文件大小不完全一致，特别是当存在大量未写入数据的“空洞”时。

### fd在父子进程间的继承
在Linux中，当通过fork()系统调用来创建子进程时，父进程的所有已打开的文件描述符（FDs）都会被子进程继承。这意味着子进程会拥有和父进程相同的文件描述符集合，包括它们所对应的文件或设备。不仅文件描述符会被继承，连同这些文件描述符的当前偏移量（offset）也是相同的。

然而，需要注意的是，虽然偏移量相同，但是每个进程对文件的操作是独立的。例如，如果一个进程改变了文件偏移量，这个改变不会影响到其他进程中的偏移量。此外，如果子进程随后执行了exec()家族函数来加载新的程序，那么尽管文件描述符可能仍然保持打开状态（除非明确关闭或设置了FD_CLOEXEC标志），新的程序将从文件的当前偏移量开始操作，这个偏移量可能在exec()调用前后由同一个进程中设置。


## 文件操作
kernel中的file_operations结构体实现了一个文件类型操作的anything
```C
struct file_operations {
   struct module *owner;
   loff_t (*llseek) (struct file *, loff_t, int);
   ssize_t (*read) (struct file *, char __user *, size_t, loff_t *);
   ssize_t (*write) (struct file *, const char __user *, size_t, loff_t *);
   ssize_t (*aio_read) (struct kiocb *, const struct iovec *, unsigned long, loff_t);
   ssize_t (*aio_write) (struct kiocb *, const struct iovec *, unsigned long, loff_t);
   int (*readdir) (struct file *, void *, filldir_t);
   unsigned int (*poll) (struct file *, struct poll_table_struct *);
   long (*unlocked_ioctl) (struct file *, unsigned int, unsigned long);
   long (*compat_ioctl) (struct file *, unsigned int, unsigned long);
   int (*mmap) (struct file *, struct vm_area_struct *);
   int (*open) (struct inode *, struct file *);
   int (*flush) (struct file *, fl_owner_t id);
   int (*release) (struct inode *, struct file *);
   int (*fsync) (struct file *, loff_t, loff_t, int datasync);
   int (*aio_fsync) (struct kiocb *, int datasync);
   int (*fasync) (int, struct file *, int);
   int (*lock) (struct file *, int, struct file_lock *);
   ssize_t (*sendpage) (struct file *, struct page *, int, size_t, loff_t *, int);
   unsigned long (*get_unmapped_area)(struct file *, unsigned long, unsigned long, unsigned long, unsigned long);
   int (*check_flags)(int);
   int (*flock) (struct file *, int, struct file_lock *);
   ssize_t (*splice_write)(struct pipe_inode_info *, struct file *, loff_t *, size_t, unsigned int);
   ssize_t (*splice_read)(struct file *, loff_t *, struct pipe_inode_info *, size_t, unsigned int);
   int (*setlease)(struct file *, long, struct file_lock **);
   long (*fallocate)(struct file *file, int mode, loff_t offset, loff_t len);
};
```


## 文件系统
### 创建和挂载
在一个块设备上使用mkfs可以创建文件系统。使用mount系统调用可以将文件系统挂载到指定的目录。本质上是将新的文件系统粘贴到目录树的这个点上。

### 硬链接
使用link系统调用（ln命令是它的封装），可以在一个目录内创建对一个文件的硬链接。将一个新文件名硬链接到一个旧文件，实际上就是创建了另一种引用同一个文件的方法。（在ext2中就是加入一个新的文件名，inode二元组）。硬链接不复制文件。unix中删除文件的系统调用是unlink。当作用于硬链接时，它将引用计数减一。

### 软链接
硬链接存在局限性：不能硬链接一个目录，因为担心会形成环；也不能硬链接到另一个文件系统中的文件，因为inode号只在一个文件系统中唯一。、

软链接（符号链接）实际上就是一个“快捷方式”。它是一个文件，文件内容是指向的文件的路径。`ln -s`用于创建软链接。删除软链接的目标文件会导致悬空引用。

操作系统通过文件类型来判断一个文件是软链接（正如判断一个文件是目录一样）。


### 实现
- 磁盘：仅支持块读取和块写入的块设备
- 文件：字节序列

文件系统就是在只有`bread`和`bwrite`两个API的块设备上实现文件和目录的抽象。

### FAT
软盘时代，一个块设备可能只有几千个块。文件系统应当尽可能简洁。链表是最简洁的数据结构。

文件实现上为一个链表，链起组成文件的块。链表设计有两种选择：1. 在每块中划分空间，存储下一块的地址 2. 集中存放每一块的下一块指针。 
方法1会导致单纯的lseek也需要读出整个块。方法2会导致如果集中存放的区域损坏，文件系统会崩溃

显然，方法1的问题更大（无法解决）。方法2可以通过备份这片区域解决。于是FAT采用方法2。称为FAT表。

FAT表中每一个块都有一个项，记录了块的下一块等信息。FAT中有至少两张一模一样的FAT表作为备份。

FAT的目录就是一个文件，存储文件名和文件的第一块等信息。根目录对应的文件存放于一个根据FAT表就立即可达的位置。进而我们可以访问所有文件。

### ext2
FAT对大文件的支持不理想（读取一个4GB的文件末尾可能需要上千次链表访问）。因此产生ext2文件系统，以期同时很好地支持大文件和小文件。

> 设计高速文件系统时的朋友：局部性+缓存（邻近数据有一同访问的倾向，数据先缓存稍后写回） 敌人：读/写放大

ext2中，文件和目录都用inode表示。小文件用数组表示，大文件用b-tree表示。

inode中有文件创建时间等meta data。一个next[10],表示文件的前十个块。一级索引，二级索引等，表示文件的树结构。因此同时支持了小文件和大文件。即使是大文件，读出文件头（file命令）也是很常用的操作，也能快速进行。

ext2的局部性体现在创建时间接近的文件（如同一个目录中的文件）的inode号往往接近，因而存储在靠近的区域。

文件和目录都用inode表示，称为low level name。目录也是一个文件，内容是简单的文件名和inode的二元组列表。

## 可靠性
### persistent
磁盘可能损坏，如何保证数据不丢失？
#### RAID
将多块硬盘虚拟成一块盘。
- RAID-0
  两块盘都用于存储数据。2x读写速度 2x容量
- RAID-1
  一块盘用于存储数据。另一块盘是第一块盘的完整镜像。2x读 1x写 1x容量
- RAID-N
  99块盘存储数据，一块盘用来奇偶校验。假设只有一块盘会损坏，奇偶校验位可以恢复损坏的内容。存在一个问题，奇偶校验盘会成为瓶颈，无论写哪个盘都要写奇偶校验盘。RAID论文将奇偶校验盘均匀分散在所有盘里，一块盘既存数据也存奇偶校验，解决了瓶颈问题。

### crash consistency
#### FSCK
在crash发生后将文件系统恢复到最可能的状态。如assert(t->parent->left == t || t->parent->right == t)

#### Journal
使用append-only的方式向Journal中写入操作序列。等待操作序列落盘完成后再对文件系统进行实际操作。
1. lseek to end of journal
2. bflush TXB op op op ... op
3. bflush
4. bwrite TXE
5. bflush
6. perform ops
7. bflush
8. delete journal


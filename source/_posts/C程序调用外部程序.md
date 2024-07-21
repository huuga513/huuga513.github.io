---
title: C程序调用外部程序
date: 2024-06-13 18:05:58
tags:
---

一个C程序可以通过链接调用静态库和动态库的代码，直接使用库中提供的功能。但是假如我们想在其他程序的基础上编写自己的程序，又没有程序的源代码。能否直接把想要利用的外部程序当作一个黑盒来使用，提供命令行参数，然后获得输出呢？通过pipe(), fork(), execve()三板斧，我们就可以实现它。

## 调用程序

在GNU/Linux中，启动一个程序的唯一方法是fork和execve系统调用。fork可以理解为复制一份**完全一模一样**的当前程序的拷贝，execve则可以

理解为使用指定的可执行文件确定的程序初始状态替换当前程序。通过先fork，再execve，我们便可以在C程序中启动任何一个程序。

以启动ls为例，

```C
pid_t pid = fork();

if (pid == 0) {

    // child

    execve("/bin/ls", argv, envp);

} else {

    // parent

    ...

}
```

其中，execve的第一个参数是可执行文件地址，第二个参数是命令行参数argv，第三个参数是环境变量，诸如PATH一类的环境变量就通过它传递给程序。

当然，上面的代码还不能直接运行，我们还需要填充argv和envp的值。

根据约定，argv[0]是程序自己的名字，argv[1]开始是要传递给程序的参数。argv的最后一项应该是NULL。

所以，我们可以这样填充argv, 即`ls . -l`：

```C
char* exec_argv[] = {"ls", ".", "-l", NULL};
```

而对于envp，如果没有特别的需要，可以直接将main函数的envp作为参数传入（毕竟环境变量也不会那么容易变嘛）。

下面这段代码可以启动并执行`ls . -l`

```C
#include <unistd.h>

int main(int argc, char* argv[], char* envp[]) {

    pid_t pid = fork();

    if (pid == 0) {

        // child

        char* exec_argv[] = {"ls", ".", "-l", NULL};

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

    }

    return 0;

}
```

## 获得输出

光执行程序是不够的，我们还需要获得程序的输出。这时候，就需要使用GNU/Linux中的**匿名管道**机制。匿名管道提供了父子进程之间方便的

交流方式。当然，你猜对了，fork创建的新进程正是原来进程的子进程。

使用pipe()创建匿名管道，然后通过dup2()重定向stdout或stderr，就可以像读文件一样读取程序的输出。

我们修改上面的程序，首先创建一个匿名管道。

```C
#include <unistd.h>

int main(int argc, char* argv[], char* envp[]) {

    int pipefd[2]; // 新增的代码

    if (pipe(pipefd) == -1) {

        // error

        return 1;

    }

    pid_t pid = fork();

    if (pid == 0) {

        // child

        char* exec_argv[] = {"ls", ".", "-l", NULL};

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

    }

    return 0;

}
```

新增加的四行代码实现了创建一个匿名管道并存入pipefd。其中，pipefd[0]是读端的文件描述符，pipefd[1]是写端的文件描述符。

接下来，我们就可以在父子进程中使用这个管道。匿名管道之中的数据只能单向流动，即父子进程中一个必须关闭读口另一个必须关闭写口。因为我们的目标是获得外部程序的输出，所以我们在父进程中关闭写口，在子进程中关闭读口。

```C
#include <unistd.h>

int main(int argc, char* argv[], char* envp[]) {

    int pipefd[2];

    if (pipe(pipefd) == -1) {

        // error

        return 1;

    }

    pid_t pid = fork();

    if (pid == 0) {

        // child

        close(pipefd[0]);

        char* exec_argv[] = {"ls", ".", "-l", NULL};

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

        close(pipefd[1]);

    }

    return 0;

}
```

然后，我们将子进程的标准输出重定向到管道写口。

```C
#include <unistd.h>

int main(int argc, char* argv[], char* envp[]) {

    int pipefd[2];

    if (pipe(pipefd) == -1) {

        // error

        return 1;

    }

    pid_t pid = fork();

    if (pid == 0) {

        // child

        close(pipefd[0]);

        // copy pipefd[1] to STDOUT_FILENO

        if (dup2(pipefd[1], STDOUT_FILENO) == -1) {

            return 1;

        }

        close(pipefd[1]);

        char* exec_argv[] = {"ls", ".", "-l", NULL};

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

        close(pipefd[1]);

    }

    return 0;

}
```

在上面的代码中，我们将pipefd[1]（即写口）复制到了stdout。在复制完成后，我们就可以关闭pipefd[1]，因为现在stdout已经绑定到了管道写口，我们没有必要保留两个对写口的绑定。

最后一步，就是在父进程中得到子进程的输出，直接读pipefd[0]就可以了。

我们假设希望一次读取一行子进程的输出。下面的程序在子进程的输出前加上"Child output:"的前缀后原封不动第输出子进程的输出。

```C
#include <unistd.h>

#include <stdio.h>

int main(int argc, char* argv[], char* envp[]) {

    int pipefd[2];

    if (pipe(pipefd) == -1) {

        // error

        return 1;

    }

    pid_t pid = fork();

    if (pid == 0) {

        // child

        close(pipefd[0]);

        // copy pipefd[1] to STDOUT_FILENO

        if (dup2(pipefd[1], STDOUT_FILENO) == -1) {

            return 1;

        }

        close(pipefd[1]);

        char* exec_argv[] = {"ls", ".", "-l" ,NULL};

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

        close(pipefd[1]);

        FILE* r = fdopen(pipefd[0], "r");

        char buf[1024];

        while (fgets(buf, 1024, r)) {

            printf("Child output: %s",buf);

        }

        fclose(r);

        return 0;

    }

    return 0;

}
```

这里，buf中就存储着外部程序每一行的输出。

## 更进一步

当然，我们开头说的是能否将外部函数当成一个“库函数”使用。上面的写法显然不是很像一个库函数。再做一点适当的包装，我们就能把外部程序ls包装成一个函数。进而愉快地使用它。至此，我们的ls函数就实现了`ls . -l`的功能，完全不需要知道`ls`的源代码，我们就可以把它当成库使用。那确实挺不错的。你们觉得怎么样呢？

```C
#include <unistd.h>

// ls the files in pwd and store in result

int ls(char* result) {

    int pipefd[2];

    if (pipe(pipefd) == -1) {

        // error

        return 1;

    }

    pid_t pid = fork();

    if (pid == 0) {

        // child

        close(pipefd[0]);

        // copy pipefd[1] to STDOUT_FILENO

        if (dup2(pipefd[1], STDOUT_FILENO) == -1) {

            return 1;

        }

        close(pipefd[1]);

        char* exec_argv[] = {"ls", ".", "-l" ,NULL};

        char* exec_envp[] = {NULL}; // ls不使用环境变量也可使用

        execve("/bin/ls", exec_argv, envp);

    } else {

        // parent

        close(pipefd[1]);

        int len = 0;

        while (1) {

            int rlen = read(pipefd[0], result+len,1024);

            if (rlen <= 0) {

                close(pipefd[0]);

                return 1;

            }

            len += rlen;

        }

        return 0;

    }

    return 0;

}



int main() {

    char buf[1024];

    ls(buf);

    printf("%s\n",buf);

    return 0;

}
```

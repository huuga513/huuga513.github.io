---
title: hexo图片无法显示解决
date: 2024-07-23 16:50:25
tags:
---
## 问题
使用markdown作为源文件，hexo生成html网页。打开网页却发现所有引用的图片都无法加载成功。markdown中以相对路径，即`![](xxx.png)`的方式引用图片。
尝试将图片放置在markdown源文件同一个文件夹中也无法解决问题。

## 关键
最大的问题在于hexo在将markdown渲染为html时，极其暴力地将markdown的图片引用（无论是相对引用还是绝对引用）都翻译为相对网站根目录的绝对引用。

如：文件夹`_posts/post.md`和图片`_posts/img.png`。经过hexo渲染后，会生成一个类似于`2024/7/23/post/index.html`的文件。
其中，对图片的引用`![](xxx.png)`会被渲染为`<img src="/xxx.png">`。显然，这是一个绝对路径引用。在此路径下找不到图片，自然无法显示。

## 解决方案
最简单的解决方案就是把图片放到hexo认为它应该在的地方（Make them happy）。

hexo的网站根路径位于`public`文件夹。只要在`public`文件夹中新建一个文件夹用于存放图片（当然，也可以利用现成的`images`文件夹）。比如，将img.png复制到`images`文件夹中，然后将markdown的图片引用改成`images/img.png`，就能愉快地显示图片了。（如果你不想改markdown文件，甚至可以直接将图片丢到public根目录下，这样也能显示。或者可以改一改html文件的img控件内容）。
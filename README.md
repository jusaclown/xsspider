# 小说下载

> 有些hp网站就是不提供下载，于是我就通过爬虫爬取所有的章节然后下载下来-.-
## 新笔趣阁
就是通过爬虫爬取所有的章节，然后一一下载到txt文本中，由于只是单线程的（或者可以搞个生产者消费者模式的多线程？）所以下载速度有点慢。
### 使用方法
    # python3 xbiquge.py
    # 输入你要搜索的小说
    # 选择你要下载的小说
    # 开始下载
在下载过程中会生成一个`.txt.saved`格式的文件，用来存储已经下载的章节，这样就算程序中断了，也可以重启程序继续下载， 这个文件下载完成后会自动删除。

### 问题
1. 由于代理比较垃圾，所以requests请求老是报错，我就想报错后重行发送请求，然后我就在异常处理部分重新调用发送请求的函数，结果应该是可行的，但总感觉怪怪的，然后我问了一下，有人告诉我用`retry`，虽然可以让不断执行，但出现异常函数还是会返回结果，于是后面的函数得到一个空的结果就会报错。还是说我的用法错了。。。如果有人知道该怎么解决，望告之。
2. 有没有在`.txt.saved`中只保存上次下载的最后章节数据的方法，保留一老串感觉好憨，我想实现从文件中读取上一次的下载数据，然后每次下载一章后就更新这个数据，就是太菜了，不知道怎么做，望大佬告知。


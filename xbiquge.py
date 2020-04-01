import re, os
import time
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from retrying import retry

WEBSITE_URL = "http://www.xbiquge.la"
SEARCH_URL = "http://www.xbiquge.la/modules/article/waps.php"
GET_PROXY_URL = "http://127.0.0.1:5555/random"
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'}
CODING = "utf-8"
PROXIES = False
FLAG = True


# 获取代理
def get_proxy():
    global PROXIES
    proxy = requests.get(GET_PROXY_URL).text.strip()
    print('使用代理:', proxy)
    PROXIES = True
    return {'http': 'http://' + proxy}


# 发送请求
"""
1、stop_max_attempt_number：用来设定最大的尝试次数，超过该次数就停止重试
2、stop_max_delay：比如设置成10000，那么从被装饰的函数开始执行的时间点开始，到函数成功运行结束或者失败报错中止的时间点，只要这段时间超过10秒，函数就不会再执行了
3、wait_fixed：设置在两次retrying之间的停留时间
4、wait_random_min和wait_random_max：用随机的方式产生两次retrying之间的停留时间
5、wait_exponential_multiplier和wait_exponential_max：以指数的形式产生两次retrying之间
"""
# @retry()
def get_html(url, data=None):
    try:
        # 代理太垃圾了，还不如不用
        # global PROXIES
        # if not PROXIES:
        #     PROXIES = get_proxy()
        if data is None:
            r = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=10)
        else:
            payload = {"searchkey": data}
            r = requests.post(url, headers=HEADERS, data=payload,
                              proxies=PROXIES, timeout=10)
        r.raise_for_status()
        r.encoding = CODING
        return r.text
    except HTTPError as e:
        print('\nHTTPError...', e)
        print('等一哈,可能是下载太快了...')
        time.sleep(10)
        # PROXIES = False
        return get_html(url, data)
    # except Timeout as e:
    #     print('Timeout...', e)
    #     PROXIES = False
    #     return get_html(url, data)
    except RequestException as e:
        print('\n', e)
        print("别问，问就是垃圾代理")
        # PROXIES = False
        return get_html(url, data)


# 解析搜索页面，返回搜索结果
def parse_search_page(html):
    search_soup = BeautifulSoup(html, 'lxml')
    trs = search_soup("tr")  # 等价于soup.find_all("tr")
    if len(trs) == 1:
        print("搜索结果为空，请重新输入")
        return None, None, None
    print("搜索结果如下所示:")
    num = 1
    article_links = []
    article_names = []
    latest_chapter_links = []
    print(trs[0].get_text().split())
    for tr in trs[1:]:
        article_names.append(tr.td.a.string)
        links = tr.find_all(href=True)
        article_links.append(links[0].get('href'))
        latest_chapter_links.append(urljoin(WEBSITE_URL, links[1].get('href')))
        # 第一种方法和第二种等价, 返回一个列表，第三种方法返回的是字符串
        # text = tr.get_text().split()
        text = [text for text in
                tr.stripped_strings]  # 使用 .stripped_strings 可以去除多余空白内容:
        # text = tr.get_text(", ", strip=True)  # strip=True 去除获得文本内容的前后空白
        print(num, text)
        num += 1
    return article_names, article_links, latest_chapter_links


# 解析章节目录页面，返回章节名和地址
def parse_article_page(html, start_num):
    global FLAG
    article_soup = BeautifulSoup(html, 'lxml')
    article_name = article_soup.find('div', id='info').h1.string
    print(article_name)
    dds = article_soup.find('div', id='list').find_all('dd')
    if FLAG:
        dds = dds[start_num:]
        FLAG = False
    for dd in dds:
        chapter_link = urljoin(WEBSITE_URL, dd.a['href'])
        chapter_title = dd.string
        yield {
            "chapter_link": chapter_link,
            "chapter_title": chapter_title,
        }


# 解析文章页面，返回文章内容
def parse_chapter_page(html):
    chapter_soup = BeautifulSoup(html, 'lxml')
    # content = chapter_soup.find('div', id = 'content').get_text()
    content = chapter_soup.find('div', id='content')
    content.p.decompose()
    content = re.sub(r'<.*?>', '\n', str(content))
    # print(content)
    return content


def main():
    while True:
        data = input("请输入你想搜寻的书籍：")
        # data = '斗破苍穹'
        search_html = get_html(SEARCH_URL, data)
        article_names, article_links, latest_chapter_links = parse_search_page(search_html)
        if article_links:
            # print(len(article_link),'\n', len(latest_chapter_link))
            break

    choice = int(input("请选择你想看的书籍[数字]："))
    article_name = article_names[choice - 1]
    article_html = get_html(article_links[choice - 1])

    path = os.path.join(os.path.dirname(__file__), article_name + '.txt')
    path_saved = path + '.saved'
    # 每次开始运行程序时，先检查是否有下载记录，如果有，那么就继续下载
    with open(path, 'a', encoding='utf-8') as fp, open(path_saved, 'a+') as  sp:
        sp.seek(0, 0)
        start = sp.readlines()
        start_num = 0 if not start else int(start[-1].rstrip())
        for chapter in parse_article_page(article_html, start_num):
            chapter_link = chapter.get('chapter_link')
            chapter_title = chapter.get('chapter_title')
            # print(chapter_title)
            fp.write(chapter_title + "\n")
            chapter_html = get_html(chapter_link)
            # 如果下载太快,那就等一哈
            # while not chapter_html:
            #     print('等一哈,下载太快了...')
            #     time.sleep(10)
            #     chapter_html = get_html(chapter_link)
            content = parse_chapter_page(chapter_html)
            fp.write(content + "\n")
            print('\r', chapter_title, '下载完成', end='')
            start_num += 1
            sp.write(str(start_num) + '\n')
            time.sleep(0.2)
        print('\n', article_name, '下载完成')
        os.remove(path_saved)


if __name__ == "__main__":
    main()

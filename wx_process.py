import requests
from bs4 import BeautifulSoup
import re

def count_textchars(text):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)
    return cn_char_count, en_char_count
        
def get_content(url):
    if 'mp.weixin' in url:
        return get_wx_content(url)
    if 'baijiahao' in url:
        return get_bjh_content(url)
        
def get_wx_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取文章标题
    title = soup.find('h1', class_='rich_media_title').text.strip()
    print("标题：", title)

    # 提取文章作者
    author = soup.find('strong', class_='profile_nickname').text.strip()
    print("作者：", author)

    # 提取发布时间
    publish_time = soup.find('em', class_='rich_media_meta rich_media_meta_text').text.strip()
    print("发布时间：", publish_time)

    # 提取正文内容
    content = ''
    # 找到'div'标签，其class属性为'rich_media_content'
    container = soup.find('div', class_='rich_media_content')

    # 如果找到了容器，抓取其中的<p>和<section>标签内容
    if container:
        last_text = '' #辨别<section>中相同内容
        for tag in container.find_all(['p', 'section']):
            # 如果当前标签是<p>，将其内容添加到结果中
            if tag.name == 'p':
                content += tag.text + '\n'
                if tag.text != '':
                    last_text = tag.text
            # 如果当前标签是<section>，且其子节点中没有<p>
            elif tag.name == 'section' and not tag.find('p'):
                if tag.text != last_text:
                    content += tag.text + '\n'
                    if tag.text != '':
                        last_text = tag.text
    else:
        print("找不到指定的容器")

    # 删除多余的换行符
    content = re.sub('\n{3,}', '\n\n', content)
    content = '标题：' + title + '\n作者：' + author + '\n\n' + content

    cn_char_count, en_char_count = count_textchars(content)
    print("\n字数：", cn_char_count, en_char_count)
    # 如果字符数大于3000，仅保留前2500个字符
    if cn_char_count + en_char_count > 3000:
        content = content[:2500]
        
    return content

def get_bjh_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'BIDUPSID=99C3247B58571936BAFC9FD8A493FC1E; PSTM=1678622396; BAIDUID=99C3247B585719360DDCDA13FB020A1C:FG=1; BAIDUID_BFESS=99C3247B585719360DDCDA13FB020A1C:FG=1; BDRCVFR[C0p6oIjvx-c]=I67x6TjHwwYf0; delPer=0; PSINO=1; H_PS_PSSID=36544_38470_38368_38468_38289_38377_36807_38486_37923_38493; BDUSS=HIwdVlzNlZEVE41TXdWZTB0ZVRQN3k5Rmt1T3BaTWJ2Um5GZGo5YkR4S2J-VjVrRVFBQUFBJCQAAAAAAAAAAAEAAACZpWg5waLM5cn5yrXR6crSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJtwN2SbcDdkM; BDUSS_BFESS=HIwdVlzNlZEVE41TXdWZTB0ZVRQN3k5Rmt1T3BaTWJ2Um5GZGo5YkR4S2J-VjVrRVFBQUFBJCQAAAAAAAAAAAEAAACZpWg5waLM5cn5yrXR6crSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJtwN2SbcDdkM; ab_sr=1.0.1_YTdmZjYzMzFlMDliZDQ5MjdmM2ViZWNjN2M5ZjhlZDkyZGRjMmQ4ZWZjZGZiMWJhYzRkY2Y2MDYwM2JlNzg1MGFkZjE0M2UxMzBiNmRiNTU3YzIxNDExZDEwOTRmNTIzMjljNGVmNWU0Mjc2ZTJkM2NiMTJmMGMzOTUzNDIyNjU4ZjA1NmViOGQ0Y2Y4NDM5OWJmZTA5NDM3ZjE3NDY0Mg==',
        'Host': 'baijiahao.baidu.com',
        'Referer': 'https://passport.baidu.com/',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }

    # 发送HTTP GET请求并获取HTML内容
    response = requests.get(url, headers=headers)
    response.encoding = 'UTF-8'
    html = response.text
    print(response, "html text:", html)
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    title = soup.find('div', class_='_28fPT').text

    # 提取作者
    author = soup.find('p', class_='_7y5nA').text

    # 提取正文
    content_tags = soup.find_all('div', class_='_3ygOc')

    # 将所有正文内容拼接在一起
    content = ''.join([tag.text for tag in content_tags])

    print("标题：", title)
    print("作者：", author)
    print("正文：", content)
    content = '标题：' + title + '\n作者：' + author + '\n\n' + content
    return content
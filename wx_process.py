import requests
from bs4 import BeautifulSoup
import re

def split_text(text, max_length, index):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)
    
    print("\n字数：", cn_char_count, en_char_count)
    # Truncate text if it exceeds max_length
    if cn_char_count > max_length or en_char_count > max_length:
        last_newline = text.rfind('\n', 0, max_length)
        if last_newline != -1:
            text = text[:last_newline]

    # Split text into sub-strings
    content_list = []
    start = 0
    while start < len(text):
        end = start + index
        if end < len(text):
            next_newline = text.find('\n', end)
            if next_newline != -1:
                end = next_newline + 1
        content_list.append(text[start:end])
        start = end

    # Merge short sub-strings
    if len(content_list) > 1 and len(content_list[-1]) < 200:
        content_list[-2] += content_list[-1]
        del content_list[-1]

    with open('content_list.txt', 'w') as f:
        for content in content_list:
            f.write(content + '\n*****\n')

    return content_list
        
def get_content(url):
    if 'mp.weixin' in url:
        return get_wx_content(url)
    if 'baijiahao' or 'mbd.baidu' in url:
        return get_baidu_content(url)
    return 'Error'
        
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

    content_list = split_text(content, 6000, 2000)

    return content_list

def get_baidu_content(url):
    if 'baijiahao' in url:
        hostlink = 'baijiahao.baidu.com'
    if 'mbd.baidu' in url:
        hostlink = 'mbd.baidu.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'BIDUPSID=99C3247B58571936BAFC9FD8A493FC1E; PSTM=1678622396; BAIDUID=99C3247B585719360DDCDA13FB020A1C:FG=1; BAIDUID_BFESS=99C3247B585719360DDCDA13FB020A1C:FG=1; BDRCVFR[C0p6oIjvx-c]=I67x6TjHwwYf0; delPer=0; PSINO=1; H_PS_PSSID=36544_38470_38368_38468_38289_38377_36807_38486_37923_38493; BDUSS=HIwdVlzNlZEVE41TXdWZTB0ZVRQN3k5Rmt1T3BaTWJ2Um5GZGo5YkR4S2J-VjVrRVFBQUFBJCQAAAAAAAAAAAEAAACZpWg5waLM5cn5yrXR6crSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJtwN2SbcDdkM; BDUSS_BFESS=HIwdVlzNlZEVE41TXdWZTB0ZVRQN3k5Rmt1T3BaTWJ2Um5GZGo5YkR4S2J-VjVrRVFBQUFBJCQAAAAAAAAAAAEAAACZpWg5waLM5cn5yrXR6crSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJtwN2SbcDdkM; ab_sr=1.0.1_YTdmZjYzMzFlMDliZDQ5MjdmM2ViZWNjN2M5ZjhlZDkyZGRjMmQ4ZWZjZGZiMWJhYzRkY2Y2MDYwM2JlNzg1MGFkZjE0M2UxMzBiNmRiNTU3YzIxNDExZDEwOTRmNTIzMjljNGVmNWU0Mjc2ZTJkM2NiMTJmMGMzOTUzNDIyNjU4ZjA1NmViOGQ0Y2Y4NDM5OWJmZTA5NDM3ZjE3NDY0Mg==',
        'Host': hostlink,
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
    print(response)
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    title = soup.find('div', class_='_28fPT').text

    # 提取作者
    author = soup.find('p', class_='_7y5nA').text

    # 提取正文
    content_tags = soup.find_all('div', class_='_3ygOc')

    # 将所有正文内容拼接在一起
    content = '\n'.join([tag.text for tag in content_tags])
    
    content = '标题：' + title + '\n作者：' + author + '\n\n' + content
    
    content_list = split_text(content, 6000, 2000)
    
    return content_list
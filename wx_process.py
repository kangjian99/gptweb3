import requests
from bs4 import BeautifulSoup
import re

def get_wx_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    def count_chars(text):
        cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
        cn_chars = cn_pattern.findall(text)

        en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
        en_chars = en_pattern.findall(text)

        cn_char_count = len(cn_chars)
        en_char_count = len(en_chars)
        return cn_char_count, en_char_count

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

    cn_char_count, en_char_count = count_chars(content)
    print("\n字数：", cn_char_count, en_char_count)
    # 如果字符数大于3000，仅保留前2500个字符
    if cn_char_count + en_char_count > 3000:
        content = content[:2500]
        
    return content
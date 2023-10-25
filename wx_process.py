import requests
from bs4 import BeautifulSoup
import re

index_max = 8000

def extract_links(text):
    # 更新后的 URL 正则表达式，可以匹配没有 www 的链接
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    # 在文本中查找所有匹配的 URL
    urls = url_pattern.findall(text)
    
    # 如果需要，为没有 http:// 或 https:// 的链接添加 http:// 前缀
    # urls = ['http://' + url if not url.startswith('http') else url for url in urls]
    
    # 去掉链接后的文本
    cleaned_text = re.sub(url_pattern, '', text)
    
    return urls, cleaned_text

def split_text(text, max_length, index):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)
    
    print("\n总字数，中文，英文：", len(text), cn_char_count, en_char_count)
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

    if len(content_list) > 1:
        with open('content_list.txt', 'w') as f:
            for content in content_list:
                f.write(content + '\n*****\n')

    return content_list
        
def get_content(url):
    if 'mp.weixin' in url:
        return get_wx_content(url)
    if 'baijiahao' in url or 'mbd.baidu' in url:
        return get_baidu_content(url)
    if 'dongchedi' in url:
        return get_dchd_content(url)
    if 'toutiao' in url:
        return get_tt_content(url)
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

    content_list = split_text(content, 20000, index_max)

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
    title = soup.find('div', class_='_3tNyU').text

    # 提取作者
    author = soup.find('span', class_='_2gGWi').text

    # 提取正文
    content_tags = soup.find_all('div', class_='dpu8C _2kCxD')

    # 将所有正文内容拼接在一起
    content = '\n'.join([tag.text for tag in content_tags])
    
    content = '标题：' + title + '\n作者：' + author + '\n\n' + content
    
    content_list = split_text(content, 20000, index_max)
    
    return content_list

def get_dchd_content(url):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'cookie': 'tt_web_version=new; is_dev=false; is_boe=false; ttwid=1%7CYy-BK_TKgQyK7pk2pSTbcrZFp6kWOz785xGMG4ci6l4%7C1698209450%7Cc6503d83f157e6b1b335f8581c5a5ce2d70f538b64ba2799696d8d833ecd67d1; tt_webid=7293754007183869449; Hm_lvt_3e79ab9e4da287b5752d8048743b95e6=1698209452; city_name=%E5%8C%97%E4%BA%AC; s_v_web_id=verify_lo5a281l_E0aRrNrz_aGQK_4t5Y_BYwj_AHNJRSqT0Dxy; _gid=GA1.2.353875491.1698209458; Hm_lpvt_3e79ab9e4da287b5752d8048743b95e6=1698211893; _ga=GA1.1.364565764.1686876659; msToken=_DL4R-_UCzRAVBsOK1g_c9nfzA9q0myOuI8Nvoo8yUjIn-LR0J1wirmqIcesgh7M8EnDu7oDnrs_qxEjRfJpwjZYq_KPGczRfWA1_Yo=; _ga_YB3EWSDTGF=GS1.1.1698211871.4.1.1698211981.57.0.0',
        'referer': url,
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'}

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取文章标题
    title = soup.find('h1', class_="jsx-1513769121 title").text.strip()
    print("标题：", title)

    # 提取文章作者
    author = soup.find('a', class_="jsx-1513769121 source g-active-link-text").text.strip()
    print("作者：", author)

    # 提取发布时间
    publish_time = soup.find('span', class_="jsx-1513769121 time").text.strip()
    print("发布时间：", publish_time)

    # 提取正文内容
    content = ''
    # 找到 'section' 标签，其 id 属性为 'article'
    section = soup.find('section', id='article')
    # 如果找到了 section，抓取其中的 <p> 标签内容
    if section:
        for p_tag in section.find_all('p'):
            content += p_tag.get_text() + '\n'
    else:
        print("找不到指定的 section")

    content = '标题：' + title + '\n作者：' + author + '\n\n' + content

    content_list = split_text(content, 20000, index_max)

    return content_list

def get_tt_content(url):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'cookie': '__ac_signature=_02B4Z6wo00f01xA9xAAAAIDAhOufD1EU9dMQHcCAAKA296; tt_webid=7215872493613008440; ttcid=1cfa7ab5c4614326b0d375faf038b4bd28; csrftoken=8cfaba15f85bbd11c84525ff5beb1255; _ga=GA1.1.1287499458.1680076252; s_v_web_id=verify_libfqro9_JjEzLdW1_i5Gp_4TPs_8paC_ieX7x4dgSwtA; local_city_cache=%E5%8C%97%E4%BA%AC; passport_csrf_token=18c3f696801c2282c8eafdd1804d2bee; _S_WIN_WH=1510_852; _S_DPR=2; _S_IPAD=0; n_mh=MJsBwg-wlGGe2CNMPTg43RYAoHiWBGJ9fHISF4kDg-8; sso_uid_tt=a10931b713bd2ace0d83cb612d7f09bf; sso_uid_tt_ss=a10931b713bd2ace0d83cb612d7f09bf; toutiao_sso_user=952c4be4bcc34f6b104ef71aa0efd92d; toutiao_sso_user_ss=952c4be4bcc34f6b104ef71aa0efd92d; sid_ucp_sso_v1=1.0.0-KGE2N2Y0ZDUwNGVjMzRkM2ZhNTcyNTY3MmYyMjUwYzA4ZTI5MzA5M2QKGwie96DvGBDri6-kBhgYIAww0__VugU4BkD0BxoCbGYiIDk1MmM0YmU0YmNjMzRmNmIxMDRlZjcxYWEwZWZkOTJk; ssid_ucp_sso_v1=1.0.0-KGE2N2Y0ZDUwNGVjMzRkM2ZhNTcyNTY3MmYyMjUwYzA4ZTI5MzA5M2QKGwie96DvGBDri6-kBhgYIAww0__VugU4BkD0BxoCbGYiIDk1MmM0YmU0YmNjMzRmNmIxMDRlZjcxYWEwZWZkOTJk; passport_auth_status=9315fda5e6f2caa53ff8dd020d75229e%2C; passport_auth_status_ss=9315fda5e6f2caa53ff8dd020d75229e%2C; sid_guard=e1512f203550c21987d92dc86788d922%7C1686881772%7C5184001%7CTue%2C+15-Aug-2023+02%3A16%3A13+GMT; uid_tt=4766faec1529edea608729aab7f4a09a; uid_tt_ss=4766faec1529edea608729aab7f4a09a; sid_tt=e1512f203550c21987d92dc86788d922; sessionid=e1512f203550c21987d92dc86788d922; sessionid_ss=e1512f203550c21987d92dc86788d922; sid_ucp_v1=1.0.0-KDBmODBkMDU3ODI3NGY0ZmM2Yjg0ZDZlZjFmNjZlNjJiYTg4N2YwMTkKFQie96DvGBDsi6-kBhgYIAw4BkD0BxoCaGwiIGUxNTEyZjIwMzU1MGMyMTk4N2Q5MmRjODY3ODhkOTIy; ssid_ucp_v1=1.0.0-KDBmODBkMDU3ODI3NGY0ZmM2Yjg0ZDZlZjFmNjZlNjJiYTg4N2YwMTkKFQie96DvGBDsi6-kBhgYIAw4BkD0BxoCaGwiIGUxNTEyZjIwMzU1MGMyMTk4N2Q5MmRjODY3ODhkOTIy; store-region=cn-bj; store-region-src=uid; odin_tt=46681f6e7b3aa0b5ee17474fa546b48cca5c0b559342d0423c00e565c9bfa2f9224e0953758b13a4361dd92ee6d57958; _ga_QEHZPBE5HH=GS1.1.1686879437.6.1.1686881777.0.0.0; tt_anti_token=vRV6npBSa3B4v5-feba4d186d346e97ed22334172ffb1b9d76a3704d359e8d874da6a760c253efd; ttwid=1%7CDmJFaTgEYgKBKp7CGB6pzRXB-prJ_gTUpOxDPY8ii74%7C1686881778%7Cef12b27cb948fe17f0ad681204332ae9804bbe008a60e9a8175b3641d5a3ec82; tt_scid=UINlxdzddw.CVr-qXOu5.iglvfNDlaVESagl7n2u1h5Ij.LZWXNV2xBMoAWurquG320e; msToken=5BcTWycxubgx4FMvWt0ZpoCEPltprIemlSqkWyeN_CGoy4Ed9zoTSjnr4cfOYeCjKLsltxS4m_BV6NhGNohdh0cpXX253xm3p1KJuNRXLn8=',
        'referer': url,
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    # print(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到div标签，其class属性为'article-content'
    container = soup.find('div', class_='article-content')

    if container:
        # 提取文章标题
        title = soup.find('h1').text.strip()
        print("标题：", title)

        # 提取发布时间
        publish_time = soup.find('div', class_='article-meta').find('span').text.strip()
        print("发布时间：", publish_time)

        # 提取文章作者
        author = soup.find('span', class_='name').find('a').text.strip()
        print("作者：", author)

        # 提取正文内容
        content = ''
        article = soup.find('article', class_='syl-article-base tt-article-content syl-page-article syl-device-pc')
        for paragraph in article.find_all('p'):
            content += paragraph.text + '\n'

    else:
        print("找不到指定的容器")

    content = '标题：' + title + '\n作者：' + author + '\n\n' + content

    content_list = split_text(content, 20000, index_max)

    return content_list

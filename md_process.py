import re
import markdown
import html

def is_html(text):
    html_pattern = re.compile(r'.*<\S+>.*')
    return bool(html_pattern.search(text) and not ("include <" in text and "```" in text)) # c++代码单独判断

def generate_markdown_message(text):
    if text.startswith("\n\n"):
        text = text[2:]

    if is_html(text):
        escaped_text = html.escape(text) # 将HTML标签转换为实体
        text = f"<pre style='white-space: pre-wrap;'>{escaped_text}</pre>"
        return text
      
    pattern = r'#{2,6}(?!\w)|\*\*[\s\S]*?\*\*|\*[\s\S]*?\*|\||^-{1,}\s|```'
    is_markdown = re.search(pattern, text) # 先判断是否markdown
    if is_markdown:
        text = text.replace("\n\n\n", "\n\n")
        is_codeblock = bool('```' in text)
        if is_codeblock:
            text = text.replace("#", "%35%")
            text = text.replace("\n\n", "\n")
            # 获取text中```出现的次数
            num_ticks = text.count('```')
            # 如果出现次数是奇数，则在text的末尾添加```
            if num_ticks % 2 == 1:
                text += '```' if text[-1] != '`' else '`'
        markdown_message = markdown.markdown(text, extensions=["tables", "nl2br"]) # 将返回的字符串转换为Markdown格式的HTML标记
        if is_codeblock:
            markdown_message = markdown_message.replace("%35%", "#")
            markdown_message = re.sub(r'^(#|\/\/)', '\n\\1', markdown_message, flags=re.MULTILINE)
        return markdown_message
    else:
        text = text.replace("\n", "<br>")
        return text

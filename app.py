from flask import Flask, request, render_template, session, redirect, url_for, flash, Response
import re
import json
import uuid
import time
from datetime import datetime
from settings import *
from db_process import *
from md_process import *
from wx_process import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SESSION_SECRET_KEY # SECRET_KEY是Flask用于对session数据进行加密和签名的一个关键值。如果没有设置将无法使用session

stream_data = {}
table_name = 'prompts'

def Chat_Completion(model, question, tem, messages, stream):
    try:
        messages.append({"role": "user", "content": question})
        print("generate_text:", messages, "\nmodel:", model)
        response = openai.ChatCompletion.create(
        model= model,
        messages= messages,
        temperature=tem,
        stream=stream,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
        )
        if not stream:
            print(f"{response['usage']}\n")
            session['tokens'] = response['usage']['total_tokens']
            return response["choices"][0]['message']['content']
        return response
        
    except Exception as e:
        print(e)
        return "Connection Error! Please try again."

def send_gpt(model, prompt, tem, messages, user_id):
    partial_words = ""
    response = Chat_Completion(model, prompt, tem, messages, True)
    
    # 添加如下调试信息
    # print("Response:", response)
    # print("Response status code:", response.status_code)
    # print("Response headers:", response.headers)

    for chunk in response:
        if chunk:
            # print("Decoded chunk:", chunk)  # 添加这一行以打印解码的块
            try:
                if "delta" in chunk['choices'][0]:
                    finish_reason = chunk['choices'][0]['finish_reason']
                    if finish_reason == "stop":
                        break
                    if "content" in chunk['choices'][0]["delta"]:
                        partial_words += chunk['choices'][0]["delta"]["content"]
                        # print("Content found:", partial_words)  # 添加这一行以打印找到的内容
                        yield {'content': partial_words}
                    else:
                        print("No content found in delta:", chunk['choices'][0]["delta"])  # 添加这一行以打印没有内容的 delta
                else:
                    pass
            except json.JSONDecodeError:
                pass

#        print(f"{response['usage']}\n")
#        session['tokens'] = response['usage']['total_tokens']
        
def count_chars(text, user_id, messages):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    tokens = num_tokens(text)
    # 将当前统计结果添加为字典
    stats = {'user_id': user_id, 'datetime': now, 'cn_char_count': cn_char_count, 'en_char_count': en_char_count, 'tokens': tokens}
    print(stats)
    
    if stats:
        insert_db(stats, user_id, messages)

    return 'success'
    
@app.route('/', methods=['GET', 'POST'])
def get_request_json():
    # global session['messages']
    prompts = read_table_data(table_name)
    if request.method == 'POST':
        if 'clear' in request.form:
            session['messages'] = [] #不改变session['logged_in']
            clear_messages(session['user_id'])
            return redirect(url_for('get_request_json'))
        else:
            return render_template('chat.html', model=model, user_id=session.get('user_id'), pid=",".join(prompts.keys()))
    else:
        session['messages'] = []
        if 'user_id' in session and 'password' in session and authenticate_user(session['user_id'], session['password']) == True:
            clear_messages(session['user_id'])
            return render_template('chat.html', model=model, user_id=session.get('user_id'), question=0, pid = ",".join(prompts.keys()))
        else:
            return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session.update(logged_in=True, user_id=username, password=password)
            return redirect(url_for('get_request_json'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # session.pop('logged_in', None)
    session.clear()
    return redirect(url_for('get_request_json'))

@app.route('/stream_get/<unique_url>', methods=['GET'])
def stream_get(unique_url):
    if unique_url in stream_data:
        response_data = stream_data[unique_url]['response']
        # del stream_data[unique_url]
        return Response(response_data, content_type='text/event-stream')
    else:
        return "Error: Invalid URL", 400

@app.route('/stream', methods=['POST'])
def stream():
    if 'messages' not in session:
        session['messages'] = []
    prompts = read_table_data(table_name)

    if len(request.form['question']) < 1:
        return redirect(url_for('get_request_json'))

    user_id = session.get('user_id')
    keyword = request.form['question']
    context = request.form['context']
    temperature = float(request.form['temperature'])
    template_file = request.files.get('template_file')
    if not template_file:
        dropdown = request.form.get('dropdown')
        prompt_template = list(prompts.items())[int(dropdown) - 1] #元组
    else:
        prompt_template = template_file.read().decode('utf-8')
    question = ['']
    
    session['messages']  = get_user_messages(user_id)
    if session['messages'] == []:
        words = int(request.form['words']) if request.form['words'] != '' else 800
        if '{url}' in prompt_template[1]:
            url_list = extract_links(keyword+context)
            text = get_content(url_list[0].strip())
            if len(url_list) == 1 or text == 'Error': # 单链接或非链接
                if text == 'Error':
                    text = keyword +'\n' + context
                    question[0] = prompt_template[1].format(url=text, context=context.strip(), words=words)
                else:
                    question[0] = prompt_template[1].format(url=text[0], context=context.strip(), words=words)
                    question[1:] = [list(prompts.values())[-2].format(content=t, count=i+2) for i, t in enumerate(text[1:])] #超长用特定模版处理
            else:
                merge_text = ''
                first_url_text = text[0] + '\n'
                print("链接1: ", text[0])
                count = 2
                for line in url_list[1:]:
                    text = get_content(line)
                    print(f"链接{count}:{text}")
                    if (text != 'Error') and (num_tokens(first_url_text+merge_text+text[0])<10000):
                        merge_text += text[0] + '\n'
                        count += 1
                if '定制文章' in prompt_template[0]:
                   question[0] = f"{prompt_template[1].format(keyword=keyword, url=first_url_text, context=merge_text+context.strip(), words=words)!s}" 
                else:
                    question[0] = f"{prompt_template[1].format(url=first_url_text+merge_text, context=context.strip(), words=words)!s}"
        elif '{lang}' in prompt_template[1]:
            text = split_text(keyword, 20000, 6000)
            question = [prompt_template[1].format(lang=t) for t in text]            
        else:
            question[0] = f"{prompt_template[1].format(keyword=keyword, words=words, context=context)!s}"
    else:
        if 'act' in prompt_template[0]:
            question[0] = keyword + '\n' + prompt_template[1].split('\n')[0]
        else:
            question[0] = keyword
        
    messages = session['messages']
    # tokens = session.get('tokens')
    def process_data():
        # token_counter = 0
        nonlocal messages
        counter = 0
        for prompt in question:
            res = None
            if counter > 0:
                messages = []
                # time.sleep(5)
            counter += 1
            model_gpt = model_16k if num_tokens(prompt) > 2500 else model
            try:
                for res in send_gpt(model_gpt, prompt, temperature, messages, user_id):
                    if 'content' in res:
                        markdown_message = generate_markdown_message(res['content'])
                        # print(f"Yielding markdown_message: {markdown_message}")  # 添加这一行
                        # token_counter += 1
                        yield f"data: {json.dumps({'data': markdown_message})}\n\n" # 将数据序列化为JSON字符串
            finally:
                # 如果生成器停止，仍然会执行
                messages.append({"role": "assistant", "content": res['content']})
                join_message = "".join([msg["content"] for msg in messages])
                print("精简前messages:", messages)
                rows = history_messages(user_id, prompt_template[0]) # 历史记录条数
                if len(messages) > rows:
                    messages = messages[-rows:] #对话仅保留最新rows条
                if rows == 0:
                    save_user_messages(user_id, []) # 清空历史记录
                else:
                    save_user_messages(user_id, messages)
                # session['messages'] = messages
                count_chars(join_message, user_id, messages)
            
    if stream_data:
        stream_data.pop(list(stream_data.keys())[0])  # 删除已使用的URL及相关信息              
    unique_url = uuid.uuid4().hex
    stream_data[unique_url] = {
        'response': process_data(),
        'messages': session['messages'],
    }
    
    print(session)    
    session['tokens'] = 0
    return 'stream_get/' + unique_url                


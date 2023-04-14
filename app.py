from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify, Response, stream_with_context
import re
import json
import requests
import uuid
from datetime import datetime
from settings import *
from db_process import *
from md_process import *
from wx_process import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SESSION_SECRET_KEY # SECRET_KEY是Flask用于对session数据进行加密和签名的一个关键值。如果没有设置将无法使用session

timeout_streaming = 5
stream_data = {}

def get_prompt_templates():
    filename = 'prompts.txt'
    with open(filename, 'r') as f:
        lines = f.readlines()
    prompts = {}
    for i in range(0, len(lines)-1, 2):
        prompts[lines[i].strip()] = lines[i+1].strip()
    return prompts

def generate_text(prompt, tem, messages):
    try:
        messages.append({"role": "user", "content": prompt})
        print("generate_text:", messages)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }

        # history = [construct_system(system_prompt), *history]

        payload = {
            "model": model,
            "messages": messages,  # [{"role": "user", "content": f"{inputs}"}],
            "temperature": tem,  # 1.0,
            "n": 1,
            "stream": True,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }
        timeout = timeout_streaming

        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=timeout)
        return response

    except Exception as e:
        print(e)
        return "Connection Error! Please try again."

def send_gpt(prompt, tem, messages, user_id):
    partial_words = ""
    response = generate_text(prompt, tem, messages)
    
    # 添加如下调试信息
    # print("Response:", response)
    # print("Response status code:", response.status_code)
    # print("Response headers:", response.headers)

    for chunk in response.iter_lines():
        if chunk:
            chunk = chunk.decode()
            # print("Decoded chunk:", chunk)  # 添加这一行以打印解码的块
            chunklength = len(chunk)
            data = json.loads(chunk[6:])
            # print(data['choices'][0]["delta"])
            try:
                if chunklength > 6 and "delta" in data['choices'][0]:
                    finish_reason = data['choices'][0]['finish_reason']
                    if finish_reason == "stop":
                        break
                    if "content" in data['choices'][0]["delta"]:
                        partial_words += data['choices'][0]["delta"]["content"]
                        # print("Content found:", partial_words)  # 添加这一行以打印找到的内容
                        yield {'content': partial_words}
                    else:
                        print("No content found in delta:", data['choices'][0]["delta"])  # 添加这一行以打印没有内容的 delta
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
    prompts = get_prompt_templates()
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
    prompts = get_prompt_templates()

    if len(request.form['question']) < 1:
        return redirect(url_for('get_request_json'))

    user_id = session.get('user_id')
    keyword = request.form['question']
    context = request.form['context']
    session['messages']  = get_user_messages(user_id)
    temperature = float(request.form['temperature'])

    if session['messages'] == []:
        words = int(request.form['words']) if request.form['words'] != '' else 800
        template_file = request.files.get('template_file')
        if not template_file:
            dropdown = request.form.get('dropdown')
            prompt_template = list(prompts.values())[int(dropdown) - 1]
        else:
            prompt_template = template_file.read().decode('utf-8')
        if 'url' in prompt_template:
            keyword_list = [line.rstrip() for line in keyword.split('\n') if line.strip()]
            if len(keyword_list) == 1:
                text = get_content(keyword)
                question = f"{prompt_template.format(url=text)!s}"
            else:
                extract_text = ''
                count = 1
                for line in keyword_list:
                    messages = []
                    text = get_content(line)
                    print(text)
                    if text != 'Error':
                        question = f"{prompt_template.format(url=text)!s}"
                        try:
                            messages.append({"role": "user", "content": question})
                            response = openai.ChatCompletion.create(
                            model= model,
                            messages= messages,
                            temperature=temperature,
                            top_p=1.0,
                            frequency_penalty=0,
                            presence_penalty=0
                            )
                            print(f"{response['usage']}\n")
                            session['tokens'] = response['usage']['total_tokens']
                        except Exception as e:
                            print(e)
                            return "Connection Error! Please try again."
                        messages.append({"role": "assistant", "content": response["choices"][0]['message']['content']})
                        join_message = "".join([msg["content"] for msg in messages])
                        print("精简前messages:", messages)
                        # rows = history_messages(user_id) # 历史记录条数
                        # if len(messages) > rows:
                        #     messages = messages[-rows:] #仅保留最新两条
                        # session['messages'] = messages
                        count_chars(join_message, user_id, messages)
                        extract_text += f'【文章{count}：】\n' + response["choices"][0]['message']['content'] + '\n'
                        count += 1
                prompt_template = list(prompts.values())[-1]
                question = f"{prompt_template.format(words=words, context=extract_text)!s}"
        else:
            question = f"{prompt_template.format(keyword=keyword, words=words, context=context)!s}"
    else:
        question = keyword
        
    messages = session['messages']
    # tokens = session.get('tokens')
    def process_data():
        # token_counter = 0
        res = None
        nonlocal messages
        try:
            for res in send_gpt(question, temperature, messages, user_id):
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
            # rows = history_messages(user_id) # 历史记录条数
            # if len(messages) > rows:
            #     messages = messages[-rows:] #仅保留最新两条
            save_user_messages(user_id, []) # messages
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5858)
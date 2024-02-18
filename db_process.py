#import pyodbc
import json
import tiktoken
from settings import *
from supabase import create_client, Client

supabase: Client = create_client(DB_URL, DB_KEY)

def authenticate_user(username, password):
    response = supabase.table('userinfo').select('password').eq('username', username).execute()

    if 'error' in response:
        print('Error:', response.error)
        return False

    user_data = response.data

    if user_data:
        stored_password = user_data[0]['password']
        if stored_password == password:
            return True

    return False
    
def read_table_data(table_name):
    # 从表中读取数据
    query = supabase.table(table_name).select("*")
    response = query.execute()

    # 检查错误
    if 'error' in response:
        raise RuntimeError(f"Error reading table {table_name}: {response.text}")

    # 将数据转换为字典
    prompts_dict = {row["name"]: row["prompt"] for row in response.data}

    return prompts_dict

def insert_db(result, user_id=None, messages=[]):
    # 获取要插入的结果数据
    now = result.get('datetime')
    user_id = result.get('user_id')
    cn_char_count = result.get('cn_char_count')
    en_char_count = result.get('en_char_count')
    tokens = result.get('tokens')

    # If user_id is provided, insert messages into the table
    if user_id:
        messages_str = json.dumps(messages, ensure_ascii=False)
        response = supabase.table('gptweb_stats').insert({
            'user_id': user_id,
            'datetime': now,
            'messages': messages_str,
            'tokens': tokens
        }).execute()

        # Check for errors in the response
        if 'error' in response:
            raise RuntimeError(f"Error inserting into session table: {response['error']}")
               
def clear_messages(user_id):
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(f'{directory}/messages_{user_id}.txt', 'w') as file:
        file.truncate(0)
        
def save_user_messages(user_id, messages):
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(f'{directory}/messages_{user_id}.txt', 'w') as f:
        for message in messages:
            f.write(json.dumps(message) + '\n')
            
def get_user_messages(user_id):
    messages = []
    try:
        with open(f'{directory}/messages_{user_id}.txt', 'r') as f:
            for line in f.readlines():
                messages.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass
    return messages

def history_messages(user_id, prompt_template):
    rows = 0
    if user_id == 'sonic' or 'auto' in prompt_template:
        rows = 4
    if 'smart' in prompt_template:
        rows = 5
    if 'Chat' in prompt_template:
        rows = 2
    return rows

def num_tokens(string: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

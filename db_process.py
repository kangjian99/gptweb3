import pyodbc
import json
import tiktoken
from settings import *
    
def authenticate_user(username, password):
    # 连接到 Azure SQL 数据库，并检查 user_info 表格中是否存在提供的用户名和密码
    cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={db_username};PWD={db_password}')
    cursor = cnxn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_info WHERE user_id = ? AND password = ?", (username, password))
    count = cursor.fetchone()[0]

    # 关闭数据库连接
    cursor.close()
    cnxn.close()

    # 如果找到匹配的用户名和密码，则返回 True，否则返回 False
    return count == 1

def insert_db(result, user_id=None, messages=[]):
    # 连接到数据库
    cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={db_username};PWD={db_password}')
    
    # 获取要插入的结果数据
    now = result.get('datetime')
    user_id = result.get('user_id')
    cn_char_count = result.get('cn_char_count')
    en_char_count = result.get('en_char_count')
    tokens = result.get('tokens')
    
    # 构建插入语句并执行
    query = "INSERT INTO stats (user_id, datetime, cn_char_count, en_char_count, tokens) VALUES (?, ?, ?, ?, ?);"
    params = (user_id, now, cn_char_count, en_char_count, tokens)
    cursor = cnxn.cursor()
    cursor.execute(query, params)
    
    if user_id:
        messages_str = json.dumps(messages, ensure_ascii=False)
        # 构建插入语句并执行
        query = "INSERT INTO session (user_id, messages) VALUES (?, ?);"
        params = (user_id, messages_str)
        cursor = cnxn.cursor()
        cursor.execute(query, params)
        
    cnxn.commit()
    cnxn.close()
    
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
    rows = 2
    if user_id == 'sonic':
        rows = 4
    if 'Chat' not in prompt_template:
        rows = 0
    return rows

def num_tokens(string: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens
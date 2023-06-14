import os
import openai

model = 'gpt-3.5-turbo' # or text-davinci-003
model_16k = 'gpt-3.5-turbo-16k'

SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY')

server = 'tcp:kj99.database.windows.net,1433'
database = 'database'
db_username = os.environ.get('DB_USERNAME')
db_password = os.environ.get('DB_PASSWORD')
driver = '{ODBC Driver 18 for SQL Server}'

openai.api_key = os.environ.get('OPENAI_API_KEY')

directory = 'session_messages'

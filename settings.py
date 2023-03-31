import os
import openai

# openai.api_key = "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"
model = 'gpt-3.5-turbo' # or text-davinci-003
SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY')

server = 'tcp:kj99.database.windows.net,1433'
database = 'database'
db_username = os.environ.get('DB_USERNAME')
db_password = os.environ.get('DB_PASSWORD')
driver = '{ODBC Driver 18 for SQL Server}'

openai_api_key = os.environ.get('OPENAI_API_KEY')
API_URL = "https://api.openai.com/v1/chat/completions"

directory = 'session_messages'

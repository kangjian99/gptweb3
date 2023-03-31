import os
import openai

# openai.api_key = "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"
model = 'gpt-3.5-turbo' # or text-davinci-003
SESSION_SECRET_KEY = 'Drmhe86EPcv0fN_81Zj-nA'

server = 'tcp:kj99.database.windows.net,1433'
database = 'database'
db_username = 'kangjian99'
db_password = 'bibqen-6vavTi-jugson'
driver = '{ODBC Driver 18 for SQL Server}'

openai_api_key = "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"
API_URL = "https://api.openai.com/v1/chat/completions"

directory = 'session_messages'
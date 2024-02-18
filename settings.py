import os
from openai import OpenAI

#from dotenv import load_dotenv
#load_dotenv()

client = OpenAI(
  api_key = os.environ.get('OPENAI_API_KEY'),
)
  
model = 'gpt-3.5-turbo-0125'
model_4 = 'gpt-4-0125-preview'

SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY')

#server = 'tcp:kj99.database.windows.net,1433'
#database = 'db'
#db_username = os.environ.get('DB_USERNAME')
#db_password = os.environ.get('DB_PASSWORD')
#driver = '{ODBC Driver 18 for SQL Server}'

DB_URL: str = os.environ.get("SUPABASE_URL")
DB_KEY: str = os.environ.get("SUPABASE_KEY")

#openai.api_key = os.environ.get('OPENAI_API_KEY')

directory = 'session_messages'

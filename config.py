import os 
from dotenv import load_dotenv



load_dotenv()
BOT_TOKEN = os.getenv("TOKEN_BOT")

EXCHANGE_API = os.getenv("EXCHANGE_API")
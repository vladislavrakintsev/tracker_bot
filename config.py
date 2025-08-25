import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Google Sheets
SHEET_ID = os.getenv('SHEET_ID')
CREDENTIALS_FILE = 'credentials.json'

# Названия листов
PROJECTS_SHEET = 'Projects'
TASKS_SHEET = 'Tasks'
NOTES_SHEET = 'Notes'
SECRETS_SHEET = 'Secrets'
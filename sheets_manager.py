import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDENTIALS_FILE, SHEET_ID
from datetime import datetime


class SheetsManager:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(SHEET_ID)
        self._initialize_sheets()

    def _initialize_sheets(self):
        """Создает листы если их нет"""
        try:
            worksheets = [ws.title for ws in self.sheet.worksheets()]

            # Projects sheet
            if 'Projects' not in worksheets:
                ws = self.sheet.add_worksheet(title='Projects', rows=1000, cols=5)
                ws.append_row(['ID', 'Name', 'Description', 'Created', 'Status'])

            # Tasks sheet
            if 'Tasks' not in worksheets:
                ws = self.sheet.add_worksheet(title='Tasks', rows=1000, cols=8)
                ws.append_row(['ID', 'Project', 'Title', 'Description', 'Status', 'Priority', 'Deadline', 'Created'])

            # Notes sheet
            if 'Notes' not in worksheets:
                ws = self.sheet.add_worksheet(title='Notes', rows=1000, cols=6)
                ws.append_row(['ID', 'Title', 'Content', 'Tags', 'Created', 'Project'])

            # Secrets sheet
            if 'Secrets' not in worksheets:
                ws = self.sheet.add_worksheet(title='Secrets', rows=1000, cols=5)
                ws.append_row(['ID', 'Name', 'Description', 'Created', 'Data'])
        except Exception as e:
            print(f"Ошибка инициализации таблиц: {e}")

    # PROJECTS
    def get_projects(self):
        try:
            worksheet = self.sheet.worksheet('Projects')
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            print(f"Ошибка получения проектов: {e}")
            return []

    def add_project(self, name, description=""):
        try:
            worksheet = self.sheet.worksheet('Projects')
            new_id = len(worksheet.get_all_records()) + 1
            worksheet.append_row([
                new_id,
                name,
                description,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active'
            ])
            return new_id
        except Exception as e:
            print(f"Ошибка добавления проекта: {e}")
            return None

    def delete_project(self, project_id):
        try:
            worksheet = self.sheet.worksheet('Projects')
            records = worksheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if int(record['ID']) == int(project_id):
                    worksheet.delete_rows(i)
                    return True
            return False
        except Exception as e:
            print(f"Ошибка удаления проекта: {e}")
            return False

    # TASKS
    def get_tasks(self, project_name=None):
        try:
            worksheet = self.sheet.worksheet('Tasks')
            records = worksheet.get_all_records()
            if project_name:
                records = [r for r in records if r['Project'] == project_name]
            return records
        except Exception as e:
            print(f"Ошибка получения задач: {e}")
            return []

    def add_task(self, project, title, description="", priority="medium", deadline=""):
        try:
            worksheet = self.sheet.worksheet('Tasks')
            new_id = len(worksheet.get_all_records()) + 1
            worksheet.append_row([
                new_id,
                project,
                title,
                description,
                "todo",
                priority,
                deadline,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            return new_id
        except Exception as e:
            print(f"Ошибка добавления задачи: {e}")
            return None

    def update_task_status(self, task_id, status):
        try:
            worksheet = self.sheet.worksheet('Tasks')
            records = worksheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if int(record['ID']) == int(task_id):
                    worksheet.update_cell(i, 5, status)  # Status column
                    return True
            return False
        except Exception as e:
            print(f"Ошибка обновления задачи: {e}")
            return False

    # NOTES
    def get_notes(self, project_name=None):
        try:
            worksheet = self.sheet.worksheet('Notes')
            records = worksheet.get_all_records()
            if project_name:
                records = [r for r in records if r['Project'] == project_name]
            return records
        except Exception as e:
            print(f"Ошибка получения заметок: {e}")
            return []

    def add_note(self, title, content, tags="", project=""):
        try:
            worksheet = self.sheet.worksheet('Notes')
            new_id = len(worksheet.get_all_records()) + 1
            worksheet.append_row([
                new_id,
                title,
                content,
                tags,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                project
            ])
            return new_id
        except Exception as e:
            print(f"Ошибка добавления заметки: {e}")
            return None

    # SECRETS
    def get_secrets(self):
        try:
            worksheet = self.sheet.worksheet('Secrets')
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            print(f"Ошибка получения секретов: {e}")
            return []

    def add_secret(self, name, description="", data=""):
        try:
            worksheet = self.sheet.worksheet('Secrets')
            new_id = len(worksheet.get_all_records()) + 1
            worksheet.append_row([
                new_id,
                name,
                description,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data  # TODO: Добавить шифрование
            ])
            return new_id
        except Exception as e:
            print(f"Ошибка добавления секрета: {e}")
            return None
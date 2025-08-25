import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from sheets_manager import SheetsManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация менеджера Google Sheets
sheets_manager = SheetsManager()

# Порт для сервера
PORT = int(os.environ.get('PORT', 8000))


# Главное меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Проекты", callback_data='projects')],
        [InlineKeyboardButton("✅ Задачи", callback_data='tasks')],
        [InlineKeyboardButton("📝 Заметки", callback_data='notes')],
        [InlineKeyboardButton("🔐 Секреты", callback_data='secrets')],
        [InlineKeyboardButton("➕ Создать проект", callback_data='create_project')],
        [InlineKeyboardButton("➕ Добавить задачу", callback_data='select_project_for_task')],
        [InlineKeyboardButton("➕ Добавить заметку", callback_data='add_note')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                "🏠 Главное меню\n\nВыберите действие:",
                reply_markup=reply_markup
            )
        except:
            await update.callback_query.message.reply_text(
                "🏠 Главное меню\n\nВыберите действие:",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            "🏠 Главное меню\n\nВыберите действие:",
            reply_markup=reply_markup
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await show_main_menu(update, context)


# Проекты
async def projects_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список проектов"""
    projects = sheets_manager.get_projects()

    if not projects:
        message = "📭 Нет проектов. Создайте первый!"
        keyboard = [
            [InlineKeyboardButton("➕ Создать проект", callback_data='create_project')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]
    else:
        message = "📁 Ваши проекты:\n\n"
        for project in projects:
            message += f"🔹 {project['ID']}. {project['Name']}\n"
            if project['Description']:
                message += f"   {project['Description']}\n"
            message += "\n"

        # Кнопки для каждого проекта + главное меню
        keyboard = []
        for project in projects[:10]:  # Ограничим 10 проектами
            keyboard.append([InlineKeyboardButton(
                f"📝 {project['Name']}",
                callback_data=f'project_tasks_{project["ID"]}'
            )])

        keyboard.append([InlineKeyboardButton("➕ Создать проект", callback_data='create_project')])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# Задачи
async def tasks_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех задач"""
    tasks = sheets_manager.get_tasks()

    if not tasks:
        message = "📭 Нет задач. Создайте первую!"
        keyboard = [
            [InlineKeyboardButton("➕ Добавить задачу", callback_data='select_project_for_task')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]
    else:
        # Группировка по проектам
        projects = {}
        for task in tasks:
            project = task['Project']
            if project not in projects:
                projects[project] = []
            projects[project].append(task)

        message = "✅ Ваши задачи:\n\n"
        for project, project_tasks in projects.items():
            message += f"📁 {project}:\n"
            for task in project_tasks[:5]:  # Ограничим 5 задачами на проект
                status_icon = "✅" if task['Status'] == 'done' else "⏳" if task['Status'] == 'in_progress' else "📝"
                priority_icon = "🔴" if task['Priority'] == 'high' else "🟡" if task['Priority'] == 'medium' else "🟢"
                message += f"  {status_icon} {priority_icon} {task['ID']}. {task['Title']}\n"
                if task['Deadline']:
                    message += f"     📅 {task['Deadline']}\n"
            message += "\n"

        keyboard = [
            [InlineKeyboardButton("➕ Добавить задачу", callback_data='select_project_for_task')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# Задачи конкретного проекта
async def project_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задачи конкретного проекта"""
    query = update.callback_query
    project_id = query.data.split('_')[2]

    # Найдем проект по ID
    projects = sheets_manager.get_projects()
    project_name = None
    for project in projects:
        if str(project['ID']) == project_id:
            project_name = project['Name']
            break

    if not project_name:
        await query.answer("Проект не найден")
        return

    tasks = sheets_manager.get_tasks(project_name)

    if not tasks:
        message = f"📭 Нет задач в проекте '{project_name}'"
    else:
        message = f"✅ Задачи проекта '{project_name}':\n\n"
        for task in tasks:
            status_icon = "✅" if task['Status'] == 'done' else "⏳" if task['Status'] == 'in_progress' else "📝"
            priority_icon = "🔴" if task['Priority'] == 'high' else "🟡" if task['Priority'] == 'medium' else "🟢"
            message += f"{status_icon} {priority_icon} {task['ID']}. {task['Title']}\n"
            if task['Description']:
                message += f"   {task['Description']}\n"
            if task['Deadline']:
                message += f"   📅 {task['Deadline']}\n"
            message += "\n"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить задачу", callback_data=f'add_task_to_project_{project_id}')],
        [InlineKeyboardButton("📋 Все проекты", callback_data='projects')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.edit_text(message, reply_markup=reply_markup)
    except:
        await query.message.reply_text(message, reply_markup=reply_markup)


# Выбор проекта для создания задачи
async def select_project_for_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор проекта для создания задачи"""
    projects = sheets_manager.get_projects()

    if not projects:
        message = "Сначала создайте проект!"
        keyboard = [
            [InlineKeyboardButton("➕ Создать проект", callback_data='create_project')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]
    else:
        message = "Выберите проект для новой задачи:"
        keyboard = []
        for project in projects:
            keyboard.append([InlineKeyboardButton(
                project['Name'],
                callback_data=f'selected_project_{project["ID"]}'
            )])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# После выбора проекта - ввод задачи
async def project_selected_for_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проект выбран, теперь вводим задачу"""
    query = update.callback_query
    project_id = query.data.split('_')[2]

    # Найдем проект по ID
    projects = sheets_manager.get_projects()
    project_name = None
    for project in projects:
        if str(project['ID']) == project_id:
            project_name = project['Name']
            break

    if not project_name:
        await query.answer("Проект не найден")
        return

    context.user_data['selected_project'] = project_name

    message = f"Создание задачи для проекта: {project_name}\n\n"
    message += "Введите задачу в формате:\n"
    message += "Название задачи\n"
    message += "Описание задачи (опционально)\n"
    message += "Приоритет (high/medium/low, опционально)\n"
    message += "Дедлайн (опционально, формат: YYYY-MM-DD)"

    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.edit_text(message, reply_markup=reply_markup)
    except:
        await query.message.reply_text(message, reply_markup=reply_markup)
    context.user_data['waiting_for'] = 'task_info'


# Заметки
async def notes_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список заметок"""
    notes = sheets_manager.get_notes()

    if not notes:
        message = "📭 Нет заметок. Создайте первую!"
        keyboard = [
            [InlineKeyboardButton("➕ Добавить заметку", callback_data='add_note')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]
    else:
        message = "📝 Ваши заметки:\n\n"
        for note in notes[:10]:
            message += f"📌 {note['ID']}. {note['Title']}\n"
            if note['Tags']:
                message += f"   🏷️ {note['Tags']}\n"
            message += f"   {note['Content'][:100]}{'...' if len(note['Content']) > 100 else ''}\n"
            message += f"   📅 {note['Created']}\n\n"

        if len(notes) > 10:
            message += f"... и еще {len(notes) - 10} заметок\n\n"

        keyboard = [
            [InlineKeyboardButton("➕ Добавить заметку", callback_data='add_note')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# Секреты
async def secrets_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список секретов"""
    secrets = sheets_manager.get_secrets()

    if not secrets:
        message = "📭 Нет секретов. Добавьте первый!"
        keyboard = [
            [InlineKeyboardButton("➕ Добавить секрет", callback_data='add_secret')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]
    else:
        message = "🔐 Ваши секреты:\n\n"
        for secret in secrets[:5]:
            message += f"🔒 {secret['ID']}. {secret['Name']}\n"
            if secret['Description']:
                message += f"   {secret['Description']}\n"
            message += f"   📅 {secret['Created']}\n\n"

        if len(secrets) > 5:
            message += f"... и еще {len(secrets) - 5} секретов\n\n"

        keyboard = [
            [InlineKeyboardButton("➕ Добавить секрет", callback_data='add_secret')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


# Создание проекта
async def create_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания проекта"""
    message = "Введите название проекта и описание (через новую строку):\n"
    message += "Пример:\n"
    message += "Мой проект\n"
    message += "Описание проекта"

    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

    context.user_data['waiting_for'] = 'project_info'


# Добавление заметки
async def add_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления заметки"""
    message = "Введите заметку в формате:\n"
    message += "Заголовок\n"
    message += "Содержание\n"
    message += "Теги (опционально, через запятую)\n"
    message += "Проект (опционально)"

    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

    context.user_data['waiting_for'] = 'note_info'


# Добавление секрета
async def add_secret_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления секрета"""
    message = "Введите секрет в формате:\n"
    message += "Название\n"
    message += "Описание\n"
    message += "Данные (логин/пароль и т.д.)"

    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

    context.user_data['waiting_for'] = 'secret_info'


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    if 'waiting_for' not in context.user_data:
        return

    text = update.message.text

    if context.user_data['waiting_for'] == 'project_info':
        lines = text.split('\n')
        name = lines[0]
        description = lines[1] if len(lines) > 1 else ""

        project_id = sheets_manager.add_project(name, description)
        if project_id:
            await update.message.reply_text(f"✅ Проект '{name}' создан! ID: {project_id}")
        else:
            await update.message.reply_text("❌ Ошибка создания проекта")

        context.user_data.pop('waiting_for', None)
        # Показать главное меню
        await show_main_menu(update, context)

    elif context.user_data['waiting_for'] == 'task_info':
        lines = text.split('\n')
        if len(lines) < 1:
            await update.message.reply_text("Неверный формат! Нужно минимум 1 строка")
            return

        project = context.user_data.get('selected_project', 'Без проекта')
        title = lines[0]
        description = lines[1] if len(lines) > 1 else ""
        priority = lines[2] if len(lines) > 2 else "medium"
        deadline = lines[3] if len(lines) > 3 else ""

        # Валидация приоритета
        if priority not in ['high', 'medium', 'low']:
            priority = 'medium'

        task_id = sheets_manager.add_task(project, title, description, priority, deadline)
        if task_id:
            await update.message.reply_text(f"✅ Задача '{title}' создана! ID: {task_id}")
        else:
            await update.message.reply_text("❌ Ошибка создания задачи")

        context.user_data.pop('waiting_for', None)
        context.user_data.pop('selected_project', None)
        # Показать главное меню
        await show_main_menu(update, context)

    elif context.user_data['waiting_for'] == 'note_info':
        lines = text.split('\n')
        if len(lines) < 2:
            await update.message.reply_text("Неверный формат! Нужно минимум 2 строки")
            return

        title = lines[0]
        content = lines[1]
        tags = lines[2] if len(lines) > 2 else ""
        project = lines[3] if len(lines) > 3 else ""

        note_id = sheets_manager.add_note(title, content, tags, project)
        if note_id:
            await update.message.reply_text(f"✅ Заметка '{title}' создана! ID: {note_id}")
        else:
            await update.message.reply_text("❌ Ошибка создания заметки")

        context.user_data.pop('waiting_for', None)
        # Показать главное меню
        await show_main_menu(update, context)

    elif context.user_data['waiting_for'] == 'secret_info':
        lines = text.split('\n')
        if len(lines) < 2:
            await update.message.reply_text("Неверный формат! Нужно минимум 2 строки")
            return

        name = lines[0]
        description = lines[1]
        data = lines[2] if len(lines) > 2 else ""

        secret_id = sheets_manager.add_secret(name, description, data)
        if secret_id:
            await update.message.reply_text(f"✅ Секрет '{name}' сохранен! ID: {secret_id}")
        else:
            await update.message.reply_text("❌ Ошибка сохранения секрета")

        context.user_data.pop('waiting_for', None)
        # Показать главное меню
        await show_main_menu(update, context)


# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()

    if query.data == 'main_menu':
        await show_main_menu(update, context)

    elif query.data == 'projects':
        await projects_list(update, context)

    elif query.data == 'tasks':
        await tasks_list(update, context)

    elif query.data == 'notes':
        await notes_list(update, context)

    elif query.data == 'secrets':
        await secrets_list(update, context)

    elif query.data == 'create_project':
        await create_project_start(update, context)

    elif query.data == 'select_project_for_task':
        await select_project_for_task(update, context)

    elif query.data.startswith('selected_project_'):
        await project_selected_for_task(update, context)

    elif query.data.startswith('project_tasks_'):
        await project_tasks(update, context)

    elif query.data.startswith('add_task_to_project_'):
        project_id = query.data.split('_')[4]
        # Переход к выбору проекта для задачи
        await select_project_for_task(update, context)

    elif query.data == 'add_note':
        await add_note_start(update, context)

    elif query.data == 'add_secret':
        await add_secret_start(update, context)


def main():
    """Запуск бота"""
    print("🚀 Запуск TaskBot...")

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("projects", projects_list))
    application.add_handler(CommandHandler("tasks", tasks_list))
    application.add_handler(CommandHandler("notes", notes_list))

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен! Нажмите Ctrl+C для остановки")

    # Для локальной разработки
    if os.environ.get('RENDER') is None:
        application.run_polling()
    else:

        # Для Render - webhook
        WEBHOOK_URL = f"https://ваш_домен_на_Render.com/webhook"
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )


if __name__ == '__main__':
    main()

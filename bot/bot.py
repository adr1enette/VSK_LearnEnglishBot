# Standard libraries
import os
import re
import sqlite3
import time
import random
from datetime import datetime

# External libraries
import requests
import telebot
from prettytable import PrettyTable


with open("token.txt", "r") as token_file:
    TOKEN = token_file.read().strip()

bot = telebot.TeleBot(TOKEN)

def create_database_if_not_exists():
    if not os.path.exists('bot.db'):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            start_time TEXT NOT NULL,
                            username TEXT,
                            first_name TEXT,
                            last_name TEXT,
                            language_code TEXT,
                            is_premium BOOLEAN NOT NULL
                        )''')
        
        conn.commit()
        conn.close()

create_database_if_not_exists()

def get_db_connection():
    conn = sqlite3.connect('bot.db')
    return conn, conn.cursor()


# /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    conn, cursor = get_db_connection()

    cursor.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user:
        start_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        language_code = message.from_user.language_code
        is_premium = message.from_user.is_premium
        cursor.execute("INSERT INTO users (user_id, start_time, username, first_name, last_name, language_code, is_premium) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (message.from_user.id, start_time, username, first_name, last_name, language_code, is_premium))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"Новый пользователь {username} ({message.from_user.id}), начавший пользоваться ботом в {start_time}. " \
              f"Всего пользователей: {user_count}")

    conn.close()

    intro_message = "Привет! Я бот для изучения английского языка. Моя задача — помочь тебе расширить свой словарный запас и улучшить знание английских слов. Давай начнем! 😊"
    bot.send_message(message.chat.id, intro_message)
    
    time.sleep(3)
    
    handle_main_menu(message)


# /main
@bot.message_handler(commands=['main'])
def handle_main_menu(message):
    main_menu_message = "Для использования моих функций, просто выбери одну из следующих команд:\n" \
                        "- /add book - книга (добавить слово)\n" \
                        "- /delete book (удалить слово или попроще /delete index)\n" \
                        "- /words (твой накопившейся словарь)\n" \
                        "- /test (слова для проверки себя)\n" \
                        "- /check (проверь себя!)\n" \
                        "- /define hello (фонетика, аудио, объяснение)\n" \
                        "- /help (если возникли вопросы 😅)"
    bot.send_message(message.chat.id, main_menu_message)


# /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    help_message = """
    Привет! Я бот для изучения английского языка. Моя задача — помочь тебе расширить словарный запас и улучшить знание английских слов. Давай начнем! 😊

    **Команды:**

    - `/add` - добавить слова: добавляй английские слова и их русские переводы в свой словарь.
    - `/delete` - удалить слова: удаляй слова из своего словаря по английскому слову или его индексу.
    - `/words` - твой список слов: просматривай список слов в своем словаре.
    - `/test` - слова для проверки себя: получи готовые слова из своего словаря для проверки.
    - `/check` - проверь себя!: проверь свои знания, сравнивая свои ответы с правильными.
    - `/define` - больше о слове: узнавай произношение, значение, примеры использования, синонимы и антонимы слова.
    - `/help` - помощь с обучением: получай советы и рекомендации по изучению английского языка.

    **Подсказка:** используй команду `/help`, чтобы узнать больше о каждой команде и как правильно пользоваться ботом.

    **Часто задаваемые вопросы (FAQ):**

    1. **Как добавить слово в словарь?**
       Для добавления слова в словарь используй команду `/add`, за которой следует английское слово, затем тире и русский перевод. Например:
       `/add book - книга`

    2. **Как удалить слово из словаря?**
       Для удаления слова из словаря используй команду `/delete`, за которой следует английское слово. Например:
       `/delete book`

    3. **Как просмотреть список слов в моем словаре?**
       Для просмотра списка слов в словаре используй команду `/words`.

    4. **Как проверить свои знания?**
       Функция проверки знаний пока недоступна, но скоро появится новое обновление!

    **Советы на будущее:**

    - Не забывай регулярно пополнять свой словарный запас!
    - Используй команду `/help`, чтобы получить дополнительную информацию и подсказки.
    - Следи за обновлениями бота, чтобы быть в курсе новых функций и возможностей!
    """
    bot.send_message(message.chat.id, help_message, parse_mode='Markdown')


# /add
@bot.message_handler(commands=['add'])
def handle_add_word_text(message):
    if len(message.text.split()) == 1:
        example_message = "Чтобы добавить слово, используйте команду /add, " \
                          "за которой следует английское слово, затем тире и русский перевод. Например:\n\n" \
                          "/add book - книга"
        bot.send_message(message.chat.id, example_message)
        return
    
    lines = message.text.strip().split("\n")
    
    added_words = []
    
    for line in lines:
        line = line.replace("/add", "").strip()
        
        if not re.match(r'^[a-zA-Z]+\s*-\s*[а-яА-Я]+$', line):
            bot.send_message(message.chat.id, "Неверный формат ввода. Правильно: Eng - Rus\nПример: `/add book - книга`", parse_mode='Markdown')
            continue

        english_word, russian_word = map(str.strip, line.split("-", 1))

        english_word = english_word.lower()
        russian_word = russian_word.lower()

        conn, cursor = get_db_connection()

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
            table_exists = cursor.fetchone()
            if not table_exists:
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS user_{message.from_user.id} (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    english_word TEXT NOT NULL,
                                    russian_word TEXT NOT NULL
                                )''')
                conn.commit()
                print(f"Создана таблица user_{message.from_user.id} для пользователя {message.from_user.username} ({message.from_user.id}).")

            cursor.execute(f"SELECT * FROM user_{message.from_user.id} WHERE english_word=?", (english_word,))
            existing_word = cursor.fetchone()
            if existing_word:
                bot.send_message(message.chat.id, f"Слово '{english_word}' уже есть в вашем словаре. " \
                                                   f"Его перевод: '{existing_word[2]}'.")
                continue

            cursor.execute(f"INSERT INTO user_{message.from_user.id} (english_word, russian_word) VALUES (?, ?)", (english_word, russian_word))
            conn.commit()

            added_words.append(english_word)
        except sqlite3.Error as e:
            print(f"Ошибка SQLite: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка при добавлении слова. Попробуйте еще раз.")
        finally:
            conn.close()

    if added_words:
        if len(added_words) == 1:
            success_message = f"Слово '{added_words[0]}' успешно добавлено в ваш словарь."
        else:
            success_message = f"Слова '{', '.join(added_words)}' успешно добавлены в ваш словарь."
        bot.send_message(message.chat.id, success_message)
        print(f"Сообщение об успешном добавлении слов пользователю {message.from_user.username} ({message.from_user.id}).")


# /delete
@bot.message_handler(commands=['delete'])
def handle_delete_word_text(message):
    if len(message.text.split()) == 1:
        example_message = "Чтобы удалить слово, используйте команду /delete, за которой следует " \
                          "английское слово или индекс слова. Например:\n\n" \
                          "`/delete book`\n" \
                          "`/delete 5`"
        bot.send_message(message.chat.id, example_message, parse_mode='Markdown')
        return

    word_or_index = message.text.strip().replace("/delete", "").strip().strip("'")

    word_or_index = word_or_index.lower()

    conn, cursor = get_db_connection()

    try:
        if re.match(r'^\d+$', word_or_index):
            word_index = int(word_or_index)

            cursor.execute(f"SELECT english_word FROM user_{message.from_user.id}")
            words = cursor.fetchall()

            if 0 < word_index <= len(words):
                word_to_delete = words[word_index - 1][0]
                delete_confirmation_message = f"Желаете удалить слово '{word_to_delete}'?\n" \
                                              f"Если это слово, выполните команду:\n" \
                                              f"`/delete {word_to_delete}`\n" \
                                              f"Выбрать другое слово - `/delete index`"
                bot.send_message(message.chat.id, delete_confirmation_message, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, f"Слово с индексом {word_index} не найдено.\nВыберите другое слово по индексу `/delete index`", parse_mode= 'Markdown')
        elif word_or_index.lower() == "index":
            show_words_table(message)
        else:
            word = word_or_index

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
            table_exists = cursor.fetchone()
            if not table_exists:
                bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте с помощью команды /add.")
                return

            cursor.execute(f"SELECT * FROM user_{message.from_user.id} WHERE LOWER(english_word)=?", (word,))
            existing_word = cursor.fetchone()
            if existing_word:
                cursor.execute(f"DELETE FROM user_{message.from_user.id} WHERE LOWER(english_word)=?", (word,))
                conn.commit()

                bot.send_message(message.chat.id, f"Слово '{word}' успешно удалено из вашего словаря.")
            else:
                cursor.execute(f"SELECT * FROM user_{message.from_user.id} WHERE LOWER(russian_word)=?", (word,))
                russian_word_match = cursor.fetchone()
                if russian_word_match:
                    bot.send_message(message.chat.id, f"Найдено слово, чей перевод является '{word}'.\n" \
                                                     "Чтобы удалить слово, вспомни его перевод 😉")
                else:
                    bot.send_message(message.chat.id, f"Слово '{word}' не найдено в вашем словаре.",
                                     parse_mode='Markdown')
    finally:
        conn.close()

def show_words_table(message):
    conn, cursor = get_db_connection()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
        table_exists = cursor.fetchone()
        if not table_exists:
            bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте с помощью команды /add.")
            return

        cursor.execute(f"SELECT english_word FROM user_{message.from_user.id}")
        words = cursor.fetchall()

        table = PrettyTable(["Индекс", "Английское слово"])
        for i, word in enumerate(words, start=1):
            table.add_row([i, word[0]])

        table.align = "l"

        bot.send_message(message.chat.id, f"Таблица слов из вашего словаря:\n\n```\n{table}\n```", parse_mode='Markdown')
    finally:
        conn.close()


# /words
@bot.message_handler(commands=['words'])
def handle_words(message):
    conn, cursor = get_db_connection()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
    table_exists = cursor.fetchone()
    if not table_exists:
        bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте с помощью команды /add.")
        return

    cursor.execute(f"SELECT english_word, russian_word FROM user_{message.from_user.id}")
    words = cursor.fetchall()

    if words:
        table = PrettyTable(["Английское слово", "Русское слово"])

        for word in words:
            table.add_row(word)

        table.align = "l"

        bot.send_message(message.chat.id, f"Слова в вашем словаре:\n\n```\n{table}\n```", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте с помощью команды /add.")

    conn.close()


# /test
@bot.message_handler(commands=['test'])
def handle_test_command(message):
    if len(message.text.split()) == 1:
        example_message = "Чтобы начать тестирование, используйте команду /test, за которой следует " \
                          "один из аргументов: `en`, `ru` или `random`.\n\n" \
                          "Например:\n\n" \
                          "`/test en` - тестирование на английские слова."
        bot.send_message(message.chat.id, example_message, parse_mode='Markdown')
        return

    conn, cursor = get_db_connection()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
    table_exists = cursor.fetchone()
    if not table_exists:
        bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте слова с помощью команды /add.")
        return

    cursor.execute(f"SELECT english_word, russian_word FROM user_{message.from_user.id}")
    words = cursor.fetchall()

    if not words:
        bot.send_message(message.chat.id, "В вашем словаре еще нет слов. Добавьте слова с помощью команды /add.")
        return

    command_args = message.text.split()[1].lower()

    good_luck_message = "Удачи с проверкой! Вот ваши слова:\n\n"

    selected_words = []

    if command_args == "en":
        selected_words = random.sample(words, min(10, len(words)))
    elif command_args == "ru":
        selected_words = random.sample(words, min(10, len(words)))
    elif command_args == "random":
        selected_word = random.choice(words)
        selected_words.append(selected_word)
    else:
        example_message = "Пожалуйста, укажите один из аргументов: `en`, `ru` или `random`."
        bot.send_message(message.chat.id, example_message, parse_mode='Markdown')
        return

    test_message = good_luck_message

    if command_args == 'random':
        test_message += "`/check "
    else:
        test_message += "```text\n/check\n"
        
    for word_pair in selected_words:
        if command_args == "en":
            test_message += f"{word_pair[0]} -\n"
        elif command_args == "ru":
            test_message += f"{word_pair[1]} -\n"
        else:
            test_message += f"{word_pair[0]} -\n"
            
    if command_args == 'random':
        test_message += "`"
    else:
        test_message += "```\n"

    bot.send_message(message.chat.id, test_message, parse_mode= 'Markdown')


# /check
@bot.message_handler(commands=['check'])
def handle_check(message):
    if len(message.text.split()) == 1:
        example_message = "Чтобы проверить свои знания, введите пары слов в формате:\n\n" \
                          "слово1 - перевод1\nслово2 - перевод2\n...\n\n" \
                          "Используйте команду /test (en, ru, random) для получения слов для проверки."
        bot.send_message(message.chat.id, example_message)
        return

    conn, cursor = get_db_connection()

    lines = message.text.split('\n')
    
    lines = [line.replace('/check', '') for line in lines]
    
    score = 0
    total_words = 0
    
    for line in lines:
        pairs = re.findall(r'\b\w+\s*-\s*\w+\b', line)
        
        for pair in pairs:
            words = pair.split('-')
            
            words = [word.strip() for word in words]
            
            if words[0].isalpha() and words[0].isascii():
                # Первое слово - английское, ищем его перевод в русских словах из базы данных
                cursor.execute(f"SELECT russian_word FROM user_{message.from_user.id} WHERE english_word=?", (words[0],))
                translation = cursor.fetchone()

                if translation:
                    if translation[0] == words[1]:
                        score += 1
                    else:
                        bot.send_message(message.chat.id, f"Неверно! Правильный перевод для слова \'{words[0]}\' - \'{translation[0]}\'.")
                else:
                    bot.send_message(message.chat.id, f"Неверно! Слово \'{words[0]}\' отсутствует в вашем словаре.")
            else:
                cursor.execute(f"SELECT english_word FROM user_{message.from_user.id} WHERE russian_word=?", (words[0],))
                translation = cursor.fetchone()

                if translation:
                    if translation[0] == words[1]:
                        score += 1
                    else:
                        bot.send_message(message.chat.id, f"Неверно! Правильный перевод для слова \"{words[0]}\" - \"{translation[0]}\".")
                else:
                    bot.send_message(message.chat.id, f"Неверно! Слово \"{words[0]}\" отсутствует в вашем словаре.")

            total_words += 1

    conn.close()

    accuracy = score / total_words * 100 if total_words > 0 else 0

    bot.send_message(message.chat.id, f"Вы набрали {score} из {total_words} баллов. ({accuracy:.2f}% правильных ответов)")
    
    
# /define
@bot.message_handler(commands=['define'])
def handle_define(message):
    arg = message.text.split()[1]

    if arg.isdigit():
        word_index = int(arg)

        conn, cursor = get_db_connection()

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"user_{message.from_user.id}",))
            table_exists = cursor.fetchone()

            if not table_exists:
                error_message = "У вас нет словаря. Добавьте слова с помощью команды /add."
                bot.send_message(message.chat.id, error_message)
                return

            cursor.execute(f"SELECT COUNT(*) FROM user_{message.from_user.id}")
            words_count = cursor.fetchone()[0]
            if words_count == 0:
                error_message = "В вашем словаре нет слов. Добавьте слова с помощью команды /add."
                bot.send_message(message.chat.id, error_message)
                return

            cursor.execute(f"SELECT english_word FROM user_{message.from_user.id} LIMIT 1 OFFSET {word_index}")
            row = cursor.fetchone()
            if row:
                word = row[0]
            else:
                error_message = f"Слово с индексом {word_index} не найдено в вашем словаре."
                bot.send_message(message.chat.id, error_message)
                return
        finally:
            conn.close()
    else:
        word = arg

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            word_data = data[0]
            definition_message = f"Определение для слова *{word_data['word']}*:"
            phonetic = word_data.get('phonetic')
            meanings = word_data['meanings']

            if phonetic:
                definition_message += f"\n\nФонетическое произношение: {phonetic}"

            phonetics = word_data.get('phonetics')
            if phonetics:
                for phonetic_info in phonetics:
                    audio_url = phonetic_info.get('audio')
                    if audio_url:
                        bot.send_audio(message.chat.id, audio_url)

            for meaning in meanings:
                part_of_speech = meaning['partOfSpeech']
                definitions = meaning['definitions']
                definition_message += f"\n\n*{part_of_speech.capitalize()}*:"
                
                for idx, definition in enumerate(definitions, start=1):
                    definition_text = definition['definition']
                    definition_message += f"\n{idx}. {definition_text}"

                    if 'example' in definition:
                        example = definition['example']
                        definition_message += f"\nПример: {example}"

                    if definition['synonyms']:
                        synonyms = ', '.join(definition['synonyms'])
                        definition_message += f"\nСинонимы: {synonyms}"

                    if definition['antonyms']:
                        antonyms = ', '.join(definition['antonyms'])
                        definition_message += f"\nАнтонимы: {antonyms}"

            bot.send_message(message.chat.id, definition_message, parse_mode="Markdown")
        else:
            error_message = f"Не удалось получить определение для слова \"{word}\". Пожалуйста, попробуйте еще раз позже."
            bot.send_message(message.chat.id, error_message)
    except Exception as e:
        error_message = f"Произошла ошибка при запросе определения для слова \"{word}\". Пожалуйста, попробуйте еще раз позже."
        bot.send_message(message.chat.id, error_message)
        print(f"Error: {e}")

bot.polling()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM МАССОВЫЙ ОТПРАВИТЕЛЬ v4.0
Работает с личного аккаунта через Termux
Автор: west_hub
"""

import asyncio
import json
import os
import sys
import time
import random
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import InputPeerUser, InputPeerChannel, InputPeerChat
import logging

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== КОНСТАНТЫ ==========
VERSION = "4.0"
CONFIG_FILE = "config.json"
DATA_DIR = "data"
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
FOLDERS_FILE = os.path.join(DATA_DIR, "folders.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
BLACKLIST_FILE = os.path.join(DATA_DIR, "blacklist.json")

# Глобальные переменные для рассылки
sending_active = False
sent_count = 0
error_count = 0
start_time = None
current_task = None

# ========== УТИЛИТЫ ==========
def clear_screen():
    """Очистка экрана"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header(title="ТЕЛЕГРАМ БОТ v4.0"):
    """Красивый заголовок"""
    clear_screen()
    border = "═" * 40
    print(f"╔{border}╗")
    print(f"║{title.center(40)}║")
    print(f"╚{border}╝")
    
    # Статус рассылки
    if sending_active:
        elapsed = time.time() - start_time
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        print(f"\n🔥 Рассылка активна: {sent_count} отправлено, {error_count} ошибок")
        print(f"⏰ Время работы: {time_str}\n")
    else:
        print("\n📱 Готов к работе\n")

def load_json(filepath, default=None):
    """Загрузка JSON файла"""
    if default is None:
        default = {}
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {filepath}: {e}")
    return default

def save_json(filepath, data):
    """Сохранение в JSON файл"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения {filepath}: {e}")
        return False

def create_default_files():
    """Создание всех необходимых файлов"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    defaults = {
        CHATS_FILE: [],
        FAVORITES_FILE: [],
        FOLDERS_FILE: {"default": []},
        TEMPLATES_FILE: {
            "приветствие": "👋 Привет! Как дела?",
            "реклама": "🎯 Хотите увеличить продажи? Пишите!",
            "новость": "📰 У нас важные новости!"
        },
        STATS_FILE: {"total_sent": 0, "total_errors": 0, "last_active": ""},
        BLACKLIST_FILE: []
    }
    
    for filepath, default_data in defaults.items():
        if not os.path.exists(filepath):
            save_json(filepath, default_data)
    
    logger.info("Файлы данных созданы")

# ========== КЛАСС БОТА ==========
class TelegramSender:
    def __init__(self):
        self.client = None
        self.config = load_json(CONFIG_FILE, {})
        self.me = None
        
        # Загрузка данных
        self.chats = load_json(CHATS_FILE, [])
        self.favorites = load_json(FAVORITES_FILE, [])
        self.folders = load_json(FOLDERS_FILE, {"default": []})
        self.templates = load_json(TEMPLATES_FILE, {})
        self.stats = load_json(STATS_FILE, {"total_sent": 0, "total_errors": 0, "last_active": ""})
        self.blacklist = load_json(BLACKLIST_FILE, [])
        
        create_default_files()

    async def connect(self):
        """Подключение к Telegram"""
        if not self.config.get("api_id") or not self.config.get("api_hash"):
            return False
        
        try:
            session_name = "telegram_sender"
            self.client = TelegramClient(session_name, self.config["api_id"], self.config["api_hash"])
            
            # Проверяем существование сессии
            if os.path.exists(f"{session_name}.session"):
                await self.client.start()
            else:
                await self.client.connect()
                
                if not await self.client.is_user_authorized():
                    print("\n📱 ВХОД В ТЕЛЕГРАМ")
                    print("=" * 40)
                    phone = input("📞 Введите номер телефона (с кодом страны): ").strip()
                    
                    await self.client.send_code_request(phone)
                    
                    code = input("📝 Введите код из Telegram: ").strip()
                    
                    try:
                        await self.client.sign_in(phone, code)
                    except SessionPasswordNeededError:
                        password = input("🔐 Введите пароль 2FA: ").strip()
                        await self.client.sign_in(password=password)
            
            self.me = await self.client.get_me()
            logger.info(f"Успешный вход: {self.me.first_name} (@{self.me.username})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            return False

    async def get_chats(self):
        """Получение списка диалогов"""
        try:
            dialogs = await self.client.get_dialogs()
            chats_list = []
            
            for dialog in dialogs:
                if dialog.is_group or dialog.is_channel or dialog.is_user:
                    chat_info = {
                        "id": dialog.id,
                        "title": getattr(dialog.entity, 'title', ''),
                        "username": getattr(dialog.entity, 'username', ''),
                        "type": "channel" if dialog.is_channel else "group" if dialog.is_group else "user"
                    }
                    chats_list.append(chat_info)
            
            # Сохраняем в файл
            self.chats = chats_list
            save_json(CHATS_FILE, chats_list)
            
            return chats_list
            
        except Exception as e:
            logger.error(f"Ошибка получения чатов: {e}")
            return []

    async def send_message(self, chat_id, text, retries=3):
        """Отправка сообщения с повторными попытками"""
        global sent_count, error_count
        
        for attempt in range(retries):
            try:
                await self.client.send_message(chat_id, text)
                sent_count += 1
                self.stats["total_sent"] += 1
                save_json(STATS_FILE, self.stats)
                logger.info(f"Сообщение отправлено в {chat_id}")
                return True
                
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1}/{retries} не удалась: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
        
        error_count += 1
        self.stats["total_errors"] += 1
        save_json(STATS_FILE, self.stats)
        logger.error(f"Не удалось отправить в {chat_id}")
        return False

    async def mass_send(self, chat_ids, text, delay=2, infinite=False, cycles=1, cycle_delay=5):
        """Массовая рассылка"""
        global sending_active, start_time
        
        sending_active = True
        start_time = time.time()
        
        cycle_count = 0
        total_cycles = 0 if infinite else cycles
        
        try:
            while sending_active and (infinite or cycle_count < cycles):
                cycle_count += 1
                
                if not infinite:
                    print(f"\n📦 Цикл {cycle_count}/{cycles}")
                
                for i, chat_id in enumerate(chat_ids):
                    if not sending_active:
                        break
                    
                    # Пропускаем черный список
                    if str(chat_id) in self.blacklist:
                        continue
                    
                    print(f"[{i+1}/{len(chat_ids)}] Отправка в {chat_id}...")
                    
                    # Рандомизация текста
                    if isinstance(text, list):
                        message_text = random.choice(text)
                    else:
                        message_text = text
                    
                    await self.send_message(chat_id, message_text)
                    
                    if i < len(chat_ids) - 1 and sending_active:
                        await asyncio.sleep(delay)
                
                # Пауза между циклами
                if sending_active and (infinite or cycle_count < cycles):
                    print(f"\n⏸️ Пауза между циклами: {cycle_delay} сек...")
                    for sec in range(cycle_delay, 0, -1):
                        if not sending_active:
                            break
                        print(f"⏳ {sec}...", end='\r')
                        await asyncio.sleep(1)
                    print()
            
            print("\n✅ Рассылка завершена!")
            
        except Exception as e:
            logger.error(f"Ошибка в массовой рассылке: {e}")
            print(f"\n❌ Ошибка: {e}")
        
        finally:
            sending_active = False
            self.stats["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(STATS_FILE, self.stats)

# ========== ФУНКЦИИ ИНТЕРФЕЙСА ==========
def show_main_menu(bot):
    """Главное меню"""
    while True:
        print_header()
        
        menu_options = [
            "[1] 📋 Мои чаты",
            "[2] 📤 Отправить одно сообщение",
            "[3] 🚀 Обычная рассылка", 
            "[4] ♾️ БЕСКОНЕЧНАЯ рассылка",
            "[5] 🛑 Остановить рассылку",
            "[6] 📁 Папки с чатами",
            "[7] 💾 Избранные чаты",
            "[8] 📝 Шаблоны текстов",
            "[9] 📊 Статистика",
            "[0] ⚙️ Настройки",
            "[x] 🚪 Выход"
        ]
        
        for option in menu_options:
            print(option)
        
        choice = input("\n🎯 Выберите действие: ").strip().lower()
        
        if choice == '1':
            show_my_chats(bot)
        elif choice == '2':
            send_single_message(bot)
        elif choice == '3':
            start_mass_send(bot, infinite=False)
        elif choice == '4':
            start_mass_send(bot, infinite=True)
        elif choice == '5':
            stop_sending()
        elif choice == '6':
            manage_folders(bot)
        elif choice == '7':
            manage_favorites(bot)
        elif choice == '8':
            manage_templates(bot)
        elif choice == '9':
            show_statistics(bot)
        elif choice == '0':
            show_settings(bot)
        elif choice == 'x':
            print("\n👋 Выход...")
            stop_sending()
            time.sleep(2)
            sys.exit(0)
        else:
            print("\n❌ Неверный выбор!")
            time.sleep(1)

def show_my_chats(bot):
    """Показать мои чаты"""
    print_header("📋 МОИ ЧАТЫ")
    
    if not bot.chats:
        print("\n📭 Чатов нет. Загружаю...")
        asyncio.run(bot.get_chats())
    
    for i, chat in enumerate(bot.chats[:50], 1):  # Показываем первые 50
        fav_icon = "⭐" if str(chat["id"]) in bot.favorites else "  "
        print(f"{i:3}. {fav_icon} {chat['title'][:30]:30} ({chat['type']}) ID: {chat['id']}")
    
    if len(bot.chats) > 50:
        print(f"\n... и еще {len(bot.chats) - 50} чатов")
    
    print(f"\n📊 Всего чатов: {len(bot.chats)}")
    
    input("\n↵ Нажмите Enter для возврата...")

def send_single_message(bot):
    """Отправить одно сообщение"""
    print_header("📤 ОТПРАВКА СООБЩЕНИЯ")
    
    print("🎯 Куда отправить?")
    print("1. По ID чата")
    print("2. По username (@channel)")
    print("3. По ссылке (t.me/channel)")
    choice = input("\nВыберите: ").strip()
    
    chat_input = input("Введите ID/username/ссылку: ").strip()
    text = input("Введите текст сообщения: ").strip()
    
    if not text:
        print("\n❌ Текст не может быть пустым!")
        time.sleep(2)
        return
    
    print("\n⏳ Отправляю...")
    
    try:
        asyncio.run(bot.send_message(chat_input, text))
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    time.sleep(2)

def start_mass_send(bot, infinite=False):
    """Запуск массовой рассылки"""
    global sending_active
    
    if sending_active:
        print("\n⚠️ Рассылка уже активна!")
        time.sleep(2)
        return
    
    print_header("♾️ БЕСКОНЕЧНАЯ РАССЫЛКА" if infinite else "🚀 МАССОВАЯ РАССЫЛКА")
    
    # Выбор источника чатов
    print("📁 Выберите источник чатов:")
    print("1. Из папки")
    print("2. Из избранного")
    print("3. Все мои чаты")
    print("4. Ввести вручную (через запятую)")
    
    source_choice = input("\nВыберите: ").strip()
    
    chat_ids = []
    
    if source_choice == '1':
        # Из папки
        if not bot.folders:
            print("\n❌ Папки не созданы!")
            time.sleep(2)
            return
        
        print("\n📂 Доступные папки:")
        for folder_name in bot.folders.keys():
            print(f"- {folder_name} ({len(bot.folders[folder_name])} чатов)")
        
        folder_name = input("Введите имя папки: ").strip()
        if folder_name in bot.folders:
            chat_ids = bot.folders[folder_name]
        else:
            print("❌ Папка не найдена!")
            time.sleep(2)
            return
            
    elif source_choice == '2':
        # Из избранного
        chat_ids = [int(cid) for cid in bot.favorites]
        
    elif source_choice == '3':
        # Все чаты
        chat_ids = [chat["id"] for chat in bot.chats]
        
    elif source_choice == '4':
        # Вручную
        manual_input = input("Введите ID чатов через запятую: ").strip()
        chat_ids = [int(cid.strip()) for cid in manual_input.split(',') if cid.strip().isdigit()]
    
    if not chat_ids:
        print("\n❌ Нет чатов для рассылки!")
        time.sleep(2)
        return
    
    # Выбор текста
    print("\n📝 Выберите текст:")
    print("1. Ввести текст")
    print("2. Выбрать шаблон")
    print("3. Несколько вариантов (для рандомизации)")
    
    text_choice = input("Выберите: ").strip()
    
    if text_choice == '1':
        text = input("Введите текст сообщения: ").strip()
        
    elif text_choice == '2':
        if not bot.templates:
            print("❌ Шаблонов нет!")
            time.sleep(2)
            return
        
        print("\n📋 Доступные шаблоны:")
        for name, template_text in bot.templates.items():
            print(f"- {name}: {template_text[:50]}...")
        
        template_name = input("Введите имя шаблона: ").strip()
        if template_name in bot.templates:
            text = bot.templates[template_name]
        else:
            print("❌ Шаблон не найден!")
            time.sleep(2)
            return
    
    elif text_choice == '3':
        variants = []
        print("\n📝 Введите несколько вариантов текста (пустая строка для завершения):")
        while True:
            variant = input(f"Вариант {len(variants)+1}: ").strip()
            if not variant:
                break
            variants.append(variant)
        
        if not variants:
            print("❌ Нет вариантов!")
            time.sleep(2)
            return
        text = variants
    
    else:
        print("❌ Неверный выбор!")
        time.sleep(2)
        return
    
    # Настройки задержки
    try:
        delay = float(input("Задержка между сообщениями (сек, по умолчанию 2): ") or "2")
        cycle_delay = float(input("Пауза между циклами (сек, по умолчанию 5): ") or "5")
        
        if not infinite:
            cycles = int(input("Количество циклов (0 = бесконечно): ") or "1")
        else:
            cycles = 0
        
    except ValueError:
        print("❌ Неверное число!")
        time.sleep(2)
        return
    
    # Подтверждение
    print_header("ПОДТВЕРЖДЕНИЕ")
    print(f"📊 Чатов для рассылки: {len(chat_ids)}")
    print(f"📝 Текст: {text[:50]}{'...' if len(str(text)) > 50 else ''}")
    print(f"⏱️ Задержка: {delay} сек")
    print(f"⏸️ Пауза между циклами: {cycle_delay} сек")
    print(f"♾️ Циклов: {'Бесконечно' if cycles == 0 or infinite else cycles}")
    
    confirm = input("\n🚀 Начать рассылку? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\n✅ Запускаю рассылку...")
        print("ℹ️ Чтобы остановить: выберите [5] в главном меню")
        
        # Запуск в фоне
        async def run_send():
            await bot.mass_send(chat_ids, text, delay, infinite or cycles == 0, 
                               cycles if cycles > 0 else 1, cycle_delay)
        
        asyncio.create_task(run_send())
        time.sleep(2)
    else:
        print("❌ Отменено!")
        time.sleep(1)

def stop_sending():
    """Остановить рассылку"""
    global sending_active
    if sending_active:
        sending_active = False
        print("\n🛑 Останавливаю рассылку...")
        time.sleep(2)
    else:
        print("\n⚠️ Рассылка не активна!")
        time.sleep(1)

def manage_folders(bot):
    """Управление папками с чатами"""
    print_header("📁 ПАПКИ С ЧАТАМИ")
    
    while True:
        print("\n1. 📂 Создать папку")
        print("2. 📋 Показать папки")
        print("3. ➕ Добавить чат в папку")
        print("4. 🗑️ Удалить папку")
        print("5. ↩️ Назад")
        
        choice = input("\nВыберите: ").strip()
        
        if choice == '1':
            folder_name = input("Введите имя папки: ").strip()
            if folder_name and folder_name not in bot.folders:
                bot.folders[folder_name] = []
                save_json(FOLDERS_FILE, bot.folders)
                print(f"✅ Папка '{folder_name}' создана!")
            else:
                print("❌ Папка уже существует или имя пустое!")
        
        elif choice == '2':
            if not bot.folders:
                print("\n📭 Папок нет")
            else:
                print("\n📂 Ваши папки:")
                for folder_name, chats in bot.folders.items():
                    print(f"- {folder_name}: {len(chats)} чатов")
        
        elif choice == '3':
            if not bot.folders:
                print("❌ Сначала создайте папку!")
                continue
            
            print("\n📂 Выберите папку:")
            for folder_name in bot.folders.keys():
                print(f"- {folder_name}")
            
            folder_name = input("Имя папки: ").strip()
            if folder_name not in bot.folders:
                print("❌ Папка не найдена!")
                continue
            
            chat_id = input("Введите ID чата: ").strip()
            if chat_id.isdigit():
                if int(chat_id) not in bot.folders[folder_name]:
                    bot.folders[folder_name].append(int(chat_id))
                    save_json(FOLDERS_FILE, bot.folders)
                    print("✅ Чат добавлен!")
                else:
                    print("⚠️ Чат уже в папке")
            else:
                print("❌ Неверный ID!")
        
        elif choice == '4':
            if not bot.folders:
                print("❌ Папок нет!")
                continue
            
            print("\n📂 Выберите папку для удаления:")
            for folder_name in bot.folders.keys():
                print(f"- {folder_name}")
            
            folder_name = input("Имя папки: ").strip()
            if folder_name in bot.folders:
                confirm = input(f"Удалить папку '{folder_name}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    del bot.folders[folder_name]
                    save_json(FOLDERS_FILE, bot.folders)
                    print("✅ Папка удалена!")
            else:
                print("❌ Папка не найдена!")
        
        elif choice == '5':
            break
        
        time.sleep(1)

def manage_favorites(bot):
    """Управление избранными чатами"""
    print_header("💾 ИЗБРАННЫЕ ЧАТЫ")
    
    while True:
        print(f"\n⭐ Избранных: {len(bot.favorites)}")
        print("\n1. 📋 Показать избранное")
        print("2. ➕ Добавить в избранное")
        print("3. 🗑️ Удалить из избранного")
        print("4. ↩️ Назад")
        
        choice = input("\nВыберите: ").strip()
        
        if choice == '1':
            if not bot.favorites:
                print("\n📭 Избранных чатов нет")
            else:
                print("\n⭐ Избранные чаты:")
                for i, chat_id in enumerate(bot.favorites[:20], 1):
                    # Найдем информацию о чате
                    chat_info = next((c for c in bot.chats if str(c["id"]) == chat_id), None)
                    if chat_info:
                        print(f"{i}. {chat_info['title'][:30]} (ID: {chat_id})")
                    else:
                        print(f"{i}. ID: {chat_id}")
        
        elif choice == '2':
            chat_id = input("Введите ID чата: ").strip()
            if chat_id and chat_id not in bot.favorites:
                bot.favorites.append(chat_id)
                save_json(FAVORITES_FILE, bot.favorites)
                print("✅ Добавлено в избранное!")
            else:
                print("⚠️ Уже в избранном или пустой ID")
        
        elif choice == '3':
            if not bot.favorites:
                print("❌ Избранных нет!")
                continue
            
            print("\nВыберите чат для удаления:")
            for i, chat_id in enumerate(bot.favorites, 1):
                print(f"{i}. ID: {chat_id}")
            
            try:
                index = int(input("Номер: ").strip()) - 1
                if 0 <= index < len(bot.favorites):
                    removed = bot.favorites.pop(index)
                    save_json(FAVORITES_FILE, bot.favorites)
                    print(f"✅ Чат {removed} удален!")
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
        
        elif choice == '4':
            break
        
        time.sleep(1)

def manage_templates(bot):
    """Управление шаблонами текстов"""
    print_header("📝 ШАБЛОНЫ ТЕКСТОВ")
    
    while True:
        print(f"\n📋 Шаблонов: {len(bot.templates)}")
        print("\n1. 📖 Показать шаблоны")
        print("2. ✏️ Создать шаблон")
        print("3. 🗑️ Удалить шаблон")
        print("4. ↩️ Назад")
        
        choice = input("\nВыберите: ").strip()
        
        if choice == '1':
            if not bot.templates:
                print("\n📭 Шаблонов нет")
            else:
                print("\n📋 Ваши шаблоны:")
                for name, text in bot.templates.items():
                    print(f"\n📌 {name}:")
                    print(f"   {text}")
        
        elif choice == '2':
            name = input("Название шаблона: ").strip()
            if not name:
                print("❌ Имя не может быть пустым!")
                continue
            
            print("Введите текст шаблона (Ctrl+D для завершения):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            
            text = "\n".join(lines)
            if text:
                bot.templates[name] = text
                save_json(TEMPLATES_FILE, bot.templates)
                print(f"✅ Шаблон '{name}' сохранен!")
            else:
                print("❌ Текст не может быть пустым!")
        
        elif choice == '3':
            if not bot.templates:
                print("❌ Шаблонов нет!")
                continue
            
            print("\nВыберите шаблон для удаления:")
            for i, name in enumerate(bot.templates.keys(), 1):
                print(f"{i}. {name}")
            
            try:
                index = int(input("Номер: ").strip()) - 1
                names = list(bot.templates.keys())
                if 0 <= index < len(names):
                    removed = names[index]
                    confirm = input(f"Удалить '{removed}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        del bot.templates[removed]
                        save_json(TEMPLATES_FILE, bot.templates)
                        print(f"✅ Шаблон '{removed}' удален!")
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
        
        elif choice == '4':
            break
        
        time.sleep(1)

def show_statistics(bot):
    """Показать статистику"""
    print_header("📊 СТАТИСТИКА")
    
    print(f"\n📨 Всего отправлено: {bot.stats.get('total_sent', 0)}")
    print(f"❌ Ошибок отправки: {bot.stats.get('total_errors', 0)}")
    print(f"📅 Последняя активность: {bot.stats.get('last_active', 'никогда')}")
    
    if bot.me:
        print(f"\n👤 Аккаунт: {bot.me.first_name} (@{bot.me.username})")
        print(f"🆔 User ID: {bot.me.id}")
    
    print(f"\n📁 Папок: {len(bot.folders)}")
    print(f"⭐ Избранных: {len(bot.favorites)}")
    print(f"📝 Шаблонов: {len(bot.templates)}")
    print(f"🚫 Черный список: {len(bot.blacklist)} чатов")
    
    print("\n💾 Экспорт данных:")
    print("1. 📤 Экспортировать все чаты")
    print("2. 📤 Экспортировать шаблоны")
    print("3. 📥 Импортировать данные")
    
    choice = input("\nВыберите действие (или Enter для выхода): ").strip()
    
    if choice == '1':
        export_file = f"chats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(export_file, bot.chats)
        print(f"✅ Чаты экспортированы в {export_file}")
        time.sleep(2)
    
    elif choice == '2':
        export_file = f"templates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(export_file, bot.templates)
        print(f"✅ Шаблоны экспортированы в {export_file}")
        time.sleep(2)
    
    elif choice == '3':
        file_path = input("Введите путь к файлу JSON: ").strip()
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    bot.chats.extend(data)
                    save_json(CHATS_FILE, bot.chats)
                    print(f"✅ Импортировано {len(data)} чатов")
                elif isinstance(data, dict):
                    bot.templates.update(data)
                    save_json(TEMPLATES_FILE, bot.templates)
                    print(f"✅ Импортировано {len(data)} шаблонов")
                
            except Exception as e:
                print(f"❌ Ошибка импорта: {e}")
        else:
            print("❌ Файл не найден!")
        time.sleep(2)

def show_settings(bot):
    """Настройки"""
    print_header("⚙️ НАСТРОЙКИ")
    
    while True:
        print(f"\n📱 API ID: {bot.config.get('api_id', 'не установлен')}")
        print(f"🔑 API Hash: {bot.config.get('api_hash', 'не установлен')[:10]}...")
        
        print("\n1. 🔄 Обновить API данные")
        print("2. 🚫 Управление черным списком")
        print("3. ⏱️ Настройка задержек")
        print("4. 🧹 Очистить данные")
        print("5. ℹ️ Информация о боте")
        print("6. ↩️ Назад")
        
        choice = input("\nВыберите: ").strip()
        
        if choice == '1':
            print("\n🔧 НАСТРОЙКА API")
            print("=" * 40)
            print("1. Получите API ID и Hash на my.telegram.org")
            print("2. Войдите в свой аккаунт Telegram")
            print("3. Перейдите в раздел 'API development tools'")
            print("4. Создайте приложение и скопируйте данные\n")
            
            api_id = input("Введите API ID: ").strip()
            api_hash = input("Введите API Hash: ").strip()
            
            if api_id.isdigit() and api_hash:
                bot.config["api_id"] = int(api_id)
                bot.config["api_hash"] = api_hash
                save_json(CONFIG_FILE, bot.config)
                print("✅ API данные сохранены!")
                print("⚠️ Перезапустите бота для применения изменений")
                time.sleep(3)
            else:
                print("❌ Неверные данные!")
        
        elif choice == '2':
            manage_blacklist(bot)
        
        elif choice == '3':
            print("\n⏱️ НАСТРОЙКА ЗАДЕРЖЕК")
            default_delay = bot.config.get("default_delay", 2)
            print(f"Текущая задержка по умолчанию: {default_delay} сек")
            
            new_delay = input("Новая задержка (сек): ").strip()
            if new_delay.replace('.', '').isdigit():
                bot.config["default_delay"] = float(new_delay)
                save_json(CONFIG_FILE, bot.config)
                print("✅ Задержка сохранена!")
            time.sleep(1)
        
        elif choice == '4':
            confirm = input("\n⚠️ Очистить ВСЕ данные? (y/n): ").strip().lower()
            if confirm == 'y':
                files_to_remove = [
                    CHATS_FILE, FAVORITES_FILE, FOLDERS_FILE,
                    TEMPLATES_FILE, STATS_FILE, BLACKLIST_FILE,
                    "telegram_sender.session"
                ]
                
                for file in files_to_remove:
                    if os.path.exists(file):
                        os.remove(file)
                        print(f"🗑️ Удалено: {file}")
                
                print("\n✅ Все данные очищены!")
                print("⚠️ Бот будет перезапущен")
                time.sleep(3)
                sys.exit(0)
        
        elif choice == '5':
            print("\n🤖 ИНФОРМАЦИЯ О БОТЕ")
            print("=" * 40)
            print(f"Версия: {VERSION}")
            print("Автор: Swill Way")
            print("Дата создания: 26.09.2025")
            print("\n📞 Поддержка: @swill_way")
            print("💾 GitHub: github.com/swill-way")
            print("\n⚠️ Используйте ответственно!")
            input("\n↵ Нажмите Enter для продолжения...")
        
        elif choice == '6':
            break
        
        time.sleep(1)

def manage_blacklist(bot):
    """Управление черным списком"""
    print_header("🚫 ЧЕРНЫЙ СПИСОК")
    
    while True:
        print(f"\n🚫 Чатов в черном списке: {len(bot.blacklist)}")
        print("\n1. 📋 Показать черный список")
        print("2. ➕ Добавить в черный список")
        print("3. 🗑️ Удалить из черного списка")
        print("4. ↩️ Назад")
        
        choice = input("\nВыберите: ").strip()
        
        if choice == '1':
            if not bot.blacklist:
                print("\n📭 Черный список пуст")
            else:
                print("\n🚫 Черный список:")
                for i, chat_id in enumerate(bot.blacklist[:20], 1):
                    print(f"{i}. ID: {chat_id}")
        
        elif choice == '2':
            chat_id = input("Введите ID чата: ").strip()
            if chat_id and chat_id not in bot.blacklist:
                bot.blacklist.append(chat_id)
                save_json(BLACKLIST_FILE, bot.blacklist)
                print("✅ Добавлено в черный список!")
            else:
                print("⚠️ Уже в списке или пустой ID")
        
        elif choice == '3':
            if not bot.blacklist:
                print("❌ Список пуст!")
                continue
            
            print("\nВыберите для удаления:")
            for i, chat_id in enumerate(bot.blacklist, 1):
                print(f"{i}. ID: {chat_id}")
            
            try:
                index = int(input("Номер: ").strip()) - 1
                if 0 <= index < len(bot.blacklist):
                    removed = bot.blacklist.pop(index)
                    save_json(BLACKLIST_FILE, bot.blacklist)
                    print(f"✅ Чат {removed} удален из списка!")
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
        
        elif choice == '4':
            break
        
        time.sleep(1)

# ========== УСТАНОВОЧНЫЙ СКРИПТ ==========
async def setup_wizard():
    """Мастер настройки"""
    print_header("⚡ ТЕЛЕГРАМ РАССЫЛКА v4.0")
    
    print("👋 Добро пожаловать!")
    print("\nПеред началом работы:")
    print("1. 📱 Убедитесь, что у вас есть доступ к аккаунту Telegram")
    print("2. 🌐 Получите API ID и Hash на сайте my.telegram.org")
    print("3. 📞 Будьте готовы ввести номер телефона и код из Telegram")
    
    input("\n↵ Нажмите Enter для продолжения...")
    
    # Проверяем существующую конфигурацию
    config = load_json(CONFIG_FILE, {})
    
    if config.get("api_id") and config.get("api_hash"):
        print("\n✅ Найдена сохраненная конфигурация!")
        use_existing = input("Использовать сохраненные данные? (y/n): ").strip().lower()
        if use_existing == 'y':
            return config
    
    # Получаем новые данные
    print("\n🔧 НАСТРОЙКА API")
    print("=" * 50)
    
    while True:
        api_id = input("\nВведите API ID (с my.telegram.org): ").strip()
        api_hash = input("Введите API Hash: ").strip()
        
        if api_id.isdigit() and api_hash:
            config = {
                "api_id": int(api_id),
                "api_hash": api_hash,
                "setup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_json(CONFIG_FILE, config)
            print("\n✅ API данные сохранены!")
            break
        else:
            print("❌ Неверные данные! Попробуйте снова.")
    
    return config

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
async def main():
    """Основная функция"""
    print_header("⚡ ЗАГРУЗКА...")
    
    print("🔍 Проверяю настройки...")
    
    # Проверка API данных
    if not os.path.exists(CONFIG_FILE):
        print("❌ Конфигурация не найдена!")
        print("🔄 Запускаю мастер настройки...")
        config = await setup_wizard()
    else:
        config = load_json(CONFIG_FILE)
    
    if not config.get("api_id") or not config.get("api_hash"):
        print("❌ API данные не настроены!")
        print("🔄 Запускаю мастер настройки...")
        config = await setup_wizard()
    
    # Инициализация бота
    print("\n🤖 Инициализация бота...")
    bot = TelegramSender()
    
    # Подключение к Telegram
    print("📡 Подключение к Telegram...")
    connected = await bot.connect()
    
    if not connected:
        print("\n❌ Ошибка подключения!")
        print("Возможные причины:")
        print("1. Неверный API ID/Hash")
        print("2. Проблемы с интернетом")
        print("3. Аккаунт заблокирован")
        input("\n↵ Нажмите Enter для выхода...")
        return
    
    # Загрузка чатов
    print("📋 Загрузка чатов...")
    await bot.get_chats()
    
    print(f"\n✅ Бот готов!")
    print(f"👤 Аккаунт: {bot.me.first_name if bot.me else 'Неизвестно'}")
    print(f"📊 Загружено чатов: {len(bot.chats)}")
    
    time.sleep(2)
    
    # Показываем главное меню
    show_main_menu(bot)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        # Проверка на уже запущенный процесс
        pid_file = "bot.pid"
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                old_pid = f.read().strip()
                if os.path.exists(f"/proc/{old_pid}"):
                    print("⚠️ Бот уже запущен!")
                    choice = input("Все равно запустить? (y/n): ").strip().lower()
                    if choice != 'y':
                        sys.exit(0)
        
        # Сохраняем PID
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Запуск бота
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Получен сигнал прерывания...")
        stop_sending()
        print("👋 Завершение работы...")
        time.sleep(1)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте файл logs/bot.log для деталей")
        input("\n↵ Нажмите Enter для выхода...")
        
    finally:
        # Удаляем PID файл
        if os.path.exists("bot.pid"):
            os.remove("bot.pid")

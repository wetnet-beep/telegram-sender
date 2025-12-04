#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Установщик для Termux - проверка и настройка окружения
Автор: wetnet-beep
"""

import os
import sys
import subprocess
import platform
import time

def print_colored(text, color='white'):
    """Цветной вывод"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def run_command(command, description=""):
    """Выполнить команду с описанием"""
    if description:
        print_colored(f"\n▶️ {description}", 'cyan')
    print_colored(f"$ {command}", 'yellow')
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_colored("✅ Успешно", 'green')
            return True
        else:
            print_colored(f"❌ Ошибка: {result.stderr}", 'red')
            return False
            
    except subprocess.TimeoutExpired:
        print_colored("⏰ Таймаут команды", 'yellow')
        return False
    except Exception as e:
        print_colored(f"💥 Исключение: {e}", 'red')
        return False

def check_system():
    """Проверка системы"""
    print_colored("\n" + "═" * 50, 'blue')
    print_colored("🔍 ПРОВЕРКА СИСТЕМЫ", 'blue')
    print_colored("═" * 50, 'blue')
    
    system = platform.system()
    print_colored(f"Система: {system}", 'white')
    
    if system != "Linux":
        print_colored("⚠️  Внимание: Скрипт оптимизирован для Termux (Android)", 'yellow')
        print_colored("   На других системах могут быть проблемы", 'yellow')
    
    return system

def install_dependencies():
    """Установка зависимостей"""
    print_colored("\n" + "═" * 50, 'blue')
    print_colored("📦 УСТАНОВКА ЗАВИСИМОСТЕЙ", 'blue')
    print_colored("═" * 50, 'blue')
    
    # Обновление пакетов
    run_command("pkg update -y", "Обновление пакетов")
    run_command("pkg upgrade -y", "Обновление системы")
    
    # Установка Python
    run_command("pkg install python -y", "Установка Python")
    
    # Установка Git
    run_command("pkg install git -y", "Установка Git")
    
    # Дополнительные утилиты
    run_command("pkg install nano -y", "Установка текстового редактора")
    run_command("pkg install wget -y", "Установка wget")
    
    return True

def install_python_packages():
    """Установка Python пакетов"""
    print_colored("\n" + "═" * 50, 'blue')
    print_colored("🐍 УСТАНОВКА PYTHON ПАКЕТОВ", 'blue')
    print_colored("═" * 50, 'blue')
    
    # Обновление pip
    run_command("pip install --upgrade pip", "Обновление pip")
    
    # Установка Telethon
    run_command("pip install telethon==1.28.5", "Установка Telethon")
    
    # Дополнительные пакеты
    run_command("pip install colorama", "Установка Colorama для цветов")
    
    return True

def setup_project_structure():
    """Настройка структуры проекта"""
    print_colored("\n" + "═" * 50, 'blue')
    print_colored("📁 НАСТРОЙКА СТРУКТУРЫ ПРОЕКТА", 'blue')
    print_colored("═" * 50, 'blue')
    
    # Создание директорий
    directories = ['data', 'logs', 'backups']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print_colored(f"📁 Создана папка: {directory}", 'green')
        else:
            print_colored(f"📁 Папка уже существует: {directory}", 'yellow')
    
    # Создание файлов данных
    default_data = {
        'data/chats.json': [],
        'data/favorites.json': [],
        'data/folders.json': {"default": []},
        'data/templates.json': {
            "приветствие": "👋 Привет! Как дела?",
            "реклама": "🎯 Специальное предложение!",
            "новость": "📢 У нас важные новости!"
        },
        'data/stats.json': {"total_sent": 0, "total_errors": 0, "last_active": ""},
        'data/blacklist.json': []
    }
    
    import json
    for filepath, data in default_data.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print_colored(f"📄 Создан файл: {filepath}", 'green')
    
    return True

def set_permissions():
    """Установка прав доступа"""
    print_colored("\n" + "═" * 50, 'blue')
    print_colored("🔐 НАСТРОЙКА ПРАВ ДОСТУПА", 'blue')
    print_colored("═" * 50, 'blue')
    
    scripts = ['main.py', 'setup.py', 'start.sh', 'install.sh', 'update.sh', 'uninstall.sh']
    
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)  # rwxr-xr-x
            print_colored(f"🔧 Права установлены: {script}", 'green')
    
    return True

def show_instructions():
    """Показать инструкции"""
    print_colored("\n" + "═" * 50, 'green')
    print_colored("🎉 УСТАНОВКА ЗАВЕРШЕНА!", 'green')
    print_colored("═" * 50, 'green')
    
    print_colored("\n📱 ДЛЯ ЗАПУСКА БОТА:", 'cyan')
    print_colored("1. Запустите бота:", 'white')
    print_colored("   python main.py", 'yellow')
    
    print_colored("\n🚀 АЛИАСЫ (добавьте в ~/.bashrc):", 'cyan')
    print_colored("   alias tg='cd ~/telegram-sender && python main.py'", 'white')
    print_colored("   alias tg-start='cd ~/telegram-sender && python main.py'", 'white')
    print_colored("   alias tg-update='cd ~/telegram-sender && git pull'", 'white')
    print_colored("   alias tg-logs='tail -f ~/telegram-sender/logs/bot.log'", 'white')
    
    print_colored("\n📞 ПОДДЕРЖКА:", 'cyan')
    print_colored("   GitHub: github.com/wetnet-beep", 'white')
    print_colored("   Telegram: @wetnet_beep", 'white')
    
    print_colored("\n⚠️  ВАЖНО:", 'yellow')
    print_colored("   1. Получите API ключи на my.telegram.org", 'white')
    print_colored("   2. Используйте разумные задержки (2+ секунды)", 'white')
    print_colored("   3. Не делитесь файлом .session!", 'white')
    
    print_colored("\n" + "═" * 50, 'green')
    print_colored("Нажмите Enter для запуска бота...", 'cyan')
    input()

def main():
    """Основная функция"""
    # Красивый заголовок
    print_colored("╔══════════════════════════════════════════╗", 'blue')
    print_colored("║   TELEGRAM SENDER v4.0 - УСТАНОВЩИК     ║", 'blue')
    print_colored("║           Автор: wetnet-beep            ║", 'blue')
    print_colored("╚══════════════════════════════════════════╝", 'blue')
    print_colored("\n👋 Добро пожаловать! Начинаю установку...\n", 'cyan')
    
    try:
        # Шаг 1: Проверка системы
        check_system()
        time.sleep(1)
        
        # Шаг 2: Установка зависимостей
        install_dependencies()
        time.sleep(1)
        
        # Шаг 3: Установка Python пакетов
        install_python_packages()
        time.sleep(1)
        
        # Шаг 4: Настройка структуры
        setup_project_structure()
        time.sleep(1)
        
        # Шаг 5: Права доступа
        set_permissions()
        time.sleep(1)
        
        # Шаг 6: Инструкции
        show_instructions()
        
        # Запуск бота
        print_colored("\n🚀 Запускаю бота...", 'green')
        os.system("python main.py")
        
    except KeyboardInterrupt:
        print_colored("\n\n⚠️ Установка прервана пользователем", 'yellow')
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n💥 Критическая ошибка: {e}", 'red')
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/bin/bash
# Автоустановщик Telegram Sender v4.0
# Автор: wetnet-beep

clear
echo "╔══════════════════════════════════════════╗"
echo "║     TELEGRAM SENDER v4.0 - Установка    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "👋 Привет! Устанавливаю Telegram рассылку..."
echo ""

# Обновление пакетов
echo "🔄 Обновляю пакеты..."
pkg update -y && pkg upgrade -y

# Установка зависимостей
echo "📦 Устанавливаю Python и Git..."
pkg install python git -y

echo "📦 Устанавливаю Telethon..."
pip install telethon

# Скачивание бота
echo "⬇️ Скачиваю бота с GitHub..."
git clone https://github.com/wetnet-beep/telegram-sender

# Переход в папку
cd telegram-sender

# Настройка прав
chmod +x main.py
chmod +x start.sh

echo ""
echo "✅ Установка завершена!"
echo ""
echo "🚀 ДЛЯ ЗАПУСКА:"
echo "1. Перейдите в папку: cd telegram-sender"
echo "2. Запустите бота: python main.py"
echo ""
echo "📞 Поддержка: @wetnet_beep"
echo "💾 Репозиторий: github.com/wetnet-beep"
echo ""
echo "Нажмите Enter для запуска бота..."
read
python main.py

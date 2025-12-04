#!/bin/bash
# Telegram Sender - Обновление
# Автор: wetnet-beep

echo "🔄 Обновление Telegram Sender v4.0..."

cd ~/telegram-sender

echo "📥 Получаю обновления с GitHub..."
git pull origin main

echo "📦 Обновляю зависимости..."
pip install --upgrade telethon

echo "🔧 Настраиваю права..."
chmod +x *.py *.sh

echo "✅ Обновление завершено!"
echo ""
echo "🚀 Для запуска:"
echo "   cd ~/telegram-sender"
echo "   python main.py"

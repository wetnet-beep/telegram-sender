#!/bin/bash
# Telegram Sender - Удаление
# Автор: wetnet-beep

echo "🗑️ Удаление Telegram Sender v4.0..."
echo ""

# Подтверждение
read -p "Вы уверены? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Удаление отменено"
    exit 0
fi

echo "1. Удаляю файлы бота..."
rm -rf ~/telegram-sender

echo "2. Удаляю файлы сессии..."
rm -f ~/telegram_sender.session

echo "3. Удаляю PID файл..."
rm -f ~/telegram-sender/bot.pid

echo "4. Чистка логов..."
rm -rf ~/telegram-sender/logs

echo ""
echo "✅ Бот полностью удален!"
echo ""
echo "Если хотите удалить алиасы, откройте ~/.bashrc"
echo "и удалите строки с 'Telegram Sender Aliases'"

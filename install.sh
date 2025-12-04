#!/bin/bash
# Telegram Sender v4.0 - Автоустановщик для Termux
# Автор: wetnet-beep
# GitHub: github.com/wetnet-beep

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Функции для вывода
print_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     TELEGRAM SENDER v4.0 - Установка    ║${NC}"
    echo -e "${BLUE}║         Автор: ${WHITE}wetnet-beep${BLUE}              ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${YELLOW}▶️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Проверка Termux
check_termux() {
    if [ ! -d "/data/data/com.termux/files/usr" ]; then
        print_error "Этот скрипт предназначен только для Termux!"
        echo -e "${WHITE}Установите Termux из Play Store${NC}"
        exit 1
    fi
}

# Обновление пакетов
update_packages() {
    print_step "Обновление пакетов Termux..."
    apt update -y && apt upgrade -y
    if [ $? -eq 0 ]; then
        print_success "Пакеты обновлены"
    else
        print_error "Ошибка обновления пакетов"
        exit 1
    fi
}

# Установка зависимостей
install_dependencies() {
    print_step "Установка зависимостей..."
    
    # Основные пакеты
    packages=("python" "git" "nano" "wget" "curl")
    
    for pkg in "${packages[@]}"; do
        print_info "Устанавливаю $pkg..."
        apt install -y $pkg 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "$pkg установлен"
        else
            print_error "Ошибка установки $pkg"
        fi
    done
}

# Установка Python библиотек
install_python_libs() {
    print_step "Установка Python библиотек..."
    
    # Обновление pip
    print_info "Обновляю pip..."
    pip install --upgrade pip 2>/dev/null
    
    # Установка Telethon
    print_info "Устанавливаю Telethon..."
    pip install telethon==1.28.5 2>/dev/null
    
    # Дополнительные библиотеки
    print_info "Устанавливаю colorama..."
    pip install colorama 2>/dev/null
    
    print_success "Python библиотеки установлены"
}

# Скачивание проекта
download_project() {
    print_step "Скачивание проекта с GitHub..."
    
    # Удаляем старую версию если есть
    if [ -d "telegram-sender" ]; then
        print_warning "Найдена старая версия, обновляю..."
        rm -rf telegram-sender
    fi
    
    # Скачиваем с GitHub
    print_info "Клонирую репозиторий..."
    git clone https://github.com/wetnet-beep/telegram-sender.git
    
    if [ $? -eq 0 ]; then
        print_success "Проект скачан"
    else
        print_error "Ошибка скачивания с GitHub"
        print_info "Попробую альтернативный способ..."
        
        # Альтернативный способ через wget
        if command -v wget &> /dev/null; then
            wget https://github.com/wetnet-beep/telegram-sender/archive/main.zip
            unzip main.zip
            mv telegram-sender-main telegram-sender
            rm main.zip
            print_success "Проект скачан (альтернативный способ)"
        else
            print_error "Не удалось скачать проект"
            exit 1
        fi
    fi
}

# Настройка проекта
setup_project() {
    print_step "Настройка проекта..."
    
    cd telegram-sender
    
    # Создание директорий
    print_info "Создаю структуру папок..."
    mkdir -p data logs backups
    
    # Права доступа
    print_info "Настраиваю права доступа..."
    chmod +x *.py *.sh 2>/dev/null
    
    # Создание конфигурационных файлов
    print_info "Создаю файлы конфигурации..."
    
    # Если нет файлов данных, создаем
    if [ ! -f "data/templates.json" ]; then
        cat > data/templates.json << EOF
{
  "приветствие": "👋 Привет! Как дела?",
  "реклама": "🎯 Специальное предложение!",
  "новость": "📢 У нас важные новости!"
}
EOF
    fi
    
    print_success "Проект настроен"
}

# Установка алиасов
setup_aliases() {
    print_step "Настройка алиасов..."
    
    # Проверяем наличие .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        # Проверяем, есть ли уже алиасы
        if ! grep -q "alias tg=" "$HOME/.bashrc"; then
            print_info "Добавляю алиасы в .bashrc..."
            
            cat >> "$HOME/.bashrc" << 'EOF'

# Telegram Sender Aliases (wetnet-beep)
alias tg='cd ~/telegram-sender && python main.py'
alias tg-start='cd ~/telegram-sender && python main.py'
alias tg-update='cd ~/telegram-sender && git pull'
alias tg-logs='tail -f ~/telegram-sender/logs/bot.log'
alias tg-stop='pkill -f "python main.py"'
alias tg-status='ps aux | grep "python main.py"'
EOF
            
            print_success "Алиасы добавлены"
        else
            print_info "Алиасы уже установлены"
        fi
    else
        print_warning "Файл .bashrc не найден"
    fi
}

# Показать инструкцию
show_instructions() {
    print_header
    
    echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА!${NC}"
    echo ""
    echo -e "${CYAN}🚀 КОМАНДЫ ДЛЯ ЗАПУСКА:${NC}"
    echo -e "${WHITE}1. Перейдите в папку:${NC}"
    echo -e "   ${YELLOW}cd telegram-sender${NC}"
    echo ""
    echo -e "${WHITE}2. Запустите бота:${NC}"
    echo -e "   ${YELLOW}python main.py${NC}"
    echo ""
    echo -e "${WHITE}3. Или используйте алиасы:${NC}"
    echo -e "   ${YELLOW}tg${NC}          - запуск бота"
    echo -e "   ${YELLOW}tg-update${NC}   - обновление"
    echo -e "   ${YELLOW}tg-logs${NC}     - просмотр логов"
    echo ""
    echo -e "${CYAN}📱 ПЕРВЫЙ ЗАПУСК:${NC}"
    echo -e "${WHITE}1. Получите API ключи на: ${YELLOW}my.telegram.org${NC}"
    echo -e "${WHITE}2. Введите номер телефона${NC}"
    echo -e "${WHITE}3. Введите код из Telegram${NC}"
    echo ""
    echo -e "${CYAN}📞 ПОДДЕРЖКА:${NC}"
    echo -e "${WHITE}GitHub: ${YELLOW}github.com/wetnet-beep${NC}"
    echo -e "${WHITE}Telegram: ${YELLOW}@wetnet_beep${NC}"
    echo ""
    echo -e "${RED}⚠️  ВАЖНО:${NC}"
    echo -e "${WHITE}• Используйте задержки 2+ секунды${NC}"
    echo -e "${WHITE}• Не делитесь файлом .session${NC}"
    echo -e "${WHITE}• Соблюдайте правила Telegram${NC}"
    echo ""
    echo -e "${PURPLE}Нажмите Enter для запуска бота...${NC}"
    read
}

# Запуск бота
run_bot() {
    print_info "Запускаю бота..."
    cd telegram-sender
    python main.py
}

# Основная функция
main() {
    print_header
    
    # Проверка Termux
    check_termux
    
    # Обновление пакетов
    update_packages
    
    # Установка зависимостей
    install_dependencies
    
    # Установка Python библиотек
    install_python_libs
    
    # Скачивание проекта
    download_project
    
    # Настройка проекта
    setup_project
    
    # Установка алиасов
    setup_aliases
    
    # Инструкция
    show_instructions
    
    # Запуск бота
    run_bot
}

# Обработка ошибок
handle_error() {
    print_error "Произошла ошибка!"
    print_info "Попробуйте выполнить команды вручную:"
    echo ""
    echo "1. pkg update && pkg upgrade"
    echo "2. pkg install python git"
    echo "3. pip install telethon"
    echo "4. git clone https://github.com/wetnet-beep/telegram-sender"
    echo "5. cd telegram-sender"
    echo "6. python main.py"
    exit 1
}

# Установка обработчика ошибок
trap handle_error ERR

# Запуск
main

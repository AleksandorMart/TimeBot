import telebot
import calendar
from datetime import datetime
from telebot import types

bot = telebot.TeleBot('TOKEN')

the_list = {}
flag = 0
selected_date_key = None  # Чтобы сохранить дату, на которую мы добавляем расписание

@bot.message_handler(commands=['start'])
def start(message):
    global flag
    flag = 0
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='Начать!', callback_data='begin')
    markup.add(btn1)
    bot.send_message(message.chat.id, "Привет! Я бот-помощник по контролю твоего расписания!", reply_markup=markup)

def get_calendar(call, date):
    cal = calendar.monthcalendar(date.year, date.month)
    header = calendar.month_name[date.month] + ' ' + str(date.year)
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=header, callback_data='ignore'))
    markup.row(*[types.InlineKeyboardButton(text=day, callback_data='ignore') for day in days])

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                # Преобразование даты в строку формата 'YYYY-MM-DD'
                date_str = f"{date.year}-{date.month:02d}-{day:02d}"
                row.append(types.InlineKeyboardButton(text=str(day), callback_data=date_str))
        markup.row(*row)

    btn1 = types.InlineKeyboardButton(text='Прошлый', callback_data=f"last{date.year}-{date.month:02d}")
    btn2 = types.InlineKeyboardButton(text='Следующий', callback_data=f"next{date.year}-{date.month:02d}")
    markup.row(btn1, btn2)

    # Отправляем сообщение с клавиатурой выбора даты
    bot.send_message(call.message.chat.id, "Пожалуйста, выберите дату", reply_markup=markup)

# логика следующего и прошлого месяца
def handle_calendar_navigation(call, current_year, current_month):
    if call.data.startswith('last'):
        # Переход на предыдущий месяц
        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1

        # Проверка, чтобы нельзя было выбрать дату в прошлом
        if datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1]) < datetime.now():
            bot.send_message(call.message.chat.id, 'Нельзя выбрать дату в прошлом.')
            return
    
    elif call.data.startswith('next'):
        # Переход на следующий месяц
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

    get_calendar(call, datetime(current_year, current_month, 1))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global flag, the_list, selected_date_key

    if call.data == 'begin':
        flag = 0
        selected_date_key = None
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='watch')
        btn2 = types.InlineKeyboardButton(text='Добавить расписание', callback_data='add')
        markup.row(btn1, btn2)
        bot.send_message(call.message.chat.id, 'Как я могу помочь тебе с расписанием?', reply_markup=markup)

    elif call.data == 'watch':
        flag = 1 
        #вызываем функцию построения календаря с нынешней датой
        get_calendar(call, datetime.now())

    elif call.data == 'add':
        flag = 2
        get_calendar(call, datetime.now())

    elif 'last' in call.data or 'next' in call.data:
        date_str = call.data.replace('last', "").replace('next', "")
        year = int(date_str[:4])
        month = int(date_str[5:7])
        handle_calendar_navigation(call, year, month)

    elif call.data == 'change':
        flag = 2
        selected_date = datetime.strptime(selected_date_key, '%Y-%m-%d')
        bot.send_message(call.message.chat.id, f'Введите новое расписание для {selected_date.strftime("%d-%m-%Y")}:')

    else:
        try:
            selected_date = datetime.strptime(call.data, '%Y-%m-%d')
            selected_date_key = selected_date.strftime('%Y-%m-%d')

            # Просмотр записи
            if flag == 1:
                if selected_date_key in the_list:
                    record = the_list[selected_date_key]
                    markup = types.InlineKeyboardMarkup()
                    btn3 = types.InlineKeyboardButton(text='Меню', callback_data='begin')
                    markup.row(btn3)
                    bot.send_message(call.message.chat.id, f'Расписание на {selected_date.strftime("%d-%m-%Y")}: {record}', reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    btn4 = types.InlineKeyboardButton(text='Добавить расписание', callback_data='change')
                    btn5 = types.InlineKeyboardButton(text='Меню', callback_data='begin')
                    markup.row(btn4, btn5)
                    bot.send_message(call.message.chat.id, 'Расписание не найдено.', reply_markup=markup)

            # Добавление записи
            elif flag == 2:
                if selected_date_key in the_list:
                    record = the_list[selected_date_key]
                    markup = types.InlineKeyboardMarkup()
                    # Здесь добавьте логику для изменения записи от пользователя
                    btn6 = types.InlineKeyboardButton(text='Изменить', callback_data='change')
                    btn7 = types.InlineKeyboardButton(text='Меню', callback_data='begin')
                    markup.row(btn6, btn7)
                    bot.send_message(call.message.chat.id, f'Расписание на {selected_date.strftime("%d-%m-%Y")} уже существует: {record}', reply_markup=markup)
                else:
                    bot.send_message(call.message.chat.id, f'Введите новое расписание для {selected_date.strftime("%d-%m-%Y")}:')
        except ValueError:
            bot.send_message(call.message.chat.id, 'Некорректная дата, попробуйте снова.')

@bot.message_handler(func=lambda message: flag == 2 and selected_date_key is not None)
def handle_schedule_entry(message):
    global the_list, selected_date_key

    # Сохраните сообщение пользователя как запись расписания.
    new_record = message.text
    the_list[selected_date_key] = new_record

    markup = types.InlineKeyboardMarkup()
    btn8 = types.InlineKeyboardButton(text='Меню', callback_data='begin')
    markup.row(btn8)

    bot.send_message(message.chat.id, f'Расписание добавлено на {selected_date_key}: {new_record}', reply_markup=markup)

    # Сбросьте выбранную дату, чтобы предотвратить дальнейшие непреднамеренные изменения
    selected_date_key = None

bot.polling(none_stop=True, interval=0)

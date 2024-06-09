import datetime as dt
from re import fullmatch
import os
import threading
import time

from dotenv import load_dotenv
from remind_pill import pill_reminder_handler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram.ext

from connect import DB
from delete_pill import (
    pill_delete_handler, 
    pill_command_delete_handler, 
    delete_pill
)
from edit_pill import (
    pill_edit_handler, 
    pill_command_edit_handler, 
    edit_pill, 
    change, 
    pill_change_handler
)
from log_for_bot import logger, error_handler
from taken import (
    pill_taken_handler, 
    pill_command_taken_handler, 
    taken_pill
)


def do_reminders():
    while True:
        if CURRENT_DATE < dt.datetime.now().date():
            cursor.execute(
                'UPDATE pills_reminder SET taken=0'
            )
            conn.commit()

        hour = str(dt.datetime.now().hour)
        minute = str(dt.datetime.now().minute)

        cursor.execute(
            'SELECT * FROM pills_reminder WHERE strftime("%H", time) <= (?) \
            AND strftime("%M", time) <= (?) AND taken = 0', (hour, minute)
        )

        rows = cursor.fetchall()

        for row in rows:
            name = row[2]
            pill_time = row[1]
            user_id = row[4]
            button = [[InlineKeyboardButton(f"Take {name}", callback_data=f'{name} - {pill_time} Taken')]]
            reply_markup = InlineKeyboardMarkup(button)
            
            try:
                updater.bot.send_message(
                    text=f'Time to take {name}', 
                    chat_id=user_id, 
                    reply_markup=reply_markup
                )
            
            except Exception as err:
                logger.error(
                    'Ошибка в отправке напоминания'
                    f'пользователю: {user_id}\n'
                    f' Таблетка: {name} Ошибка: {err}'
                )
            
            logger.info(
                'Отправлено напоминание пользователю'
                f'пользователю: {user_id}\n'
                f' Таблетка: {name} Время: {pill_time}'
            )

        time.sleep(50)


def show_pills(update, context):
    user_id = update.message.chat_id
    
    cursor.execute(
        'SELECT * FROM pills_reminder WHERE user_id=?', 
        (user_id,)
    )
    
    rows = cursor.fetchall()
    
    if not rows:
        update.message.reply_text('Sorry, you dont have pills!')
        return telegram.ext.ConversationHandler.END    
    
    buttons = list()

    for row in rows:
        time = row[1]
        name = row[2]
        message = f'{name} - {time}'
        buttons.append([InlineKeyboardButton(message, callback_data='pills')])

    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text('This is your current pills:', reply_markup=reply_markup)
    
    logger.info(
        f'Пользователь {user_id} запросил свой список таблеток'
    )

    return telegram.ext.ConversationHandler.END


def menu(update, context):
    logger.info(
        f'Пользователь {update.message.chat_id} начал работу с ботом'
    )
    buttons = [
        [InlineKeyboardButton("Show Pills", callback_data='show_pills')],
        [InlineKeyboardButton("Add Pill", callback_data='add_pill')],
        [InlineKeyboardButton("Delete Pill", callback_data='delete_pill')],
        [InlineKeyboardButton("Edit Pill", callback_data='edit_pill')],
        [InlineKeyboardButton("Taken Pill", callback_data='taken_pill')],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text('Choose an action:', reply_markup=reply_markup)
    return


def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'show_pills':
        show_pills(query, context)
    if fullmatch(r'\b\w+\b\s-\s\d{2}:\d{2}\sTaken', query.data):
        taken_pill(query, context)
    if fullmatch(r'\b\w+\b\s-\s\d{2}:\d{2}\sEdit', query.data):
        edit_pill(query, context)
    if fullmatch(r'\b\w+\b\s\d{2}:\d{2}\s(Change-name|Change-time|Change-all)', query.data):
        change(query, context)
    if fullmatch(r'\b\w+\b\s-\s\d{2}:\d{2}\sDelete', query.data):
        delete_pill(query, context)


if __name__ == '__main__':

    load_dotenv()

    TOKEN = os.getenv('TOKEN')

    db = DB()

    if db.connect():
        conn = db.conn
        cursor = db.cursor

    updater = telegram.ext.Updater(TOKEN, use_context=True)

    disp = updater.dispatcher

    CURRENT_DATE = dt.datetime.now().date()
    
    threading.Thread(target=do_reminders).start()

    disp.add_handler(telegram.ext.CommandHandler('start', menu))
    disp.add_handler(telegram.ext.CommandHandler('show', show_pills))
    disp.add_handler(telegram.ext.CommandHandler('menu', menu))
    disp.add_handler(pill_reminder_handler)
    disp.add_handler(pill_command_delete_handler)
    disp.add_handler(pill_delete_handler)
    disp.add_handler(pill_command_edit_handler)
    disp.add_handler(pill_edit_handler)
    disp.add_handler(pill_change_handler)
    disp.add_handler(pill_command_taken_handler)
    disp.add_handler(pill_taken_handler)
    disp.add_handler(telegram.ext.CallbackQueryHandler(button))
    disp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()
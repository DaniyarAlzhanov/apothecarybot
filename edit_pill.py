from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram.ext

from connect import DB
from log_for_bot import logger
from validators import validate_time


db = DB()

if db.connect():
    conn = db.conn
    cursor = db.cursor


def new_edit(update, context):
    if update.callback_query:
        update = update.callback_query
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
        message = f'{name} - {time} Edit'
        buttons.append([InlineKeyboardButton(message.rstrip(' Edit'), callback_data=message)])

    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text('Choose a pill:', reply_markup=reply_markup)


def edit_pill(update, context):
    current_pill, current_time = update.data.rstrip(' Edit').split(' - ')
    user_id = update.message.chat_id
    cursor.execute(
        'SELECT * FROM pills_reminder WHERE user_id=? AND name=? AND time=?', 
        (user_id, current_pill, current_time)
    )
    
    if not cursor.fetchone():
        update.message.reply_text('Sorry, this pill doesnt exist!')
        return telegram.ext.ConversationHandler.END
    
    buttons = [
        [InlineKeyboardButton('Change name', callback_data=f'{current_pill} {current_time} Change-name')],
        [InlineKeyboardButton('Change time', callback_data=f'{current_pill} {current_time} Change-time')],
        [InlineKeyboardButton('Change all', callback_data=f'{current_pill} {current_time} Change-all')],        
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    update.message.reply_text(
        'What do you want to change:',
        reply_markup=reply_markup
    )


def change(update, context):
    global name, time
    if update.callback_query:
        update = update.callback_query
    name, time, message = update.data.split()

    if message == 'Change-name':
        update.message.reply_text('Choose new name for pill')
        return 'NAME'

    elif message == 'Change-time':
        update.message.reply_text('Choose new time for pill HH:MM')
        return 'TIME'

    else:
        update.message.reply_text('Choose new name and time NAME - HH:MM')
        return 'ALL'


def change_name(update, context):
    changed_name = update.message.text
    user_id = update.message.chat_id
    
    cursor.execute(
        'UPDATE pills_reminder SET name=? WHERE user_id=? AND name=? AND time=?', 
        (changed_name, user_id, name, time)
    )
        
    conn.commit()

    update.message.reply_text(f'Pill {name} edited!')

    logger.info(
        f'Пользователь {user_id} отредактировал название таблетки {name}'
    )
    
    return telegram.ext.ConversationHandler.END


def change_time(update, context):
    changed_time = update.message.text    
    user_id = update.message.chat_id
    
    if not validate_time(time):
        update.message.reply_text('Bad form of time!')
        return telegram.ext.ConversationHandler.END

    cursor.execute(
        'UPDATE pills_reminder SET time=? WHERE user_id=? AND name=? AND time=?', 
        (changed_time, user_id, name, time)
    )
        
    conn.commit()

    update.message.reply_text(f'Pill {name} edited!')

    logger.info(
        f'Пользователь {user_id} отредактировал время принятия таблетки {name}'
    )
    
    return telegram.ext.ConversationHandler.END


def change_all(update, context):
    changed_name, changed_time = update.message.text.split(' - ')
    user_id = update.message.chat_id
    
    if not validate_time(time):
        update.message.reply_text('Bad form of time!')
        return telegram.ext.ConversationHandler.END
    
    cursor.execute(
        'UPDATE pills_reminder SET time=?, name=? WHERE user_id=? AND name=? AND time=?', 
        (changed_time, changed_name, user_id, name, time)
    )
        
    conn.commit()

    update.message.reply_text(f'Pill {name} edited!')

    logger.info(
        f'Пользователь {user_id} отредактировал таблетку {name}'
    )
    
    return telegram.ext.ConversationHandler.END


def cancel():
    return telegram.ext.ConversationHandler.END


pill_command_edit_handler = telegram.ext.CommandHandler('edit', new_edit)

pill_edit_handler = telegram.ext.CallbackQueryHandler(pattern='edit_pill', callback=new_edit)

pill_change_handler = telegram.ext.ConversationHandler(
    entry_points=[
        telegram.ext.CallbackQueryHandler(pattern=r'\b\w+\b\s\d{2}:\d{2}\s(Change-name|Change-time|Change-all)', callback=change)
    ],
    states={
        'NAME': [telegram.ext.MessageHandler(telegram.ext.Filters.text, change_name)],
        'TIME': [telegram.ext.MessageHandler(telegram.ext.Filters.text, change_time)],
        'ALL': [telegram.ext.MessageHandler(telegram.ext.Filters.text, change_all)],
    },
    fallbacks=[telegram.ext.CommandHandler('cancel', cancel)]
)

import telebot
import numpy
import requests
import sqlite3
import logging
import ssl
from aiohttp import web

import game_main
from game_folder.shop import close_shop, sell_menu, buy_menu
from game_folder.game_classes.game_control import game_control
import hangman.hangman as hangman
from faces.face_control import find_faces, add_goblin_face
import illuminaty_secrets

WEBHOOK_HOST = illuminaty_secrets.NUKE_CODE
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

API_TOKEN = illuminaty_secrets.DA_VINCI_CODE

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)


bot = telebot.TeleBot(API_TOKEN)

app = web.Application()

async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)


app.router.add_post('/{token}/', handle)


logging.basicConfig(filename='log.txt',
                            filemode='a',
                            format='%(asctime)s; %(levelname)s %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)



@bot.message_handler(commands=['start'])
def start_message(message):
    if len(message.text.split()) > 1:
        code = message.text.split()[1]

        user_slot = hangman_player()
        if user_slot.load_with_link(code):
            user_slot.playing_with = message.chat.id
            user_slot.is_waiting = False
            user_slot.invitation_link = 0
            user_slot.save(user_slot.user_id)

            user_connecting = hangman_player()
            user_connecting.create_new(message)
            user_connecting.user_id = message.from_user.id
            user_connecting.language = message.from_user.language_code
            user_connecting.synhronize(user_slot)

            user_connecting.save(message.from_user.id)
            user_slot.send_message(bot, message)

        else:
            bot.send_message(message.chat.id, 'Link is no longer valid')
        return 0 


    if message.from_user.language_code == 'ru':
        text = 'Добро пожаловать, '+message.from_user.first_name+'. Чтобы посмотреть все функции бота, нажмите /help'
    else:
        text = 'Welcome '+message.from_user.first_name+'. To see available commands type /help'
    bot.send_message(message.chat.id, text)

   

@bot.message_handler(commands=['game'])
def game_message(message):

    game_control().delete(message.from_user.id)
    game_control().create(message.from_user.id)


    logging.info(message.from_user.first_name+' started the game.')

    info = 'Welcome to the world of Laindor!\nTo exit the game type /quit or /exit.\nTo see your characters status type /status.'+\
    '\nTo see game ratings type /rating_game'
    bot.send_message(message.chat.id, info)
    game_main.create_character(bot, message, True)


@bot.message_handler(commands=['help'])
def help_message(message):
    if message.from_user.language_code == 'ru':
        text = 'На данный момент бот имеет следующие команды:\n'
        text += '/start - начать \n/help - помощь \n/roll - бросить кубики \n\n/game - сыграть в dungeon crawler (EN)'
        text += '\n/rating_game - таблица лидеров в игре \n\n/hangman - сыграть в виселицу \n/rating_hangman - таблица лидеров в виселице'
        text += '\n\nТакже бот умеет обрабатывать селфи, просто киньте ему фото.'
    else:
        text = 'Currently bot is capable of performing the following commands:\n'
        text += '/start - begin \n/help - the description of commands \n/roll - roll dices \n\n/game - play an adventure (EN)'
        text += '\n/rating_game - game leaderboard \n\n/hangman - play hangman (RU) \n/rating_hangman - hangman leaderboard'
        text += '\n\nBot is also able to eddit your selfies, just send him a photo.'
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['rating_game'])
def rating_game(message):
    game_main.show_rating(bot, message)
    return 0 

@bot.message_handler(commands=['rating_hangman'])
def rating_hangman(message):
    hangman.hangman_show_rating(bot, message)
    return 0

@bot.message_handler(commands=['roll'])
def roll_message(message):

    def rolling(N, M):
        try:
            N = int(N)
            M = int(M)
        except ValueError:
            bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только целые числа.')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIFL15SqRFlR3iRIgHDugABWD-c9d8d_QACMQQAAo-dWgUlIW0uOAXokRgE')
            return False

        if M > 0 and N > 0:
            if M < 1000 and N < 1000:
                try:
                    x =  numpy.random.randint(low=1, high=M+1, size=N)
                    result = ''
                    for i in range(len(x)):
                        if i == len(x)-1:
                            result += str(x[i])
                        else:
                            result += str(x[i])+', '
                        
                    return result
                except Exception:
                    bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только целые числа.')
                    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIFL15SqRFlR3iRIgHDugABWD-c9d8d_QACMQQAAo-dWgUlIW0uOAXokRgE')
                    return False
            else:
                bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте числа меньше 1000.')
                return False
        else: 
            bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только положительные числа.')
            return False


    text = message.text.split(' ')
    logging.info(message.from_user.first_name+': '+message.text)
    error_flag = True
    if len(text) > 1:
        for i in range(1, len(text)):
            element = text[i]
            if len(element) >= 3: # 3 is minimum in 'NdM' construction
                x = element.lower().split('d')
                if len(x) == 2:
                    error_flag = False
                    result = rolling(x[0], x[1])
                    if result:
                        bot.send_message(message.chat.id, 'Результаты броска: \n'+result)
                        return 0

    if error_flag:
        bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'')





@bot.message_handler(commands=['hangman'])
def play_hangman(message):

    hangman.hangman_player().create_new(message)

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row(u'\U0001F1F7\U0001F1FA', u'\U0001F1EC\U0001F1E7')
    bot.send_message(message.chat.id, 'Select language first:', reply_markup=keyboard)
    return 0 



@bot.callback_query_handler(func=lambda call: True)
def query_text(call):
    if 'Welcome' in call.message.text.split() and 'shop' in call.message.text.split():
        if call.data == 'close':
            close_shop(bot, call)
            game_main.game(bot, call)
        elif call.data == 'sell':
            sell_menu(bot, call)
        elif call.data == 'buy':
            buy_menu(bot, call)
        return 0
    if 'sell' in call.data.split('->'):
        sell_menu(bot, call)
        return 0
    if 'buy' in call.data.split('<-'):
        buy_menu(bot, call)
        return 0
    
    x = game_main.inventory_buttons(bot, call)
    if x == 1:
        game_main.clean_history(call)
    

def analyze_end_of_sentence(text):
    question_flag = False
    exclamation_flag = False
    for i in range(len(text)):
        element = text[i]
        if element[0] == '?' or element[-1] == '?':
            question_flag = True
        if element[0] == '!' or element[-1] == '!':
            exclamation_flag = True
        if element[0] == '?' or element[0] == '!':
            text[i] = element[1:]
        if element[-1] == '?' or element[-1] == '!':
            text[i] = element[:-1]
    return question_flag, exclamation_flag, text
        


@bot.message_handler(content_types=['text'])
def send_text(message):
    # hangman part
    if check_if_playing(message.from_user.id, 'hangman/hangman_users.bd'):
        # open file and get current status
        user_slot = hangman.hangman_player()
        user_slot.load(message.from_user.id)

        # check whether word has already been selected
        if user_slot.selected_word == ' ':
            if message.text == u'\U0001F1F7\U0001F1FA':
                word = hangman.choose_word('ru')
            elif message.text == u'\U0001F1EC\U0001F1E7':
                word = hangman.choose_word('en')
            else:
                bot.send_message(message.chat.id,'Select the language first')
                return 0 

            user_slot.selected_word = word[0]
            user_slot.current_word = hangman.select_letters(user_slot.selected_word)
            

            logging.info(message.from_user.first_name+' started hangman with word: '+word[0])

            user_slot.is_waiting = True
            if message.from_user.language_code == 'ru':
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row('Играть одному', 'Играть с другом')
                bot.send_message(message.chat.id, 'Вы хотите играть один или с другом?', reply_markup=keyboard)
            else:
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row('Play by yourself', 'Play with friend')
                bot.send_message(message.chat.id, 'Do you want to play by yourself or with friend?', reply_markup=keyboard)
            user_slot.save(message.from_user.id)
            return 0

        # wait for connection from other user
        if user_slot.is_waiting:
            if message.text.lower() in ['play by yourself', 'играть одному']:
                user_slot.is_waiting = False
                add = user_slot.selected_word[0]
                for i in range(1,len(user_slot.selected_word)):
                    add += ' '+user_slot.current_word[i]
                if message.from_user.language_code == 'ru':
                    information = 'Чтобы закончить игру, напишите /exit, /quit.\nЧтобы посмотреть рейтинг игроков, напишите /rating_hangman\n\n'
                    bot.send_message(message.chat.id, 'Виселица началась!\n'+information+'Загаданное слово:\n'+add)
                else:
                    information = 'To end the game type /exit or /quit.\nTo see the leaderboard type /rating_hangman\n\n'
                    bot.send_message(message.chat.id, 'Hangman starts!\n'+information+'The hidden word:\n'+add)
                bot.send_photo(message.chat.id, photo=open('hangman/75px-Hangman-0.png', 'rb'))
                user_slot.save(message.from_user.id)
                return 0

            if message.text.lower() in ['play with friend', 'играть с другом']:
                link = 'https://t.me/GronxBot?start=' + user_slot.generate_link() 
                if message.from_user.language_code == 'ru':
                    information = 'Отправьте эту ссылку другу: '+link+\
                    '\n\nЧтобы закончить игру, напишите /exit, /quit.\nЧтобы посмотреть рейтинг игроков, напишите /rating_hangman\n\n'
                else:
                    information = 'Send this link to your friend: '+link+\
                    '\n\nTo end the game type /exit or /quit.\nTo see the leaderboard type /rating_hangman\n\n'
                bot.send_message(message.chat.id, information)

            if message.text.lower() in ['/exit', '/quit']:
                user_slot.delete(message.from_user.id)
                bot.send_message(message.chat.id, 'The game of hangman has ended.')
                
            user_slot.save(message.from_user.id)
            return 0
            

        text = message.text.lower().split(' ')
        if len(text) > 1:
            bot.send_message(message.chat.id, 'Type no more then 1 letter.')

        if len(text) == 1:
            letter = text[0]
            if len(letter) != 1:
                if letter == 'exit' or letter == '/exit' or letter == 'quit' or letter == '/quit':
                    user_slot.delete(message.from_user.id)
                    bot.send_message(message.chat.id, 'The game of hangman has ended.')
                else: 
                    bot.send_message(message.chat.id, 'Type no more then 1 letter.')
            else:
                hangman.hangman_game(bot, letter, message)
        return 0


    # dungeon part
    if check_if_playing(message.from_user.id, 'game_folder/game_control.bd'):
        if message.text == 'exit' or message.text == '/exit' or message.text == 'quit' or message.text == '/quit':
            game_main.clean_history(message)
            bot.send_message(message.chat.id, 'The game has ended.')
        elif message.text == '/status':
            game_main.show_status(bot, message)
            return 0
        else:
            x = game_main.game(bot, message)
            if x == 1:
                game_main.clean_history(message)

        return 0 

    user_first_name = message.from_user.first_name
    logging.info('')
    logging.info(message.from_user.first_name+': '+message.text)

    talking_about_bot_flag = False
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Категорически приветствую, '+user_first_name)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMuXlKHWtcszX07qNYvk2ZAwopM4egAAkAEAAKPnVoFHHWgrTzYiJQYBA')
    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, 'Прощай, '+user_first_name)
    else:
        text = message.text.lower().split()
        question_flag, exclamation_flag, text = analyze_end_of_sentence(text)
        if 'ты' in text or 'тебе' in text or 'тебя' in text or 'тобой' in text or 'тобою' in text:
            talking_about_bot_flag = True
        if 'нужно' in text or 'нуждаешься' in text and talking_about_bot_flag:
            bot.send_message(message.chat.id, 'У меня есть шоколадка несквик, сигареты и святой источник, мне этого хватает.')
        elif question_flag and talking_about_bot_flag:
            if 'как' in text:
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIIVl5TxfHi--uGmDug7Zv-QAABGsFpSAACxwQAAo-dWgV9IAe0tiMd5xgE')
            elif 'кто' in text:
                bot.send_message(message.chat.id, 'Смотря кто спрашивает.')
            elif 'что' in text:
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIIWl5Txq5DFQ_gklYgWPSKFeiL97HMAAJxBAACj51aBfB-Mj_Qs-ClGAQ')
            elif 'где' in text:
                bot.send_message(message.chat.id, 'На небесах. С Аллахом!'+u'\U0000261D')
            elif 'зачем' in text:
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIIXF5Tx0s-YKIJiS2pUfUbVRqL3h9oAAKBBAACj51aBYU0D7R4w6pBGAQ')
            elif 'откуда' in text:
                bot.send_message(message.chat.id, 'Откуда надо...')
            elif 'чей' in text:
                bot.send_message(message.chat.id, 'Я русский, а русский значит принадлежу только богу'+u'\U0000261D')
            else:
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIIXl5Tynv-Nd1EKU6K4QABx07bpEDgoAACHgQAAo-dWgXEDr_TruJ1PxgE')
            

        else:
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAANDXlKMLgmAusLnZwQN3kq3BJo8xTAAAiUEAAKPnVoFiKge6n984mIYBA')

@bot.message_handler(content_types=['sticker'])
def return_sticker_id(message):
    logging.info('')
    logging.info(message.from_user.first_name+': '+message.sticker.file_id)
    
    rand_number = numpy.random.randint(low=0, high=4, size=1)
    if rand_number == 0:
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMvXlKIY3fZt1k7MQ9WXCaC9JE799YAAh0EAAKPnVoFWYV6aEDzMekYBA')
    if rand_number == 1:
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMwXlKInxNNnePPaKeKQmAk-kBMDR4AAioEAAKPnVoF2zEO1mJAARQYBA')
    if rand_number == 2:
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMxXlKIwm2YVeZ6h_dk-rt5mIKkfoAAAscEAAKPnVoFfSAHtLYjHecYBA')
    if rand_number == 3:
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMyXlKJPWff4M193uuTDiJcp17TnaQAAjAEAAKPnVoFafFq3fvGJ2gYBA')
    if rand_number == 4:
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMzXlKJsqrLerBBdn9Jf76IrgN8xsgAAmcFAAKPnVoFM89GkQ4uguAYBA')




@bot.message_handler(content_types=['photo'])
def change_faces(message):
    logging.info(message.from_user.first_name+': '+'Uploaded photo')

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open('faces/image.png', 'wb') as output:
        output.write(downloaded_file)

    faces = find_faces()
    if len(faces) == 0:
        bot.send_message(message.chat.id, 'Я не вижу лица.')
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIHHV5S8h6BYwfsTx1qfQcAAUDbjsijmwACbAUAAo-dWgWXYQu0FK_CYRgE')
        return 0
    add_goblin_face(faces)

    bot.send_photo(message.chat.id, photo=open('faces/goblin_image.png', 'rb'))




def check_if_playing(user_id, file_game):
    conn = sqlite3.connect(file_game)
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? LIMIT 1', [user_id])
    temp = c.fetchall() 
    conn.close()

    if len(temp) == 1:
        return True
    else:
        return False






# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Build ssl context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start aiohttp server
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)

#bot.polling()



import telebot
import numpy
from PIL import Image
import cv2
import requests
import game_main
from pandas.plotting import table 
import matplotlib.pyplot as plt
import pandas
import sqlite3
import random
import string

import logging
import ssl
from aiohttp import web
import asyncio

WEBHOOK_HOST = ''
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

API_TOKEN = ''

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


def fun(n):
    x = game_main.game_control()
    x.delete(n)
    x.create(n)

#fun(100747297)    

@bot.message_handler(commands=['game'])
def game_message(message):

    game_main.game_control().delete(message.from_user.id)
    game_main.game_control().create(message.from_user.id)


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
    hangman_show_rating(bot, message)
    return 0

@bot.message_handler(commands=['roll'])
def roll_message(message):
    logging.info('')
    cool_check = True

    def rolling(N, M):
        try:
            N = int(N)
            M = int(M)
        except ValueError:
            bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только целые числа.')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIFL15SqRFlR3iRIgHDugABWD-c9d8d_QACMQQAAo-dWgUlIW0uOAXokRgE')
            return numpy.array([-1])

        if M > 0 and N > 0:
            if M < 1000 and N < 1000:
                try:
                    return numpy.random.randint(low=1, high=M+1, size=N)
                except Exception:
                    bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только целые числа.')
                    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIFL15SqRFlR3iRIgHDugABWD-c9d8d_QACMQQAAo-dWgUlIW0uOAXokRgE')
                    return numpy.array([-1])
            else:
                bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте числа меньше 1000.')
                return numpy.array([-1])
        else: 
            bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'. Используйте только положительные числа.')
            return numpy.array([-1])


    text = message.text.split(' ')
    logging.info(message.from_user.first_name+': '+message.text)
    result = numpy.array([-2])
    if len(text) > 1:
        for i in range(1, len(text)):
            element = text[i]
            if len(element) >= 3: # 3 is minimum in 'NdM' construction
                x = element.lower().split('d')
                if len(x) == 1: # no 'd' in the word
                    y = element.lower().split('к') # maybe it's 'к' instead of 'd'?
                    if len(y) != 2: continue #it's not 'к' or it's not a correct construction
                    else: 
                        result = rolling(y[0], y[1])
                        if result[0] != -1:
                            bot.send_message(message.chat.id, 'Результаты броска: \n'+str(result)+'\nСумма: '+str(numpy.sum(result)))
                            cool_check = False
                if len(x) > 2: continue # several 'd's in the word
                if len(x) == 2:
                    result = rolling(x[0], x[1])
                    if result[0] != -1:
                        bot.send_message(message.chat.id, 'Результаты броска: \n'+str(result)+'\nСумма: '+str(numpy.sum(result)))
                        cool_check = False

            if len(element) == 0: continue #for cases with extra spaces

    if cool_check and result[0] == [-2]: 
        bot.send_message(message.chat.id, 'После /roll напишите количество N и тип кубиков M в формате \'NdM\'')


class hangman_player():
    """docstring for hangman_player"""
    def __init__(self):
        self.selected_word = ' '*100
        self.current_word = ' '*100
        self.number_of_attempts = 0
        self.user_id = 0
        self.language = ' '*10

        self.invitation_link = ' '*100
        self.is_waiting = False
        self.playing_with = 0

    def generate_link(self):
        letters = string.ascii_lowercase
        code = ''.join(random.choice(letters) for i in range(20))
        self.invitation_link = code
        return code

    def send_message(self, bot, message):
        bot.send_message(self.user_id, message.from_user.first_name+' connected')

        word = self.selected_word[0]
        for i in range(1,len(self.selected_word)):
            word += ' '+self.current_word[i]
        if self.language == 'ru':
            information = 'Чтобы закончить игру, напишите /exit, /quit.\nЧтобы посмотреть рейтинг игроков, напишите /rating_hangman\n\n'
            bot.send_message(self.user_id, 'Виселица началась!\n'+information+'Загаданное слово:\n'+word)
        else:
            information = 'To end the game type /exit or /quit.\nTo see the leaderboard type /rating_hangman\n\n'
            bot.send_message(self.user_id, 'Hangman starts!\n'+information+'The hidden word:\n'+word)
        bot.send_photo(self.user_id, photo=open('hangman/75px-Hangman-0.png', 'rb'))


        if message.from_user.language_code == 'ru':
            information = 'Чтобы закончить игру, напишите /exit, /quit.\nЧтобы посмотреть рейтинг игроков, напишите /rating_hangman\n\n'
            bot.send_message(message.chat.id, 'Виселица началась!\n'+information+'Загаданное слово:\n'+word)
        else:
            information = 'To end the game type /exit or /quit.\nTo see the leaderboard type /rating_hangman\n\n'
            bot.send_message(message.chat.id, 'Hangman starts!\n'+information+'The hidden word:\n'+word)
        bot.send_photo(message.chat.id, photo=open('hangman/75px-Hangman-0.png', 'rb'))
        

    def synhronize(self, friend):
        self.selected_word = friend.selected_word
        self.current_word = friend.current_word
        self.playing_with = friend.user_id


    def load(self, user_id):
        conn = sqlite3.connect('hangman/hangman_users.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM players WHERE user_id = ? LIMIT 1', [user_id])
        temp = c.fetchall()[0]
        conn.close()

        self.selected_word = temp[1]
        self.current_word = temp[2]
        self.number_of_attempts = int(temp[3])
        self.user_id = int(temp[0])
        self.language = temp[4]

        self.invitation_link = temp[5]
        self.is_waiting = bool(int(temp[6]))
        self.playing_with = int(temp[7])


    def create_new(self, message):
        conn = sqlite3.connect('hangman/hangman_users.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO players VALUES (?,?,?,?,?,?,?,?)', 
            (message.from_user.id, ' ', ' ', 0, message.from_user.language_code, ' ', 0, 0))
        conn.commit()
        conn.close()


    def save(self, user_id):
        conn = sqlite3.connect('hangman/hangman_users.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO players VALUES (?,?,?,?,?,?,?,?)', 
            (user_id, self.selected_word, self.current_word, self.number_of_attempts, 
                self.language, self.invitation_link, int(self.is_waiting), self.playing_with))
        conn.commit()
        conn.close()

    def delete(self, user_id):
        conn = sqlite3.connect('hangman/hangman_users.bd')
        c = conn.cursor()
        c.execute('DELETE FROM players WHERE user_id = ? LIMIT 1', [user_id])
        conn.commit()
        conn.close()

    def load_with_link(self, link):
        conn = sqlite3.connect('hangman/hangman_users.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM players WHERE invitation_link = ? LIMIT 1', [link])
        temp = c.fetchall()
        conn.close()

        if len(temp) == 1:
            temp = temp[0]
            self.selected_word = temp[1]
            self.current_word = temp[2]
            self.number_of_attempts = int(temp[3])
            self.user_id = int(temp[0])
            self.language = temp[4]

            self.invitation_link = temp[5]
            self.is_waiting = bool(int(temp[6]))
            self.playing_with = int(temp[7])
            return True
        else:
            return False






def choose_word(language_code):
    if language_code == 'ru':
        dictionary = numpy.genfromtxt('word_rus.txt', dtype=numpy.unicode_)
    else:
        dictionary = numpy.genfromtxt('hangman/conv.data.noun', dtype=numpy.unicode_)
    index = numpy.random.randint(low=0, high=len(dictionary), size=1)
    return dictionary[index]

def select_letters(word):
    current_word = word[0]
    for i in range(1, len(word)):
        if word[i] == word[-1] or word[i] == word[0]:
            current_word += word[i]
        else:
            current_word += '_'
    return current_word


@bot.message_handler(commands=['hangman'])
def play_hangman(message):
    global user_slot

    hangman_player().create_new(message)

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row(u'\U0001F1F7\U0001F1FA', u'\U0001F1EC\U0001F1E7')
    bot.send_message(message.chat.id, 'Select language first:', reply_markup=keyboard)
    return 0 


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
        user_slot = hangman_player()
        user_slot.load(message.from_user.id)

        # check whether word has already been selected
        if user_slot.selected_word == ' ':
            if message.text == u'\U0001F1F7\U0001F1FA':
                word = choose_word('ru')
            elif message.text == u'\U0001F1EC\U0001F1E7':
                word = choose_word('en')
            else:
                bot.send_message(message.chat.id,'Select the language first')
                return 0 

            user_slot.selected_word = word[0]
            user_slot.current_word = select_letters(user_slot.selected_word)
            

            logging.info('')
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
                hangman_game(letter, message)
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            x = loop.run_until_complete(game_main.game(bot, message))
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

def find_faces():
    imagePath = 'faces/image.png'
    cascPath = "faces/haarcascade_frontalface_default.xml"

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    # Read the image
    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(30, 30)
        #flags = cv2.cv.CV_HAAR_SCALE_IMAGE
    )

    logging.info("Found {0} faces!".format(len(faces)))

    # Draw a rectangle around the faces
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imwrite('faces/image_rect.png', image)
    return faces

def add_goblin_face(faces):
    img = Image.open('faces/image.png')
    rand_number = numpy.random.randint(low=1, high=5, size=len(faces))
    for i in range(len(faces)):
        goblin_name = 'faces/goblin_face/goblin_face-'+str(rand_number[i])+'.png'
        goblin_img = Image.open(goblin_name)
        x, y, w, h = faces[i] 
        goblin_img = goblin_img.resize((int(w*1.18), int(h*1.4)))
        img.paste(goblin_img, (x-int(w*0.09), y-int(h*0.2)), goblin_img)

    img.save('faces/goblin_image.png')


@bot.message_handler(content_types=['photo'])
def change_faces(message):
    logging.info('')
    logging.info(message.from_user.first_name+': '+'Uploaded photo')

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    #file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(API_TOKEN, file_info.file_path))
    with open('faces/image.png', 'wb') as output:
        output.write(downloaded_file)

    faces = find_faces()
    if len(faces) == 0:
        bot.send_message(message.chat.id, 'Я не вижу лица.')
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIHHV5S8h6BYwfsTx1qfQcAAUDbjsijmwACbAUAAo-dWgWXYQu0FK_CYRgE')
        return 0
    add_goblin_face(faces)

    bot.send_photo(message.chat.id, photo=open('faces/goblin_image.png', 'rb'))


def hangman_game(letter, message):
    check_for_winning = True

    logging.info('')
    logging.info(message.from_user.first_name+' playing hangman: '+message.text)
    
    user_slot = hangman_player()
    user_slot.load(message.from_user.id)

    if len(user_slot.selected_word.split(letter)) != 1:
        memory = numpy.zeros(len(user_slot.selected_word))
        for i in range(1, len(user_slot.selected_word)-1):
            if user_slot.selected_word[i] == letter:
                memory[i] = 1

        index, = numpy.where(memory != 0)
        for i in index:
            temp = user_slot.current_word[0:i]+letter
            user_slot.current_word = temp + user_slot.current_word[i+1:]

        #check for winning
        for i in range(len(user_slot.current_word)):
            if user_slot.current_word[i] == '_':
                check_for_winning = False

        if check_for_winning:
            rating = hangman_rating(message, True)
            if message.from_user.language_code == 'ru':
                info = '.\nВы находитесь на '+str(rating)+' месте. Чтобы увидеть весь рейтинг напишите /rating_hangman'
                bot.send_message(message.chat.id, 'Вы выиграли! Загаданное слово было '+user_slot.selected_word+info)
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIF3l5SxwdmJLonehCJ_kXytXOFEDVJAAJqBQACj51aBezX_MwOvzwHGAQ')
            else:
                info = '.\nYou are on '+str(rating)+' place. To see the whole leaderboard type /rating_hangman'
                bot.send_message(message.chat.id, 'You won! The hidden word was '+user_slot.selected_word+info)

            if user_slot.playing_with != 0:
                bot.send_message(user_slot.playing_with, message.from_user.first_name+' won!')
                
            user_slot.delete(message.from_user.id)
            return 0


        add = user_slot.selected_word[0]
        for i in range(1,len(user_slot.selected_word)):
            add += ' '+user_slot.current_word[i]
        if message.from_user.language_code == 'ru': 
            bot.send_message(message.chat.id, 'Загаданное слово:\n'+add)
        else: 
            bot.send_message(message.chat.id, 'The hidden word:\n'+add)
        photo_name = 'hangman/75px-Hangman-'+str(int(user_slot.number_of_attempts))+'.png'
        bot.send_photo(message.chat.id, photo=open(photo_name, 'rb'))
        
        if user_slot.playing_with != 0: 
            bot.send_message(user_slot.playing_with, message.from_user.first_name+' guessed a letter')
        
        user_slot.save(message.from_user.id)
    else:
              
        user_slot.number_of_attempts += 1
        if user_slot.number_of_attempts < 6:
            add = user_slot.selected_word[0]
            for i in range(1,len(user_slot.selected_word)):
                add += ' '+user_slot.current_word[i]
            if message.from_user.language_code == 'ru': 
                bot.send_message(message.chat.id, 'Загаданное слово:\n'+add)
            else: 
                bot.send_message(message.chat.id, 'The hidden word:\n'+add)
            user_slot.save(message.from_user.id)

            photo_name = 'hangman/75px-Hangman-'+str(int(user_slot.number_of_attempts))+'.png'
            bot.send_photo(message.chat.id, photo=open(photo_name, 'rb'))
        else:
            rating = hangman_rating(message, False)
            if message.from_user.language_code == 'ru':
                info = '.\nВы находитесь на '+str(rating)+' месте. Чтобы увидеть весь рейтинг напишите /rating_hangman'
                bot.send_message(message.chat.id, 'Вы проиграли. Загаданное слово было '+user_slot.selected_word+info)
                bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIFo15Sw_qBwmahpFlx4bIlbxesVJcTAAKIBQACj51aBdyiLJa0XpXkGAQ')
            else:
                info = '.\nYou are on '+str(rating)+' place. To see the whole leaderboard type /rating_hangman'
                bot.send_message(message.chat.id, 'You lost. The hidden word was '+user_slot.selected_word+info)
            
            if user_slot.playing_with != 0:
                bot.send_message(user_slot.playing_with, message.from_user.first_name+' lost!')

            user_slot.delete(message.from_user.id)
            return 0


def hangman_rating(message, win):
    conn = sqlite3.connect('hangman/final_score.bd')
    c = conn.cursor()

    user_name = message.from_user.first_name
    user_id = message.from_user.id
    c.execute('SELECT * FROM score WHERE user_id=?', [(user_id)])
    scores = c.fetchall()
    scores = numpy.asarray(scores)
    if len(scores) == 1:
        scores = scores[0]
        if win:
            c.execute('INSERT or REPLACE INTO score VALUES (?,?,?,?,?)', 
                (scores[0], int(scores[1])+1, int(scores[2])+1, round((int(scores[1])+1)/(int(scores[2])+1)*100,2), int(scores[4])))
        else:
            c.execute('INSERT or REPLACE INTO score VALUES (?,?,?,?,?)', 
                (scores[0], int(scores[1]), int(scores[2])+1, round(int(scores[1])/(int(scores[2])+1)*100,2), int(scores[4])))
        conn.commit()
    elif len(scores) == 0:
        if win:
            c.execute('INSERT INTO score VALUES (?,?,?,?,?)', (user_name, 1, 1, 100.0, user_id))
        else:
            c.execute('INSERT INTO score VALUES (?,?,?,?,?)', (user_name, 0, 1, 0.0, user_id))
        conn.commit()
    else:
        logging.warning('There is someone else with the same user id')



    c.execute('SELECT * FROM score')
    players = c.fetchall()
    conn.close()

    percent_of_wins = numpy.zeros(len(players))
    N_games = numpy.zeros(len(players))
    for i in range(len(players)):
        percent_of_wins[i] = players[i][3]
        N_games[i] = players[i][2] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(percent_of_wins))
    players = players[index][:10]
    percent_of_wins = percent_of_wins[index][:10]
    N_games = N_games[index][:10]

    for i in range(len(percent_of_wins)):
        if i != 0 and percent_of_wins[i] == percent_of_wins[i-1]:
            continue

        sel = (percent_of_wins == percent_of_wins[i])
        temp2 = N_games[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]

    k, = numpy.where(players[:,0] == user_name)
    
    conn.close()
    return k[0]+1

def hangman_show_rating(bot, message):
    
    fig, ax = plt.subplots(1, frameon=False, figsize=(6,4), edgecolor='black') # no visible frame
    ax.xaxis.set_visible(False)  # hide the x axis
    ax.yaxis.set_visible(False)  # hide the y axis

    
    conn = sqlite3.connect('hangman/final_score.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM score')
    players = c.fetchall()
    conn.close()

    percent_of_wins = numpy.zeros(len(players))
    N_games = numpy.zeros(len(players))
    for i in range(len(players)):
        percent_of_wins[i] = players[i][3]
        N_games[i] = players[i][2] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(percent_of_wins))
    players = players[index][:10]
    percent_of_wins = percent_of_wins[index][:10]
    N_games = N_games[index][:10]

    for i in range(len(percent_of_wins)):
        if i != 0 and percent_of_wins[i] == percent_of_wins[i-1]:
            continue

        sel = (percent_of_wins == percent_of_wins[i])
        temp2 = N_games[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]


    columns = ['Name', 'W', 'G', '%']
    index = range(1, len(players)+1, 1)

    dataframe = pandas.DataFrame(data=players[:,0:4], index=index, columns=columns)
    table(ax, dataframe, loc='center', colWidths=[0.2, 0.1, 0.1, 0.1])  # where df is your data frame
    plt.tight_layout(rect=(-0.35, -0.3, 1.35, 1.3))
    plt.savefig('hangman/results.png', dpi=150)
    plt.close(fig)
    

    with open('hangman/results.png', 'rb') as result:
        bot.send_photo(message.chat.id, result)
        result.close()

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



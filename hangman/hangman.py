from pandas.plotting import table 
import matplotlib.pyplot as plt
import pandas
import sqlite3
import random
import string
import numpy
import logging



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

def hangman_game(bot, letter, message):
    check_for_winning = True

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
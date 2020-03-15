import telebot
import logging
from numpy.random import randint
import sqlite3

from game_folder.game_classes.game_control import game_control
from game_folder.game_classes.dungeon_classes import Item
from game_folder.game_classes.damage_types import Damage
from game_folder.generate_item import random_consumable, random_equipment


def open_shop(bot, game_user, folder=''):
    conn = sqlite3.connect('game_folder/shop.bd')
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE user_id = ?', [game_user.user_id])
    conn.commit()
    conn.close()

    
    text, keyboard = main_menu(game_user)

    bot.send_photo(chat_id=game_user.user_id, 
                     photo=open(folder+'shop_pixelated.png', 'rb'))
    bot.send_message(chat_id=game_user.user_id, 
                     text=text,
                     parse_mode='Markdown',
                     reply_markup=keyboard
                     )
    return 0


def main_menu(game_user):
    keyboard = telebot.types.InlineKeyboardMarkup(True)

    button_sell = telebot.types.InlineKeyboardButton('Sell', callback_data='sell')
    button_buy = telebot.types.InlineKeyboardButton('Buy', callback_data='buy')
    keyboard.row(button_sell, button_buy)

    button = telebot.types.InlineKeyboardButton('Close', callback_data='close')
    keyboard.row(button)

    text = 'Welcome to my shop {0}! Please, take a look at my wares.\nYou have *{1} gold*'.format(
                game_user.character.name, game_user.character.inventory.gold)

    return text, keyboard
    


def sell_menu(bot, call):
    game_user = game_control()
    game_user.load(call.from_user.id)
    #game_user.character.load_from_repository(game_user.user_id, folder='game_folder/')

    if 'Back' in call.data.split('->'):
        text, keyboard = main_menu(game_user)
        bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id,
                          text=text, reply_markup=keyboard, parse_mode='Markdown')
        return 0


    backpack = game_user.character.show_backpack()
    prices = calculate_buying_price(game_user.character.show_backpack())
    if call.data != 'sell' and call.data.split('->')[1] in backpack:
        sell = call.data.split('->')[1]
        for i in range(len(backpack)):
            if sell == backpack[i]:
                game_user.character.inventory.gold += prices[i]

                item = sell.split(',')[0]
                if item[0] == '(':
                    item = item.split(')')[1]
                    item = item[1:]

                for j in range(len(game_user.character.backpack)):
                    if item == game_user.character.backpack[j].description:
                        game_user.character.backpack.pop(j)
                        break
                break
        else:
            raise
        game_user.save(call.from_user.id)
        bot.send_message(game_user.user_id, 'You recieved *{0} gold*'.format(prices[i]), parse_mode='Markdown')

    
    backpack = game_user.character.show_backpack()
    prices = calculate_buying_price(game_user.character.show_backpack())
    backpack += ['Back']

    backpack_text = [' ']*len(backpack)

    keyboard = telebot.types.InlineKeyboardMarkup(True)
    for i in range(len(backpack)):
        if i != (len(backpack) -1):
            backpack_text[i] = backpack[i]+ ' ({0} gold)'.format(prices[i])
        else:
            backpack_text[i] = backpack[i]
        button = telebot.types.InlineKeyboardButton(backpack_text[i], callback_data='sell->'+backpack[i])
        keyboard.row(button)
    text = 'Have you found anything interesting in your adventures?\nYou have *{0} gold*'.format(game_user.character.inventory.gold)
    bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id,
                          text=text, reply_markup=keyboard, parse_mode='Markdown')
    return 0


def calculate_buying_price(backpack):
    for i in range(len(backpack)):
        if len(backpack[i].split(') ')) != 1:
            backpack[i] = backpack[i].split(') ')[1]



    fixed_price = {
        'potion of healing': 5,
        'great potion of healing': 10,
        'scroll of teleportation': 7,
        'map': 15
    }

    price = []
    for line in backpack:
        temp = line.split()
        if 'healing,' in temp:
            if 'great' in temp:
                price.append(fixed_price['great potion of healing'])
            else:
                price.append(fixed_price['potion of healing'])
        elif 'map,' in temp:
            price.append(fixed_price['map'])
        elif 'teleportation,' in temp:
            price.append(fixed_price['scroll of teleportation'])
        else:
            pass

        if 'strength' in temp or 'intellect' in temp or 'endurance' in temp:
            bonus = int(temp[-2])
            price.append(int(round(bonus*3.75)))

        if 'damage' in temp or 'protection' in temp:
            if 'damage' in temp:
                temp = temp[-3].split('-')
                comp1 = int(temp[0])*20
                comp2 = int(temp[1])*12
                price.append(comp1 + comp2)
            else:
                bonus = int(temp[-4][:-1])/100
                price.append(int(round(bonus*125)))

    return price


def buy_menu(bot, call):
    game_user = game_control()
    game_user.load(call.from_user.id)

    if 'back' in call.data.split('<-'):
        text, keyboard = main_menu(game_user)
        bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id,
                          text=text, reply_markup=keyboard, parse_mode='Markdown')
        return 0

    conn = sqlite3.connect('game_folder/shop.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM items WHERE user_id = ?', [game_user.user_id])
    items = c.fetchall()
    conn.close()

    if len(items) == 0:
        keyboard = items_for_selling(game_user.user_id)
    else:
        keyboard = telebot.types.InlineKeyboardMarkup(True)
        result_items = []
        items_lines = []
        prices = []
        for i in range(len(items)):
            temp = Item()
            temp.load(items[i][1][:-1])
            line = temp.inventory_line()

            result_items.append(temp)
            items_lines.append(temp.description[:25])

            price = int(items[i][2])
            prices.append(price)
            price = ' ({0} gold)'.format(price)
            callback_data = 'buy<-'+temp.description[:25]
            button = telebot.types.InlineKeyboardButton(line+price, callback_data=callback_data)
            keyboard.row(button)


        if call.data != 'buy' and call.data.split('<-')[1] in items_lines:
            idx = items_lines.index(call.data.split('<-')[1])
            if game_user.character.inventory.gold - prices[idx] >= 0:
                game_user.character.inventory.gold -= prices[idx]
                game_user.character.add_to_backpack([result_items[idx]])
                result_items.pop(idx); prices.pop(idx)

                keyboard = telebot.types.InlineKeyboardMarkup(True)
                for i in range(len(result_items)):
                    line = result_items[i].inventory_line()
                    price = ' ({0} gold)'.format(prices[i])
                    callback_data = 'buy<-'+result_items[i].description
                    button = telebot.types.InlineKeyboardButton(line+price, callback_data=callback_data)
                    keyboard.row(button)
            else:
                bot.send_message(game_user.user_id, 'You don\'t have enough money')
                return 0


    button = telebot.types.InlineKeyboardButton('Back', callback_data='buy<-back')
    keyboard.row(button)
    text = 'Let\'s see how I can help you\nYou have *{0} gold*'.format(game_user.character.inventory.gold)
    game_user.save(call.from_user.id)
    bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id,
                          text=text, reply_markup=keyboard, parse_mode='Markdown')
    return 0


def items_for_selling(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup(True)

    roll = randint(low=5, high=8)
    conn = sqlite3.connect('game_folder/shop.bd')
    c = conn.cursor()
    for i in range(roll):
        if i == 0:
            item = random_consumable()
        else:
            item = random_equipment()

        price = calculate_selling_price(item)

        c.execute('INSERT INTO items VALUES (?,?,?)', (user_id, item.save_line(), price))
        conn.commit()

        price = ' ({0} gold)'.format(price)
        line = item.inventory_line()
        callback_data = 'buy<-'+item.description[:25]

        button = telebot.types.InlineKeyboardButton(line+price, callback_data=callback_data)
        keyboard.row(button)
    
    conn.close()

    return keyboard


def calculate_selling_price(item):
    fixed_price = {
        'potion of healing': 12,
        'great potion of healing': 20,
        'scroll of teleportation': 16,
        'map': 22
    }

    
    if item.type == 'consumable':
        temp = item.description.split()
        if 'healing' in temp:
            if 'great' in temp:
                return fixed_price['great potion of healing']
            else:
                return fixed_price['potion of healing']
        elif 'map' in temp:
            return fixed_price['map']
        elif 'teleportation' in temp:
            return fixed_price['scroll of teleportation']
        
    if item.type == 'equipable':
        if item.effect == 'weapon':
            temp = item.add[0].split(';')
            comp1 = int(temp[0])*43
            comp2 = int(temp[1])*22
            return comp1 + comp2
        else:
            bonus = item.add[0]
            return int(round(bonus*650))


def close_shop(bot, call):
    game_user = game_control()
    game_user.load(call.from_user.id)

    conn = sqlite3.connect('game_folder/shop.bd')
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE user_id = ?', [call.from_user.id])
    conn.commit()
    conn.close()


    bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id, 
                          text='See you later, traveler!')
    game_user.in_shop = False
    game_user.save(game_user.user_id)
    return 0
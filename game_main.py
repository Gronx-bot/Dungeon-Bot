import numpy 
import telebot
import logging
from pandas.plotting import table 
import matplotlib.pyplot as plt
import pandas
import sqlite3
import sys

import game_folder.generate_dungeon
from game_folder.game_classes.game_control import game_control
from game_folder.game_classes.player_classes import Player, Warrior, Mage
from game_folder.game_classes.dungeon_classes import Room, Furniture, Item
from game_folder.game_classes.damage_types import Damage
from game_folder.shop import open_shop


def show_status(bot, message):
    game_user = game_control()
    game_user.load(message.from_user.id)

    if message.from_user.id == game_user.user_id and game_user.character.name != "____no_name____":
        character_text = 'Name: '+game_user.character.name+\
        '\nRace: '+game_user.character.race+'\nClass: '+game_user.character.role+'\nStrength: '+str(game_user.character.strength)+\
        '\nIntellect: '+str(game_user.character.intellect)+'\nEndurance: '+str(game_user.character.endurance)+\
        '\nHealth: '+str(game_user.character.hp)+'\nScore: '+str(game_user.character.score)+'\nGold: '+str(game_user.character.inventory.gold)
        
        damage_type = str(Damage(game_user.character.damage_type)).split('.')[1].lower()
        character_text += '\nDamage: {0}-{1} {2}'.format(
            game_user.character.damage_min, game_user.character.damage_max, damage_type)

        character_text += '\nProtection: '
        for i in range(len(game_user.character.protection)):
            if game_user.character.protection[i] != 0:
                damage_type = str(Damage(game_user.character.damage_type)).split('.')[1].lower()
                character_text += '{0}% {1}'.format(int(game_user.character.protection[i]*100), damage_type)
        
        bot.send_message(message.chat.id, character_text)
        return 0
    else:
        bot.send_message(message.chat.id, 'First create your character')
        return 0
        




def spawn_item(description, it_type='consumable', effect='healing', add=1):
    x = Item()
    x.description = description
    x.type = it_type
    x.effect = effect
    x.add = add
    return x



def clean_history(message):
    game_control().delete(message.from_user.id)
    


def create_character(bot, message, start):
    game_user = game_control()
    game_user.load(message.from_user.id)

    game_user.creating_character = True
    status_change = True

    conn = sqlite3.connect('game_folder/character_save.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM characters WHERE user_id = ? LIMIT 1', [game_user.user_id]) 
    temp = c.fetchall() 
    conn.close()

    if len(temp) == 1:
        game_user.veteran_character = True
        game_user.user_id = message.from_user.id
        game_user.character.load_from_repository(game_user.user_id, folder='game_folder/')
        if game_user.character.role == 'warrior':
            game_user.choose_class(Warrior())
        if game_user.character.role == 'mage':
            game_user.character.damage_type = Damage.ARCANE.value
            game_user.choose_class(Mage())
        game_user.save(game_user.user_id)

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row('Yes', 'No')
        bot.send_message(game_user.user_id, 'You have the following saved character:', reply_markup=keyboard)
        show_status(bot, message)
        bot.send_message(game_user.user_id, 'Do you want to play as this character (yes) or create a new one (no)?\nIf you choose to create a new one, old character will be deleted.')
        return 0




    if start:
        bot.send_message(game_user.user_id, 'Enter character name:')
        game_user.save(game_user.user_id)
    else:
        text = message.text
        if text.lower() in ['human', 'elf', 'dwarf', 'ork'] and game_user.last_status == 1:
            text = text.lower()
            game_user.character.race = text

            if text == 'elf':
                game_user.character.strength = 45
                game_user.character.intellect = 55

            if text == 'dwarf':
                game_user.character.strength = 45
                game_user.character.endurance = 55

            if text == 'ork':
                game_user.character.strength = 55
                game_user.character.intellect = 45

            game_user.save(game_user.user_id)

            choose_role_text = 'Next select a class:'
            keyboard_role = telebot.types.ReplyKeyboardMarkup(True)
            keyboard_role.row('warrior', 'mage')
            bot.send_message(game_user.user_id, choose_role_text, reply_markup=keyboard_role)
        elif text.lower() in ['warrior', 'mage'] and game_user.last_status == 1:
            text = text.lower()
            game_user.character.role = text
            game_user.character.set_max_hp()

            if text == 'warrior':
                game_user.character.strength += 5
                game_user.choose_class(Warrior())

            if text == 'mage':
                game_user.character.intellect += 5
                game_user.choose_class(Mage())

            game_user.last_status = 0
            character_created_text = 'Congratulations, your character is created!\nName: '+game_user.character.name+\
            '\nRace: '+game_user.character.race+'\nClass: '+game_user.character.role+'\nStrength: '+str(game_user.character.strength)+\
            '\nIntellect: '+str(game_user.character.intellect)+'\nEndurance: '+str(game_user.character.endurance)+\
            '\nHealth: '+str(game_user.character.hp)
            game_user.save(game_user.user_id)

            keyboard_1 = telebot.types.ReplyKeyboardMarkup(True)
            keyboard_1.row('Next')
            bot.send_message(game_user.user_id, character_created_text, reply_markup=keyboard_1)
            status_change = False
            logging.info(message.from_user.first_name+' created a character')
        elif game_user.last_status == 0:
            if game_user.character.name == '____no_name____':
                if len(text) > 15:
                    bot.send_message(game_user.user_id, 'Name cannot be longer than 15 letters.')
                    return status_change

                game_user.character.set_name(text)
                game_user.last_status = 1
                game_user.save(game_user.user_id)

                choose_race_text = 'Now choose race:'
                keyboard_race = telebot.types.ReplyKeyboardMarkup(True)
                keyboard_race.row('human', 'elf', 'dwarf', 'ork')
                bot.send_message(game_user.user_id, choose_race_text, reply_markup=keyboard_race)
            else:
                bot.send_message(game_user.user_id, 'Your character died during birth.')
                game_user.delete(game_user.user_id)
        else:
            bot.send_message(game_user.user_id, 'Use only options available on buttons.')

    return status_change


def game(bot, message):
    game_user = game_control()
    game_user.load(message.from_user.id)
    logging.info(message.from_user.first_name+' is playing')

    if game_user.creating_character:
        if message.text.lower() == 'yes' and game_user.veteran_character:
            game_user.creating_character = False 
            game_user.last_status = 1 # sending player to shop
            game_user.save(game_user.user_id)

            keyboard = telebot.types.ReplyKeyboardMarkup(True)
            keyboard.row('Next')
            bot.send_message(game_user.user_id, 'Adventures of '+game_user.character.name+' continues!',reply_markup=keyboard)
            return 0 
        if message.text.lower() == 'no' and game_user.veteran_character:
            game_user.character.delete_from_repository(game_user.user_id, folder='game_folder/')
            game_user.delete(game_user.user_id)
            game_user.create(game_user.user_id)
            create_character(bot,message,True)
            return 0
        if game_user.veteran_character:
            bot.send_message(game_user.user_id, 'Answer with yes (continue as this character) or no (start with a new one)')
            return 0

        status_change = create_character(bot, message, False)
        try:
            game_user.load(game_user.user_id)
        except:
            return 1
        game_user.creating_character = status_change
        

        if status_change == False:
            # trying to get some item from storage
            temp = Item()
            result = temp.transfer_from_storage(game_user.user_id, folder='game_folder/')
            if result:
                game_user.character.add_to_backpack([temp])
                text = 'You have recieved an item left for you by another player.'+\
                '\nIt\'s '+temp.description
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row(u'\U0001F44D','Into the dungeon')
                bot.send_message(game_user.user_id, text, reply_markup=keyboard)
        game_user.save(game_user.user_id)
        return 0

    if len(game_user.dungeon) == 0:

        # rewarding for transfered item
        if len(game_user.character.backpack) != 0 and game_user.veteran_character == False:
            effect = game_user.character.backpack[0].effect.split(',')
            game_user.character.backpack[0].effect = effect[0]
            item_type = game_user.character.backpack[0].type.split(',')
            game_user.character.backpack[0].type = item_type[0]
            game_user.save(game_user.user_id)
            if message.text == u'\U0001F44D':
                add_likes(bot, message, int(effect[1]), int(item_type[1]), numpy.random.randint(low=46, high=55))
            if message.text.lower() == 'into the dungeon':
                add_likes(bot, message, int(effect[1]), int(item_type[1]), numpy.random.randint(low=26, high=35))



        # visiting shop
        if game_user.veteran_character and game_user.last_status == 1:
            game_user.last_status = 0
            game_user.in_shop = True
            game_user.save(game_user.user_id)
            open_shop(bot, game_user, folder='game_folder/')
            return 0

        if game_user.in_shop:
            bot.send_message(game_user.user_id, 'If you want to continue, press close in the shop window')
            return 0



        # generating dungeon
        oppening, creators, doom = game_folder.generate_dungeon.main(game_user.character, 
            game_user.user_id, folder='game_folder/', veteran=game_user.veteran_character)
        game_user.load(game_user.user_id) # now dungeon part was added to the database

        game_user.creators = creators
        game_user.doom = doom
        game_user.save(game_user.user_id)
        bot.send_message(game_user.user_id, oppening)

        
        buffer = game_folder.generate_dungeon.draw_dungeon(game_user.dungeon, [game_user.x, game_user.y], 
                                                    game_user.user_id, 
                                                    folder='game_folder/', 
                                                    map_found=game_user.has_map)
        keyboard = move_keyboard(game_user)
        bot.send_photo(game_user.user_id, photo=buffer, reply_markup=keyboard)
        bot.send_message(game_user.user_id, game_user.dungeon[game_user.in_room_now].description)
        return 0


    if game_user.is_fighting:
        game_user = fight(bot, message, game_user)
        game_user.save(game_user.user_id)
        if game_user.dead:
            return 1
        else:
            return 0


    if game_user.is_being_teleported:
        try:
            game_user.teleport(int(message.text))
            text = 'Winds of magic swirl around you as you finish reading the scroll. '+\
            'You open your eyes in completly different place. '+game_user.dungeon[game_user.in_room_now].description
            
            buffer = game_folder.generate_dungeon.draw_dungeon(game_user.dungeon, [game_user.x, game_user.y], 
                                                    game_user.user_id,
                                                    folder='game_folder/', 
                                                    map_found=game_user.has_map)
            bot.send_photo(game_user.user_id, photo=buffer)

            game_user.check_completion()
            if game_user.complete:
                if len(game_user.character.show_backpack()) != 0:
                    text = 'Congratulations! You have completed the dungeon.'+\
                    ' Do you want to help other players and leave one of your items for future adventurers?'
                    keyboard = telebot.types.ReplyKeyboardMarkup(True)
                    keyboard.row('Yes', 'No')
                    bot.send_message(game_user.user_id, text, reply_markup=keyboard)
                    game_user.save(game_user.user_id)
                    return 0
                else:
                    end_game(bot, message, game_user)
                    game_user.save(game_user.user_id)
                    return 1


            game_user.save(game_user.user_id)
            keyboard = move_keyboard(game_user)
            bot.send_message(game_user.user_id, text, reply_markup=keyboard)

            if game_user.is_fighting:
                game_user = fight(bot, message, game_user)
                game_user.save(game_user.user_id)
                if game_user.dead:
                    return 1
        except:
            import traceback
            bot.send_message(game_user.user_id, 'Enter the number of the room on the map')
            traceback.print_exc()
        return 0


    if game_user.complete:
        if message.text.lower() == 'yes':
            game_user.last_status = 1
            open_inventory(bot, game_user)
            game_user.save(game_user.user_id)
            return 0
        elif message.text.lower() == 'no':
            end_game(bot, message, game_user)
            return 1
        else:
            bot.send_message(game_user.user_id, 'Select one of the buttons')


    # blocks move, look around, search, backpack buttons if backpack is open
    if game_user.last_status == 1:
        bot.send_message(game_user.user_id, 'You need to close the backpack to do that')
        return 0

    if message.text.lower() == 'look around':
        bot.send_message(game_user.user_id, game_user.dungeon[game_user.in_room_now].look_around())
        return 0


    if message.text.lower() == 'search':
        items, text = game_user.dungeon[game_user.in_room_now].loot_room()
        if len(items) != 0: 
            game_user.character.add_to_backpack(items)
        game_user.save(game_user.user_id)
        bot.send_message(game_user.user_id, text)
        return 0


    if message.text.lower() == 'backpack':
        game_user.last_status = 1
        open_inventory(bot, game_user)
        game_user.save(game_user.user_id)
        return 0


    moves = game_user.determine_possible_moves()
    if message.text in moves:
        game_user.move(message.text)
        game_user.check_completion()
        n = game_user.how_many_rooms_left()

        if game_user.complete:
            if len(game_user.character.show_backpack()) != 0:
                game_user.save(game_user.user_id)
                text = 'Congratulations! You have completed the dungeon.'+\
                ' Do you want to help other players and leave one of your items for future adventurers?'
                keyboard = telebot.types.ReplyKeyboardMarkup(True)
                keyboard.row('Yes', 'No')
                bot.send_message(game_user.user_id, text, reply_markup=keyboard)
                return 0
            else:
                end_game(bot, message, game_user)
                return 1


        buffer = game_folder.generate_dungeon.draw_dungeon(game_user.dungeon, [game_user.x, game_user.y], 
                                                    game_user.user_id,
                                                    folder='game_folder/', 
                                                    map_found=game_user.has_map)
        keyboard = move_keyboard(game_user)
        bot.send_photo(game_user.user_id, photo=buffer, reply_markup=keyboard)
        bot.send_message(game_user.user_id, game_user.dungeon[game_user.in_room_now].description+'\nYou have '+str(n)+' more unexplored rooms.')

        if game_user.is_fighting:
            game_user = fight(bot, message, game_user)
            game_user.save(game_user.user_id)
            if game_user.dead:
                return 1
        else:
            game_user.save(game_user.user_id)
            return 0


    logging.info("Recieved: "+ message.text)


def fight(bot, message, game_user):

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('Attack')


    if game_user.monster.score == 0:
        game_user.monster.set_up_monster(game_folder.generate_dungeon.generate_monster(game_user.dungeon[game_user.in_room_now],
                                                                         game_user.creators, 
                                                                         game_user.doom,
                                                                         folder='game_folder/',
                                                                         veteran=game_user.veteran_character))
        bot.send_message(game_user.user_id, 'In the room you see '+game_user.monster.name)
        hp_bar = 'Opponents hp: *{0}/{1}* \nYour hp: *{2}/{3}*'.format(
            game_user.monster.hp, game_user.monster.max_hp, game_user.character.hp, game_user.character.max_hp)
        bot.send_message(game_user.user_id, hp_bar, parse_mode='Markdown')

        abilities = game_user.character.update(start=True)
        keyboard.row(*abilities)
        bot.send_message(game_user.user_id, 'What do you want to do?', reply_markup=keyboard)
        return game_user
    else:
        if message.text.lower() == 'attack':

            # player block
            dmg = numpy.random.randint(low=game_user.character.damage_min, high=game_user.character.damage_max+1)
            text = ''
            if game_user.character.role == 'warrior':
                roll_to_hit = roll(game_user.character.strength)
                if roll_to_hit == 0:
                    dmg = 6 #critical hit
                    text = 'It\'s a critical hit! '
                if roll_to_hit < 3:
                    damage_type = str(Damage(game_user.character.damage_type)).split('.')[1].lower()
                    dmg = game_user.monster.take_damage(dmg, game_user.character.damage_type)
                    text += '*{0}* strikes and deals {1} {2} damage.'.format(game_user.character.name.capitalize(), dmg, damage_type)
                else:
                    text = '*{0}* miss!'.format(game_user.character.name.capitalize())
            if game_user.character.role == 'mage':
                roll_to_hit = roll(game_user.character.intellect)
                if roll_to_hit == 0:
                    dmg = 6 #critical hit
                    text = 'It\'s a critical hit! '
                if roll_to_hit < 3:
                    damage_type = str(Damage(game_user.character.damage_type)).split('.')[1].lower()
                    dmg = game_user.monster.take_damage(dmg, game_user.character.damage_type)
                    text += '*{0}* launches magic missiles and deals {1} {2} damage.'.format(game_user.character.name.capitalize(), dmg, damage_type)
                else:
                    text = '*{0}* miss!'.format(game_user.character.name.capitalize())


            # monster block
            game_user, text = monster_attacks(game_user, text)

            

            abilities = game_user.character.update()
            keyboard.row(*abilities)
            bot.send_message(game_user.user_id, text, reply_markup=keyboard, parse_mode='Markdown')

            if game_user.character.hp <= 0:
                game_user = hero_dies(bot, message, game_user)
                return game_user

            if game_user.monster.hp <= 0:
                game_user = monster_dies(bot, message, game_user)
                return game_user

            hp_bar = 'Opponents hp: *{0}/{1}* \nYour hp: *{2}/{3}*'.format(
                game_user.monster.hp, game_user.monster.max_hp, game_user.character.hp, game_user.character.max_hp)
            bot.send_message(game_user.user_id, hp_bar, parse_mode='Markdown')

            return game_user

        if game_user.character.role == 'warrior':
            if message.text.lower() == 'stun attack: stuns opponent for 1 round':
                stun = game_user.character.stun()
                if stun == 'stun':
                    game_user.monster.score = 2
                    abilities = game_user.character.update()
                    keyboard.row(*abilities)
                    bot.send_message(game_user.user_id, 'With blunt strike you stun the opponent. He will miss his next turn.', reply_markup=keyboard)
                    return game_user
                else:
                    bot.send_message(game_user.user_id, 'Stun attack is currently on a cooldown')
                    return game_user

            if message.text.lower() == 'second breath: heals 4-8 hp':
                text = game_user.character.second_breath()
                if text != 0:
                    abilities = game_user.character.update()
                    keyboard.row(*abilities)
                    bot.send_message(game_user.user_id, text, reply_markup=keyboard)
                    return game_user
                else:
                    bot.send_message(game_user.user_id, 'You have already used second breath')
                    return game_user

        if game_user.character.role == 'mage':
            if message.text.lower() == 'fireball: deals 6 damage':
                fireball = game_user.character.fireball()
                if fireball == 'fireball':
                    dmg = game_user.monster.take_damage(6, Damage.FIRE.value)

                    text = '*{0}* launches fireball setting opponent on fire. He recieves {1} {2} damage'.format(game_user.character.name.capitalize(), dmg, 'fire')
                    game_user, text = monster_attacks(game_user, text)

                    abilities = game_user.character.update()
                    keyboard.row(*abilities)
                    bot.send_message(game_user.user_id, text, reply_markup=keyboard, parse_mode='Markdown')
                    hp_bar = 'Opponents hp: *{0}/{1}* \nYour hp: *{2}/{3}*'.format(
                        game_user.monster.hp, game_user.monster.max_hp, game_user.character.hp, game_user.character.max_hp)
                    bot.send_message(game_user.user_id, hp_bar, parse_mode='Markdown')

                    if game_user.character.hp <= 0:
                        game_user = hero_dies(bot, message, game_user)
                        return game_user

                    if game_user.monster.hp <= 0:
                        game_user = monster_dies(bot, message, game_user)
                        return game_user

                    return game_user
                else:
                    bot.send_message(game_user.user_id, 'Fireball is currently on a cooldown')
                    return game_user

            if message.text.lower() == 'healing spell: heals 4-6 hp':
                text = game_user.character.healing()
                if text != 0:
                    abilities = game_user.character.update()
                    keyboard.row(*abilities)
                    bot.send_message(game_user.user_id, text, reply_markup=keyboard)
                    return game_user
                else:
                    bot.send_message(game_user.user_id, 'You have already used healing spell')
                    return game_user

        if (message.text.lower() in ['attack', 'healing spell: heals 4-6 hp', 'fireball: deals 6 damage', 
            'stun attack: stuns opponent for 1 round', 'second breath: heals 4-8 hp']) == False:
            bot.send_message(game_user.user_id, 'Use options available on the buttons')
            return game_user




def monster_dies(bot, message, game_user):
    game_user.is_fighting = False
    game_user.character.score += 5
    game_user.monster.score = 0
    text = 'Your final hit finishes off '+game_user.monster.race+'. You walk victoriously away from the battle.'

    keyboard = move_keyboard(game_user)

    buffer = game_folder.generate_dungeon.draw_dungeon(game_user.dungeon, [game_user.x, game_user.y], 
                                                    game_user.user_id, 
                                                    folder='game_folder/', 
                                                    map_found=game_user.has_map)
    bot.send_photo(game_user.user_id, photo=buffer)
    bot.send_message(game_user.user_id, text, reply_markup=keyboard)
    return game_user


def hero_dies(bot, message, game_user):
    game_user.dead = True
    game_user.character.delete_from_repository(game_user.user_id, folder='game_folder/')
    text = 'The final hit was too much for your feeble body. Your legs don\'t support you anymore, you fall down on the ground and die.\n'
    text += 'Another life that won\'t be remembered...'
    bot.send_message(game_user.user_id, text)
    bot.send_message(game_user.user_id, '*GAME OVER*', parse_mode='Markdown')
    bot.send_message(game_user.user_id, 'Try again?.. \n/game')
    return game_user


def monster_attacks(game_user, text):
    if game_user.monster.score == 3 or game_user.monster.score == 2: # stunned
        game_user.monster.score -= 1
    else:
        dmg = numpy.random.randint(low=game_user.monster.damage_min, high=game_user.monster.damage_max+1)
        text += '\n'

        if game_user.monster.role == 'warrior':
            roll_to_hit = roll(game_user.monster.strength)
            if roll_to_hit == 0:
                dmg = 6 #critical hit
                text += 'Opponent deals a critical hit! '
            if roll_to_hit < 3:
                damage_type = str(Damage(game_user.monster.damage_type)).split('.')[1].lower()
                dmg = game_user.character.take_damage(dmg, game_user.monster.damage_type)
                text += '*{0}* blows a series of hits and deals {1} {2} damage to you.'.format(game_user.monster.race.capitalize(), dmg, damage_type)
            else:
                text += '*{0}* misses!'.format(game_user.monster.race.capitalize())

        if game_user.monster.role == 'mage':
            roll_to_hit = roll(game_user.monster.intellect)
            if roll_to_hit == 0:
                dmg = 6 #critical hit
                text += 'Opponent deals a critical hit! '
            if roll_to_hit < 3:
                damage_type = str(Damage(game_user.monster.damage_type)).split('.')[1].lower()
                dmg = game_user.character.take_damage(dmg, game_user.monster.damage_type)
                text += 'Using arcane powers *{0}* deals {1} {2} damage to you.'.format(game_user.monster.race.capitalize(), dmg, damage_type)
            else:
                text += '*{0}* misses!'.format(game_user.monster.race.capitalize())

    return game_user, text


def open_inventory(bot, game_user):
    backpack = game_user.character.show_backpack()
    callback_data = []
    for i in backpack:
        callback_data.append(i[:50])

    if game_user.complete == False: 
        backpack += ['Close']
        callback_data += ['close']

    keyboard = telebot.types.InlineKeyboardMarkup(True)
    for i in range(len(backpack)):
        button = telebot.types.InlineKeyboardButton(backpack[i], callback_data=callback_data[i])
        keyboard.row(button)
    text = game_user.character.name + '\'s backpack:' 
    bot.send_message(game_user.user_id, text, reply_markup=keyboard)
    return 0


def inventory_buttons(bot, call):
    game_user = game_user = game_control()
    game_user.load(call.from_user.id)


    if game_user.complete and call.data in game_user.character.show_backpack():
        game_user.last_status = 0
        item = call.data.split(',')[0]
        item = game_user.character.take_from_backpack(item)
        item.transfer_to_storage(game_user.user_id, game_user.user_id, folder='game_folder/')
        end_game(bot, call, game_user) # I send call here instead of message, but it should work
        game_user.save(game_user.user_id)
        return 1


    if call.data.lower() == 'close' and game_user.last_status == 1:
        game_user.last_status = 0
        keyboard = move_keyboard(game_user)
        game_user.save(game_user.user_id)
        bot.delete_message(chat_id=game_user.user_id, message_id=call.message.message_id)
        bot.send_message(game_user.user_id, 'Backpack closed', reply_markup=keyboard)
        return 0



    backpack = game_user.character.show_backpack()
    callback_data = []
    for i in backpack:
        callback_data.append(i[:50])

    if call.data in callback_data and game_user.last_status == 1:
        idx = callback_data.index(call.data)
        item = backpack[idx].split(',')[0]
        if item[0] == '(':
            item = item.split(')')[1]
            item = item[1:]
        if item == 'scroll of teleportation':
            game_user.is_being_teleported = True
            game_user.last_status = 0
            text = 'Enter the number of the room to which you wish to be teleported'
            bot.send_message(game_user.user_id, text)
            game_user.save(game_user.user_id)
            return 0
        elif item == 'map':
            game_user.has_map = True
            for i in range(len(game_user.character.backpack)):
                if game_user.character.backpack[i].description == 'map':
                    game_user.character.backpack.pop(i)
                    break

            text = 'Now you have a map, you will know the whole layout!'
            buffer = game_folder.generate_dungeon.draw_dungeon(game_user.dungeon, [game_user.x, game_user.y], 
                                                    game_user.user_id,
                                                    folder='game_folder/', 
                                                    map_found=game_user.has_map)
            bot.send_photo(game_user.user_id, photo=buffer)
        else:
            text = game_user.character.use(item)

        bot.send_message(game_user.user_id, text)
        game_user.last_status = 1
        


        backpack = game_user.character.show_backpack()
        callback_data = []
        for i in backpack:
            callback_data.append(i[:50])

        if game_user.complete == False: 
            backpack += ['Close']
            callback_data += ['close']

        keyboard = telebot.types.InlineKeyboardMarkup(True)
        for i in range(len(backpack)):
            button = telebot.types.InlineKeyboardButton(backpack[i], callback_data=callback_data[i])
            keyboard.row(button)
        text = game_user.character.name + '\'s backpack:' 
        bot.edit_message_text(chat_id=game_user.user_id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
        game_user.save(game_user.user_id)
        return 0 
    else:
        bot.send_message(call.from_user.id, 'Backpack menu is inactive right now.')
        return 0

def end_game(bot, message, game_user):
    game_user.character.save_to_repository(game_user.user_id, folder='game_folder/')

    if game_user.how_many_rooms_left() == 0: 
        likes = numpy.random.randint(low=11, high=15)
    else: 
        likes = numpy.random.randint(low=8, high=12) 
    place = ratings(message, game_user.character.score, game_user.character.name, likes)
    if place == 1: add = 'st'
    if place == 2: add = 'nd'
    if place == 3: add = 'rd'
    if place > 3: add = 'th'
    text = game_user.character.name+', powerful '+game_user.character.role+', overcame all obstacles, '+ \
    'defeated all monster, reached final destination and now can peacefully retire. \nYour final score is: '+str(game_user.character.score)+\
    '.\nYou are on '+str(place)+add +' place in global ranking!\n\nTo see the whole ranking type /rating_game.\nTo start new game type /game.'
    bot.send_message(game_user.user_id, text)
    return 1


def roll(hero_stat):
    hero_stat = 100*(1-numpy.exp(-hero_stat/72.13))
    dice = numpy.random.randint(low=1, high=101, size=1)
    # 2 = regular success; 1 = hard success; 0 = extreme success; 3 = fail
    if dice <= hero_stat: 
        if dice <= int(hero_stat/5):
            return 0
        elif dice <= int(hero_stat/2):
            return 1
        else:
            return 2
    else: 
        return 3


def move_keyboard(game_user):
    moves = game_user.determine_possible_moves()
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row(*moves)
    keyboard.row('Look around', 'Search', 'Backpack')
    return keyboard


def ratings(message, new_score, character_name, new_likes):
    if len(character_name) > 15:
        character_name = character_name[:15]

    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()

    user_name = message.from_user.first_name
    user_id = message.from_user.id
    c.execute('SELECT * FROM rating WHERE user_id=?', [(user_id)])
    scores = c.fetchall()
    scores = numpy.asarray(scores)
    if len(scores) == 1:
        scores = scores[0]
        if new_score > int(scores[1]):
            c.execute('INSERT or REPLACE INTO rating VALUES (?,?,?,?,?)', 
                (scores[0], int(new_score), character_name, int(scores[3])+new_likes, user_id))
            conn.commit()
        
    elif len(scores) == 0:
        c.execute('INSERT INTO rating VALUES (?,?,?,?,?)', 
                (user_name, int(new_score), character_name, new_likes, user_id))
        conn.commit()
    else:
        logging.warning('There is someone else with the same user id')



    c.execute('SELECT * FROM rating')
    players = c.fetchall()
    conn.close()

    score = numpy.zeros(len(players))
    likes = numpy.zeros(len(players))
    for i in range(len(players)):
        score[i] = players[i][1]
        likes[i] = players[i][3] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(score))
    players = players[index][:10]
    score = score[index][:10]
    likes = likes[index][:10]

    for i in range(len(score)):
        if i != 0 and score[i] == score[i-1]:
            continue

        sel = (score == score[i])
        temp2 = likes[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]

    k, = numpy.where(players[:,0] == user_name)
    
    conn.close()
    return k[0]+1


def show_rating(bot, message):
    fig, ax = plt.subplots(1, frameon=False, figsize=(6,4)) 
    ax.xaxis.set_visible(False) 
    ax.yaxis.set_visible(False) 
    
    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM rating')
    players = c.fetchall()
    conn.close()

    score = numpy.zeros(len(players))
    likes = numpy.zeros(len(players))
    for i in range(len(players)):
        score[i] = players[i][1]
        likes[i] = players[i][3] 

    players = numpy.asarray(players)

    index = numpy.flip(numpy.argsort(score))
    players = players[index][:10]
    score = score[index][:10]
    likes = likes[index][:10]

    for i in range(len(score)):
        if i != 0 and score[i] == score[i-1]:
            continue

        sel = (score == score[i])
        temp2 = likes[sel]
        index_flip = numpy.flip(numpy.argsort(temp2))
        players[sel] = players[sel][index_flip]

    columns = ['Name', 'Score', 'Character', 'Likes']
    index = range(1, len(players)+1, 1)
    dataframe = pandas.DataFrame(data=players[:,0:4], index=index, columns=columns)

    table_obj = table(ax, dataframe, loc='center', colWidths=[0.1, 0.1, 0.1, 0.1])  
    table_obj.auto_set_font_size(False)
    table_obj.set_fontsize(10)
    plt.tight_layout(rect=(-0.6, -0.3, 1.6, 1.3))
    plt.savefig('game_folder/score.png', dpi=150)
    plt.close(fig)

    with open('game_folder/score.png', 'rb') as result:
        bot.send_photo(message.chat.id, result)
        result.close()


def add_likes(bot, message, sender_id, sender_chat_id, new_likes):
    conn = sqlite3.connect('game_folder/final_score.bd')
    c = conn.cursor()

    c.execute('SELECT * FROM rating WHERE user_id=?', [(sender_id)])
    scores = c.fetchall()
    scores = numpy.asarray(scores)
    if len(scores) == 1:
        scores = scores[0]
        c.execute('INSERT or REPLACE INTO rating VALUES (?,?,?,?,?)', 
            (scores[0], int(scores[1]), scores[2], int(scores[3])+new_likes, sender_id))
        conn.commit()
    else:
        logging.warning('There is someone else with the same user id')
    conn.close()


    bot.send_message(sender_chat_id, 'You recieved '+u'\U0001F44D'+' from '+message.from_user.first_name)

    user_name = message.from_user.first_name
    user_id = message.from_user.id

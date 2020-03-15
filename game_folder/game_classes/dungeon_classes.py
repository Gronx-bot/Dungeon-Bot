import numpy
import sqlite3

from game_folder.game_classes.damage_types import Damage

class Room:
    """docstring for Room"""
    def __init__(self):
        self.room_id = 0
        self.purpose = ' '*100
        self.chamber_state = ' '*100
        self.air = ' '*100
        self.description = ' '*300
        self.content = [Furniture(), Furniture(), Furniture(), Furniture()]
        self.neighbours = [' ', ' ', ' ', ' ']
        self.coord_x = 0
        self.coord_y = 0
        self.is_cleared = False
        self.has_monster = False

    def add_neigbour(self, neighbour_id):
        for i in range(len(self.neighbours)):
            if self.neighbours[i] == neighbour_id:
                break
            if self.neighbours[i] == ' ':
                self.neighbours[i] = neighbour_id
                break

    def number_of_neighbours(self):
        c = 0
        for i in range(4):
            if self.neighbours[i] != ' ':
                c += 1
        return c

    def set_coordinates(self, x, y):
        self.coord_x = x
        self.coord_y = y

    def look_around(self):
        c = []
        for i in range(3):
            if self.content[i].description != ' '*100:
                c.append(i)

        if len(c) == 0:
            return 'There is nothing of interest in this room.'
        else:
            text = 'You see '
            for i in c:
                text += self.content[i].description
                if i != c[-1]:
                    text += ', '
                else:
                    text += '.'
            return text

    def loot_room(self):
        temp = []
        for i in range(3):
            if self.content[i].is_container == True:
                temp.append(self.content[i].take_item())
        if len(temp) == 0:
            text = 'There is nothing of value in this room.'
        else:
            text = 'You have found '
            for i in range(len(temp)):
                text += temp[i].description
                if i != len(temp)-1:
                    text += ', '
        return temp, text

    def load(self, furn, item):
        furn = furn.split(';\n')[:-1]
        for i in range(len(furn)):
            furniture = furn[i].split('\n')
            self.content[i].description = furniture[0].split(' = ')[1]
            self.content[i].is_container = bool(int(furniture[1].split(' = ')[1]))

        if len(item) != 0:
            item = item.split(';\n')[:-1]
            j = 0
            for i in range(len(self.content)):
                if self.content[i].is_container:
                    temp = item[j].split('\n')
                    self.content[i].content.description = temp[0].split(' = ')[1]
                    self.content[i].content.type = temp[1].split(' = ')[1]
                    self.content[i].content.effect = temp[2].split(' = ')[1]
                    self.content[i].content.add = int(temp[3].split(' = ')[1])
                    j += 1



class Furniture:
    """docstring for Furniture"""
    def __init__(self):
        self.description = ' '*100
        self.is_container = False
        self.content = Item()

    def take_item(self):
        if self.is_container == True:
            item = self.content
            self.is_container = False
            self.content = 0
            return item

    def put_item(self, item):
        if self.is_container == False:
            self.content = item
            self.is_container == True

    def save_line(self):
        text = 'description = '+self.description+'\n'
        text+= 'is_container = '+str(int(self.is_container))+';'
        return text
            


class Item:
    def __init__(self):
        self.description = ' '*100
        # ['score', 'stats', 'consumable', 'equipable']
        self.type = 'score'

        # ['healing', 'travel'] for consumable
        # ['strength', 'intellect', 'endurance'] for stats
        # ['head', 'body', 'arms', 'legs', 'weapon'] for equipable
        self.effect = 0
        self.add = 0

    def use(self):
        if self.type == 'consumable':
            return self.effect, self.add
        if self.type == 'stats':
            return self.effect, self.add

    def equip(self):
        if self.type == 'score':
            return self.add
        

    def inventory_line(self):
        if self.type != 'score':
            text = self.description
            if self.type == 'stats':
                text += ', +'+str(self.add)+' '+self.effect
            if self.type == 'consumable':
                if self.effect == 'healing':
                    text += ', restores '+str(self.add)+' hp'
                if self.effect == 'travel':
                    if self.description == 'scroll of teleportation':
                        text += ', teleports you into any room'
                    if self.description == 'map':
                        text += ', shows purpose of all rooms'
            if self.type == 'equipable':
                if self.effect == 'weapon':
                    temp = self.add[0].split(';')
                    dmg = temp[0]+'-'+temp[1]
                    damage_type = str(Damage(self.add[1])).split('.')[1].lower()
                    text += ', '+dmg+' '+damage_type+' damage'
                else:
                    dmg = str(round(self.add[0]*100))+'%'+' protection'
                    damage_type = str(Damage(self.add[1])).split('.')[1].lower()
                    text += ', '+dmg+' from '+damage_type
            return text

    def save_line(self):
        text = 'description = '+self.description+'\n'
        text+= 'type = '+self.type+'\n'
        text+= 'effect = '+self.effect+'\n'
        text+= 'add = '+str(self.add)+';'
        return text


    def load(self, temp):
        temp = temp.split('\n')
        self.description = temp[0].split(' = ')[1]
        self.type = temp[1].split(' = ')[1]
        self.effect = temp[2].split(' = ')[1]

        bonus = temp[3].split(' = ')[1]
        if len(bonus.split(', ')) != 1:
            bonus = bonus[1:-1].split(', ')
            assert len(bonus) == 2
            damage_type = int(bonus[1])
            if len(bonus[0].split(';')) == 2:
                self.add = [bonus[0][1:-1], damage_type]
            else:
                self.add = [float(bonus[0]), damage_type]
        else:
            self.add = int(bonus)


    def transfer_to_storage(self, user_id, user_chat_id, folder=''):
        conn = sqlite3.connect(folder+'item_storage.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM items')
        temp = c.fetchall()  
        row_id = len(temp)+1
        c.execute('INSERT INTO items VALUES (?,?,?,?,?,?,?)', 
            (self.description, self.type, str(self.effect), str(self.add), user_id, user_chat_id, row_id))
        conn.commit()
        conn.close()

    def transfer_from_storage(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'item_storage.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM items WHERE user_id != ?', [user_id])
        temp = c.fetchall()   

        if len(temp) == 0:
            conn.close()
            return False
        else:
            roll = numpy.random.randint(low=0, high=len(temp))
            temp = temp[roll]

            c.execute('DELETE FROM items WHERE id = ? LIMIT 1', [temp[6]])
            conn.commit()
            conn.close()

            self.description = temp[0]
            self.type = temp[1]+', '+str(temp[5])
            self.effect = temp[2]+', '+str(temp[4])
            bonus = str(temp[3])
            if len(bonus.split(', ')) != 1:
                bonus = bonus[1:-1].split(', ')
                assert len(bonus) == 2
                self.add = [int(bonus[0]), int(bonus[1])]
            else:
                self.add = int(bonus)
            
            return True

    
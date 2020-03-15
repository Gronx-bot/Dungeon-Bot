import numpy
import sqlite3

from game_folder.game_classes.player_classes import Player, Warrior, Mage
from game_folder.game_classes.dungeon_classes import Room, Furniture, Item

class game_control:
    """docstring for game_control"""
    def __init__(self):
        self.user_id = 0
        self.character = Player()
        self.monster = Player()
        self.creating_character = False
        self.veteran_character = False
        self.last_status = 0
        self.complete = False
        self.dead = False
        self.dungeon = []
        self.creators = 0
        self.doom = 0
        self.x = 0; self.y = 0
        self.in_room_now = 0
        self.has_map = False
        self.is_being_teleported = False
        self.is_fighting = False
        self.fighting_counter = 4
        self.in_shop = False

    def choose_class(self, new_class):
        new_class.name = self.character.name 
        new_class.race = self.character.race
        new_class.role = self.character.role
        new_class.set_stats(self.character.strength, self.character.intellect, self.character.endurance)
        new_class.score = self.character.score
        new_class.hp = self.character.hp

        new_class.backpack = self.character.backpack
        new_class.inventory = self.character.inventory

        new_class.damage_min = self.character.damage_min
        new_class.damage_max = self.character.damage_max
        new_class.damage_type = self.character.damage_type
        new_class.protection = self.character.protection 
        new_class.vulnerability = self.character.vulnerability

        self.character = new_class
        

    def load(self, user_id, folder='game_folder/'):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()

        c.execute('SELECT * FROM players WHERE user_id = ? LIMIT 1', [user_id]) 
        temp = c.fetchall()
        temp = temp[0]
        self.user_id = int(temp[0])
        self.creating_character = bool(int(temp[2]))
        self.veteran_character = bool(int(temp[3]))
        self.last_status = int(temp[4])
        self.complete = bool(int(temp[5]))
        self.dead = bool(int(temp[6]))
        self.creators = str(temp[7])
        self.doom = str(temp[8])
        self.x = int(temp[9]); self.y = int(temp[10])
        self.in_room_now = int(temp[11])
        self.has_map = bool(int(temp[12]))
        self.is_being_teleported = bool(int(temp[13]))
        self.is_fighting = bool(int(temp[14]))
        self.fighting_counter = int(temp[15])
        self.in_shop = bool(int(temp[16]))

        if temp[1] == 'warrior':
            self.character = Warrior()
            self.character.load(user_id, 'character', folder)
        if temp[1] == 'mage':
            self.character = Mage()
            self.character.damage_type = 7
            self.character.load(user_id, 'character', folder)

        self.monster = Player()
        self.monster.load(user_id, 'monster', folder)

        self.dungeon = load_dungeon(user_id, folder)

        conn.close()

    
    def delete(self, user_id, folder='game_folder/'):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()
        c.execute('DELETE FROM players WHERE user_id = ? LIMIT 1', [user_id])
        conn.commit()
        conn.close()

        self.character.delete(user_id, 'character', folder)
        self.monster.delete(user_id, 'monster', folder)
        delete_dungeon(user_id, folder)
    
    def save(self, user_id, folder='game_folder/'):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, self.character.role, int(self.creating_character), int(self.veteran_character),
             self.last_status, int(self.complete), int(self.dead), str(self.creators), str(self.doom), self.x, 
                self.y, self.in_room_now, int(self.has_map), int(self.is_being_teleported),
                 int(self.is_fighting), self.fighting_counter, int(self.in_shop)))
        conn.commit()
        conn.close()

        self.character.save(user_id, 'character', folder)
        self.monster.save(user_id, 'monster', folder)
        update_dungeon(self.dungeon, user_id, folder)

    def create(self, user_id, folder='game_folder/'):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
            (int(user_id), str('warrior'), int(False), int(False),
             int(0), int(False), int(False), str(0), str(0), int(0), 
                int(0), int(0), int(False), int(False),
                 int(False), int(4), int(False)))
        conn.commit()
        conn.close() 

        self.character.create_new(user_id, folder)

    def how_many_rooms_left(self):
        temp = len(self.dungeon)
        for i in range(len(self.dungeon)):
            if self.dungeon[i].is_cleared:
                temp -= 1
        return temp

    def check_completion(self):
        if self.dungeon[-1].is_cleared and self.complete == False:
            self.complete = True
            self.character.calculate_score()

    def determine_possible_moves(self):
        temp = [0,0,0,0]
        room = self.dungeon[self.in_room_now]
        for i in range(len(room.neighbours)):
            if room.neighbours[i] != ' ':
                next_room = self.dungeon[room.neighbours[i]]
                if room.coord_x > next_room.coord_x:
                    temp[0] = u'\U00002B05'
                if room.coord_y > next_room.coord_y:
                    temp[1] = u'\U00002B07'
                if room.coord_y < next_room.coord_y:
                    temp[2] = u'\U00002B06'
                if room.coord_x < next_room.coord_x:
                    temp[3] = u'\U000027A1'
        
        temp = list(filter(lambda a: a != 0, temp))
                
        return temp

    def move(self, message):
        if message == u'\U00002B05':
            self.x -= 1
        if message == u'\U000027A1':
            self.x += 1
        if message == u'\U00002B07':
            self.y -= 1
        if message == u'\U00002B06':
            self.y += 1
        for i in range(len(self.dungeon)):
            if self.dungeon[i].coord_x == self.x \
            and self.dungeon[i].coord_y == self.y:

                self.in_room_now = self.dungeon[i].room_id
                if self.dungeon[self.in_room_now].is_cleared == False \
                and self.in_room_now != self.dungeon[-1].room_id:
                    self.check_for_monster()
                self.dungeon[self.in_room_now].is_cleared = True


    def teleport(self, where_to):
        if where_to > self.dungeon[-1].room_id or where_to < 0:
            raise
        else:
            for i in range(len(self.dungeon)):
                if self.dungeon[i].room_id == where_to:
                    self.x = self.dungeon[i].coord_x
                    self.y = self.dungeon[i].coord_y
                    self.in_room_now = self.dungeon[i].room_id
                    self.is_being_teleported = False
                    self.dungeon[i].is_cleared = True

                    if self.in_room_now != self.dungeon[-1].room_id:
                        self.check_for_monster()

                    for j in range(len(self.character.backpack)):
                        if self.character.backpack[j].description == 'scroll of teleportation':
                            self.character.backpack.pop(j)
                            break
                    break


    def check_for_monster(self):
        if self.dungeon[self.in_room_now].has_monster:
            self.is_fighting = True
            self.fighting_counter = 4
            self.dungeon[self.in_room_now].has_monster = False
        else:
            self.fighting_counter -= 1
            roll = numpy.random.randint(low=0, high=4)
            if roll > self.fighting_counter:
                self.is_fighting = True
                self.fighting_counter = 4


def set_dungeon(dungeon, user_id, folder=''):
    conn = sqlite3.connect(folder+'game_control.bd')
    c = conn.cursor()
    for i in range(len(dungeon)):
        neighbours = ''
        for j in range(len(dungeon[i].neighbours)):
            neighbours += str(dungeon[i].neighbours[j])+';'

        room = dungeon[i]
        furniture = ''
        items = ''
        for j in room.content:
            if j.description != ' '*100:
                furniture += j.save_line()+'\n'
                if j.is_container:
                    items += j.content.save_line()+'\n'

        c.execute('INSERT INTO dungeon VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, dungeon[i].room_id, dungeon[i].purpose, dungeon[i].chamber_state, 
            dungeon[i].air, dungeon[i].description, int(dungeon[i].coord_x), int(dungeon[i].coord_y),
            int(dungeon[i].is_cleared), int(dungeon[i].has_monster), neighbours, furniture, items))
    conn.commit()
    conn.close()

def update_dungeon(dungeon, user_id, folder):
    delete_dungeon(user_id, folder)
    set_dungeon(dungeon, user_id, folder)

def delete_dungeon(user_id, folder=''):
    conn = sqlite3.connect(folder+'game_control.bd')
    c = conn.cursor()
    c.execute('DELETE FROM dungeon WHERE user_id = ?', [user_id])
    conn.commit()
    conn.close()


def load_dungeon(user_id, folder=''):
    dungeon = []
    conn = sqlite3.connect(folder+'game_control.bd')
    c = conn.cursor()
    c.execute('SELECT * FROM dungeon WHERE user_id = ?', [user_id]) 
    room = c.fetchall()
    conn.close()
    for i in range(len(room)):
        temp = room[i]
        x = Room()
        x.room_id = int(temp[1])
        x.purpose = temp[2]
        x.chamber_state = temp[3]
        x.air = temp[4]
        x.description = temp[5]
        x.coord_x = int(temp[6])
        x.coord_y = int(temp[7])
        x.is_cleared = bool(int(temp[8]))
        x.has_monster = bool(int(temp[9]))

        neighbours = []
        for j in temp[10].split(';')[:-1]:
            if j != ' ':
                neighbours.append(int(j)) 
            else:
                neighbours.append(' ')
        x.neighbours = neighbours

        # furniture and items
        if len(temp[11]) != 0:
            x.load(temp[11], temp[12])

        dungeon.append(x)

    return dungeon
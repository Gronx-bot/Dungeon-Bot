import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sqlite3
import sys
import logging


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


class Item:
    def __init__(self):
        self.description = ' '*100
        # ['score', 'stats', 'consumable']
        self.type = 'score'
        # ['healing', 'travel']
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
            return text

    def save_line(self):
        text = 'description = '+self.description+'\n'
        text+= 'type = '+self.type+'\n'
        text+= 'effect = '+self.effect+'\n'
        text+= 'add = '+str(self.add)+';'
        return text


    def transfer_to_storage(self, user_id, user_chat_id, folder=''):
        conn = sqlite3.connect(folder+'item_storage.bd')
        c = conn.cursor()
        c.execute('INSERT INTO items VALUES (?,?,?,?,?,?)', 
            (self.description, self.type, str(self.effect), self.add, user_id, user_chat_id))
        conn.commit()
        conn.close()

    def transfer_from_storage(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'item_storage.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM items WHERE user_id != ? LIMIT 1', [user_id])
        temp = c.fetchall()   

        if len(temp) == 0:
            conn.close()
            return 'nothing to transfer'
        if len(temp) == 1:
            temp = temp[0]

            c.execute('DELETE FROM items WHERE user_id = ? LIMIT 1', [temp[4]])
            conn.commit()
            conn.close()

            self.description = temp[0]
            self.type = temp[1]+', '+str(temp[5])
            self.effect = temp[2]+', '+str(temp[4])
            self.add = temp[3]
            
            return 'success'


def clean_file(file_name):
    with open(file_name, 'r') as file:
        text = ''
        for line in file:
            k = 0
            for i in range(len(line)):
                try:
                    letter = int(line[i])
                    k = i+2
                except Exception:
                    continue

            text += line[k:]
        file.close()


    with open(file_name, 'w') as file:
        file.write(text)
        file.close()


def return_line(file_name, line_number):
    temp = ''
    with open(file_name, 'r') as file:
        lines = file.readlines()
        temp = lines[line_number]
        for i in range(len(lines)):
            if lines[i] == '\n':
                k = i
                break

        analysis = temp.lower().split()
        if 'roll' in analysis:
            roll = numpy.random.randint(low=k+1, high=len(lines), size=1)[0]
            temp = lines[roll]
        file.close()

    return temp[:-1]+'.'



def generate_outlines(folder):
    text = 'After a long and exhausting journey, you arrive at your destination. In the \'Drums\' tavern in the megapolis '+\
    'of Nak-Rompork, you heard a rumor about the '


    roll = numpy.random.randint(low=0, high=8, size=1)[0]
    location = return_line(folder+'dungeons/purpose.txt', roll)
    text += location.lower()[:-1]
    purpose = location.lower()[:-1]

    text += ' lying here '
    roll = numpy.random.randint(low=0, high=24, size=1)[0]
    location = return_line(folder+'dungeons/location.txt', roll)
    text += location.lower()

    text += ' It is said that this place was created by '
    roll = numpy.random.randint(low=0, high=12, size=1)[0]
    location = return_line(folder+'dungeons/creators.txt', roll)
    text += location.lower()
    creators = location.lower()[:-1]

    text += ' However, as the rumor tells, '
    roll = numpy.random.randint(low=0, high=10, size=1)[0]
    history = return_line(folder+'dungeons/history.txt', roll)
    if roll >= 3 and roll <=7:
        text += history.lower()
    else:
        text += 'it was '+history.lower()

    return text, purpose, creators, history.lower()


def generate_dungeon():
    # the whole dungeon is on the grid with x=[0;4] and y=[0;4]
    # with rooms being 0.2 boxes
    dungeon = [Room()]
    dungeon[0].set_coordinates(0, 0)
    this_room = dungeon[0]
    last_id = this_room.room_id

    x = numpy.arange(0.1, 1, 0.2)
    y = numpy.arange(0.1, 1, 0.2)
    grid = numpy.meshgrid(x, y)[0] #[x,y]
    grid[0,0] = 99 # means taken

    where_to_next = []
    check = True
    while check:
        # grid coordinates
        x = this_room.coord_x
        y = this_room.coord_y

        # determening number of possible neighbours
        number_of_possible_nbrs = 4 
        if x == 0 or x == 4:
            number_of_possible_nbrs -= 1
            if y != 0 and y != 4 and grid[x,y+1] == 99:
                number_of_possible_nbrs -= 1
            if y != 0 and y != 4 and grid[x,y-1] == 99:
                number_of_possible_nbrs -= 1
            if x != 0 and grid[x-1,y] == 99:
                number_of_possible_nbrs -= 1
            if x != 4 and grid[x+1,y] == 99:
                number_of_possible_nbrs -= 1
        if y == 0 or y == 4:
            number_of_possible_nbrs -= 1
            if x != 0 and x != 4 and grid[x+1,y] == 99:
                number_of_possible_nbrs -= 1
            if x != 0 and x != 4 and grid[x-1,y] == 99:
                number_of_possible_nbrs -= 1
            if y != 0 and grid[x,y-1] == 99:
                number_of_possible_nbrs -= 1
            if y != 4 and grid[x,y+1] == 99:
                number_of_possible_nbrs -= 1
        if x != 0 and x != 4 and y != 0 and y != 4:
            if grid[x+1, y] == 99:
                number_of_possible_nbrs -= 1
            if grid[x-1, y] == 99:
                number_of_possible_nbrs -= 1
            if grid[x, y+1] == 99:
                number_of_possible_nbrs -= 1
            if grid[x, y-1] == 99:
                number_of_possible_nbrs -= 1


        # random nuber of neighbours
        roll = numpy.random.randint(low=0, high=number_of_possible_nbrs+1)

        # setting up so that dungeon always has more than 9 rooms
        if roll == 0 and len(dungeon) < 9:
            roll = 1

        if len(dungeon) > 13:
            once_more = numpy.random.randint(low=0, high=101)
            if once_more < 40:
                roll = 0
            if len(dungeon) > 15 and once_more < 80:
                roll = 0

        

        # setting up available directions
        directions = []
        if x == 0:
            if grid[x+1, y] != 99:
                directions.append('right')
            if y != 4 and grid[x, y+1] != 99:
                directions.append('up')
            if y != 0 and grid[x, y-1] != 99:
                directions.append('down')
        if y == 0:
            if grid[x, y+1] != 99:
                directions.append('up')
            if x != 4 and grid[x+1, y] != 99:
                directions.append('right')
            if x != 0 and grid[x-1, y] != 99:
                directions.append('left')
        if x == 4:
            if grid[x-1, y] != 99:
                directions.append('left')
            if y != 4 and grid[x, y+1] != 99:
                directions.append('up')
            if y != 0 and grid[x, y-1] != 99:
                directions.append('down')
        if y == 4: 
            if grid[x, y-1] != 99:
                directions.append('down')
            if x != 4 and grid[x+1, y] != 99:
                directions.append('right')
            if x != 0 and grid[x-1, y] != 99:
                directions.append('left')
        if x != 0 and x != 4 and y != 0 and y != 4:
            if grid[x+1, y] != 99:
                directions.append('right')
            if grid[x-1, y] != 99:
                directions.append('left')
            if grid[x, y+1] != 99:
                directions.append('up')
            if grid[x, y-1] != 99:
                directions.append('down')

        directions = list(dict.fromkeys(directions))
        for i in range(roll):
            try:
                rand_direct = numpy.random.randint(low=0, high=len(directions))
            except ValueError:
                print(ValueError, directions, this_room.room_id, this_room.coord_x, this_room.coord_y)
                print(grid)
                return dungeon
            where = directions[rand_direct]
            directions.pop(rand_direct)

            dungeon.append(Room())
            last_id += 1
            dungeon[-1].room_id = last_id 
            this_room.add_neigbour(dungeon[-1].room_id)
            dungeon[-1].add_neigbour(this_room.room_id)

            if i >= 1:
                where_to_next.append(dungeon[-1].room_id)
            if i == 0:
                next_index = last_id

            if where == 'up':
                dungeon[-1].set_coordinates(this_room.coord_x, this_room.coord_y + 1)
                grid[x,y+1] = 99
            if where == 'down':
                dungeon[-1].set_coordinates(this_room.coord_x, this_room.coord_y - 1)
                grid[x,y-1] = 99
            if where == 'right':
                dungeon[-1].set_coordinates(this_room.coord_x + 1, this_room.coord_y)
                grid[x+1,y] = 99
            if where == 'left':
                dungeon[-1].set_coordinates(this_room.coord_x - 1, this_room.coord_y) 
                grid[x-1,y] = 99



        if roll >= 1:
            this_room = dungeon[next_index]
        if roll == 0 and len(where_to_next) != 0:
            this_room = dungeon[where_to_next[-1]]
            where_to_next.pop()
        if roll == 0 and len(where_to_next) == 0:
            check = False

    # check for all neighbours
    for l in range(len(dungeon)):
        for k in range(len(dungeon)):
            if k != l:
                if numpy.abs(dungeon[k].coord_x - dungeon[l].coord_x) == 1.1:
                    dungeon[l].add_neigbour(dungeon[k].room_id)
                if numpy.abs(dungeon[k].coord_y - dungeon[k].coord_y) == 1.1:
                    dungeon[l].add_neigbour(dungeon[k].room_id)


    return dungeon
            

def generate_room(room, purpose_meta, folder):
    room_id = room.room_id

    with open(folder+'dungeons/air.txt', 'r') as file:
        air = file.readlines()
        file.close()
    roll = numpy.random.randint(low=0, high=len(air))
    room.air = air[roll].lower()[:-1]

    with open(folder+'dungeons/chamber_state.txt', 'r') as file:
        chamber_state = file.readlines()
        file.close()
    roll = numpy.random.randint(low=0, high=len(chamber_state))
    room.chamber_state = chamber_state[roll].lower()[:-1]

    isolated_room_flag = True
    while isolated_room_flag:
        roll_meta = numpy.random.randint(low=0, high=101)
        if roll_meta < 60:
            purpose = purpose_meta.split()
            if len(purpose) != 1:
                purpose = 'dungeons/'+purpose[0]+'_'+purpose[1]+'.txt'
            else:
                purpose = 'dungeons/'+purpose[0]+'.txt'

            with open(folder+purpose, 'r') as file:
                specific_purpose = file.readlines()
                file.close()
            roll = numpy.random.randint(low=0, high=len(specific_purpose))
            purpose = specific_purpose[roll].lower()[:-1]            
        else:
            with open(folder+'dungeons/general_purpose.txt', 'r') as file:
                general_purpose = file.readlines()
                file.close()
            roll = numpy.random.randint(low=0, high=len(general_purpose))
            purpose = general_purpose[roll].lower()[:-1]

        if room.number_of_neighbours() != 1:
            if 'bedroom' in purpose.split() or 'latrine' in purpose.split() or \
            'vault' in purpose.split() or 'strong' in purpose.split():
                isolated_room_flag = True
            else:
                isolated_room_flag = False
        else:
            isolated_room_flag = False


    if purpose.split()[0][-1] != 's':
        if purpose.split()[0][0] in ['a', 'o', 'u', 'e', 'i']:
            room.purpose = 'an '+purpose
        else:
            room.purpose = 'a '+purpose
    else:
        room.purpose = purpose


    if room_id == 0:
        room.purpose = 'an entrance to the '+purpose_meta
        room.is_cleared = True


    room.description = 'As you enter the room you notice '+room.chamber_state+'. It seems like this chamber serves as '+\
    room.purpose+'. Air here is '+room.air+'.'

    if ('stripped' in room.chamber_state.split()) == False and room_id != 0:

        max_number_of_furniture = 4
        min_number_of_furniture = 1
        if 'wrecked' in room.chamber_state.split() or 'ashes' in room.chamber_state.split() or 'damaged' in room.chamber_state.split():
            max_number_of_furniture -= 1
        if 'pristine' in room.chamber_state.split():
            min_number_of_furniture += 1

        if 'smoky' in room.air.split() or 'smoke' in room.air.split():
            room.content[2].description = random_material('brazier and charcoal', metal=True)
            max_number_of_furniture -= 1

        if ('entrance' in room.purpose.split()) == False: 
            if 'bedroom' in room.purpose.split() or 'dormitory' in room.purpose.split():
                room.content[0].description = random_material('bed', wood=True)
                max_number_of_furniture -= 1

            if 'dining' in room.purpose.split() or 'kitchen' in room.purpose.split() or 'banquet' in room.purpose.split() \
            or 'refectory' in room.purpose.split():
                tables = ['large', 'long', 'low', 'round', 'small', 'trestle']
                roll = numpy.random.randint(low=0, high=len(tables))
                room.content[0].description = random_material(tables[roll]+' table', metal=True, wood=True, stone=True)
                max_number_of_furniture -= 1

            if 'throne' in room.purpose.split():
                room.content[0].description = random_material('throne', metal=True, wood=True)
                max_number_of_furniture -= 1

            if 'dressing' in room.purpose.split() or 'robing' in room.purpose.split() or 'closet' in room.purpose.split():
                room.content[0].description = random_material('wardrobe', wood=True)
                room.content[0].is_container = True
                max_number_of_furniture -= 1

            if 'vault' in room.purpose.split() or 'strong' in room.purpose.split():
                room.content[0].description = random_material('chest', metal=True, wood=True)
                room.content[0].is_container = True
                room.content[1].description = random_material('trunk', metal=True, wood=True)
                room.content[1].is_container = True
                max_number_of_furniture -= 2

            if 'temple' in room.purpose.split() or 'shrine' in room.purpose.split() \
            or 'chantry' in room.purpose.split() or 'chapel' in room.purpose.split():
                room.content[0].description = random_material('altar', wood=True, stone=True)
                max_number_of_furniture -= 1

            if 'armory' in room.purpose.split():
                room.content[0].description = random_material('weapon rack', metal=True, wood=True)
                room.content[0].is_container = True
                max_number_of_furniture -= 1

            if 'workshop' in room.purpose.split():
                room.content[0].description = random_material('workbench', wood=True)
                max_number_of_furniture -= 1

            if 'crypt' in room.purpose.split() or 'tomb' in room.purpose.split():
                room.content[0].description = random_material('sarcophagus', stone=True)
                max_number_of_furniture -= 1

            if 'gallery' in room.purpose.split() or 'trophy' in room.purpose.split():
                room.content[0].description = random_painting(folder)
                max_number_of_furniture -= 1

            if 'library' in room.purpose.split() or 'study' in room.purpose.split() or 'library,' in room.purpose.split():
                room.content[0].description = random_material('bookshelf', wood=True)
                room.content[0].is_container = True
                max_number_of_furniture -= 1

            if 'laboratory' in room.purpose.split() or 'study' in room.purpose.split() or 'library,' in room.purpose.split() \
            or 'library' in room.purpose.split() or 'office' in room.purpose.split() or 'observatory' in room.purpose.split():
                room.content[1].description = random_material('shelf', wood=True)
                room.content[1].is_container = True
                max_number_of_furniture -= 1

            roll = numpy.random.randint(low=0, high=101)
            if roll < 40:
                room.content[0].description = random_material('chest', metal=True, wood=True)
                room.content[0].is_container = True
                max_number_of_furniture -= 1



        with open(folder+'dungeons/furniture.txt', 'r') as file:
            general_furniture = file.readlines()
            file.close()

        with open(folder+'dungeons/mage_furniture.txt', 'r') as file:
            mage_furniture = file.readlines()
            file.close()

        with open(folder+'dungeons/religious_furniture.txt', 'r') as file:
            religious_furniture = file.readlines()
            file.close()


        if purpose_meta == 'planar gate': 
            general_furniture += mage_furniture
        if purpose_meta == 'shrine' or purpose_meta == 'tomb':
            general_furniture += religious_furniture

        
        try:
            roll_meta = numpy.random.randint(low=min_number_of_furniture, high=max_number_of_furniture)
        except ValueError:
            roll_meta = 0
        for i in range(4):
            if room.content[i].description == " "*100 and roll_meta != 0:

                roll = numpy.random.randint(low=0, high=len(general_furniture))
                room.content[i].description = general_furniture[roll].lower()[:-1]

                if room.content[i].description in ['box', 'chest', 'cabinet', 'wardrobe', 'crate', \
                'cupboard', 'sack', 'bag', 'offertory container', 'trunk', 'shelf', 'weapon rack', 'armoire',\
                'firkin', 'barrel', 'sideboard']:
                    room.content[i].is_container = True
                    if room.content[i].description in ['chest', 'weapon rack']:
                        room.content[i].description = random_material(room.content[i].description, metal=True, wood=True)

                if room.content[i].description in ['altar', 'fountain', 'fresco', 'frescoes', 'grindstone', \
                'large idol', 'pedestal', 'urn']:
                    room.content[i].description = random_material(room.content[i].description, stone=True)

                if room.content[i].description in ['armoire', 'barrel', 'bed', 'bench', 'bucket', 'buffet cabinet', \
                'bunks', 'cabinet', 'cask', 'plain chair', 'padded chair', 'workbench', 'box', 'desk', 'trunk', 'stand',\
                'wardrobe', 'sideboard', 'cupboard', 'shelf', 'crate', 'firkin', 'tub', 'dais', 'keg', 'desk']\
                or 'table' in room.content[i].description.split() or 'stool' in room.content[i].description.split()\
                or 'chair' in room.content[i].description.split():
                    room.content[i].description = random_material(room.content[i].description, wood=True)

                if room.content[i].description in ['bag', 'sack', 'blanket', 'pillow', 'small rug', 'cushion',\
                'tapestry', 'arras', 'couch', 'large carpet', 'robes', 'vestments', 'divan', 'quilt', 'sofa']:
                    room.content[i].description = random_material(room.content[i].description, fabric=True)

                if room.content[i].description in ['statue', 'throne', 'offertory container']:
                    room.content[i].description = random_material(room.content[i].description, metal=True, wood=True, stone=True)
                

                if room.content[i].description == 'painting':
                    room.content[i].description = random_painting(folder)



                roll_meta -= 1
                if roll_meta == 0: break

    return room
                    

def fill_containers(room, player_class, folder):
    consumables = ['potion of healing', 'great potion of healing', 'scroll of teleportation', 'map']
    if player_class == 'warrior':
        weapons = ['sword', 'shield', 'plate', 'mail', 'axe', 'mace', 'spear', 'warhammer', 'maul', \
        'glaive', 'halberd', 'scimitar', 'dagger']
    if player_class == 'mage':
        weapons = ['cap', 'hood', 'hat', 'robe', 'stick', 'staff', 'wand', 'rod', 'sword', \
        'mantle', 'cloak', 'ring']

    general = ['azurite gem', 'blue quartz', 'eye agate', 'lapis lazuli', 'malachite', 'tiger eye', \
    'turquoise', 'onyx', 'moonstone', 'citrine', 'zircon', 'amber', 'amethyst', 'jade', 'pearl', 'silver ewer', \
    'small gold bracelet', 'bronze crown', 'silver necklace with a gemstone pendant', 'carved ivory statuette',\
    'box of turquoise animal figurines', 'carved bone statuette', 'copper chalice with silver filigree']


    map_flag = True
    for i in range(4):
        if room.content[i].is_container:
            roll_meta = numpy.random.randint(low=0, high=4)

            if roll_meta <= 1:
                roll = numpy.random.randint(low=0, high=len(consumables))
                room.content[i].content.description = consumables[roll]
                room.content[i].content.type = 'consumable'
                if roll < 2:
                    room.content[i].content.effect = 'healing'
                    if roll == 0:
                        room.content[i].content.add = 2
                    if roll == 1:
                        room.content[i].content.add = 4
                if roll == 2 or roll == 3:
                    room.content[i].content.effect = 'travel'

            if roll_meta == 2 or 'weapon' in room.content[i].description.split():
                roll = numpy.random.randint(low=0, high=len(weapons))
                room.content[i].content.description = random_material(weapons[roll], metal=True)
                room.content[i].content.type = 'stats'
                roll_stat = numpy.random.randint(low=0, high=3)
                roll_add = numpy.random.randint(low=1, high=5)
                if roll_stat == 0:
                    room.content[i].content.effect = 'strength'
                    room.content[i].content.add = roll_add
                if roll_stat == 1:
                    room.content[i].content.effect = 'intellect'
                    room.content[i].content.add = roll_add
                if roll_stat == 2:
                    room.content[i].content.effect = 'endurance'
                    room.content[i].content.add = roll_add

            if roll_meta == 3 or 'bookshelf' in room.content[i].description.split():
                roll = numpy.random.randint(low=0, high=101)
                roll_add = numpy.random.randint(low=1, high=5)
                room.content[i].content.type = 'score'
                room.content[i].content.effect = 'score'
                room.content[i].content.add = roll_add

                if 'bookshelf' in room.content[i].description.split():
                    roll = 40

                if roll < 30:
                    roll = numpy.random.randint(low=0, high=len(general))
                    room.content[i].content.description = general[roll]
                    room.content[i].content.add = roll_add+2
                elif roll >= 30 and roll < 50:
                    room.content[i].content.description = random_book(folder)
                    room.content[i].content.add = roll_add + 1
                else:
                    roll = numpy.random.randint(low=9, high=46)
                    room.content[i].content.description = 'a sack of '+str(roll)+' gold coins'
                    room.content[i].content.add = int(roll/45*5)

            if 'office' in room.purpose.split() or 'observatory' in room.purpose.split() \
            or 'study' in room.purpose.split() or 'library' in room.purpose.split() \
            or 'library,' in room.purpose.split():
                if ('bookshelf' in room.content[i].description.split()) == False and map_flag:
                    room.content[i].content.description = 'map'
                    room.content[i].content.type = 'consumable'
                    room.content[i].content.effect = 'travel'
                    map_flag = False

            if 'laboratory' in room.purpose.split():
                roll = numpy.random.randint(low=0, high=2)
                room.content[i].content.description = consumables[roll]
                room.content[i].content.type = 'consumable'
                room.content[i].content.effect = 'healing'
                if roll == 0:
                    room.content[i].content.add = 2
                if roll == 1:
                    room.content[i].content.add = 4


    return room
    




def draw_dungeon(dungeon, player, k, folder='', map_found=False):
    fig, ax = plt.subplots(1, frameon=False, figsize=(4,4))
    ax.xaxis.set_visible(False) 
    ax.yaxis.set_visible(False) 
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.scatter(2, 2, color='silver', label='cleared')
    ax.scatter(1, 2, color='grey', label='unknown')
    ax.scatter(0, 2, color='salmon', label='player')
    ax.scatter(2, 1, color='green', label='goal')
    ax.legend()

    for i in range(len(dungeon)):
        x = dungeon[i].coord_x/5 + 0.01
        y = dungeon[i].coord_y/5 + 0.01
        rect = patches.Rectangle((x-0.005, y-0.005), 0.19, 0.19, edgecolor='black', facecolor='darkgrey')
        ax.add_patch(rect)
        if dungeon[i].is_cleared:
            rect = patches.Rectangle((x, y), 0.18, 0.18, edgecolor='black', facecolor='silver')
        else:
            rect = patches.Rectangle((x, y), 0.18, 0.18, edgecolor='black', facecolor='grey')
        ax.add_patch(rect)

        if map_found:
            purpose_meta = dungeon[i].purpose.split()
            if purpose_meta[0] in ['a', 'an']:
                purpose = purpose_meta[1]
                if purpose_meta[1] in ['small', 'great', 'central', 'grand', 'large']:
                    purpose = purpose_meta[2]
                if purpose[-1] in [',', '.']:
                    purpose = purpose[:-1]
                ax.text(x+0.005,y+0.008, str(purpose), size=8.5)
            else:
                ax.text(x+0.005,y+0.008, str(purpose_meta[0]), size=8.5)
            ax.text(x+0.005,y+0.041, str(dungeon[i].room_id))
        else:
            ax.text(x+0.005,y+0.005, str(dungeon[i].room_id))


        nbs = dungeon[i].neighbours
        index, = numpy.where(nbs != ' ')

        for j in range(len(index)):
            if dungeon[int(nbs[index[j]])].coord_x == dungeon[i].coord_x:
                x = dungeon[i].coord_x/5 + 0.075
                if dungeon[int(nbs[index[j]])].coord_y > dungeon[i].coord_y:
                    y = dungeon[int(nbs[index[j]])].coord_y/5 - 0.015
                else:
                    y = dungeon[i].coord_y/5 - 0.015
                rect = patches.Rectangle((x, y), 0.05, 0.03, edgecolor='black', facecolor='brown')
            else:
                y =  dungeon[i].coord_y/5 + 0.075
                if dungeon[int(nbs[index[j]])].coord_x > dungeon[i].coord_x:
                    x = dungeon[int(nbs[index[j]])].coord_x/5 - 0.015
                else: 
                    x = dungeon[i].coord_x/5 - 0.015
                rect = patches.Rectangle((x, y), 0.03, 0.05, edgecolor='black', facecolor='brown')

            ax.add_patch(rect)

    circle = patches.Circle((player[0]/5 + 0.1, player[1]/5 + 0.1), 0.04, edgecolor='red', facecolor='salmon')
    ax.add_patch(circle)
    arrow = patches.Arrow(dungeon[-1].coord_x/5 + 0.1, dungeon[-1].coord_y/5 + 0.12, 0, -0.04, width=0.1, edgecolor='black', facecolor='green')
    ax.add_patch(arrow)
    plt.tight_layout(rect=(-0.05, -0.03, 1.03, 1.03))
    name = folder+'dungeon_map_'+str(k)+'.png'
    plt.savefig(name)
    plt.close()


def random_material(this_object, metal=False, wood=False, stone=False, fabric=False):
    metal_materials = ['iron', 'gold', 'copper', 'silver', 'steel', 'brass', 'zinc', 'tin', 'bronze', \
    'aluminium', 'nickel', 'platinum', 'mithral', 'adamantine']

    wood_materials = ['oak', 'birch', 'ash', 'beech', 'cherry', 'maple', 'mahogany', 'spruce', 'fir', \
    'teak', 'walnut', 'pine', 'larch', 'cedar', 'yew']

    stone_materials = ['basalt', 'gabbro', 'granite', 'obsidian', 'pumice', 'breccia', 'limestone', \
    'sandstone', 'shale', 'gneiss', 'marble', 'schist', 'slate']

    fabric_materials = ['wool', 'linen', 'flannel', 'tweed', 'cashmere', 'silk', 'twill', 'cotton', 'jute', 'lether']

    table = []
    if metal: table += metal_materials
    if wood: table += wood_materials
    if stone: table += stone_materials
    if fabric: table += fabric_materials

    roll = numpy.random.randint(low=0, high=len(table))
    this_object = table[roll]+' '+this_object

    gems = ['azurite', 'blue quartz', 'eye agate', 'lapis lazuli', 'malachite', 'tiger eye', \
    'turquoise', 'onyx', 'moonstone', 'citrine', 'zircon', 'amber', 'amethyst', 'jade', 'pearl',\
    'emerald', 'ruby', 'diamond', 'black pearl']

    # encrustation
    roll = numpy.random.randint(low=0, high=101)
    if roll < 20:
        roll = numpy.random.randint(low=0, high=len(gems))
        this_object += ' encrusted with '+gems[roll]
        encrusted_flag = True
    else:
        encrusted_flag = False

    # decoration
    roll = numpy.random.randint(low=0, high=101)
    if roll < 35:
        table = metal_materials+wood_materials+stone_materials
        roll = numpy.random.randint(low=0, high=len(table))
        if encrusted_flag:
            this_object += ' and'
        this_object += ' decorated with '+table[roll]

    return this_object


def random_painting(folder=''):
    paintings = ['portrait', 'landscape', 'still life painting', 'real life painting', 'historic painting', 'religious painting', 'abstraction']
    style = ['romantic', 'old', 'surreal', 'expressive', 'classical']

    roll = numpy.random.randint(low=0, high=len(style))
    text = style[roll]

    roll = numpy.random.randint(low=0, high=len(paintings))
    text += ' '+paintings[roll]

    return text+' created by '+random_name(folder)

def random_book(folder=''):
    with open(folder+'dungeons/books.txt', 'r') as file:
        book = file.readlines()
        file.close()
    roll = numpy.random.randint(low=0, high=len(book))
    return book[roll].lower()[:-1]+' by '+random_name(folder)

def random_name(folder=''):
    conn = sqlite3.connect(folder+'names.bd')
    c = conn.cursor()

    name_not_ok = True
    name = ''
    while name_not_ok:
        roll = numpy.random.randint(low=1, high=20000)
        c.execute('SELECT first_name FROM people WHERE rowid=?', [str(roll)])
        temp = c.fetchall()
        if temp[0][0] != None:
            name_not_ok = False
            name += temp[0][0]

    c.execute('SELECT last_name FROM people')
    temp = c.fetchall()

    roll = numpy.random.randint(low=1, high=len(temp))
    name += ' '+temp[roll][0]

    occupation = ['famous', 'infamous', 'mediocre', 'poorly known', 'talanted', 'who identified as']
    roll = numpy.random.randint(low=0, high=len(occupation))
    occupation = ', '+occupation[roll]+' '


    job_not_ok = True
    while job_not_ok:
        roll = numpy.random.randint(low=1, high=300)
        c.execute('SELECT occupation FROM people WHERE rowid=? LIMIT 1', [str(roll)])
        temp = c.fetchall()
        try:
            if temp[0][0] != None:
                job_not_ok = False
                occupation += temp[0][0].lower()
        except:
            logging.warning(temp, roll)
            raise

    born = ' born in '+str(numpy.random.randint(low=1000, high=4600))
    conn.close()
    return name+occupation+born



def main(player, folder=''):
    text, purpose, creators, history = generate_outlines(folder)

    d = []
    error_flag = True
    while error_flag:
        try:
            if len(d) < 9:
                d = generate_dungeon()
            else:
                error_flag = False
        except:
            logging.warning(sys.exc_info()[0])


    for i in range(len(d)):
        d[i] = generate_room(d[i], purpose, folder)
        d[i] = fill_containers(d[i], player.role, folder)  

    d = set_monsters(d)  

    return text, creators, history, d


def set_monsters(dungeon):
    for i in range(len(dungeon)):
        room = dungeon[i].purpose.split()
        
        if 'guardroom' in room or 'kennel' in room or 'bestiary' in room \
        or 'zoo' in room or 'barracks' in room or 'watchroom' in room or 'guard' in room:
            dungeon[i].has_monster = True

        if 'crypt' in room or 'tomb' in room or 'conjuring' in room:
            roll = numpy.random.randint(low=0, high=101)
            if 'storage' in room or 'entrance' in room: roll = 100
            if roll < 50:
                dungeon[i].has_monster = True

    return dungeon


def generate_monster(room, creators, doom, folder=''):
    invaders_flag = False; undead_flag = False; divine_flag = False
    magic_flag = False; alien_flag = False; beast_flag = False
    epic_flag = False
    if 'invaders' in doom.split() or 'raiders.' in doom.split() or 'internal' in doom.split():
        invaders_flag = True

    if 'plague.' in doom.split():
        undead_flag = True

    if 'cursed' in doom.split() or 'miracle.' in doom.split() \
    or 'worshiping' in creators.split() or 'worshipers' in creators.split():
        divine_flag = True

    if 'magical' in doom.split() or 'magic' in creators.split() or 'lich' in creators.split() \
    or 'beholder' in creators.split() or 'elemental' in creators.split():
        magic_flag = True

    if 'discovery' in doom.split() or 'mindflayers' in creators.split():
        alien_flag = True


    room = room.purpose.split()
    if 'conjuration' in room or 'planar' in room or 'conjuring' in room:
        alien_flag = True

    if 'guardroom' in room or 'barracks' in room or 'watchroom' in room:
        invaders_flag = True

    if 'kennel' in room or 'zoo' in room or 'bestiary' in room or 'lair' in room:
        beast_flag = True

    if 'crypt' in room or 'tomb' in room: 
        undead_flag = True


    if invaders_flag == False and undead_flag == False and divine_flag == False \
    and magic_flag == False and alien_flag == False and beast_flag == False:
        invaders_flag = True
        beast_flag = True

    roll = numpy.random.randint(low=0, high=101)
    if roll < 5:
        epic_flag = True


    table = []
    if invaders_flag: table += [('humanoid')]
    if undead_flag: table += [('undead')]
    if divine_flag: table += [('divine')]
    if magic_flag: table += [('magic')]
    if alien_flag: table += [('alien')]
    if beast_flag: table += [('beast')]
    if epic_flag: table += [('epic')]

    


    conn = sqlite3.connect(folder+'enemies.bd')
    c = conn.cursor()
    all_monsters = []
    for i in range(len(table)):
        c.execute('SELECT * FROM monsters WHERE type=?', [(table[i])])
        all_monsters += c.fetchall()


    roll = numpy.random.randint(low=0, high=len(all_monsters))
    all_monsters = all_monsters[roll]
    conn.close()

    DC = numpy.random.randint(low=0, high=4)
    hp = all_monsters[2]
    if DC == 0:
        stats = numpy.random.randint(low=35, high=45, size=3) + numpy.array([all_monsters[3], all_monsters[4], all_monsters[5]])
    if DC == 1:
        stats = numpy.random.randint(low=45, high=55, size=3) + numpy.array([all_monsters[3], all_monsters[4], all_monsters[5]])
    if DC == 2:
        stats = numpy.random.randint(low=55, high=65, size=3) + numpy.array([all_monsters[3], all_monsters[4], all_monsters[5]])
    if DC == 3:
        stats = numpy.random.randint(low=65, high=75, size=3) + numpy.array([all_monsters[3], all_monsters[4], all_monsters[5]])

    if all_monsters[3] >= all_monsters[4]:
        how_to_attack = 'warrior'
    else:
        how_to_attack = 'mage'


    weapons = ['longsword', 'shortsword', 'greatsword', 'battleaxe', 'handaxe', 'mace', 'spear', 'warhammer', 'maul', \
    'glaive', 'halberd', 'scimitar', 'dagger', 'twin swords']


    monster_type = all_monsters[1]
    if all_monsters[0] == 'humanoid':
        if creators in ['dwarves', 'elves', 'hobgoblins', 'humans'] or 'snake' in creators.split() or 'fish' in creators.split():
            roll = numpy.random.randint(low=0, high=101)
            if roll < 30:
                if 'snake' in creators.split(): monster_type = 'yuan-ti snake person'
                elif 'fish' in creators.split(): monster_type = 'kuo-toa fish person'
                elif creators in ['dwarves', 'elves']:
                    monster_type = creators[:-3]+'f'
                else:
                    monster_type = creators[:-1]


        status = ['a novice', 'an adequate', 'a skilled', 'a professional']
        roles = ['thug', 'bandit', 'robber', 'spy', 'grave digger', 'con artist', \
        'raider', 'soldier', 'mercenary', 'sellsword', 'cult member', 'gang memeber', \
        'looter', 'criminal', 'fraud', 'paladin', 'adventurer', 'knight', 'squire', \
        'ronin', 'samurai', 'guard', 'champion', 'local hero', 'pirat', 'wrecker', 'inquisitor']
        roll = numpy.random.randint(low=0, high=len(roles))
        description = random_name(folder).split(',')[0]+', '+monster_type+', '+status[DC]+' '+roles[roll]

        roll = numpy.random.randint(low=0, high=len(weapons))
        description += ' wielding '+random_material(weapons[roll], metal=True)


    if all_monsters[0] == 'beast':
        status = ['a wild', 'an angry', 'a savage', 'a dangerous']
        bodyparts = ['sharp', 'large', 'small', 'bloodied', 'razor-sharp', 'terrifying', 'blunt', \
        'threatening', 'murderous', 'minacious', 'menacing']
        roll = numpy.random.randint(low=0, high=len(bodyparts))
        description = status[DC]+" "+all_monsters[1]+' with '+bodyparts[roll]+' '+all_monsters[6]


    if all_monsters[0] == 'undead':
        status = ['a hungry', 'an undead', 'a shattering', 'a powerful']
        if (all_monsters[1] in ['wraith', 'lich']) == False:
            description = status[DC]+' '+all_monsters[1]+' in his mortal life known as '+random_name(folder)
        elif all_monsters[1] == 'wraith':
            roll = numpy.random.randint(low=0, high=len(weapons))
            description = status[DC]+' '+all_monsters[1]+' wielding '+random_material(weapons[roll], metal=True)
        elif all_monsters[1] == 'lich':
            description = status[DC]+' '+all_monsters[1]+', a vicious mage in his mortal life who lusted for immortality and ultimate power'


    if all_monsters[0] == 'alien':
        status = ['a hideous', 'an abnormal', 'an incomprehensible', 'a horrific']
        aura = ['slimy', 'time disturbing', 'space tearing', 'mind shattering', 'revolting', \
        'sickening', 'nauseating', 'rotting', 'twisting', 'salty', 'sludgy', 'accursed']
        roll = numpy.random.randint(low=0, high=len(aura))
        description = status[DC]+' '+all_monsters[1]+' emanating '+aura[roll]+' aura'
        if all_monsters[1] in ['optical aberration', 'color out of space']:
            aura = ['space tearing', 'sickening', 'nauseating', 'glistering', 'disturbing', 'faint', 'bending', 'pooring']
            roll = numpy.random.randint(low=0, high=len(aura))
            description = status[DC]+' '+all_monsters[1]+' emanating '+aura[roll]+' light like you have never seen before'
        if all_monsters[1] in ['alien abomination', 'interdimensional raider']:
            roll_w = numpy.random.randint(low=0, high=len(weapons))
            description = status[DC]+' '+all_monsters[1]+' wielding '+aura[roll]+' '+random_material(weapons[roll_w], metal=True)
        if all_monsters[1] == 'mindflayers':
            description = status[DC]+' '+all_monsters[1]+' moving their '+aura[roll]+' wet face tentacles towards you'


    if all_monsters[0] == 'divine':
        good = ['angel', 'serafim', 'archangel', 'erinyes']
        bad = ['imp', 'demon', 'devil', 'inkubus', 'succubus', 'shadow demon', 'mezzoloth']
        if all_monsters[1] in bad:
            status = [ 'a laughable', 'a wicked', 'a hellish', 'the prince of corruption,']
            bodypart = ['wings', 'spikes', 'swollen abscesses', 'infernal runes', 'chains']
            roll = numpy.random.randint(low=0, high=len(bodypart))
            description = status[DC]+' '+all_monsters[1]+' straightening shoulders holding '+bodypart[roll]+' on them'

            roll = numpy.random.randint(low=0, high=101)
            if roll < 25:
                roll = numpy.random.randint(low=0, high=len(good))
                description += '. You watch as '+all_monsters[1]+' pearces '+good[roll]+' killing him off. Then looks at you and ' +\
                'with wiecked smile says: \'You are next\'.'

        if all_monsters[1] in good:
            status = ['a godly', 'a divine servant,', 'the champion of justice,','an all-powerful']
            roll = numpy.random.randint(low=0, high=len(weapons))
            description = status[DC]+' '+all_monsters[1]+' straightens wings and swings his '+random_material(weapons[roll], metal=True)


            roll = numpy.random.randint(low=0, high=101)
            if roll < 25:
                roll = numpy.random.randint(low=0, high=len(bad))
                description += '. You watch as '+all_monsters[1]+' tears '+bad[roll]+' killing him off. Then looks at you and ' +\
                'with sinister tone says: \'Another demon spawn...\'.'


    if all_monsters[0] == 'magic':
        status = ['an uncanny', 'a magical', 'a mystical','an ancient']
        description = status[DC]+' '+all_monsters[1]+', '+all_monsters[6]


    if all_monsters[0] == 'epic':
        description = 'a powerful and extremly dangerous '+all_monsters[1]+', '+all_monsters[6]


    return [description, monster_type, hp, stats, how_to_attack]

#clean_file('dungeons/religious_furniture.txt')
#main([0,0])

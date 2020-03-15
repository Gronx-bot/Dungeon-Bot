import numpy
import sqlite3

from game_folder.game_classes.dungeon_classes import Item
from game_folder.game_classes.damage_types import Damage
from game_folder.game_classes.inventory import Inventory

class Player:
    """docstring for Player"""
    def __init__(self):
        self.name = '____no_name____'
        self.race = 'human'
        self.role = 'warrior'
        self.strength = 50
        self.intellect = 50
        self.endurance = 50
        self.max_hp = 12
        self.hp = 12
        
        # For monsters: 0 = no monster; 1 = active monster; 2 = stunned monster
        self.score = 0 
        self.backpack = []
        self.inventory = Inventory()

        self.damage_min = 2
        self.damage_max = 4
        self.damage_type = Damage.SLASHING.value
        self.protection = [0]*len(Damage) #setting base protection to 0 to all types of damage
        self.vulnerability = [0]*len(Damage)
        

    def show_backpack(self):
        temp = [];
        final = []
        for i in range(len(self.backpack)):
            line = self.backpack[i].inventory_line()
            if line in temp:
                idx = temp.index(line)
                line = final[idx]
                if line[0] == '(':
                    lk = len(line.split(')')[0])
                    if lk > 2:
                        line = '('+str(int(line[1:lk])+1)+line[lk:]
                    else:
                        line = '('+str(int(line[1])+1)+line[2:]
                    final[idx] = line
                else:
                    line = '(2) '+line
                    final[idx] = line
            else:
                temp.append(line)
                final.append(line)

        return final

    def add_to_backpack(self, items):
        for i in range(len(items)):
            if items[i].type == 'score':
                if 'coins' in items[i].description.split():
                    self.inventory.gold += items[i].add
                else:
                    self.score += items[i].equip()
            else:
                if items[i].type == 'stats':
                    self.score += 2
                self.backpack.append(items[i])


    def take_from_backpack(self, desc):
        if desc[0] == '(':
            desc = desc.split(')')[1]
            desc = desc[1:]
        for i in range(len(self.backpack)):
            if desc == self.backpack[i].description:
                item = self.backpack[i]
                self.backpack.pop(i)
                return item

    def use(self, item):
        for i in range(len(self.backpack)):
            if item == self.backpack[i].description:
                if self.backpack[i].type != 'equipable':
                    effect, add = self.backpack[i].use()
                    self.backpack.pop(i)
                    if effect == 'strength': 
                        self.strength += add
                        return item+' increased your '+effect+' by '+str(add)
                    if effect == 'intellect': 
                        self.intellect += add
                        return item+' increased your '+effect+' by '+str(add)
                    if effect == 'endurance': 
                        self.endurance += add
                        return item+' increased your '+effect+' by '+str(add)
                    if effect == 'healing':
                        self.heal(add)
                        return 'You have healed. Your current hp: '+str(self.hp)
                else:
                    if self.backpack[i].effect == 'weapon':
                        bonus = self.backpack[i].add[0]
                        bonus = bonus.split(';')
                        self.damage_min = int(bonus[0])
                        self.damage_max = int(bonus[1])
                        prev_item, self.damage_type = self.inventory.equip_weapon(self.backpack[i], self.damage_type)
                    else:
                        prev_item, self.protection = self.inventory.equip_armor(self.backpack[i], self.protection)

                    text = self.backpack[i].description+' equiped.'
                    self.backpack.pop(i)
                    if prev_item:
                        self.add_to_backpack([prev_item])
                        text+= '\n'+self.backpack[-1].description+' added back into backpack'
                    return text


    def heal(self, hp):
        if (self.hp + hp) >= self.max_hp:
            self.hp = self.max_hp
        else:
            self.hp += hp

    def set_stats(self, strength, intellect, endurance):
        self.strength = strength
        self.intellect = intellect
        self.endurance = endurance
        self.max_hp = int(endurance/5) + 2

    def set_name(self, name):
        self.name = name

    def set_max_hp(self):
        self.max_hp = int(self.endurance/5) + 2
        self.hp = self.max_hp

    def calculate_score(self):
        self.score += 0.1*self.endurance
        if self.role == 'warrior':
            self.score += 0.1*self.strength+0.2*self.intellect
        elif self.role == 'mage':
            self.score += 0.2*self.strength+0.1*self.intellect
        self.score = int(self.score)

    def set_up_monster(self, monster):
        self.score = 1
        self.name = monster[0] #description
        self.race = monster[1] #class
        self.max_hp = monster[2] 
        self.hp = monster[2] 
        self.strength = monster[3][0] 
        self.intellect = monster[3][1]
        self.endurance = monster[3][2]
        self.role = monster[4]

        self.damage_type = monster[5]
        self.vulnerability = monster[6]
        self.protection = monster[7]

    def take_damage(self, dmg, dmg_type):
        if self.protection[dmg_type] > 1:
            defence = 1
        else:
            defence = self.protection[dmg_type]

        if self.vulnerability[dmg_type] > 1:
            vuln = 1
        else:
            vuln = self.vulnerability[dmg_type]

        dmg = round(dmg - defence*dmg + vuln*dmg)
        self.hp -= int(dmg)
        return dmg

    def damage_save(self):
        text = 'dmg_min='+str(self.damage_min)+'\n'
        text += 'dmg_max='+str(self.damage_max)+'\n'
        text += 'dmg_type='+str(self.damage_type)+'\n'
        text += 'protection='+str(self.protection)+'\n'
        text += 'vulnerability='+str(self.vulnerability)
        return text

    def damage_load(self, temp):
        temp = temp.split('\n')
        self.damage_min = int(temp[0].split('=')[1])
        self.damage_max = int(temp[1].split('=')[1])
        self.damage_type = int(temp[2].split('=')[1])

        prot = temp[3].split('=')[1]
        vuln = temp[4].split('=')[1]

        prot = prot[1:-1].split(', ')
        vuln = vuln[1:-1].split(', ')

        for i in range(len(Damage)):
            self.protection[i] = float(prot[i])
            self.vulnerability[i] = float(vuln[i])



    def save_to_repository(self, user_id, folder=''):
        backpack = ''
        for i in range(len(self.backpack)):
            backpack += self.backpack[i].save_line()
            backpack += '\n'

        inventory = self.inventory.save_text()

        damage = self.damage_save()

        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO characters VALUES (?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, self.name, self.race, self.role, self.strength, self.intellect, 
                self.endurance, self.score, backpack, inventory, damage))
        conn.commit()
        conn.close()


    def load_items_to_backpack(self, temp):
        backpack = temp.split(';\n')
        if len(backpack) != 1: 
            result = []
            for i in range(len(backpack)-1):
                temp = backpack[i]
                x = Item()
                x.load(temp)
                result.append(x)

            self.add_to_backpack(result)


    def load_items_to_inventory(self, temp):
        inventory = temp.split(';\n')
        for i in range(len(inventory)-1):
            temp = inventory[i].split(':')
            self.inventory.load_item(temp)


    def load_from_repository(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('SELECT * FROM characters WHERE user_id = ? LIMIT 1', [user_id]) 
        temp = c.fetchall() 
        conn.close()

        temp = temp[0]
        self.name = temp[1]
        self.race = temp[2]
        self.role = temp[3]
        self.set_stats(temp[4], temp[5], temp[6])
        self.hp = self.max_hp
        self.score = temp[7]

        self.load_items_to_backpack(temp[8])
        self.load_items_to_inventory(temp[9])

        self.damage_load(temp[10])

    def delete_from_repository(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'character_save.bd')
        c = conn.cursor()
        c.execute('DELETE FROM characters WHERE user_id = ? LIMIT 1', [user_id])
        conn.commit()
        conn.close()

    def create_new(self, user_id, folder=''):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()
        c.execute('INSERT or REPLACE INTO character VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, '____no_name____', 'human', 'warrior', 50, 50, 50, 
                12, 0, '', 1, 5, '', self.damage_save()))
        c.execute('INSERT or REPLACE INTO monster VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', 
            (user_id, '____no_name____', 'human', 'warrior', 50, 50, 50, 
                6, 0, 5, self.damage_save(), ''))
        conn.commit()
        conn.close()            

    def save(self, user_id, who, folder=''):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()

        if who == 'character':
            backpack = ''
            for i in range(len(self.backpack)):
                backpack += self.backpack[i].save_line()
                backpack += '\n'

            if self.role == 'warrior':
                c.execute('INSERT or REPLACE INTO character VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                    (user_id, self.name, self.race, self.role, self.strength, self.intellect, self.endurance, 
                        self.hp ,self.score, backpack, int(self.has_used_second_breath), self.stun_cooldown,
                        self.inventory.save_text(), self.damage_save()))
            if self.role == 'mage':
                c.execute('INSERT or REPLACE INTO character VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                    (user_id, self.name, self.race, self.role, self.strength, self.intellect, self.endurance, 
                        self.hp ,self.score, backpack, int(self.has_used_healing), self.fireball_cooldown,
                        self.inventory.save_text(), self.damage_save()))
        if who == 'monster':
            c.execute('INSERT or REPLACE INTO monster VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', 
                (user_id, self.name, self.race, self.role, self.strength, self.intellect, self.endurance, 
                    self.hp ,self.score, self.max_hp, self.damage_save(), ''))
            
        conn.commit()
        conn.close()

    def load(self, user_id, who, folder=''):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()

        if who == 'character':
            c.execute('SELECT * FROM character WHERE user_id = ? LIMIT 1', [user_id]) 
            temp = c.fetchall() 
            temp = temp[0]
            self.name = temp[1]
            self.race = temp[2]
            self.role = temp[3]
            self.set_stats(int(temp[4]), int(temp[5]), int(temp[6]))
            self.hp = int(temp[7])
            self.score = int(temp[8])
            if self.role == 'warrior':
                self.has_used_second_breath = bool(int(temp[10]))
                self.stun_cooldown = int(temp[11])
            if self.role == 'mage':
                self.has_used_healing = bool(int(temp[10]))
                self.fireball_cooldown = int(temp[11])

            self.load_items_to_backpack(temp[9])
            self.load_items_to_inventory(temp[12])
            self.damage_load(temp[13])

        if who == 'monster':
            c.execute('SELECT * FROM monster WHERE user_id = ? LIMIT 1', [user_id]) 
            temp = c.fetchall() 
            temp = temp[0]
            self.name = temp[1]
            self.race = temp[2]
            self.role = temp[3]
            self.set_stats(int(temp[4]), int(temp[5]), int(temp[6]))
            self.hp = int(temp[7])
            self.max_hp = int(temp[9])
            self.score = int(temp[8])

            self.damage_load(temp[10])

        conn.close()

    def delete(self, user_id, who, folder=''):
        conn = sqlite3.connect(folder+'game_control.bd')
        c = conn.cursor()
        if who == 'monster':
            c.execute('DELETE FROM monster WHERE user_id = ? LIMIT 1', [user_id])
        if who == 'character':
            c.execute('DELETE FROM character WHERE user_id = ? LIMIT 1', [user_id])
        conn.commit()
        conn.close()


class Warrior(Player):
    has_used_second_breath = False
    stun_cooldown = 5

    def second_breath(self):
        if self.has_used_second_breath == False:
            roll = numpy.random.randint(low=4, high=9)
            self.heal(roll)
            self.has_used_second_breath = True
            return 'You have healed '+str(roll)+' hp.\nYour current hp: '+str(self.hp)
        else:
            return 0

    def stun(self):
        if self.stun_cooldown == 5:
            self.stun_cooldown = 4
            return 'stun'

    def update(self, start=False):
        temp = [0,0]
        if self.stun_cooldown == 5:
            temp[1] = 'Stun attack: stuns opponent for 1 round'
        if self.stun_cooldown != 5 and self.stun_cooldown != 0:
            if not start:
                self.stun_cooldown -= 1
            temp[1] = 'CD: '+str(self.stun_cooldown)
        if self.stun_cooldown == 0:
            self.stun_cooldown = 5
            temp[1] = 'Stun attack: stuns opponent for 1 round'

        if self.has_used_second_breath:
            temp[0] = 'Used'
        else:
            temp[0] = 'Second breath: heals 4-8 hp'

        return temp


class Mage(Player):
    has_used_healing = False
    fireball_cooldown = 5

    def healing(self):
        if self.has_used_healing == False:
            roll = numpy.random.randint(low=4, high=7)
            self.heal(roll)
            self.has_used_healing = True
            return 'You have healed '+str(roll)+' hp.\nYour current hp: '+str(self.hp)
        else:
            return 0

    def fireball(self):
        if self.fireball_cooldown == 5:
            self.fireball_cooldown = 4
            return 'fireball'

    def update(self, start=False):
        temp = [0,0]
        if self.fireball_cooldown == 5:
            temp[1] = 'Fireball: deals 6 damage'
        if self.fireball_cooldown != 5 and self.fireball_cooldown != 0:
            if not start:
                self.fireball_cooldown -= 1
            temp[1] = 'CD: '+str(self.fireball_cooldown)
        if self.fireball_cooldown == 0:
            self.fireball_cooldown = 5
            temp[1] = 'Fireball: deals 6 damage'

        if self.has_used_healing:
            temp[0] = 'Used'
        else:
            temp[0] = 'Healing spell: heals 4-6 hp'

        return temp
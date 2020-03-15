from game_folder.game_classes.dungeon_classes import Item


class Inventory():
    """docstring for Inventory"""
    def __init__(self):
        self.gold = 0

        self.head = []
        self.arms = []
        self.body = []
        self.legs = []
        self.weapon = []

    def equip_armor(self, item, parameter):
        if item.effect == 'head':
            return self.change_item(self.head, item, parameter)
           
        if item.effect == 'arms':
            return self.change_item(self.arms, item, parameter)

        if item.effect == 'body':
            return self.change_item(self.body, item, parameter)

        if item.effect == 'legs':
            return self.change_item(self.legs, item, parameter)

    def equip_weapon(self, item, attack):
        self.weapon.append(item)
        attack = item.add[1]
        if len(self.weapon) != 1:
            prev_item = self.weapon.pop(0)
            return prev_item, attack
        else:
            return False, attack

    def change_item(self, slot, item, parameter):
        slot.append(item)
        parameter = self.add_bonuses(item.add, parameter)
        if len(slot) != 1:
            prev_item = slot.pop(0)
            bonus = prev_item.add.copy()
            bonus[0] = -bonus[0]
            parameter = self.add_bonuses(bonus, parameter)
            return prev_item, parameter
        else:
            return False, parameter


    def add_bonuses(self, bonus, parameter):
        assert len(bonus) == 2
        assert len(parameter) == 10
        parameter[bonus[1]] += bonus[0]
        return parameter


    def save_text(self):
        text = 'gold:'+str(self.gold)+';'
        if len(self.head) != 0:
            text += '\nhead:'+self.head[0].save_line()
        else:
            text += '\nhead:0;'
        if len(self.arms) != 0:
            text += '\narms:'+self.arms[0].save_line()
        else:
            text += '\narms:0;'
        if len(self.body) != 0:
            text += '\nbody:'+self.body[0].save_line()
        else:
            text += '\nbody:0;'
        if len(self.legs) != 0:
            text += '\nlegs:'+self.legs[0].save_line()
        else:
            text += '\nlegs:0;'
        if len(self.weapon) != 0:
            text += '\nweapon:'+self.weapon[0].save_line()+'\n'
        else:
            text += '\nweapon:0;\n'
        return text

    def load_item(self, temp):
        if temp[0] == 'gold':
            self.gold = int(temp[1])
        elif temp[1] != '0':

            x = Item()
            x.load(temp[1])

            if temp[0] == 'head':
                self.head = [x]

            if temp[0] == 'arms':
                self.arms = [x]

            if temp[0] == 'body':
                self.body = [x]

            if temp[0] == 'legs':
                self.legs = [x]

            if temp[0] == 'weapon':
                self.weapon = [x]
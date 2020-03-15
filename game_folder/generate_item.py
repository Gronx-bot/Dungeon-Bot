import numpy

from game_folder.game_classes.dungeon_classes import Item
import game_folder.generate_dungeon
from game_folder.game_classes.damage_types import Damage




def random_consumable(not_random=''):
    result = Item()
    result.type = 'consumable'

    consumables = ['potion of healing', 'great potion of healing', 'scroll of teleportation', 'map']
    
    if not_random in consumables:
        result.description = not_random
        if not_random == 'potion of healing':
            result.effect = 'healing'
            result.add = 4
        if not_random == 'great potion of healing':
            result.effect = 'healing'
            result.add = 7
        if not_random in ['scroll of teleportation','map']:
            result.effect = 'travel'

    else:
        roll = numpy.random.randint(low=0, high=len(consumables))
        result.description = consumables[roll]
        if roll < 2:
            result.effect = 'healing'
            if roll == 0:
                result.add = 4
            if roll == 1:
                result.add = 7
        if roll == 2 or roll == 3:
            result.effect = 'travel'

    return result


def random_stats(role='warrior'):
    if role == 'warrior':
        weapons = ['sword', 'shield', 'plate', 'mail', 'axe', 'mace', 'spear', 'warhammer', 'maul', \
        'glaive', 'halberd', 'scimitar', 'dagger']
    if role == 'mage':
        weapons = ['cap', 'hood', 'hat', 'robe', 'stick', 'staff', 'wand', 'rod', 'sword', \
        'mantle', 'cloak', 'ring']


    result = Item()

    roll = numpy.random.randint(low=0, high=len(weapons))
    if weapons[roll] in ['hat', 'hood', 'robe', 'mantle', 'cloak']:
        result.description = game_folder.generate_dungeon.random_material(weapons[roll], fabric=True)
    else:
        result.description = game_folder.generate_dungeon.random_material(weapons[roll], metal=True)
    result.type = 'stats'

    roll_stat = numpy.random.randint(low=0, high=3)
    roll_add = numpy.random.randint(low=1, high=5)
    if roll_stat == 0:
        result.effect = 'strength'
        result.add = roll_add
    if roll_stat == 1:
        result.effect = 'intellect'
        result.add = roll_add
    if roll_stat == 2:
        result.effect = 'endurance'
        result.add = roll_add

    return result


def random_equipment(not_random=''):

    weapons = ['longsword', 'shortsword', 'greatsword', 'battleaxe', 'handaxe', 
        'glaive', 'halberd', 'twin swords', 'spear', 'dagger', 'rapier', 'trident', 
        'mace', 'warhammer', 'maul', 'scimitar', 'club', 'claimore', 'zweihander', 
        'estoc', 'katana', 'falchion', 'sabre', 'staff']


    head_arcane = ['cap', 'wizzard hat']
    head_physical = ['mail coif', 'great helm', 'sallet', 'barbute', 'close helm', 'foil hat']

    body_arcane = ['hood', 'robe', 'mantle', 'cloak']
    body_physical = ['plate armor', 'mail shirt', 'breastplate', 'brigandine', 'cuirass']

    arms = ['gloves', 'mittens', 'gauntlets']

    legs = ['greaves', 'pants', 'trousers', 'shirts']

    result = Item()
    result.type = 'equipable'
    damage_type = Damage(numpy.random.randint(low=0, high=len(Damage))).value

    roll_meta = numpy.random.randint(low=0, high=5)
    if roll_meta == 0 or not_random == 'weapon':
        roll = numpy.random.randint(low=0, high=len(weapons))
        result.description = game_folder.generate_dungeon.random_material(weapons[roll], metal=True)
        result.effect = 'weapon'

        min_dmg = numpy.random.randint(low=1, high=3)
        max_dmg = numpy.random.randint(low=3, high=6)
        dmg = str(min_dmg)+';'+str(max_dmg)
        result.add = [dmg, damage_type]


    elif roll_meta == 1 or not_random == 'head':
        head = head_arcane+head_physical
        roll = numpy.random.randint(low=0, high=len(head))
        if head[roll] in head_arcane:
            result.description = game_folder.generate_dungeon.random_material(head[roll], fabric=True)
        else:
            result.description = game_folder.generate_dungeon.random_material(head[roll], metal=True)
        result.effect = 'head'
        prot = round(numpy.random.rand()/4,2)
        result.add = [prot, damage_type]


    elif roll_meta == 2 or not_random == 'body':
        body = body_arcane+body_physical
        roll = numpy.random.randint(low=0, high=len(body))
        if body[roll] in body_arcane:
            result.description = game_folder.generate_dungeon.random_material(body[roll], fabric=True)
        else:
            result.description = game_folder.generate_dungeon.random_material(body[roll], metal=True)
        result.effect = 'body'
        prot = round(numpy.random.rand()/2,2)
        result.add = [prot, damage_type]


    elif roll_meta == 3 or not_random == 'arms':
        roll = numpy.random.randint(low=0, high=len(arms))
        if arms[roll] == 'gauntlets':
            result.description = game_folder.generate_dungeon.random_material(arms[roll], metal=True)
        else:
            result.description = game_folder.generate_dungeon.random_material(arms[roll], fabric=True)
        result.effect = 'arms'
        prot = round(numpy.random.rand()/4,2)
        result.add = [prot, damage_type]


    elif roll_meta == 4 or not_random == 'legs':
        roll = numpy.random.randint(low=0, high=len(legs))
        if legs[roll] == 'greaves':
            result.description = game_folder.generate_dungeon.random_material(legs[roll], metal=True)
        else:
            result.description = game_folder.generate_dungeon.random_material(legs[roll], fabric=True)
        result.effect = 'legs'
        prot = round(numpy.random.rand()/4,2)
        result.add = [prot, damage_type]

    return result


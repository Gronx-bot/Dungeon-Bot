from enum import Enum

class Damage(Enum):
    FIRE = 0
    PIERCING = 1
    BLUDGEONING = 2
    SLASHING = 3
    POISON = 4
    HOLY = 5
    NECROTIC = 6
    ARCANE = 7
    PSIONIC = 8
    LIGHTNING = 9



def determine_damage_type(desc):
    damage_types = {
        'fire': Damage.FIRE,
        'piercing': Damage.PIERCING,
        'bludgeoning': Damage.BLUDGEONING,
        'slashing': Damage.SLASHING,
        'poison': Damage.POISON,
        'holy': Damage.HOLY,
        'necrotic': Damage.NECROTIC,
        'arcane': Damage.ARCANE,
        'psionic': Damage.PSIONIC,
        'lightning': Damage.LIGHTNING
    }

    lines = desc.split('\n')
    attack = False
    vulnerability = [0]*len(Damage)
    resistance = [0]*len(Damage)
    for line in lines:
        temp = line.split('=')
        if temp[0] == 'attack':
            attack = damage_types[temp[1]].value
        if temp[0] == 'vulnerability':
            vulnerability[damage_types[temp[1]].value] = 0.5
        if temp[0] == 'resistance':
            resistance[damage_types[temp[1]].value] = 0.5

    return attack, vulnerability, resistance


def determine_damage_type_from_weapon(weapon):
    weapons = {
        Damage.SLASHING: ['longsword', 'shortsword', 'greatsword', 'battleaxe', 'handaxe', 
                          'glaive', 'halberd', 'twin swords', 'claimore', 'zweihander', 
                          'katana', 'falchion', 'sabre'],
        Damage.PIERCING: ['spear', 'dagger', 'rapier', 'trident', 'estoc'],
        Damage.BLUDGEONING: ['mace', 'warhammer', 'maul', 'scimitar', 'club', 'staff']
        }


    if weapon in weapons[Damage.SLASHING]:
        return Damage.SLASHING.value
    if weapon in weapons[Damage.PIERCING]:
        return Damage.PIERCING.value
    if weapon in weapons[Damage.BLUDGEONING]:
        return Damage.BLUDGEONING.value


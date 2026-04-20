from math import ceil


STAT_CHOICES = ("STR", "DEX", "CON", "WIS", "INT", "CHA")

DAMAGE_TYPES = [
    "piercing",
    "slashing",
    "bludgeoning",
    "fire",
    "lightning",
    "radiant",
    "cold",
    "psychic",
    "acid",
    "necrotic",
    "thunder",
    "poison",
    "force",
]

STUN_EFFECT_TYPE = "Stun Effect"
PARALYZE_EFFECT_TYPE = "Paralyze Effect"
DOT_EFFECT_TYPE = "DOT Effect"
BLINDED_EFFECT_TYPE = "Blinded Effect"
RESTRAINED_EFFECT_TYPE = "Restrained Effect"
INVISIBLE_EFFECT_TYPE = "Invisible Effect"
PETRIFIED_EFFECT_TYPE = "Petrified Effect"
POISONED_EFFECT_TYPE = "Poisoned Effect"
PRONE_EFFECT_TYPE = "Prone Effect"
TYPE_RESISTANCE_TYPE = "Type Resistance"
TYPE_IMMUNITY_TYPE = "Type Immunity"
TYPE_VULNERABILITY_TYPE = "Type Vulnerability"

EFFECT_TYPES = [
    STUN_EFFECT_TYPE,
    PARALYZE_EFFECT_TYPE,
    DOT_EFFECT_TYPE,
    BLINDED_EFFECT_TYPE,
    RESTRAINED_EFFECT_TYPE,
    INVISIBLE_EFFECT_TYPE,
    PETRIFIED_EFFECT_TYPE,
    POISONED_EFFECT_TYPE,
    PRONE_EFFECT_TYPE,
]

TARGET_ADVANTAGE_SET = {
    PRONE_EFFECT_TYPE,
    RESTRAINED_EFFECT_TYPE,
    BLINDED_EFFECT_TYPE,
    STUN_EFFECT_TYPE,
    PARALYZE_EFFECT_TYPE,
}

TARGET_DISADVANTAGE_SET = {INVISIBLE_EFFECT_TYPE}

SELF_DISADVANTAGE_SET = {
    PRONE_EFFECT_TYPE,
    POISONED_EFFECT_TYPE,
    BLINDED_EFFECT_TYPE,
    RESTRAINED_EFFECT_TYPE,
}

SELF_ADVANTAGE_SET = {INVISIBLE_EFFECT_TYPE}

AOE_PERCENT_HIT_MAP = {
    "15 ft. line": lambda x: max(ceil(x * 0.15), 2),
    "20 ft. line": lambda x: max(ceil(x * 0.25), 2),
    "30 ft. line": lambda x: max(ceil(x * 0.25), 2),
    "40 ft. line": lambda x: max(ceil(x * 0.33), 2),
    "60 ft. line": lambda x: max(ceil(x * 0.33), 2),
    "90 ft. line": lambda x: max(ceil(x * 0.33), 2),
    "100 ft. line": lambda x: max(ceil(x * 0.33), 2),
    "120 ft. line": lambda x: max(ceil(x * 0.33), 2),
    "5 ft. sphere": lambda x: 1,
    "10 ft. sphere": lambda x: max(ceil(x * 0.1), 1),
    "15 ft. sphere": lambda x: max(ceil(x * 0.33), 1),
    "20 ft. sphere": lambda x: max(ceil(x * 0.33), 2),
    "30 ft. sphere": lambda x: max(ceil(x * 0.5), 2),
    "10 ft. radius": lambda x: max(ceil(x * 0.25), 1),
    "20 ft. radius": lambda x: max(ceil(x * 0.33), 1),
    "30 ft. radius": lambda x: max(ceil(x * 0.5), 1),
    "60 ft. radius": lambda x: max(ceil(x * 0.66), 1),
    "120 ft. radius": lambda x: max(ceil(x * 1.0), 1),
    "15 ft. cone": lambda x: max(ceil(x * 0.25), 1),
    "30 ft. cone": lambda x: max(ceil(x * 0.33), 1),
    "60 ft. cone": lambda x: max(ceil(x * 0.5), 1),
    "90 ft. cone": lambda x: max(ceil(x * 0.5), 1),
    "120 ft. cone": lambda x: max(ceil(x * 1.0), 1),
    "10 ft. radius cube": lambda x: max(ceil(x * 0.2), 1),
    "20 ft. radius cube": lambda x: max(ceil(x * 0.3), 1),
    "30 ft. radius cube": lambda x: max(ceil(x * 0.5), 1),
    "10 ft. cube": lambda x: max(ceil(x * 0.2), 1),
    "20 ft. cube": lambda x: max(ceil(x * 0.3), 1),
    "30 ft. cube": lambda x: max(ceil(x * 0.5), 1),
    "10 ft. cylinder": lambda x: max(ceil(x * 0.2), 1),
    "20 ft. cylinder": lambda x: max(ceil(x * 0.33), 2),
    "30 ft. cylinder": lambda x: max(ceil(x * 0.5), 2),
}

AOE_TYPES = list(AOE_PERCENT_HIT_MAP.keys())

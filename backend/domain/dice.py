from random import randint


def calc_roll(dice):
    total = 0
    for max_roll, num_dice in dice.items():
        total += sum(randint(1, int(max_roll)) for _ in range(int(num_dice)))
    return total


def d20():
    return randint(1, 20)


def parse_dice_str(dice_str):
    if dice_str is None or dice_str == "":
        return None
    split_char = " "
    for char in ",+":
        if char in dice_str:
            split_char = char
            break
    split_str = dice_str.split(split_char)

    dice_dict = {}
    for entry in split_str:
        entry = entry.strip()
        if not entry:
            continue
        if "d" not in entry:
            dice_dict[1] = int(entry)
            continue
        num_dice, num_sides = entry.split("d", 1)
        dice_dict[int(num_sides)] = int(num_dice)
    return dice_dict


def serialize_dice(dice):
    if dice is None:
        return None
    return {str(k): v for k, v in dice.items()}

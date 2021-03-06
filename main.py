import json
import math
import random

data = json.load(open('data.json'))

# Create final variables for battle index
LEFT = 0
MID_LEFT = 1
MID_RIGHT = 2
RIGHT = 3

index_position = {0: "LEFT", 1: "MID LEFT", 2: "MID RIGHT", 3: "RIGHT"}

# Create the cogs with health
cogs = [None, None, None, None]


# ======= Cog Class =======
class Cog:
    def __init__(self, level, index=0, exe=False, lured=False, soaked=False, pres_lure=False, pres_squirt=False):
        self.level = level
        self.exe = exe
        self.lured = lured
        self.pres_lure = pres_lure
        self.soaked = soaked
        self.defense = 0
        self.index = index
        self.lured_rounds = 0
        self.alive = True
        self.prev_attack = []
        # If the cog is an executive set health * 1.5
        if exe:
            self.health = (data['cogs']['health'][str(level)] * 1.5)
            self.defense = data['cogs']['exe_defense'][level - 1]
        else:
            self.health = data['cogs']['health'][str(level)]
            self.defense = data['cogs']['cog_defense'][level - 1]
        # If cog is soaked with pres squirt
        if soaked and pres_squirt:
            self.defense -= 20

    def update_round(self):
        if self.lured:
            self.lured_rounds += 1


# ======= Battle State Class =======
class BattleState:
    def __init__(self, _cogs):
        self.cogs = _cogs
        self.event_logs = []


def get_damage(track, level):
    return data['gags']['tracks'][track][level - 1]


def get_accuracy(track, level, cog, track_exp=8, bonus=0, _pres=False):
    if cog.lured:
        if track == "drop" or track == "lure" or track == "trap":
            return 0
        if cog.pres_lure:
            lure_decay = (cog.lured_rounds - 1) * 5
        else:
            lure_decay = cog.lured_rounds * 5
        print(lure_decay)
        _accuracy = 100 - lure_decay
        if _accuracy > 95:
            _accuracy = 95
        return _accuracy
    else:
        accuracies = data['gags']['accuracy']
        if track == "lure":
            base_accuracy = 50 + (10 * math.floor(level / 2))
        else:
            base_accuracy = accuracies[track]
        if track == "drop" and _pres:
            base_accuracy += 20
        calculated_accuracy = base_accuracy + (track_exp - 1) * 10 - cog.defense + (bonus * 20)
        if calculated_accuracy > 95:
            calculated_accuracy = 95
        return calculated_accuracy
    return 0


def squirt_attack(_target, _state, _pres):
    if _pres:
        if _target.index != LEFT and _target.index != RIGHT:
            _state.cogs[_target.index - 1].soaked = True
            _state.cogs[_target.index].soaked = True
            _state.cogs[_target.index + 1].soaked = True
        elif _target.index == LEFT:
            _state.cogs[_target.index].soaked = True
            _state.cogs[_target.index + 1].soaked = True
        elif _target.index == RIGHT:
            _state.cogs[_target.index - 1].soaked = True
            _state.cogs[_target.index].soaked = True
    elif not _pres:
        _state.cogs[_target.index].soaked = True


def lure_attack(_cog, _pres):
    if _pres:
        _cog.lured = True
        _cog.pres_lure = True
    else:
        _cog.lured = True


def attack_cogs(_attacks, _targets, _state):
    current_attacks = []
    # Cycle through gag turn order
    # Check if cogs are dead
    #    Process attacks by track
    #       Zap will be the hardest to determine (since targets are defined by order and initial target
    #    Group attacks with bonus damage
    #           Damage cogs per round
    #           Set dead cogs


def attack_cog(_track, _level, _target, _state, _pres):
    gag_damages = data['gags']['tracks']
    base_damage = gag_damages[_track][_level - 1]

    for _cog in _target:
        if _cog.lured and _cog.pres_lure:
            total_damage = math.ceil(base_damage * 1.65)
        elif _cog.lured and not _cog.pres_lured:
            total_damage = math.ceil(base_damage * 1.5)
        else:
            total_damage = base_damage

        accuracy = get_accuracy(_track, _level, _cog)
        if accuracy == 0:
            total_damage = 0

        _cog.prev_attack.append({"track": _track, "damage": total_damage})

        _cog.health -= total_damage
        _state.event_logs.append(f"Cog Level {_cog.level} was attacked with a {_track} gag at level {_level}"
                                 f" | Accuracy: {accuracy}, Gag Pres: {_pres}")
        if _track == "lure":
            lure_attack(_cog, _pres)
        elif _track == "squirt":
            squirt_attack(_cog, _state, _pres)
            _cog.lured = False


def setup_state(_cogs, _lured, _soaked, _pres_squirt, _pres_lure):
    # Check if cogs are lured
    index = 0
    for value in _lured:
        if value == 1 and _pres_lure:
            _cogs[index].lured = True
            _cogs[index].pres_lured = True
        elif value == 1 and not _pres_lure:
            _cogs[index].lured = True
        index += 1
    # Check if cogs are soaked
    index = 0
    for value in _soaked:
        if value == 1:
            _cogs[index].soaked = True
        index += 1
    return BattleState(_cogs)


def update_state(_state):
    bonus_damage = {"sound": 0, "squirt": 0, "throw": 0, "drop": 0}
    for _cog in _state.cogs:
        if _cog.prev_attack is not None:
            _attk_arr = []
            _bonus_trk = []
            for _atk in _cog.prev_attack:
                if _atk['track'] not in _attk_arr:
                    _attk_arr.append(_atk['track'])
                else:
                    _bonus_trk.append(_atk['track'])
            for _track in _bonus_trk:
                for _atk in _cog.prev_attack:
                    if _atk['track'] == _track:
                        bonus_damage[_track] += _atk['damage']
    print(bonus_damage)

    for _cog in _state.cogs:
        _cog.lured_rounds += 1
        _cog.prev_attack = []


def close_state(_state):
    # Remove Cogs
    for x in range(len(_state.cogs)):
        _state.cogs[x] = None


def print_state(_state):
    for _cog in _state.cogs:
        if _cog.prev_attack is not None:
            print(_cog.prev_attack)
    for _cog in _state.cogs:
        print(f"Cog Level: {_cog.level} | Cog Health: {_cog.health} | Lured: {_cog.lured} | Soaked: {_cog.soaked}"
              f" | Pres Lure: {_cog.pres_lure} | Lured Rounds: {_cog.lured_rounds} | Position: {index_position[_cog.index]}")


def get_cogs():
    _levels = [0, 0, 0, 0]
    _lured = [0, 0, 0, 0]
    # Get Cog Levels
    _levels_str = input("Levels: ")
    _levels_str = _levels_str.split()
    for x in range(4):
        _levels[x] = int(_levels_str[x])
    # Get Lured Cogs
    _lured_str = input("Lured: ")
    for x in range(4):
        _lured[x] = int(_lured_str[x])
    # Setup the state
    _state = setup_state(
        [Cog(_levels[0], LEFT), Cog(_levels[1], MID_LEFT), Cog(_levels[2], MID_RIGHT), Cog(_levels[3], RIGHT)],
        _lured, [0, 0, 0, 0], 0, True)

    return _state


if __name__ == '__main__':

    state = get_cogs()
    # attack_cog("lure", 6, state.cogs, state, True)
    attack_cog("squirt", 5, [state.cogs[LEFT]], state, False)
    attack_cog("squirt", 5, [state.cogs[LEFT]], state, False)

    print_state(state)
    update_state(state)
    close_state(state)

    for event in state.event_logs:
        print(event)

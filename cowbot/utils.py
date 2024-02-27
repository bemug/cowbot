import subprocess
import pickle
import pathlib

from enum import Enum
from datetime import datetime

class Decoration:
    def __init__(self, color: str, icon: str):
        self.color = color
        self.icon = icon

save_path = pathlib.Path(str(pathlib.Path(__file__).parent.resolve()) + "/../saves")

ERR: str = "BAH!"
colors_reset : str = "\x03" #Reset
#See https://modern.ircdocs.horse/formatting.html for formatting
#See https://defs.ircdocs.horse/info/formatting for client support
decorations = {
    "hp" : Decoration("\x0304", "♥"), #Red
    "exp" : Decoration("\x0302", "✦"), #Blue
    "dmg" : Decoration("\x0307", "✸"), #Orange
    "cash" : Decoration("\x0342", "$"), #Custom yellow, as default is too bright on some white themes
    "arm" : Decoration("\x0314", "⛨"), #Grey
    "crit" : Decoration("\x0305", "%‼"), #Brown
    "miss" : Decoration("\x0303", "%↯"), #Green
}


def decor_str(str: str, decor : Decoration, icon = True) -> str :
    decor_icon = ""
    if icon:
        decor_icon = decor.icon
    return decor.color + str + decor_icon + colors_reset


def list_str(list) -> str :
    if len(list) == 0:
        return ""
    if len(list) == 1:
        return str(list[0])
    ret_str = ", ".join(str(elem) for elem in list)
    last_sep = ret_str.rfind(", ")
    return ret_str[:last_sep] + " et" + ret_str[last_sep + 1:]


def trace(msg):
    #Remove irc colors from traces
    for decor in decorations.values():
        msg = msg.replace(decor.color, "")
    now = datetime.now()
    print("[" + str(now) + "] " + msg)


def replace_by_none(list, elem):
    list[:] = [None if x == elem else x for x in list]

def append_in_none(list, elem, nb_max):
    nb_elem = sum(x != None for x in list)
    if nb_elem >= nb_max:
        raise ValueError #TODO proper errors names
    for i, value in enumerate(list[:]):
        if value == None:
            list[i] = elem
            return
    list.append(elem)

def git_version():
    try:
        #SHA1 and date
        version = subprocess.check_output(['git', 'show', '--no-patch', '--format=%ci : %h']).decode('ascii').strip()
        #Dirty status
        dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no']).decode('ascii').strip()
        if dirty:
            version += "-dirty"
    except:
        version = "Version inconnue"
    return version

def save_save(obj, prefix):
    save_path.mkdir(exist_ok=True)
    now = datetime.now()
    fmt = "%Y-%m-%d"
    pickle.dump(obj, open(f"{str(save_path)}/{prefix}-{now.strftime(fmt)}.pkl", "wb"))

def load_save(prefix):
    last_save = list(save_path.glob(f"{prefix}-*.pkl"))[0]
    trace(f"Loading file {last_save.name}")
    return pickle.load(open(str(last_save), "rb"))


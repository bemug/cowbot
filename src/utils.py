from enum import Enum
from datetime import datetime

class Decoration:
    def __init__(self, color: str, icon: str):
        self.color = color
        self.icon = icon


ERR: str = "BAH!"
colors_reset : str = "\x03" #Reset
#See https://modern.ircdocs.horse/formatting.html for formatting
#See https://defs.ircdocs.horse/info/formatting for client support
decorations = {
    "hp" : Decoration("\x0304", " pv"), #Red
    "exp" : Decoration("\x0302", " xp"), #Blue
    "dmg" : Decoration("\x0307", " dgt"), #Orange
    "cash" : Decoration("\x0342", " $"), #Custom yellow, as default is too bright on some white themes
    "arm" : Decoration("\x0314", " arm"), #Grey
    "crit" : Decoration("\x0304", " %crit"), #Red
    "miss" : Decoration("\x0303", " %esq"), #Green
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

def append_in_none(list, elem):
    for i, value in enumerate(list[:]):
        if value == None:
            list[i] = elem
            return
    list.append(elem)

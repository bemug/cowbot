from datetime import datetime


#See https://modern.ircdocs.horse/formatting.html for formatting
#See https://defs.ircdocs.horse/info/formatting for client support
colors = {
    "red": "\x0304",
    "green": "\x0309",
    "blue": "\x0302",
    "yellow": "\x0342", #Default yellow is too bright on some white themes
    "orange": "\x0307",
    "reset": "\x03",
}

icons = {
    "hp": " ᴘᴠ",
    "exp": " ᴇxᴘ",
    "dmg": " ᴅᴍɢ",
    "cash": " $",
    "arm": " ᴀʀᴍ",
}

ERR: str = "BAH!"

def list_str(list) -> str :
    if len(list) == 0:
        return ""
    if len(list) == 1:
        return str(list[0])
    ret_str = ", ".join(str(elem) for elem in list)
    last_sep = ret_str.rfind(", ")
    return ret_str[:last_sep] + " et" + ret_str[last_sep + 1:]


def trace(msg):
        now = datetime.now()
        print("[" + str(now) + "] " + msg)


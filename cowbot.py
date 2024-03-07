import configparser
import sys
from cowbot.bot import Bot

def main():
    config_file = "config.cfg"
    config = configparser.ConfigParser()
    try:
        config.read_file(open(config_file, "r"))
    except FileNotFoundError as e:
        print(f"Configuration file '{config_file}' does not exist")
        sys.exit(1)
    try:
        cfg = config['config']
    except KeyError as e:
        print(f"Configuration section '[{e.args[0]}]' not defined in {config_file}")
        sys.exit(1)

    try:
        bot = Bot(cfg['channel'], cfg['nickname'], cfg['realname'], cfg['server'], cfg.getint('port'), cfg['password'], cfg['admin']) #type: ignore
    except KeyError as e:
        print(f"Configuration parameter '{e.args[0]}' not defined in {config_file}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration parameter 'port' must be a number")
        sys.exit(1)

    bot.debug_start()
    bot.start()


if __name__ == "__main__":
    main()

<div align="center">
  <img alt="Cowbot icon" src="https://github.com/bemug/cowbot/assets/5015627/6c55b1d9-b2eb-464f-861a-4ef1461e8e02" width="125" />
</div>

# Cowbot
Cowbot is a text-based RPG over IRC taking place in the wild west era. Players have to defend the local saloon from intruders.

## Instalation
Using virtual environements is recommended, but not mandatory.
```
python -m venv env
. env/bin/activate
```
```
pip install -r requirements.txt
```

## Configuration
TODO

## Usage
```
python src/bot.py
```

## Development
This project uses mypy to check for python errors.
```
pip -r requirements/dev.txt
mypy --strict src/*.py
```

<sub><sup>Cowboy icons created by shmai - <a href="https://www.flaticon.com/free-icons/cowboy" title="cowboy icons">Flaticon</a></sub></sup>

<div align="center">
  <img alt="Cowbot icon" src="https://github.com/bemug/cowbot/assets/5015627/6c55b1d9-b2eb-464f-861a-4ef1461e8e02" width="100" />
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
Edit run.sh with your arguments, or run directly through command line.
```
python cowbot.py '<IRC network>' '<channel>' <bot name>'
```

## Running
```
python cowbot.py
```

## Development
This project uses mypy to check for python errors.
```
pip install -r requirements/dev.txt
mypy --strict cowbot/*.py
```

<sub><sup>Cowbot icon created by shmai - <a href="https://www.flaticon.com/authors/shmai" title="shmai on Flaticon">Flaticon</a></sub></sup>

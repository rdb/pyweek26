Let There Be Light
==================

This is an entry in [PyWeek 26](https://pyweek.org/26/), with the theme "Flow".

[Click here to go to the PyWeek entry page.](https://pyweek.org/e/rdb26/)

![Screenshot](https://pyweek.org/media/dl/26/rdb26/screenshot-day7.jpg)

Dependencies
------------

This game requires Python 3.  I recommend installing the dependencies (Panda3D 1.10 and numpy) via pip, using the command:

```
pip install -r requirements.txt
```

Running the game
----------------

Open a terminal window, "cd" to the game directory and run:

```
python run_game.py
```

Playing the game
----------------

The game requires the use of keyboard and mouse.  Use the arrow keys to pan
the camera around the map.  To make a power line, click the source and then
click where you want to target it to.  Use escape to cancel.

Troubleshooting
---------------

If you can't get the game to run properly, edit `config.prc` to tweak the
settings.  In particular, if your driver refuses to open a window, remove the
line that says `framebuffer-srgb true`.  The game will look dark, however.

Controls
--------

* `1`: switch to the connection tool.
* `2`: switch to the upgrade tool.  Only to be used on pylons.
* `3`: switch to the erase tool.  Only to be used on pylons.
* The mouse wheel zooms in and out.
* Arrow keys navigate around the map.
* `space`: toggles pause.
* `tab`: cycles the camera focus between unpowered towns.
* `shift-s`: takes a screenshot and save it to the current directory.
* `shift-q`: immediately exits the game.

And these are for developer / testing use only:

* `shift-l`: dumps the scene graph to the console.
* `shift-p`: attaches to a PStats server; requires `want-pstats true` in config.prc.
* `shift-t`: spawns a new town in a random location.
* `shift-f`: switches the game speed to 10x until you change it again.

Acknowledgements
----------------

The music is Contemplation by OpenGameArt user Joth.

Many thanks to the people who keep putting up CC0 sound effects online.

Many thanks to fireclaw, wezu and others for their help testing the game.

Many thanks to those in the PyWeek team and all the other entrants for contributing to make this an awesome challenge, and (hopefully) for taking the time to run and review my game.

~rdb

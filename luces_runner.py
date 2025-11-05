#!/usr/bin/env python3
"""Controller for Luces.

This automates Luces, by managing the hours and a playlist.

Copyright © 2020-21, Plantarium Società Agricola
"""

import time
import datetime
import pathlib
import astral
import humanized_opening_hours as hoh
import subprocess

print(pathlib.PurePath(__file__).name)
print(f'Copyright © 2020-{datetime.date.today().year - 2000}, ', end='')
print('Plantarium Società Agricola\n')

home = str(pathlib.Path.home())

log = pathlib.PurePath(__file__).stem + '.log'
media_dir = f'{home}/src/Luces/Media'

location = astral.Location(('Seregno', 'Lombardy', 45.64677, 9.22676,
    'Europe/Rome', 0))
opening_hours = hoh.OHParser(
        'Mo-Fr 09:00-12:30,14:00-19:30; Sa 09:00-19:30; Su 09:00-19:00')

def get_hour():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))


def get_day():
    return datetime.date.today()


def get_sunset():
    return location.sun(date=today, local=True)['sunset']


now = get_hour()
today = get_day()
sunset = get_sunset()

with open(f'{media_dir}/luces.list', 'r') as playlist:
    projects = [project.strip() for project in playlist.readlines()]


project_counter = 0
def get_project():
    global project_counter
    if project_counter < len(projects):
        project = projects[project_counter]
        project_counter += 1
    else:
        project = projects[0]
        project_counter = 1
    return project


def write_log(message):
    with open(log, 'a') as f:
        f.write(f'----- {str(datetime.datetime.now())}: {message}\n')


while True:
    if today != get_day(): # once a day, calculate sunset time
        today = get_day()
        sunset = get_sunset()

    if opening_hours.is_open():
        if now < sunset:
            write_log('PAUSE')
            with open(log, 'a') as f:
                subprocess.run([f'{home}/midi_file_player.py',
                    'src/Luces/Media/Silenzio.mid'], stdout=f, stderr=f)
            write_log('END PAUSE\n')
            now = get_hour()
        else:
            project = get_project()
            write_log(f'SHOW: {project}')
            with open(log, 'a') as f:
                subprocess.run([f'{home}/src/Luces/luces.py', media_dir,
                    project], stdout=f, stderr=f)
            with open(log, 'a') as f:
                subprocess.run([f'{home}/midi_file_player.py',
                    'src/Luces/Media/Silenzio.mid'], stdout=f, stderr=f)
            write_log('END SHOW\n')
            now = get_hour()
    else:
        time.sleep(1) # wait 1 second

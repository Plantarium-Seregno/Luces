#!/usr/bin/env python3

import datetime
import pathlib
import astral
import subprocess


home = str(pathlib.Path.home())

log = 'luces_runner.log'
media_dir = f'{home}/src/Luces/Media'

def get_hour():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))


location = astral.Location(('Seregno', 'Lombardy', 45.64677, 9.22676,
    'Europe/Rome', 0))
now = get_hour()
today = datetime.date.today()
sunset = location.sun(date=today, local=True)['sunset']
if today.weekday() < 7:
    closing_hour = datetime.datetime.combine(today, datetime.time(19, 20),
            datetime.timezone(datetime.timedelta(hours=1)))
else:
    closing_hour = datetime.datetime.combine(today, datetime.time(18, 50),
            datetime.timezone(datetime.timedelta(hours=1)))

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


while now < sunset:
    write_log('PAUSE')
    with open(log, 'a') as f:
        subprocess.run([f'{home}/midi_file_player.py',
            'src/Luces/Media/Silenzio.mid'], stdout=f, stderr=f)
    write_log('END PAUSE')
    now = get_hour()

while now < closing_hour:
    project = get_project()
    write_log(f'SHOW: {project}')
    with open(log, 'a') as f:
        subprocess.run([f'{home}/src/Luces/luces.py', media_dir, project],
                stdout=f, stderr=f)
    with open(log, 'a') as f:
        subprocess.run([f'{home}/midi_file_player.py',
            'src/Luces/Media/Silenzio.mid'], stdout=f, stderr=f)
    write_log('END SHOW')
    now = get_hour()

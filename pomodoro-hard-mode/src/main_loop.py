#!/usr/bin/env python3
import multiprocessing as mp
import subprocess
import time
import os
import signal
import logging
logging.basicConfig(format='%(levelname)s:%(process)d:%(asctime)s:::%(message)s', datefmt='%d-%b-%y_%H:%M:%S', level=logging.DEBUG)

import setproctitle

from statusbar_utils import display_status_bar
from common_utils import kill_all

dialog_message = "Break!!"
dialog_buttons = ["OK", "Snooze", "Finish"]
dialog_button_default = 2 # Snooze

cmd_dialog = "osascript -e 'tell app \"System Events\" to display dialog \"{}\" buttons {{\"{}\", \"{}\", \"{}\"}} default button {}'"
cmd_dialog = cmd_dialog.format(dialog_message, *dialog_buttons, dialog_button_default)
cmd_sound = "afplay /System/Library/Sounds/Tink.aiff"
cmd_sound_post_snooze = "afplay /System/Library/Sounds/Glass.aiff"
cmd_screen = "pmset displaysleepnow"

MAIN_LOOP_MINS=25
SNOOZE_MINS=5
SCREEN_OFF_SECONDS=10


def wait_for_mins(mins):
    statusbar_process = mp.Process(name='pomodoro_statusbar', target=display_status_bar, args = (mins,))
    statusbar_process.start()
    wait_for_secs(mins*60)
    statusbar_process.terminate()
    statusbar_process.join()


def wait_for_secs(secs):
    time.sleep(secs)


def get_decreasing_seq():
    minl = 1
    curr = 5
    while True:
        yield curr
        curr = max(curr-1, minl)


def command_make_sound():
    setproctitle.setproctitle(mp.current_process().name)
    for interval in get_decreasing_seq():
        # Start softly but go hard later.
        subprocess.run(cmd_sound, shell=True)
        wait_for_secs(interval)


def command_screen_off():
    setproctitle.setproctitle(mp.current_process().name)
    wait_for_secs(SCREEN_OFF_SECONDS)
    subprocess.run(cmd_screen, shell=True)
    command_sound_post_snooze_process = mp.Process(name='pomodoro_sound_post_snooze', target=command_sound_post_snooze)
    command_sound_post_snooze_process.start()


def command_sound_post_snooze():
    setproctitle.setproctitle(mp.current_process().name)
    wait_for_secs(SNOOZE_MINS*60)
    for i in range(10):
        subprocess.run(cmd_sound_post_snooze, shell=True)
        wait_for_secs(1)  


def process_result(res):
    stdout = res.stdout.decode("utf-8")
    if res.returncode == 0:
        if "Finish" in stdout:
            logging.info("Exiting!")
            os.kill(os.getppid(), signal.SIGTERM)
            kill_all()
            exit(0)
        if "OK" in stdout:
            wait_time_mins = MAIN_LOOP_MINS
        else:
            wait_time_mins = SNOOZE_MINS
    else:
        # No button was pressed and the dialog timed out.
        logging.warn('No button pressed!')
        wait_time_mins = SNOOZE_MINS
    return wait_time_mins


def start_main_loop():
    setproctitle.setproctitle(mp.current_process().name)
    logging.debug('Main loop process started.')
    wait_time_mins = MAIN_LOOP_MINS
    while True:
        wait_for_mins(wait_time_mins)
        command_make_sound_process = mp.Process(name='pomodoro_make_sound', target=command_make_sound)
        command_make_sound_process.start()
        # Just comment these 2 lines if you dont want the screen to be turned off.
        command_screen_off_process = mp.Process(name='pomodoro_screen_off', target=command_screen_off)
        command_screen_off_process.start()
        res = subprocess.run(cmd_dialog, shell=True, capture_output=True)
        command_make_sound_process.terminate()
        command_screen_off_process.terminate()
        command_make_sound_process.join()
        command_screen_off_process.join()
        wait_time_mins = process_result(res)
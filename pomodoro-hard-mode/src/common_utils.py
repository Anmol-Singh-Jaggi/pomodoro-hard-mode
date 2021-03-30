#!/usr/bin/env python3
import multiprocessing as mp
import logging
import time
import threading
import subprocess


def exec_command(cmd, ignore_error=True, stderr_fatal=True):
    res = subprocess.run(cmd, shell=True, capture_output=True)
    ret_code = res.returncode
    stdout = res.stdout.decode('utf-8')
    stderr = res.stderr.decode('utf-8')
    if not ignore_error and (ret_code != 0 or (stderr_fatal and len(stderr) > 0)):
        msg = 'Process exec failed for "{}": {}'.format(cmd, res)
        logging.error(msg)
    return res.returncode, stdout, stderr


def get_process_id(process_name, ignore_error=False):
    cmd = "ps -ef | grep '{}' | grep -v grep | awk '{{print $2}}'".format(process_name)
    res = exec_command(cmd)
    ret_code, stdout, stderr = res
    if ret_code != 0 or not stdout:
        msg = 'Unable to find process ID for "{}": {}'.format(process_name, res)
        if ignore_error:
            logging.debug(msg)
            pass
        else:
            logging.error(msg)
        return None
    return stdout.strip()


def pkill(process_name, ignore_error=False):
    # For some reason the `pkill` command fails sometimes.
    # Hence first finding the process ID and then killing it using `kill`
    logging.debug("Got request to kill '{}'".format(process_name))
    process_id = get_process_id(process_name, ignore_error)
    if not process_id:
        msg = 'Unable to kill "{}" as process ID is None'.format(process_name)
        if ignore_error:
            #logging.info(msg)
            pass
        else:
            logging.error(msg)
        return
    cmd = "kill " + process_id
    logging.debug("Killing '{}' with id '{}'".format(process_name, process_id))
    subprocess.run(cmd, shell=True, capture_output=True)


def kill_main_loop_recursive():
    logging.debug('Killing main loop and its children')
    pkill('pomodoro_make_sound', True)
    pkill('pomodoro_screen_off', True)
    pkill('pomodoro_statusbar', True)
    pkill('pomodoro_main_loop')


def kill_all():
    logging.debug('Killing everything')
    kill_main_loop_recursive()
    pkill('pomodoro_screen_state_observer')
    pkill('pomodoro_root_process')
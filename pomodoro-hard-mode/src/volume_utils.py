#!/usr/bin/env python3
import logging
from common_utils import exec_command


def get_set_volume_cmd_string(new_volume):
    sudo_passwd = get_sudo_password_from_file()
    cmd = 'echo "{}" | sudo -S osascript -e "set Volume {}"'
    cmd = cmd.format(sudo_passwd, new_volume)
    return cmd


def get_sudo_password_from_file():
    with open('password.txt', 'r') as file:
        return file.read().splitlines()[0].strip()


def store_current_volume(interprocess_dict):
    res = exec_command("osascript -e 'get volume settings'", False)
    ret, stdout, stderr = res
    if ret == 0:
        current_volume = stdout.split(",")[0].split(":")[1].strip()
        interprocess_dict['current_volume'] = current_volume
        logging.debug('Stored current volume = ' + str(current_volume))
    else:
        logging.error('Error in retrieving current volume ' + str(res))


def set_volume_to_max():
    cmd = get_set_volume_cmd_string(10)
    exec_command(cmd, False, False)


def restore_volume(interprocess_dict):
    current_volume = interprocess_dict.get('current_volume', None)
    if current_volume is None:
        logging.debug('current volume is none')
        return
    current_volume_rounded = round(int(current_volume)/10)
    cmd = get_set_volume_cmd_string(current_volume_rounded)
    exec_command(cmd, False, False)
    logging.debug('Setting current_volume to None from ' + str(current_volume))
    interprocess_dict['current_volume'] = None
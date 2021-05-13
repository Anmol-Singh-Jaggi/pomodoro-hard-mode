import logging
import subprocess


def exec_command(cmd, ignore_error=True, stderr_fatal=True):
    res = subprocess.run(cmd, shell=True, capture_output=True)
    ret_code = res.returncode
    stdout = res.stdout.decode('utf-8')
    stderr = res.stderr.decode('utf-8')
    if not ignore_error and (ret_code != 0 or (stderr_fatal and len(stderr) > 0)):
        logging.error(f'Process exec failed for "{cmd}": {res}')
    return res.returncode, stdout, stderr


def get_process_id(process_name, ignore_error=False):
    cmd = f"ps -ef | grep '{process_name}' | grep -v grep | awk '{{print $2}}'"
    res = exec_command(cmd)
    ret_code, stdout, stderr = res
    if ret_code != 0 or not stdout:
        msg = f'Unable to find process ID for "{process_name}": {res}'
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
    logging.debug(f"Got request to kill '{process_name}'")
    process_id = get_process_id(process_name, ignore_error)
    if not process_id:
        if not ignore_error:
            logging.error(f'Unable to kill "{process_name}" as process ID is None')
        return
    cmd = "kill " + process_id
    logging.debug(f"Killing '{process_name}' with id '{process_id}'")
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
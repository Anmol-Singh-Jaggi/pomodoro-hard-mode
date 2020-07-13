#!/usr/bin/env python3
'''
Run in background:
nohup python3 pomodoro.py &!
'''
import multiprocessing as mp
from threading import Event
import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)

import setproctitle

from screen_state_observer import start_screen_state_observer
from main_loop import start_main_loop


def main():
    # The default 'fork' is not compatible with ScreenStateObserver related OSX code.
    # No need once python is upgraded to 3.8+ on Mac since default is spawn since that version.
    mp.set_start_method('spawn')
    setproctitle.setproctitle("pomodoro_root_process")

    logging.info('Starting the root process...')

    interprocess_dict = mp.Manager().dict()

    screen_state_observer_process = mp.Process(name='pomodoro_screen_state_observer', target=start_screen_state_observer, args=(interprocess_dict,))
    screen_state_observer_process.start()

    main_loop_process = mp.Process(name='pomodoro_main_loop', target=start_main_loop, args=(interprocess_dict,))
    main_loop_process.start()

    # Keep the process running forever to avoid garbage collection of mp.Manager()
    # One of those few instances where we have to be aware of garbage collection in Python.
    Event().wait()


if __name__ == '__main__':
    main()

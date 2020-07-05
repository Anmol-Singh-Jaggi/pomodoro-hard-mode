#!/usr/bin/env python3
import multiprocessing as mp
import logging
import time
import threading

import setproctitle
import rumps


from common_utils import pkill


def start_timer(mins, app):
    while mins > 0:
        app.title = str(mins)
        time.sleep(60)
        mins -=1
    rumps.quit_application()


def quit_callback(_):
    logging.debug('Killing main loop and status bar only')
    pkill('pomodoro_main_loop')
    rumps.quit_application()


def display_status_bar(mins):
    setproctitle.setproctitle(mp.current_process().name)
    app = rumps.App(mp.current_process().name, icon='../static/tomato.png', menu=['Quit'], quit_button=None)
    app.menu['Quit'].set_callback(quit_callback)
    t1 = threading.Thread(target=start_timer, args=(mins, app,))
    t1.start()
    app.run()
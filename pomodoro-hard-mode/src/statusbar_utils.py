#!/usr/bin/env python3
import multiprocessing as mp
import time
import threading

import setproctitle
import rumps


def start_timer(mins, app):
    while mins > 0:
        app.title = str(mins)
        time.sleep(60)
        mins -=1
    rumps.quit_application()


def display_status_bar(mins):
    setproctitle.setproctitle(mp.current_process().name)
    app = rumps.App(mp.current_process().name, icon='../static/tomato.png')
    t1 = threading.Thread(target=start_timer, args=(mins, app,))
    t1.start()
    app.run()
#!/usr/bin/env python3
import multiprocessing as mp
import subprocess
import logging
import threading
logging.basicConfig(format='%(levelname)s:%(process)d:%(asctime)s:::%(message)s', datefmt='%d-%b-%y_%H:%M:%S', level=logging.DEBUG)
import Foundation
import AppKit
from PyObjCTools import AppHelper

import setproctitle

from main_loop import pkill, main_loop


class ScreenStateObserver(AppKit.NSObject):
    def screenOffHandler_(self, _):
        logging.debug('Killing main loop and its children')
        pkill('pomodoro_main_loop')
        pkill('pomodoro_make_sound')
        pkill('pomodoro_screen_off')
        pkill('pomodoro_statusbar')

    def screenOnHandler_(self, _):
        # Semaphore is required because this method is sometimes being called
        # twice in parallel when the screen unlocks.
        # This can cause 2 main loop processes to start at the same time due to
        # race conditions.
        # Dont know why this is happening; seems like a bug in OSX libraries.
        with self.screen_on_handler_semaphore:
            logging.debug('Starting main loop again')
            cmd = "ps -ef | grep 'pomodoro_main_loop' | grep -v grep | awk '{print $2}'"
            res = subprocess.run(cmd, shell=True, capture_output=True)
            if len(res.stdout) > 0:
                logging.error('Main loop already running!!')
                return
            main_loop_process = mp.Process(name='pomodoro_main_loop', target=main_loop)
            main_loop_process.start()


def start_screen_state_observer():
    '''
    Kill the main loop whenever screen turns off, so that we dont keep getting dialogs and sounds
    even when laptop is unattended.
    Start the main loop again once screen is on again.
    '''
    logging.info('ScreenStateObserver process started.')
    setproctitle.setproctitle(mp.current_process().name)
    nc = Foundation.NSDistributedNotificationCenter.defaultCenter()
    screen_state_observer = ScreenStateObserver.new()
    screen_state_observer.screen_on_handler_semaphore = threading.Semaphore()
    nc.addObserver_selector_name_object_(screen_state_observer, 'screenOffHandler:', 'com.apple.screenIsLocked', None)
    nc.addObserver_selector_name_object_(screen_state_observer, 'screenOnHandler:', 'com.apple.screenIsUnlocked', None)
    AppHelper.runConsoleEventLoop()
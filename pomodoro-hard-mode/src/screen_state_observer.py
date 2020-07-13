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

from main_loop import start_main_loop
from common_utils import kill_main_loop_recursive, get_process_id, pkill
from volume_utils import restore_volume


class ScreenStateObserver(AppKit.NSObject):
    def screenOffHandler_(self, _):
        kill_main_loop_recursive()

    def screenOnHandler_(self, _):
        # Semaphore is required because this method is sometimes being called
        # twice in parallel when the screen unlocks.
        # This can cause 2 main loop processes to start at the same time due to
        # race conditions.
        # Dont know why this is happening; seems like a bug in OSX libraries.
        # EDIT: What the hell even semaphore is not working!!
        with self.screen_on_handler_semaphore:
            pkill('pomodoro_sound_post_snooze', True)
            restore_volume(self.interprocess_dict)
            logging.debug('Starting main loop again')
            main_loop_process_id = get_process_id('pomodoro_main_loop', True)
            if main_loop_process_id:
                logging.error('Main loop already running with process id "{}"'.format(main_loop_process_id))
                return
            main_loop_process = mp.Process(name='pomodoro_main_loop', target=start_main_loop, args=(self.interprocess_dict,))
            main_loop_process.start()


def start_screen_state_observer(interprocess_dict):
    '''
    Kill the main loop whenever screen turns off, so that we dont keep getting dialogs and sounds
    even when laptop is unattended.
    Start the main loop again once screen is on again.
    '''
    logging.info('ScreenStateObserver process started.')
    setproctitle.setproctitle(mp.current_process().name)
    nc = Foundation.NSDistributedNotificationCenter.defaultCenter()
    screen_state_observer = ScreenStateObserver.new()
    screen_state_observer.screen_on_handler_semaphore = threading.Lock()
    screen_state_observer.interprocess_dict = interprocess_dict
    nc.addObserver_selector_name_object_(screen_state_observer, 'screenOffHandler:', 'com.apple.screenIsLocked', None)
    nc.addObserver_selector_name_object_(screen_state_observer, 'screenOnHandler:', 'com.apple.screenIsUnlocked', None)
    AppHelper.runConsoleEventLoop()
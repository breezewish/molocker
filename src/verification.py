#!/usr/bin/env python
# encoding: utf-8


import os
import sys
import time
import numpy
import thread
import inspect
import scipy.io as io

sys.path.insert(0, "../lib")
import Leap
from dollar import Recognizer

# src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
# arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
# sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

USAGE   = "usage: %prog [options] arg1 arg2"
VERSION = 'v1.0.0'
DEBUG = False
WINDOWS_PATH = 'C:\\molocker'
INTERVAL = 0.8


def verify(r, all_tip_position):
    """TODO: Docstring for verify.

    :r: TODO
    :all_tip_position: TODO
    :returns: TODO

    """
    temp = []

    for index in range(3):
        for item in range(5):
            temp = temp + all_tip_position[index][item]

    return r.recognize(temp)


def add_password(r, file_handler):
    """TODO: Docstring for verify.
    :returns: TODO

    """
    temp = io.loadmat(WINDOWS_PATH + '\\gestures\\' + file_handler)['all']

    r.addTemplate(file_handler, temp)

 

def approximate(position1, position2):
    """TODO: Docstring for approximate.

    :postion1: TODO
    :position2: TODO
    :returns: TODO

    """
    position = position1 - position2
    if position[0]**2 + position[1]**2 + position[2]**2 < 25:
        return True
    else:
        return False


def process_frame(frame, all_tip_position):
    """TODO: Docstring for process_frame.

    :frame: TODO
    :returns: TODO

    """
    if len(frame.fingers) == 0:
        return

    hand = frame.hands[0]

    for finger in hand.fingers:
        for index in range(5):
            all_tip_position[0][finger.type()].append((finger.tip_position[1], finger.tip_position[2]))
            all_tip_position[1][finger.type()].append((finger.tip_position[0], finger.tip_position[2]))
            all_tip_position[2][finger.type()].append((finger.tip_position[0], finger.tip_position[1]))

    return False


def check_motion(current_frame, all_tip_position):
    """TODO: Docstring for check_motion.

    :frame: TODO
    :returns: TODO

    """
    counter = 0
    hand = current_frame.hands[0]
    fingers = hand.fingers

    for index in range(5):
        if len(all_tip_position[index]) > 0 and approximate(fingers[index].tip_position, all_tip_position[index][-1]):
            counter = counter + 1

    if counter == 5:
        return False
    else:
        for finger in fingers:
            all_tip_position[finger.type()].append(finger.tip_position)

        return True


def unlock(r, controller, file_handler):
    """TODO: Docstring for unlock.

    :controller: TODO
    :returns: TODO

    """
    mark = True
    last_frame_id = 0
    temp = []

    all_tip_position = [[], [], []]
    for index in range(3):
        for item in range(5):
            all_tip_position[index].append([])

    temp = []
    for item in range(5):
        temp.append([])

    while True:
        current_frame = controller.frame()

        if current_frame.id == last_frame_id:
            continue

        last_frame_id = current_frame.id

        process_frame(current_frame, all_tip_position)

        hands_len = len(current_frame.hands)

        checked = check_motion(current_frame, temp)

        if checked == False and mark and hands_len:
            start_time = time.time()
            mark = False
        elif checked == False and mark == False and hands_len:
            interval = time.time() - start_time

            if interval > INTERVAL:
                return verify(r, all_tip_position)
        elif checked and hands_len:
            start_time = time.time()
            mark = True


def check_all_file():
    """TODO: Docstring for main.

    :returns: TODO

    """
    controller = Leap.Controller()

    all_files  = [os.path.splitext(x)[0] for x in os.listdir(WINDOWS_PATH + '\\gestures') if x[0] != '.']

    r = Recognizer()

    for a_file in all_files:
        add_password(r, a_file)

    return unlock(r, controller, a_file)


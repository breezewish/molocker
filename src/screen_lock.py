#!/usr/bin/env python
# encoding: utf-8


import os
import sys
import time
import json
import numpy
import struct
import thread
import inspect
import scipy.io as io
from optparse import OptionParser
from Tkinter import *

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


class Verification(Leap.Listener):

    """Docstring for Verification. """

    def on_connect(self, controller):
        """TODO: Docstring for on_connect.

        :controller: TODO
        :returns: TODO

        """
        with open(r'\\.\pipe\molocker_record', 'wb', 0) as pipe:
            pipe_str = "1"                                
            pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
            pipe.seek(0)



def get_options():
    """TODO: Docstring for get_options.
    :returns: TODO

    """
    parser = OptionParser(usage=USAGE, version=VERSION)

    parser.add_option('-n', '--name', action='store', type='string',
            help='User name.', dest='user_name')
    parser.add_option('-s', '--setting', action='store_true', dest='is_setting',
            help='Setting.')
    parser.add_option('-v', '--verify', action='store_true', dest='is_verify',
            help='Verivication.')

    return parser.parse_args()


def add_password(all_tip_position, user_name):
    """TODO: Docstring for verify.
    :returns: TODO

    """
    r = Recognizer()

    temp = []

    for index in range(3):
        for item in range(5):
            temp = temp + all_tip_position[index][item]

    r.addTemplate(user_name, temp)

    # for index, tip in enumerate(all_tip_position[0]):
        # r.addTemplate(user_name + 'yz' + str(index), tip)
    # for index, tip in enumerate(all_tip_position[1]):
        # r.addTemplate(user_name + 'xz' + str(index), tip)
    # for index, tip in enumerate(all_tip_position[2]):
        # r.addTemplate(user_name + 'xy' + str(index), tip)

    return r


def verify(r, all_tip_position, user_name):
    """TODO: Docstring for verify.

    :r: TODO
    :all_tip_position: TODO
    :returns: TODO

    """
    temp = []

    for index in range(3):
        for item in range(5):
            temp = temp + all_tip_position[index][item]

    (name, score) = r.recognize(temp)

    if name != user_name or score < 0.75:
        return False
    else:
        return True

    # for index, bone in enumerate(all_tip_position[0]):
        # (name, score) = r.recognize(bone)
        # if name != user_name + 'yz' + str(index) or score < 0.5:
            # print name, user_name + 'yz' + str(index)
            # return False

    # for index, bone in enumerate(all_tip_position[1]):
        # (name, score) = r.recognize(bone)
        # if name != user_name + 'xz' + str(index) or score < 0.5:
            # print name, user_name + 'xz' + str(index)
            # return False

    # for index, bone in enumerate(all_tip_position[2]):
        # (name, score) = r.recognize(bone)
        # if name != user_name + 'xy' + str(index) or score < 0.5:
            # print name, user_name + 'xy' + str(index)
            # return False

    return True


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


def set_password(controller, last_frame_id):
    """TODO: Docstring for set_password.

    :controller: TODO
    :returns: TODO

    """
    mark = True
    start_time = 0
    temp = []
    for item in range(5):
        temp.append([])

    all_tip_position = [[], [], []]
    for index in range(3):
        for item in range(5):
            all_tip_position[index].append([])

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
            if time.time() - start_time > INTERVAL:
                mdict = {}
                temp = []

                for index in range(3):
                    for item in range(5):
                        temp = temp + all_tip_position[index][item]

                mdict.setdefault('all', temp)

                return (all_tip_position, mdict)
        elif checked and hands_len:
            start_time = time.time()
            mark = True


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


def center_window(root, w=300, h=200):
    # get screen width and height
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    # calculate position x, y
    x = (ws/2) - (w/2)   
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))


def display_text(txt):
    """TODO: Docstring for display_text.

    :txt: TODO
    :returns: TODO

    """
    root = Tk()
    root.frame = Frame(root)
    root.frame.label = Label(root.frame, text=txt, justify="right")
    root.frame.label.pack(expand=YES)
    root.frame.label.grid()
    root.frame.grid()
    center_window(root, 500, 300)
    root.wm_attributes('-topmost',1)
    root.after(2000, lambda: root.destroy())
    root.mainloop()



def get_ready(controller, last_frame_id, options):
    """TODO: Docstring for get_ready.

    :controller: TODO
    :returns: TODO

    """
    mark = True
    start_time = 0

    all_tip_position = []
    for item in range(5):
        all_tip_position.append([])

    while True:
        current_frame = controller.frame()

        if current_frame.id == last_frame_id:
            continue

        last_frame_id = current_frame.id

        hands_len = len(current_frame.hands)

        checked = check_motion(current_frame, all_tip_position)

        if checked == False and mark and hands_len:
            start_time = time.time()
            mark = False
        elif checked == False and mark == False and hands_len:
            interval = time.time() - start_time

            if interval > INTERVAL:
                if not options.user_name:
                    options.user_name = 'default'

                with open(r'\\.\pipe\molocker_record', 'wb', 0) as pipe:
                    pipe_str = "2"                                
                    pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
                    pipe.seek(0)

                (first_tip_position, first_mdict) = set_password(controller, 0)

                first_recog = add_password(first_tip_position, options.user_name)

                break
        elif checked and hands_len:
            start_time = time.time()
            mark = True

    while True:
        current_frame = controller.frame()

        if current_frame.id == last_frame_id:
            continue

        last_frame_id = current_frame.id

        hands_len = len(current_frame.hands)

        checked = check_motion(current_frame, all_tip_position)

        if checked == False and mark and hands_len:
            start_time = time.time()
            mark = False
        elif checked == False and mark == False and hands_len:
            interval = time.time() - start_time

            if interval > INTERVAL:
                if not options.user_name:
                    options.user_name = 'default'

                with open(r'\\.\pipe\molocker_record', 'wb', 0) as pipe:
                    pipe_str = "3"                                
                    pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
                    pipe.seek(0)

                (second_tip_position, second_mdict) = set_password(controller, 0)

                # print verify(first_recog, second_tip_position, options.user_name)

                if verify(first_recog, second_tip_position, options.user_name):
                    io.savemat(WINDOWS_PATH + '\\gestures\\' + options.user_name, first_mdict)

                    with open(r'\\.\pipe\molocker_record', 'wb', 0) as pipe:
                        pipe_str = "4"                                
                        pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
                        pipe.seek(0)

                    exit(0)
                else:
                    with open(r'\\.\pipe\molocker_record', 'wb', 0) as pipe:
                        pipe_str = "5"                                
                        pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
                        pipe.seek(0)

                    exit(1)
        elif checked and hands_len:
            start_time = time.time()
            mark = True


def unlock(controller, options):
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

    if not options.user_name:
        options.user_name = 'default'

    temp = io.loadmat(WINDOWS_PATH + '\\gestures\\' + options.user_name)['all']

    r = Recognizer()

    r.addTemplate(options.user_name, temp)

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
                if verify(r, all_tip_position, options.user_name):
                    return
        elif checked and hands_len:
            start_time = time.time()
            mark = True


def main():
    """TODO: Docstring for main.

    :returns: TODO

    """
    (options, args) = get_options()

    last_frame_id = 0

    controller = Leap.Controller()

    controller.set_policy(Leap.Controller.POLICY_BACKGROUND_FRAMES)

    verification = Verification()

    controller.add_listener(verification)

    if options.is_setting:
        while True:
            if len(controller.frame().hands) > 0:
                get_ready(controller, last_frame_id, options)
                break
    elif options.is_verify:
        unlock(controller, options)


if __name__ == '__main__':
    main()

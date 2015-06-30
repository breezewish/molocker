import sys
sys.path.insert(0, "../lib")
import Leap
import thread
import time
import struct
import inspect
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
import verification

device_connected = False
pipe = open(r'\\.\pipe\molocker_event', 'r+b', 0)

class SampleListener(Leap.Listener):
    def on_connect(self, controller):
        print "Device Connected!"
        global device_connected
        global pipe
        device_connected = True
        pipe_str = "1"
        pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
        pipe.seek(0)
        #controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)

    def on_disconnect(self, controller):
        print "Device Disconnected!"
        global device_connected
        global pipe
        device_connected = False
        pipe_str = "2"
        pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
        pipe.seek(0)

def listening_thread_method():
    while True:
        time.sleep(1)
        if device_connected == True:
            global pipe
            (name, accuracy) = verification.check_all_file()
            print accuracy
            if accuracy >= 0.75:
                success = True
            else:
                success = False

            if success == True:
                with open("../credentials/%s" % name) as pwdfile:
                    pwd = pwdfile.readline()
                pipe_str = "4:%s:%s" % (name, pwd)
            else:
                pipe_str = "3"
            pipe.write(struct.pack('I', len(pipe_str)) + pipe_str)
            print "Name: %s; accuracy: %s" % (name, accuracy * 100)

if __name__ == '__main__':
    listener = SampleListener()
    controller = Leap.Controller()
    controller.set_policy(Leap.Controller.POLICY_BACKGROUND_FRAMES)
    controller.add_listener(listener)
    print "Device listener added!"

    thread.start_new_thread(listening_thread_method, ())
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass

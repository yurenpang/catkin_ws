#!/usr/bin/env python

""" ========================================================================
qrPlanner.py
Created: June, 2016
Starts a thread to grab images from the camera and scan then for ORB features
and QR codes. Imports zbar to read QR codes that are in the turtlebots view.
======================================================================== """

import cv2
from datetime import datetime
from collections import deque
import rospy
import time
import threading
from PIL import Image
#import ORBrecognizer
import string



class UpdateCamera( threading.Thread ):

    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.runFlag = True
        self.robot = bot
        self.frameAverageStallThreshold = 20
        self.frame = None
        self.stalled = False
        #self.qrInfo = None
        #self.orbInfo = None
        #self.orbScanner = ORBrecognizer.ORBrecognizer()
        #self.qrScanner = zbar.ImageScanner()

    def run(self):
        time.sleep(.5)
        runFlag = True
        cv2.namedWindow("TurtleCam", 1)
        timesImageServed = 1
        while(runFlag):
            image, timesImageServed = self.robot.getImage()
            self.frame = image

            with self.lock:
                if timesImageServed > 20:
                    if self.stalled == False:
                        print "Camera Stalled!"
                    self.stalled = True
                else:
                    self.stalled = False

            cv2.imshow("TurtleCam", image)
            cv2.waitKey()

            keypress = chr(cv2.waitKey(50) & 255)

            if keypress == 't':
                cv2.imwrite("/home/macalester/catkin_ws/src/speedy_nav/res/captures/cap-"
                                + str(datetime.now()) + ".jpg", image)
                print "Image saved!"
            if keypress == 'q':
                break

            with self.lock:
                runFlag = self.runFlag

    def isStalled(self):
        """Returns the status of the camera stream"""
        with self.lock:
            stalled = self.stalled
        return stalled

    def haltRun(self):
        with self.lock:
            self.runFlag = False

    def getImageDims(self):
        with self.lock:
            w, h, _ = self.frame.shape
        return w, h

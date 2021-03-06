import numpy as np
import cv2
import math

class Tracker(object):
	def __init__(self, track_window, found):
		""""""
		self.track_window = track_window
		self.found = found
		
		#Threshold Values
		self.trackThreshold = 80
		self.splitThreshold = 60
		
		self.checkEvery = 3
		self.sinceLastCheck = 0
		
	
	def update(self, bproj):
		self.bproj = bproj
		split = False
		if self.sinceLastCheck >= self.checkEvery:	
			self.accuracyCheck()
			split = self.needsSplitting() and self.found
			self.sinceLastCheck = 0
		
		term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
		
		window = list(self.track_window)
		for i, num in enumerate(self.track_window):
			if num < 1:
				window[i] = 1
		c,r,w,h = window
		self.track_rect, self.track_window = cv2.CamShift(bproj, (c,r,w,h), term_crit)
		
		c,r,w,h = self.track_window
		
		#Erases the area around the track_window as to not interfere with other trackers
		bproj[math.ceil(0.95*(r)):math.ceil(1.05*(r+h)), math.ceil(0.95*(c)):math.ceil(1.05*(c+w))] = 0
		
		self.sinceLastCheck += 1
		return self.track_rect, bproj, split
	
	
	def backProjAverage(self, window):
		c,r,w,h = window
		npArray = self.bproj[r:r+h, c:c+w]
		npSum = np.sum(npArray)
		area = (w+1)*(h+1)
		
		return npSum / area
	
	
	def accuracyCheck(self):
		fWidth, fHeight = self.bproj.shape
		if self.backProjAverage(self.track_window) <= self.trackThreshold:
			self.track_window = (0,0,fWidth,fHeight)
			self.found = False
		else:
			self.found = True
	
	
	def needsSplitting(self):
		center = self.getCenter()
		c,r,w,h = self.track_window
		box_width, box_height = (w // 5), (h // 5)
		box_window = (center[0] - box_width // 2), (center[1] - box_height // 2), box_width, box_height
		
		return self.backProjAverage(box_window) < self.splitThreshold
		
	
	def getTrackWindow(self):
		return self.track_window
		
	def getArea(self):
		c,r,w,h = self.track_window
		return w*h
	
	def getCenter(self):
		c,r,w,h = self.track_window
		return (c + w // 2), (r + h // 2)		
	
	def hasFound(self):
		return self.found

import cv2
import OlinGraph

class FixedActions(object):

	def __init__(self, turtleBot, multiCamShift, cameraThread):
		self.robot = turtleBot
		self.mcs = multiCamShift
		self.camera = cameraThread
		self.d2s = 0.046 # converts degrees to seconds
		self.targetArea = 0.14


	def align(self, targetRelativeArea):
		"""Drives the robot to a fixed distance from a pattern."""
		failedAttempts = 0
		centerX, centerY = self.mcs.getFrameCenter()
		patternInfo = None

		while True:
			if self.camera.isStalled():
					return None
			cv2.waitKey(200)
			patternInfo = self.mcs.getHorzPatterns()
			if patternInfo == None:
				failedAttempts += 1
				if failedAttempts > 10:
					break
				else:
					continue
			else:
				failedAttempts = 0
				pattern, (x, y), relativeArea, wallAngle = patternInfo
				difference = x - centerX
				print "patternX", x, ", centerX ", centerX, ", difference, ", difference
				if abs(difference) > 10:
					if x < centerX:
						self.turnByAngle(-10)
					else:
						self.turnByAngle(10)
				print "Angle to pattern", wallAngle

				cv2.waitKey(800)
				correction = (90 - abs(wallAngle)) / 90
				adjustedTargetArea = max(correction * targetRelativeArea, 0.12)
				if abs(adjustedTargetArea-relativeArea) > 0.04:
					if relativeArea < adjustedTargetArea:
						print 'forward'
						# causes the robot to slow down as it gets closer to the target
						adjustedSpeed = 0.06 - 0.04 * (relativeArea / adjustedTargetArea)
						self.robot.forward(adjustedSpeed, 0.2)
					else:
						self.robot.backward(0.04, 0.2)
					cv2.waitKey(800)
				else:
					break


		for i in range(20):
			patternInfo = self.mcs.getHorzPatterns()
			cv2.waitKey(200)
			if patternInfo != None:
				break
		else:  # if for loop does not break
			return None
		pattern, (x, y), relativeArea, angleToPattern = patternInfo
		print "Pattern found is " , pattern
		return pattern


	def turnToNextTarget(self, path, patternOrientation):
		wallAngle = self.robot.findAngleToWall()
		currentNode, nextNode = path[0], path[1]
		targetAngle = OlinGraph.olin.calcAngle(currentNode, nextNode)

		#determines actual orrientation given where the robot would face if it was directly
		#looking at the pattern (patternOrientation) and the currect angle to the pattern
		#(wallAngle)
		actualAngle = (patternOrientation - 90 + wallAngle) % 360

		angleToTurn = targetAngle - actualAngle
		if angleToTurn < -180:
			angleToTurn += 360
		elif 180 < angleToTurn:
			angleToTurn -= 360

		print "Turning from node " , str(currentNode) , " to node " , str(nextNode)
		self.turnByAngle(angleToTurn)


	def bumperRecovery(self, bumper_state):
		self.robot.backward(0.2, 2)
		cv2.waitKey(300)
		if bumper_state == 2:
			self.turnByAngle(45)
		if bumper_state == 1 or bumper_state == 3:
			self.turnByAngle(-45)


	def turnByAngle(self, angle):
		"""Turns the robot by the given angle, where negative is left and positive is right"""
		if self.camera.isStalled():
			return
		print 'Turning by an angle of: ', str(angle)
		turnSec = angle * self.d2s
		if angle < 0:
			turnSec = abs(turnSec)
			self.robot.turnLeft(0.4, turnSec)
		else:
			self.robot.turnRight(0.4, turnSec)






















# #!/usr/bin/env python
#
# """ ========================================================================
# ImageRecognizer.py
#
# Created: March 24, 2016
# Author: Susan
#
# This program extracts features from images and compares the images for
# similarity based on those features. See the README for more details.
#
# This is porting the CompareInfo class written in C++ in about 2011.
# ======================================================================== """
#
#
# # import sys
# import os
# import math
#
# import numpy as np
# from scipy import spatial
# import cv2
# # from espeak import espeak
#
# # import OutputLogger
# import ImageFeatures
# from DataPaths import basePath, imageDirectory, locData
# import MapGraph
#
#
# class ImageMatcher(object):
#     """..."""
#
#
#     def __init__(self, bot, logWriter,
#                  dir1 = None,locFile = None, baseName = 'foo', ext= "jpg",
#                  numMatches = 4):
#         self.currDirectory = dir1
#         self.locFile = locFile
#         self.baseName = baseName
#         self.currExtension = ext
#         self.numMatches = numMatches
#         self.threshold = 800.0
#         self.cameraNum = 0
#         self.height = 0
#         self.width = 0
#         self.logger = logWriter
#
#         self.robot = bot
#
#         # Add line to debug ORB
#         cv2.ocl.setUseOpenCL(False)
#         self.ORBFinder = cv2.ORB_create()
#
#         self.featureCollection = {} # dict with key being image number and value being ImageFeatures
#         self.numByLoc = {}
#         self.locByNum = {}
#         self.tree = None
#         self.xyArray = []
#         self.lastKnownLoc = None
#         self.radius = 2
#         self.lostCount = 0
#         self.beenGuessing = False
#
#         self.path = basePath + "scripts/olinGraph.txt"
#         self.olin = MapGraph.readMapFile(self.path)
#         # self.img = self.getOlinMap()
#
#
#     def setLogToFile(self, val):
#         if val in {False, True}:
#             self.logToFile = val
#
#
#     def setLogToShell(self, val):
#         if val in {False, True}:
#             self.logToShell = val
#
#
#     def setCurrentDir(self, currDir):
#         if type(currDir) == str:
#             self.currDirectory = currDir
#
#
#     def setSecondDir(self, sndDir):
#         if type(sndDir) == str:
#             self.secondDirectory = sndDir
#
#
#     def setExtension(self, newExt):
#         if type(newExt) == str:
#             self.currExtension = newExt
#
#
#     # def setFirstPicture(self, picNum):
#     #     if type(picNum == int) and (picNum >= 0):
#     #         self.startPicture = picNum
#
#     # def setNumPictures(self, picNum):
#     #     if type(picNum == int) and (picNum >= 0):
#     #         self.numPictures = picNum
#
#     def setCameraNum(self, camNum):
#         if type(camNum == int) and (camNum >= 0):
#             self.cameraNum = camNum
#
#     # ------------------------------------------------------------------------
#     # One of the major operations we can undertake, creates a list of ImageFeatures objects
#
#     def makeCollection(self):
#         """Reads in all the images in the specified directory, start number and end number, and
#         makes a list of ImageFeature objects for each image read in."""
#         if (self.currDirectory is None):
#             print("ERROR: cannot run makeCollection without a directory")
#             return
#         print "Current dir =", self.currDirectory
#         listDir = os.listdir(self.currDirectory)
#         print "Length of listDir =", len(listDir)
#         cnt = 1
#         for file in listDir:
#             if file[-3:] != 'jpg':
#                 print "FOUND NON IMAGE IN IMAGE FOLDER:", file
#                 continue
#             image = cv2.imread(self.currDirectory + file)
#             end = len(file) - (len(self.currExtension) + 1)
#             picNum = int(file[len(self.baseName):end])
#             if self.height == 0:
#                 self.height, self.width, depth = image.shape
#             #self.logger.log("Image = " + str(picNum))
#             features = ImageFeatures.ImageFeatures(image, picNum, self.logger, self.ORBFinder)
#             if picNum in self.featureCollection:
#                 print "ERROR: duplicate number", picNum
#             self.featureCollection[picNum] = features
#             cnt += 1
#             # if i % 100 == 0:
#             #     print i
#         print "cnt =", cnt
#         self.logger.log("Length of collection = " + str(len(self.featureCollection)))
#
#     def makeLocDict(self):
#         # picNum to x,y,heading
#         file = open(self.locFile)
#         for line in file.readlines():
#             line = line.rstrip('/n')
#             line = line.split()
#             self.locByNum[int(line[0])] = [float(x) for x in line[1:]]
#
#         # x,y to picNums w/ headings
#         for picNum in self.locByNum:
#             (x, y, h) = self.locByNum[picNum]
#             if (x, y) in self.numByLoc:
#                 self.numByLoc[(x, y)].append(picNum)
#             else:
#                 self.numByLoc[(x, y)] = [picNum]
#
#     def buildKDTree(self):
#         xyKeys = self.numByLoc.keys()
#         self.xyArray = np.asarray(xyKeys)
#         self.tree = spatial.KDTree(self.xyArray)
#
#     def setupData(self):
#         self.makeCollection()
#         self.makeLocDict()
#         self.buildKDTree()
#
#     # ------------------------------------------------------------------------
#     # One of the major operations we can undertake, comparing all pairs in a range
#     def matchImage(self, camImage):
#         """takes in a camera image and looks for a fixed number of close matches. Then uses those
#         to determine a likely location and confidence in that location."""
#         if len(self.featureCollection) == 0:
#             print("ERROR: must have built collection before running this.")
#             return
#
#         currFeat = ImageFeatures.ImageFeatures(camImage, 9999, self.logger, self.ORBFinder)
#         return self._findBestNMatches(currFeat)
#
#
#
#     def _findBestNMatches(self, currFeat):
#         """Looks through the collection of features and keeps the numMatches best matches.
#         TODO: needs serious streamlining and refactoring"""
#
#         potentialMatches = self._lookupPotentialMatches()
#         (bestScores, bestMatches) = self._selectBestN(potentialMatches, currFeat)
#
#         bestZipped = zip(bestScores, bestMatches)
#         bestZipped.sort(cmp = lambda a, b: int(a[0] - b[0]))
#         print [x[0]for x in bestZipped]
#         self.logger.log("==========Location Update==========")
#
#         (bestMatchScore, bestMatchFeatures) = bestZipped[0]
#
#         if bestMatchScore > 90:
#             self.logger.log("I have no idea where I am.")
#             self.radius = 8
#             self.lostCount += 1
#             self.beenGuessing = False
#             if self.lostCount >= 5:
#                 self.lastKnownLoc = None
#             return None
#         else:
#             self.lostCount = 0
#             im =  bestMatchFeatures.getImage()
#             locX,locY,locHead = self.locByNum[bestMatchFeatures.getIdNum()]
#             (num, x, y, dist) = self.findClosestNode((locX, locY))
#             self.logger.log("This match is tagged at " + str(locX) + ", " + str(locY) + ".")
#             self.logger.log("The closest node is " + str(num) + " at " + str(dist) + "  meters.")
#             cv2.imshow("Match Picture", im)
#             cv2.moveWindow("Match Picture", self.width + 10, 0)
#             cv2.waitKey(20)
#
#             guess, pts, head, conf = self.guessLocation(bestZipped)
#             self.logger.log("I think I am at node " + str(guess) + ", and I am " + conf)
#
#             if conf == "very confident." or conf == "close, but guessing.":
#                 print "I found my location."
#                 return guess, pts, head
#             else:
#                 return None
#
#
#     def _lookupPotentialMatches(self):
#         """Working with the current estimated location and confidence, this looks up a set of images most likely to
#         match the current one."""
#         potentialMatches = []
#         if self.lastKnownLoc is None:
#             potentialMatches = self.featureCollection.keys()
#         else:
#             pt = np.array([self.lastKnownLoc])
#             i = self.tree.query_ball_point(pt, self.radius)
#             for loc in self.xyArray[i[0]]:
#                 tup = tuple(loc)
#                 potentialMatches.extend(self.numByLoc[tup])
#             if potentialMatches == []:
#                 potentialMatches = self.featureCollection.keys()
#             self.logger.log("Potential matches length: " + str(len(potentialMatches)))
#             self.logger.log("Radius: " + str(self.radius) + " lastKnownLoc: "+ str(self.lastKnownLoc))
#         return potentialMatches
#
#
#
#
#
#     def drawPosition(self, image, x, y, heading, color):
#         cv2.circle(image, (x, y), 6, color, -1)
#         newX = x
#         newY = y
#         if heading == 0:
#             newY = y - 10
#         elif heading == 45:
#             newX = x - 8
#             newY = y - 8
#         elif heading == 90:
#             newX = x - 10
#         elif heading == 135:
#             newX = x - 8
#             newY = y + 8
#         elif heading == 180:
#             newY = y + 10
#         elif heading == 225:
#             newX = x + 8
#             newY = y + 8
#         elif heading == 270:
#             newX = x + 10
#         elif heading == 315:
#             newX = x + 8
#             newY = y - 8
#         else:
#             print "Error! The heading is", heading
#         cv2.line(image, (x,y), (newX, newY), color)
#
#     def guessLocation(self,bestZipped):
#         worst = len(bestZipped)-1
#         if bestZipped[0][0] < 70:
#             match = bestZipped[0][1]
#             idNum = match.getIdNum()
#             bestX, bestY, bestHead = self.locByNum[idNum]
#             (nodeNum, x, y, dist) = self.findClosestNode((bestX, bestY))
#             self.beenGuessing = False
#             if dist <= 0.8:
#                 # espeak.synth(str(nodeNum))
#                 self.lastKnownLoc = (x,y)
#                 self.radius = 3
#                 return nodeNum, (x,y), bestHead, "very confident."
#             else:
#                 self.lastKnownLoc = (x,y)
#                 if self.beenGuessing:
#                     self.radius += 0.25
#                 else:
#                     self.radius = 3
#                     self.beenGuessing = True
#                 return nodeNum, (x,y), bestHead, "confident, but far away."
#         else:
#             guessNodes = []
#             dist = 0
#             for j in range(len(bestZipped) - 1, -1, -1):
#                 (nextScore, nextMatch) = bestZipped[j]
#                 idNum = nextMatch.getIdNum()
#                 locX, locY, locHead = self.locByNum[idNum]
#                 (nodeNum, x, y, dist) = self.findClosestNode((locX, locY))
#                 if nodeNum not in guessNodes:
#                     guessNodes.append(nodeNum)
#             if len(guessNodes) == 1 and dist <= 0.8:
#                 self.lastKnownLoc = (x,y)
#                 if self.beenGuessing:
#                     self.radius += 0.25
#                 else:
#                     self.radius = 3
#                     self.beenGuessing = True
#                 return guessNodes[0], (x,y), locHead, "close, but guessing."
#             elif len(guessNodes) == 1:
#                 self.lastKnownLoc = (x,y)
#                 self.radius = 6
#                 self.beenGuessing = False
#                 return guessNodes[0], (x,y), locHead, "far and guessing."
#             else:
#                 nodes = str(guessNodes[0])
#                 for i in range(1,len(guessNodes)):
#                     nodes += " or " + str(guessNodes[i])
#                 self.radius = 8
#                 self.beenGuessing = False
#                 return nodes, (x,y), locHead, "totally unsure."
#
#
#     def findClosestNode(self, (x, y)):
#         """uses the location of a matched image and the distance formula to determine the node on the olingraph
#         closest to each match/guess"""
#         closestNode = None
#         closestX = None
#         closestY = None
#         for nodeNum in self.olin.getVertices():
#             if closestNode is None:
#                 closestNode = nodeNum
#                 closestX, closestY = self.olin.getData(nodeNum)
#                 bestVal = math.sqrt(((closestX - x) * (closestX - x)) + ((closestY - y) * (closestY - y)))
#             (nodeX,nodeY) = self.olin.getData(nodeNum)
#             val = math.sqrt(((nodeX - x) * (nodeX - x)) + ((nodeY - y) * (nodeY - y)))
#             if (val <= bestVal):
#                 bestVal = val
#                 closestNode = nodeNum
#                 closestX, closestY = (nodeX,nodeY)
#         return (closestNode, closestX, closestY, bestVal)
#
#     # def getOlinMap(self):
#     #     """Read in the Olin Map and return it. Note: this has hard-coded the orientation flip of the particular
#     #     Olin map we have, which might not be great, but I don't feel like making it more general. Future improvement
#     #     perhaps."""
#     #     origMap = readMap.createMapImage(basePath + "scripts/markLocations/olinNewMap.txt", 20)
#     #     map2 = np.flipud(origMap)
#     #     olinMap = np.rot90(map2)
#     #     return olinMap
#
#     def _convertWorldToMap(self, worldX, worldY):
#         """Converts coordinates in meters in the world to integer coordinates on the map
#         Note that this also has to adjust for the rotation and flipping of the map."""
#         # First convert from meters to pixels, assuming 20 pixels per meter
#         pixelX = worldX * 20.0
#         pixelY = worldY * 20.0
#         # Next flip x and y values around
#         mapX = self.mapWid - 1 - pixelY
#         mapY = self.mapHgt - 1 - pixelX
#         return (int(mapX), int(mapY))
#
#     # def _userGetInteger(self):
#     #     """Ask until user either enters 'q' or a valid nonnegative integer"""
#     #     inpStr = ""
#     #     while not inpStr.isdigit():
#     #         inpStr = raw_input("Enter nonnegative integer: ")
#     #         if inpStr == 'q':
#     #            return 'q'
#     #     num = int(inpStr)
#     #     return num
#
#
#     def getFileByNumber(self, fileNum):
#         """Makes a filename given the number and reads in the file, returning it."""
#         filename = self.makeFilename(fileNum)
#         image = cv2.imread(filename)
#         if image is None:
#             print("Failed to read image:", filename)
#         return image
#
#
#     def putFileByNumber(self, fileNum, image):
#         """Writes a file in the current directory with the given number."""
#         filename = self.makeFilename(fileNum)
#         cv2.imwrite(filename, image)
#
#
#     def makeFilename(self, fileNum):
#         """Makes a filename for reading or writing image files"""
#         formStr = "{0:s}{1:s}{2:0>4d}.{3:s}"
#         name = formStr.format(self.currDirectory,
#                               self.baseName,
#                               fileNum,
#                               self.currExtension)
#         return name
#
#
#
#
#     # def run(self):
#     #     runFlag = True
#     #     self.makeCollection()
#     #     if len(self.featureCollection) == 0:
#     #         print("ERROR: must have built collection before running this.")
#     #         return
#     #     self.logger.log("Choosing frames from video to compare to collection")
#     #     print("How many matches should it find?")
#     #     numMatches = self._userGetInteger()
#     #     while runFlag:
#     #         image = self.robot.getImage()[0]
#     #         if image is None:
#     #             break
#     #         features = ImageFeatures.ImageFeatures(image, 9999, self.logger, self.ORBFinder)
#     #         cv2.imshow("Primary image", image)
#     #         cv2.moveWindow("Primary image", 0, 0)
#     #         features.displayFeaturePics("Primary image features", 0, 0)
#     #         self._findBestNMatches(features, numMatches)
#     #         runFlag = self.runFlag
#
#     # def isStalled(self):
#     #     """Returns the status of the camera stream"""
#     #     return self.stalled
#     #
#     #
#     # def exit(self):
#     #     self.runFlag = False
#
#
# if __name__ == '__main__':
#     # REMEMBER THIS IS TEST CODE ONLY!
#     # change paths for files in OSPathDefine
#     matcher = ImageMatcher(logFile = True, logShell = True,
#                            dir1 =basePath + imageDirectory,
#                            locFile = basePath + locData,
#                            baseName = "frame",
#                            ext = "jpg")
#
#
#
#

#!/usr/bin/env python

""" ========================================================================
ImageDataset.py

Created: June 2017
Author: Susan

This creates the ImageDataset object, which reads in a set of images and a
location file, and creates dictionaries and a KDTree to hold the images
and organize them by their locations. It provides methods for getting some number
of closest matches.
======================================================================== """


import os

import numpy as np
from scipy import spatial
import cv2

import ImageFeatures


class ImageDataset(object):
    """This constructs a dataset to associate images with locations, allowing us to access the location of an
    image, and also to select images that lie within some boundary of a given location."""


    def __init__(self, logWriter, numMatches = 4):
        self.numMatches = numMatches
        self.threshold = 800.0

        self.logger = logWriter

        # Add line to debug ORB
        cv2.ocl.setUseOpenCL(False)
        self.ORBFinder = cv2.ORB_create()

        self.featureCollection = {} # dict with key being image number and value being ImageFeatures
        self.numByLoc = {}
        self.locByNum = {}
        self.tree = None
        self.xyArray = None




    def setupData(self, currDir, locFile, baseName, ext):
        """This method reads in the data and makes the various data structures."""
        self.makeCollection(currDir, baseName, ext)
        self.makeLocDict(locFile)
        self.buildKDTree()


    def makeCollection(self, currDir, baseName, ext):
        """Reads in all the images in the specified directory, start number and end number, and
        makes a list of ImageFeature objects for each image read in."""
        if (currDir is None):
            self.logger.log("ERROR: cannot run makeCollection without a directory")
            return
        self.logger.log("Reading image dataset...")
        listDir = os.listdir(currDir)
        for filename in listDir:
            # Check if the next file is the right form, and extract the number part, if it is
            (picNum, foundNum) = self._extractNumber(filename, baseName, ext)
            if not foundNum:
                continue
            image = cv2.imread(currDir + filename)
            features = ImageFeatures.ImageFeatures(image, picNum, self.logger, self.ORBFinder)
            if picNum in self.featureCollection:
                self.logger.log("ERROR: duplicate number: " +  str(picNum))
            self.featureCollection[picNum] = features
        # self.logger.log("Length of collection = " + str(len(self.featureCollection)))


    def makeLocDict(self, locFile):
        """Creates a dictionary mapping picture numbers to their locations (a list of [x, y, heading]) and
        also creates a dictionary mapping (x, y) locations to the picture numbers at those locations."""
        # picNum to x,y,heading
        filename = open(locFile, 'r')
        for line in filename:
            # line = line.strip()
            line = line.split()
            loc = int(line[0])
            x = float(line[1])
            y = float(line[2])
            h = int(line[3])
            self.locByNum[loc] = [x, y, h]
        filename.close()

        # x,y to picNums w/ headings
        for picNum in self.locByNum:
            (x, y, h) = self.locByNum[picNum]
            if (x, y) in self.numByLoc:
                self.numByLoc[(x, y)].append(picNum)
            else:
                self.numByLoc[(x, y)] = [picNum]


    def buildKDTree(self):
        """Assuming that the two dictionaries mapping picture nums to locations and vice versa are already
        built, this constructs a KDTree for the (x, y) locations of the dataset."""
        xyKeys = self.numByLoc.keys()
        self.xyArray = np.asarray(xyKeys)
        self.tree = spatial.KDTree(self.xyArray)


    def _extractNumber(self, filename, baseName, ext):
        """Pulls apart the filename to make sure it is the right format. If it is, then the picture number is returned.
        If it is no, then False is returned."""
        baseLen = len(baseName)
        extLen = len(ext)
        extStart = len(filename) - (extLen + 1)
        basePart = filename[:baseLen]
        numPart = filename[baseLen:extStart]
        extPart = filename[extStart:]
        if (extPart != '.' + ext) or (basePart != baseName) or (not numPart.isdigit()):
            self.logger.log("Found wrong format file in image folder: " + filename)
            return None, False
        else:
            return int(numPart), True


    def getLoc(self, picNum):
        """Given a picture number, return the location that is associated with it."""
        return self.locByNum[picNum]


    # ------------------------------------------------------------------------
    # matches a new image to the dataset
    def matchImage(self, camImage, lastKnown, confidence):
        """Given an image from the robot's camera, the last known location of the robot, and
        how confident the robot is about that location, this examines a subset of its dataset of images and finds
        the best matches among that subset. """

        if len(self.featureCollection) == 0:
            self.logger.log("ERROR: must have built collection before running this.")
            return

        features = ImageFeatures.ImageFeatures(camImage, 9999, self.logger, self.ORBFinder)
        bestMatches = self._findBestNMatches(features, lastKnown, confidence)
        return bestMatches


    def _findBestNMatches(self, currImFeatures, lastKnown, confidence):
        """Looks through the collection of features and keeps the numMatches
        best matches. It zips them together"""
        bestMatches = []
        bestScores = []

        potentialMatches = self._findPotentialMatches(lastKnown, confidence)
        (bestScores, bestMatches) = self._selectBestN(potentialMatches, currImFeatures)

        bestZipped = zip(bestScores, bestMatches)
        # bestZipped.sort(cmp = lambda a, b: int(a[0] - b[0]))
        bestFeat = bestZipped[0][1]
        # This is just to print the details of the similarity measures!!
        # currImFeatures.evaluateSimilarity(bestFeat, True)
        formSt = "{0:4.2f}"
        self.logger.log("Best matches have scores: " + " ".join([ formSt.format(x[0]) for x in bestZipped]))
        return bestZipped


    def _findPotentialMatches(self, lastKnown, confidence):
        """Computes the set of possible matches to be examined. In the worst case, this is the entire image
        dataset. However, it tries to reduce this using the KDTree to get only pictures within some range."""
        radius = self._confidenceToRadius(confidence)
        potentialMatches = []
        if lastKnown is None or confidence == 0.0:
            potentialMatches = self.featureCollection.keys()
        else:
            pt = np.array([lastKnown])
            i = self.tree.query_ball_point(pt, radius)
            for loc in self.xyArray[i[0]]:
                tup = tuple(loc)
                potentialMatches.extend(self.numByLoc[tup])
            if potentialMatches == []:
                potentialMatches = self.featureCollection.keys()
        # self.logger.log("Potential matches length: " + str(len(potentialMatches)))
        self.logger.log("Last Known Location: " + str(lastKnown) + " Radius: " + str(radius))
        return potentialMatches


    def _selectBestN(self, potentialMatches, currFeat):
        """Takes in a list of potential matching images (image numbers, specifically) from the dataset, and
        it checks their similarity to the current image. Keeps the best numMatches """
        bestMatches = []
        bestScores = []
        for pos in potentialMatches:
            feat = self.featureCollection[pos]
            simValue = currFeat.evaluateSimilarity(feat)
            if simValue < self.threshold:
                self._doubleInsert(simValue, feat, bestScores, bestMatches)
                if len(bestScores) > self.numMatches:
                    bestScores.pop()
                    bestMatches.pop()
        return bestScores, bestMatches


    def _doubleInsert(self, score, feat, scoreList, featList):
        """Given a score and a feature, inserts it to keep the scorelist in increasing order, inserting the feature in the
        feature list at the same point."""
        indx = 0
        while indx < len(scoreList) and (score < scoreList[indx]): #TODO:changed the second part from >
            indx += 1

        if indx == len(scoreList):
            scoreList.append(score)
            featList.append(feat)
        else:
            scoreList.insert(indx, score)
            featList.insert(indx, feat)



    def _confidenceToRadius(self, confidence):
        """Maps the confidence level that comes from outside into a radius for use in searching for
        potential matches.
        Confidence:   1  2  3  4  5  6  7  8  9  10
        Radius:      15                           3 """
        perc = 1.0 - (confidence / 10.0)
        radius = (perc * 12.0) + 3.0
        return radius



#
#
# if __name__ == '__main__':
#     # Demo code
#     matcher = ImageDataset(None, None, 3)
#     matcher.setupData(basePath + ImageDirectory, locData, "frame", "jpg")
#

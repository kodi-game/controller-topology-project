#
# Copyright (c) 2014 Garrett Brown
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import costmap
import geometry

import cv2
import heapq
import math
import numpy as np

class PriorityQueue(object):
    def __init__(self):
        self.elements = []
    
    def Empty(self):
        return len(self.elements) == 0
    
    def Put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def Get(self):
        return heapq.heappop(self.elements)[1]

class PathFinder(object):
    def __init__(self, costmap, button, goal):
        self._costmap = costmap
        self._button = button
        self._goal = goal
        self._path = self.CreatePath()

    def CreatePath(self):
        if not self._costmap or not self._button:
            return None

        xgoal, ygoal = self._goal[0]

        img = self._costmap.Image().copy()
        self.ShowStep(img)

        cameFrom = { }
        costSoFar = { }

        frontier = PriorityQueue()
        self._start = self._button.StartPoints()[0]
        #for startPoint in self._button.StartPoints():
        #    frontier.Put(startPoint, 0)
        frontier.Put(self._start, 0)

        cameFrom[self._start] = None
        costSoFar[self._start] = 0

        while not frontier.Empty():
            current = frontier.Get()

            if current == self._goal:
                break

            for next, stepCost in self.GetNeighbors(current):
                x, y = next[0]
                newCost = costSoFar[current] + stepCost * (1.0 + 10.0 * (self._costmap.Image()[y][x] ** 2) / (costmap.COST_MAX ** 2))
                if next not in costSoFar or newCost < costSoFar[next]:
                    costSoFar[next] = newCost
                    priority = newCost + math.sqrt((x - xgoal) ** 2 + (y - ygoal) ** 2)
                    frontier.Put(next, priority)
                    cameFrom[next] = current
                    img[y, x] = costmap.COST_MAX

                    self.ShowStep(img)

        cv2.destroyAllWindows()
        return img

    def ShowStep(self, img):
        try:
            self._i += 1
        except AttributeError:
            self._i = 0
        if self._i % 100 == 0:
            cv2.imshow('image', img)
            cv2.waitKey(0)

    def GetNeighbors(self, node):
        x, y = node[0]
        nodeDir = node[1]

        newDirs = [ nodeDir ]
        if nodeDir == geometry.DIRECTION_UP:
            newDirs.append(geometry.DIRECTION_UPLEFT); newDirs.append(geometry.DIRECTION_UPRIGHT)
        elif nodeDir == geometry.DIRECTION_UPRIGHT:
            newDirs.append(geometry.DIRECTION_RIGHT)
        elif nodeDir == geometry.DIRECTION_RIGHT:
            newDirs.append(geometry.DIRECTION_UPRIGHT); newDirs.append(geometry.DIRECTION_DOWNRIGHT)
        elif nodeDir == geometry.DIRECTION_DOWNRIGHT:
            newDirs.append(geometry.DIRECTION_RIGHT)
        elif nodeDir == geometry.DIRECTION_DOWN:
            newDirs.append(geometry.DIRECTION_DOWNLEFT); newDirs.append(geometry.DIRECTION_DOWNRIGHT)
        elif nodeDir == geometry.DIRECTION_DOWNLEFT:
            newDirs.append(geometry.DIRECTION_LEFT)
        elif nodeDir == geometry.DIRECTION_LEFT:
            newDirs.append(geometry.DIRECTION_UPLEFT); newDirs.append(geometry.DIRECTION_DOWNLEFT)
        elif nodeDir == geometry.DIRECTION_UPLEFT:
            newDirs.append(geometry.DIRECTION_LEFT)

        neighbors = [ ]
        for direction in newDirs:
            xdelta, ydelta = direction
            cost = 1 if abs(xdelta) + abs(ydelta) == 1 else geometry.SQRT2
            neighbors.append((((x + xdelta, y + ydelta), direction), cost))

        return filter(self.InBounds, neighbors)

    def InBounds(self, pair):
        node, cost = pair
        x, y = node[0]
        return 0 <= x and x < self._costmap.Width() and \
               0 <= y and y < self._costmap.Height()

    def Show(self):
        cv2.imshow('image', self._path)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def Save(self, filename):
        if self._path is None:
            return False
        cv2.imwrite(filename, self._path)
        return True


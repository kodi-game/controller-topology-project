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

import cv2
import heapq
import math
import numpy as np

SQRT2 = math.sqrt(2)

class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def Empty(self):
        return len(self.elements) == 0
    
    def Put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def Get(self):
        return heapq.heappop(self.elements)[1]

class PathFinder(object):
    def __init__(self, costmap, start, goal):
        self._costmap = costmap
        self._start = start
        self._goal = goal
        self._path = self.CreatePath()

    def CreatePath(self):
        if not self._costmap:
            return None

        img = self._costmap.Image().copy()

        frontier = PriorityQueue()
        frontier.Put(self._start, 0)

        cameFrom = { }
        costSoFar = { }
        cameFrom[self._start] = None
        costSoFar[self._start] = 0

        while not frontier.Empty():
            current = frontier.Get()

            if current == self._goal:
                break

            for next, stepCost in self.GetNeighbors(current):
                newCost = costSoFar[current] + stepCost# + (10.0 * self._costmap.Image()[next[1]][next[0]] / costmap.COST_MAX)
                if next not in costSoFar or newCost < costSoFar[next]:
                    costSoFar[next] = newCost
                    priority = newCost + math.sqrt((next[0] - self._goal[0]) ** 2 + (next[1] - self._goal[1]) ** 2)
                    frontier.Put(next, priority)
                    cameFrom[next] = current

            # results: cameFrom, costSoFar

        cv2.line(img, self._start, self._goal, 255, 3)

        return img

    def GetNeighbors(self, pos):
        neighbors = [((pos[0],     pos[1] + 1), 1),
                     ((pos[0] + 1, pos[1] + 1), SQRT2),
                     ((pos[0] + 1, pos[1]),     1),
                     ((pos[0] + 1, pos[1] - 1), SQRT2),
                     ((pos[0],     pos[1] - 1), 1),
                     ((pos[0] - 1, pos[1] - 1), SQRT2),
                     ((pos[0] - 1, pos[1]),     1),
                     ((pos[0] - 1, pos[1] + 1), SQRT2)]
        return filter(self.InBounds, neighbors)

    def InBounds(self, pos):
        return 0 <= pos[0][0] and pos[0][0] < self._costmap.Width() and \
               0 <= pos[0][1] and pos[0][1] < self._costmap.Height()

    def Show(self):
        cv2.imshow('image', self._path)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def Save(self, filename):
        if self._path is None:
            return False
        cv2.imwrite(filename, self._path)
        return True


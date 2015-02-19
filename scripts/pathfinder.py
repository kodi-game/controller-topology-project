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

from collections import namedtuple
import cv2
import heapq
import math
import numpy as np

STEP_SIZE      = 8
DIAG_STEP_SIZE = int(STEP_SIZE / math.sqrt(2) + 0.5)
MIN_STEP       = 16
MIN_DIAG_STEP  = int(MIN_STEP / math.sqrt(2) + 0.5)

PATH_VERT   = 'vert'
PATH_DIAG1  = 'diag1'
PATH_HORIZ1 = 'horiz1'
PATH_DIAG2  = 'diag2'
PATH_HORIZ2 = 'horiz2'

Node = namedtuple('Node', 'state %s %s %s %s %s' % (PATH_VERT, PATH_DIAG1, PATH_HORIZ1, PATH_DIAG2, PATH_HORIZ2))

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

    @staticmethod
    def MakeStartNode(dir):
        if dir == geometry.DIRECTION_UP or dir == geometry.DIRECTION_DOWN:
            return Node(PATH_VERT, 0, 0, 0, 0, 0)
        elif dir == geometry.DIRECTION_RIGHT or dir == geometry.DIRECTION_LEFT:
            return Node(PATH_HORIZ1, 0, 0, 0, 0, 0)
        else:
            return Node(PATH_DIAG1, 0, 0, 0, 0, 0)

    def CreatePath(self):
        if not self._costmap or not self._button:
            return None

        xgoal, ygoal = self._goal.pos

        img = self._costmap.Image().copy()
        #self.ShowStep(img)

        cameFrom = { }
        costSoFar = { }

        frontier = PriorityQueue()
        self._start = self._button.StartPoints()[0]

        startNode = PathFinder.MakeStartNode(self._start.dir)
        frontier.Put(startNode, 0)

        cameFrom[startNode] = None
        costSoFar[startNode] = 0

        lastNode = None

        while not frontier.Empty():
            current = frontier.Get()

            xpos, ypos = self.GetPos(current)
            if math.sqrt((xpos - xgoal) ** 2 + (ypos - ygoal) ** 2) < STEP_SIZE:
                print("Reached goal!")
                lastNode = current
                break

            for next in self.GetNeighbors(current):
                baseStepCost = geometry.SQRT2 if (next.state == PATH_DIAG1 or next.state == PATH_DIAG2) else 1
                x, y = self.GetPos(next)
                newCost = costSoFar[current] + baseStepCost * (1.0 + 100.0 * (self._costmap.Image()[y][x] ** 2) / (costmap.COST_MAX ** 2))
                if next not in costSoFar or newCost < costSoFar[next]:
                    costSoFar[next] = newCost
                    priority = newCost + math.sqrt((x - xgoal) ** 2 + (y - ygoal) ** 2)
                    frontier.Put(next, priority)
                    cameFrom[next] = current
                    #img[y][x] = costmap.COST_MAX

                    #self.ShowStep(img)

        # Draw the path
        nextNode = startNode
        while lastNode:
            previousNode = cameFrom.get(lastNode)
            if previousNode:
              cv2.line(img, self.GetPos(lastNode), self.GetPos(previousNode), int(costmap.COST_MAX * 0.1), 3)
            lastNode = previousNode

        return img

    def GetPos(self, node):
        xsense = -1 if self._goal.pos.x < self._start.pos.x else 1
        xdelta = abs(node.diag1) + abs(node.horiz1) + abs(node.diag2) + abs(node.horiz2)
        ydelta = node.vert + node.diag1 + node.diag2
        return geometry.Point(self._start.pos.x + xdelta * xsense, self._start.pos.y + ydelta)

    def GetNeighbors(self, node):
        neighbors = [ ]
        if node.state == PATH_VERT:
            ysense = self._start.dir.ystep
            neighbors.append(Node(PATH_VERT, node.vert + STEP_SIZE * ysense, 0, 0, 0, 0))
            if abs(node.vert) >= MIN_STEP:
                neighbors.append(Node(PATH_DIAG1, node.vert, STEP_SIZE * ysense, 0, 0, 0))
        elif node.state == PATH_DIAG1:
            ysense = self._start.dir.ystep
            neighbors.append(Node(PATH_DIAG1, node.vert, node.diag1 + DIAG_STEP_SIZE * ysense, 0, 0, 0))
            if abs(node.diag1) >= MIN_DIAG_STEP:
                neighbors.append(Node(PATH_HORIZ1, node.vert, node.diag1, STEP_SIZE, 0, 0))
        elif node.state == PATH_HORIZ1:
            neighbors.append(Node(PATH_HORIZ1, node.vert, node.diag1, node.horiz1 + STEP_SIZE, 0, 0))
            if abs(node.horiz1) >= MIN_STEP:
                neighbors.append(Node(PATH_DIAG2, node.vert, node.diag1, node.horiz1, DIAG_STEP_SIZE, 0))
                neighbors.append(Node(PATH_DIAG2, node.vert, node.diag1, node.horiz1, -DIAG_STEP_SIZE, 0))
        elif node.state == PATH_DIAG2:
            ysense = 1 if node.diag2 > 0 else -1
            neighbors.append(Node(PATH_DIAG2, node.vert, node.diag1, node.horiz1, node.diag2 + DIAG_STEP_SIZE * ysense, 0))
            if abs(node.diag2) >= MIN_DIAG_STEP:
                neighbors.append(Node(PATH_HORIZ2, node.vert, node.diag1, node.horiz1, node.diag2, STEP_SIZE))
        elif node.state == PATH_HORIZ2:
            neighbors.append(Node(PATH_HORIZ2, node.vert, node.diag1, node.horiz1, node.diag2, node.horiz2 + STEP_SIZE))
        return filter(self.InBounds, neighbors)

    def InBounds(self, node):
        x, y = self.GetPos(node)
        return 0 <= x and x < self._costmap.Width() and \
               0 <= y and y < self._costmap.Height()

    def Show(self):
        if self._path is not None:
            cv2.imshow('image', self._path)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def Save(self, filename):
        if self._path is not None:
            cv2.imwrite(filename, self._path)
            return True
        return False


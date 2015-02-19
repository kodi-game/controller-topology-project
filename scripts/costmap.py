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

import geometry

import math
import sys

try:
    import numpy as np
except ImportError:
    print('Error importing numpy (try sudo apt-get install python-numpy)')
    sys.exit(1)

try:
    import cv2
except ImportError:
    print('Error importing cv2 (try sudo apt-get install python-opencv)')
    sys.exit(1)

COST_MAX = 255

class Costmap(object):
    def __init__(self, width, height, buttons):
        self._width = width
        self._height = height
        self._buttons = buttons
        self._costmap = self.CreateCostMap()

    def CreateCostMap(self):
        if not self._width or not self._height or not self._buttons:
            return None

        # Allocate the final image
        result = np.zeros((self._height, self._width), np.uint8)

        # Draw the buttons
        img = np.zeros((self._height, self._width), np.uint8)
        for button in self._buttons:
            if button.Type() == geometry.BUTTON_RECTANGLE:
                cv2.rectangle(img, button.Point1(), button.Point2(), COST_MAX, -1)
            elif button.Type() == geometry.BUTTON_CIRCLE:
                cv2.circle(img, button.Center(), button.Radius(), COST_MAX, -1)
            elif button.Type() == geometry.BUTTON_DPAD:
                up, right, down, left = button.Directions()
                cv2.rectangle(img, up.Point1(), up.Point2(), COST_MAX, -1)
                cv2.rectangle(img, right.Point1(), right.Point2(), COST_MAX, -1)
                cv2.rectangle(img, down.Point1(), down.Point2(), COST_MAX, -1)
                cv2.rectangle(img, left.Point1(), left.Point2(), COST_MAX, -1)

        # Generate a roundish kernel. For size=7 this will yield
        #
        #    [[0 0 0 1 0 0 0]
        #     [0 1 1 1 1 1 0]
        #     [0 1 1 1 1 1 0]
        #     [1 1 1 1 1 1 1]
        #     [0 1 1 1 1 1 0]
        #     [0 1 1 1 1 1 0]
        #     [0 0 0 1 0 0 0]]
        #
        kernel_size = 7
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        for i in range(kernel_size):
            for j in range(kernel_size):
                x = 2.0 * i / (kernel_size - 1) - 1.0
                y = 2.0 * j / (kernel_size - 1) - 1.0
                r = math.sqrt(x * x + y * y)
                if (r > 1.0):
                    kernel[i, j] = 0

        # Iteratively dilate the image to generate costmap
        levels = 12
        for i in range(levels):
            result += img / levels
            img = cv2.dilate(img, kernel, iterations = (i + 2) / 2)

        return result

    def Show(self):
        cv2.imshow('image', self._costmap)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def Load(self, filename):
        self._costmap = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        return True

    def Save(self, filename):
        if self._costmap is None:
            return False
        cv2.imwrite(filename, self._costmap)
        return True


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

import xml.etree.ElementTree as ET

EXTENSION_POINT = 'xbmc.game.peripheral'

class Addon(object):
    def __init__(self, addon_xml_path):
        self._width = 0
        self._height = 0
        self._image_src = None
        self._costmap_src = None
        self._buttons = []
        
        root = ET.parse(addon_xml_path).getroot()
        if root.tag != 'addon':
            print('Error: can\'t find <addon> tag in addon.xml')
            return

        for extension_child in root:
            if extension_child.tag != 'extension':
                continue
            if extension_child.attrib.get('point') != EXTENSION_POINT:
                continue
            for layout_child in extension_child:
                if layout_child.tag != 'layout':
                    print('Error: expected <layout> tag under <extension> tag in addon.xml')
                    break
                try:
                    self._width = int(layout_child.attrib.get('width'))
                    self._height = int(layout_child.attrib.get('height'))
                except ValueError:
                    break
                self._image_src = layout_child.attrib.get('image')
                self._costmap_src = layout_child.attrib.get('costmap')
                for button_child in layout_child:
                    button = geometry.Button.FromNode(button_child)
                    if button:
                        self._buttons.append(button)
                break

    def IsValid(self):
        return self._width and self._height and self._costmap_src and self._buttons

    def LayoutWidth(self):
        return self._width

    def LayoutHeight(self):
        return self._height

    def LayoutImage(self):
        return self._image_src

    def CostmapImage(self):
        return self._costmap_src

    def Buttons(self):
        return self._buttons


#!/usr/bin/env python

import geometry
import costmap

import xml.etree.ElementTree as ET

EXTENSION_POINT = 'xbmc.game.peripheral'

def main():
    width = 0
    height = 0
    image_src = None
    costmap_src = None
    buttons = []
    
    root = ET.parse('addon.xml').getroot()
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
                width = int(layout_child.attrib.get('width'))
                height = int(layout_child.attrib.get('height'))
            except ValueError:
                pass
            image_src = layout_child.attrib.get('image')
            costmap_src = layout_child.attrib.get('costmap')
            for button_child in layout_child:
                button = geometry.Button.FromNode(button_child)
                if button:
                    buttons.append(button)
            break

    if not width or not height or not image_src or not costmap_src or not buttons:
        print('Error: failed to load information from addon.xml')
        return

    # TODO: Check that dimensions of image_src match width and height

    cm = costmap.Costmap(width, height, buttons)
    cm.Show()
    if not cm.Save(costmap_src):
        print('Error: failed to render costmap')
        return
    else:
        print('Saved costmap to %s' % costmap_src)


if __name__ == '__main__':
    main()


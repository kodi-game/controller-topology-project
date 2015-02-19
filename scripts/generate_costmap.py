#!/usr/bin/env python

import addon
import costmap

def main():
    ad = addon.Addon('addon.xml')
    if ad.IsValid():
        cm = costmap.Costmap(ad.LayoutWidth(), ad.LayoutHeight(), ad.Buttons())
        cm.Show()
        cm.Save(ad.CostmapImage())


if __name__ == '__main__':
    main()


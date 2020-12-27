# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import numpy as np
from tab import Tab
from point import Point

class Piece():
    def __init__(self, tabs: Tab):
        self.tabs = [tab for tab in tabs if tab]
        self.__calc_centroid()
        self.neigbors = set([])

    def __calc_centroid(self):
        cx = [tab.centroid.x for tab in self.tabs]
        cy = [tab.centroid.y for tab in self.tabs]
        self.centroid = Point(np.mean(cx), np.mean(cy))

    def border(self):
        return list({tab for tab in self.tabs for neighbor in self.neigbors if tab in neighbor.tabs or (not tab.radial and tab.rad_pos == 0)})

    def addtab(self, tab):
        if not tab in self.tabs:
            self.tabs.append(tab)
            self.__calc_centroid()

    def addneighbor(self, neighbor):
        self.neigbors.add(neighbor)

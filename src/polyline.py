# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import itertools
import tkinter
from point import Point
from segment import Segment
from typing import List


class Polyline:
    def __init__(self, points: List[Point] = None):
        self.points = [p for p in points] if points else None
        self.segments = None

    def add_points(self, newpoints: List[Point]):
        if not self.points:
            self.points = [p for p in newpoints]
           # self.points.extend(newpoints)
            return True
        elif self.points[-1] == newpoints[0]:
            self.points.extend(newpoints[1:])
            return True
        elif self.points[0] == newpoints[-1]:
            self.points.reverse()
            self.points.extend(reversed(newpoints[:-1]))
            return True
        elif self.points[-1] == newpoints[-1]:
            self.points.extend(reversed(newpoints[:-1]))
            return True
        elif self.points[0] == newpoints[0]:
            self.points.reverse()
            self.points.extend(newpoints[1:])
            return True
        else:
            #print('Noinsert WTF')
            return False

    def calc_segments(self):
        self.segments = [Segment(p1, p2)
                         for p1, p2 in zip(self.points, self.points[1:])]

    def append_other(self, other):
        return self.add_points(other.points)

    def selfintersects(self):
        if(len(self.points) < 3):
            return False
        if(self.segments is None):
            self.calc_segments()
        return any((not seg1.sharespointwith(seg2) and seg1.intersects(seg2)) for seg1, seg2 in itertools.combinations(self.segments, 2))

    def checkdistances(self, other, mindistance, offenders=[], offended=[]):
        if other is None:
            if(self.segments is None):
                self.calc_segments()
            for seg1, seg2 in itertools.combinations(self.segments, 2):
                if not seg1.sharespointwith(seg2) and seg1.dist2seg(seg2) < mindistance:
                    if not seg1 in offenders:
                        offenders.append(seg1)
                    if not seg2 in offended:
                        offended.append(seg2)
        else:
            if(self.segments is None):
                self.calc_segments()
            if(other.segments is None):
                other.calc_segments()
            for seg1, seg2 in itertools.product(self.segments, other.segments):
                if not seg1.sharespointwith(seg2) and seg1.dist2seg(seg2) < mindistance:
                    if not seg1 in offenders:
                        offenders.append(seg1)
                    if not seg2 in offended:
                        offended.append(seg2)

        return offenders, offended

    def removepoint(self, p: Point):
        if p in self.points:
            self.points.remove(p)
            self.segments = None

    def printtocanvas(self, canvas: tkinter.Canvas, tags="polyline"):
        for p1, p2 in zip(self.points, self.points[1:]):
            canvas.create_line(p1.x, p1.y, p2.x, p2.y,
                               fill="black", width=1, tags=tags)

    def printtosvg(self, dwg, offset=Point(0, 0)):
        polypoints = [((p-offset).x, (p-offset).y) for p in self.points]
        dwg.add(dwg.polyline(polypoints, stroke="red",
                             fill="none", stroke_width="0.1"))

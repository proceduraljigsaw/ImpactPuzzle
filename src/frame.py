# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


import itertools
import tkinter
from point import Point
from segment import Segment
from polyline import Polyline


class RectangularFrame:
    def __init__(self, ulc: Point, lrc: Point):
        self.ulc = ulc
        self.lrc = lrc
        self.dimensions = (abs(lrc.x-ulc.x), abs(lrc.y-ulc.y))
        self.sides = [Segment(self.ulc, Point(self.ulc.x, self.lrc.y)), Segment(Point(self.lrc.x, self.ulc.y), self.lrc), Segment(self.ulc, Point(self.lrc.x, self.ulc.y)), Segment(Point(self.ulc.x, self.lrc.y), self.lrc)]

    # def ispointinside(self,p:Point2D, strict= False):
    #     return ((self.ulc.x<=p.x<=self.lrc.x) and (self.ulc.y<=p.y<=self.lrc.y)) if strict else  ((self.ulc.x<p.x<self.lrc.x) and (self.ulc.y<p.y<self.lrc.y))
    def ispointinside(self, p: Point, strict=False):
        return ((self.ulc.x < p.x < self.lrc.x) and (self.ulc.y < p.y < self.lrc.y)) if strict else ((self.ulc.x <= p.x <= self.lrc.x) and (self.ulc.y <= p.y <= self.lrc.y))

    def ispointonborder(self, p: Point):
        return p.x == self.ulc.x or p.x == self.lrc.x or p.y == self.ulc.y or p.y == self.lrc.y

    def intesercts(self, other):
        if len(other.points) < 3:
            return False
        return any(not self.ispointinside(p) for p in other.points[1:-1])

    def intersects_strict(self, other):
        return any((not seg1.sharespointwith(seg2) and seg1.intersects(seg2)) for seg1, seg2 in itertools.product(self.sides, other.segments))

    def pointmovedtoborder(self, p: Point, prevp: Point):
        if self.ispointinside(p):
            return p
        intersecting_seg = Segment(prevp, p)
        pt, side = next(((intersecting_seg.intersectpoint(side), side)
                         for side in self.sides if side.intersects(intersecting_seg)), p)
        # This is to avoid rounding errors
        if not p is pt:
            if side.p1.x == side.p2.x:
                # Vertical
                pt.x = side.p1.x
            if side.p1.y == side.p2.y:
                # Horizontal
                pt.y = side.p1.y
        return pt

    def printtocanvas(self, canvas: tkinter.Canvas):
        poly = Polyline([self.ulc, Point(self.lrc.x, self.ulc.y),
                         self.lrc, Point(self.ulc.x, self.lrc.y), self.ulc])
        poly.printtocanvas(canvas, tags="frame")

    def printtosvg(self, dwg, offset=Point(0, 0)):
        points = [self.ulc, Point(self.lrc.x, self.ulc.y), self.lrc, Point(
            self.ulc.x, self.lrc.y), self.ulc]
        polypoints = [((p-offset).x, (p-offset).y) for p in points]
        dwg.add(dwg.polyline(polypoints, stroke="red", fill="none"))

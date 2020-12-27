# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import math
import itertools
import tkinter
from point import Point


class Segment:
    def __init__(self, p1: Point, p2: Point):
        self.p1 = p1
        self.p2 = p2

    def dist2point(self, p: Point):
        x1 = self.p1.x
        y1 = self.p1.y
        x2 = self.p2.x
        y2 = self.p2.y
        px = p.x
        py = p.y
        dx = x2 - x1
        dy = y2 - y1
        if dx == dy == 0:  # the segment's just a point
            return math.hypot(px - x1, py - y1)

        # Calculate the t that minimizes the distance.
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

        # See if this represents one of the segment's
        # end points or a point in the middle.
        if t < 0:
            dx = px - x1
            dy = py - y1
        elif t > 1:
            dx = px - x2
            dy = py - y2
        else:
            near_x = x1 + t * dx
            near_y = y1 + t * dy
            dx = px - near_x
            dy = py - near_y

        return math.hypot(dx, dy)

    def pointprojection(self, p: Point):
        if(self.p1.x == self.p2.x):
            return Point(self.p1.x,p.y)
        a = (self.p1.y-self.p2.y)/(self.p1.x-self.p2.x)
        c = self.p1.y - a*self.p1.x
        b = -1
        xp = (b*(b*p.x-a*p.y)-a*c)/(a*a+b*b)
        yp = (a*(-b*p.x+a*p.y)-b*c)/(a*a+b*b)
        p = Point(xp, yp)
        if (p-self.p1).r < self.length() and (p-self.p2).r < self.length():
            return p
        elif (p-self.p1).r < (p-self.p2).r:
            return self.p1
        else:
            return self.p2

    def length(self):
        return (self.p2-self.p1).r

    def dist2seg(self, other):
        if(self.intersects(other)):
            return 0
        distances = [self.dist2point(other.p1), self.dist2point(
            other.p2), other.dist2point(self.p1), other.dist2point(self.p2)]
        return min(distances)

    def angle(self):
        return math.atan2(self.p2.y-self.p1.y, self.p2.x-self.p1.x)

    def angle2seg(self, other):
        seg1 = self
        seg2 = other
        if self.p1 == other.p2:
            seg2 = Segment(other.p2, other.p1)
        if self.p2 == other.p2:
            seg1 = Segment(self.p2, self.p1)
            seg2 = Segment(other.p2, other.p1)
        if self.p2 == other.p1:
            seg1 = Segment(self.p2, self.p1)

        return abs(seg1.angle()-seg2.angle())
        # return min(diff,abs(math.pi-diff))

    def intersects(self, other):
        """ whether two segments in the plane intersect:
            one segment is (x11, y11) to (x12, y12)
            the other is   (x21, y21) to (x22, y22)
        """
        x11 = self.p1.x
        y11 = self.p1.y
        x12 = self.p2.x
        y12 = self.p2.y

        x21 = other.p1.x
        y21 = other.p1.y
        x22 = other.p2.x
        y22 = other.p2.y

        dx1 = x12 - x11
        dy1 = y12 - y11
        dx2 = x22 - x21
        dy2 = y22 - y21
        delta = dx2 * dy1 - dy2 * dx1
        if delta == 0:
            return False  # parallel segments
        s = (dx1 * (y21 - y11) + dy1 * (x11 - x21)) / delta
        t = (dx2 * (y11 - y21) + dy2 * (x21 - x11)) / (-delta)
        return (0 <= s <= 1) and (0 <= t <= 1)

    def intersectpoint(self, other):
        x1 = self.p1.x
        y1 = self.p1.y
        x2 = self.p2.x
        y2 = self.p2.y
        x3 = other.p1.x
        y3 = other.p1.y
        x4 = other.p2.x
        y4 = other.p2.y
        px = ((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4)) / \
            ((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))
        py = ((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4)) / \
            ((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))
        return Point(px, py)

    def pts(self):
        return self.p1, self.p2

    def sharespointwith(self, other):
        return any(p1 == p2 for p1, p2 in itertools.combinations([self.p1, self.p2, other.p1, other.p2], 2))

    def printtocanvas(self, canvas: tkinter.Canvas, color="red", width=2, scale=1, dis=Point(0, 0)):
        canvas.create_line(self.p1.x*scale+dis.x, self.p1.y*scale+dis.y,
                           self.p2.x*scale+dis.x, self.p2.y*scale+dis.y, fill=color, width=width)

# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import math

class Point:

    def __init__(self, x=None, y=None, r=None, a=None):
        self.r = 0.0
        self.a = 0.0
        self.x = 0.0
        self.y = 0.0

        if not x == None and not y == None:
            self.x = x
            self.y = y
            self._update_polar()
        elif not r == None and not a == None:
            self.r = r
            self.a = a
            self._update_cartesian()
        else:
            self.r = 0.0
            self.a = 0.0
            self.x = 0.0
            self.y = 0.0

    def _update_cartesian(self):
        self.x = self.r * math.cos(self.a)
        self.y = self.r * math.sin(self.a)

    def _update_polar(self):
        self.r = math.sqrt(self.x**2 + self.y**2)
        self.a = math.atan2(self.y, self.x)

    def setxy(self,x,y):
        self.x=x
        self.y=y
        self._update_polar()
    def xy(self):
        return (self.x, self.y)

    def rotate(self, rp, angle):
        s = math.sin(angle)
        c = math.cos(angle)
        q = self-rp
        self.x = (q.x*c-q.y*s)+rp.x
        self.y = (q.x*s+q.y*c)+rp.y
        self._update_polar()
        return self

    def traslate(self, tp):
        self.x += tp.x
        self.y += tp.y
        self._update_polar()
        return self

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self._update_polar()
        return self

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self._update_polar()
        return self

    def __mul__(self, val):
        return Point(r=self.r*val, a=self.a)

    def __rmul__(self, val):
        return Point(r=self.r*val, a=self.a)

    def __imul__(self, val):
        self.r *= val
        self._update_cartesian()
        return self

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self is other or (self.x == other.x and self.y == other.y)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

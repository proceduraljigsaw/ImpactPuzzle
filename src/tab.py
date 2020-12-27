# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import math
import tkinter
import itertools
import numpy as np
from enum import Enum
from numpy.random import uniform
from point import Point
from segment import Segment


class TabType(Enum):
    GAP = 0
    FRACTURE = 1
    JAGGED = 2
    LINE = 3


class Tab:
    def __init__(self, tabtype: TabType, p1: Point, p2: Point, rad_pos, ang_pos, radial, scaled_length, min_cl=2.0, cl_frac=0.33, tl_frac=0.5, tab_rel_depth=0.2, segvar=5.0, angvar=0.05, ndivs=5, invert=False):
        self.points = [p1, p2]
        self.rad_pos = rad_pos
        self.ang_pos = ang_pos
        self.radial = radial
        if scaled_length:
            self.scaled_length = min(self.span(), scaled_length)
        else:
            self.scaled_length = (p2-p1).r
        self.gap = False
        self.tabtype = tabtype

        if self.tabtype is TabType.GAP:
            self.make_gap()
        elif self.tabtype is TabType.FRACTURE:
            self.make_fracture(ndivs, segvar)
        elif self.tabtype is TabType.JAGGED:
            self.make_jagged(min_cl, cl_frac, tl_frac,
                             tab_rel_depth, segvar, angvar, invert)

    @classmethod
    def from_points(cls, tabtype, points, rad_pos, ang_pos, radial, scaled_length):
        # create dummy tab
        tab = Tab(TabType.LINE, points[0], points[0], rad_pos,
                  ang_pos, radial, scaled_length=scaled_length)
        tab.points = points
        tab.scaled_length = scaled_length
        tab.tabtype = tabtype
        if tab.tabtype is TabType.GAP:
            tab.gap = True
        else:
            tab.gap = False
        tab._calc_segments()
        tab._calc_centroid()
        return tab

    def make_gap(self):
        self.points = [self.points[0], self.points[-1]]
        self.gap = True
        self.tabtype = TabType.GAP
        self._calc_segments()
        self._calc_centroid()

    def make_line(self):
        self.points = [self.points[0], self.points[-1]]
        self.gap = False
        self.tabtype = TabType.LINE
        self._calc_segments()
        self._calc_centroid()

    def make_jagged(self, min_cl=2.0, cl_frac=0.33, tl_frac=0.5, tab_rel_depth=0.2, segvar=5.0, angvar=0.05, invert=False):
        p1, p2 = self.points[0], self.points[-1]
        if (self.span() * cl_frac < min_cl):
            self.make_line()
            return
        if (self.scaled_length * cl_frac < min_cl):
            self.scaled_length = self.span()
        length = (p2-p1).r
        angle = (p2-p1).a
        pp1 = Point(-length/2, 0)
        pp2 = Point(length/2, 0)

        target_side_dist = (length-self.scaled_length*cl_frac)/2.0
        target_top_len = self.scaled_length * tl_frac
        target_tab_angle = math.atan2(tab_rel_depth, (tl_frac-cl_frac)/2)
        target_tab_len = math.hypot(
            tab_rel_depth*self.scaled_length, (tl_frac-cl_frac)/2*self.scaled_length)
        segvar_pc = segvar / 100

        r1 = uniform(target_side_dist * (1-segvar_pc),
                     target_side_dist * (1+segvar_pc))
        a1 = uniform(-angvar*math.pi, angvar*math.pi)
        r2 = uniform(target_tab_len, target_tab_len * (1+2*segvar_pc))
        a2 = uniform((math.pi-a1-target_tab_angle)-math.pi *
                     angvar, (math.pi-a1-target_tab_angle)+math.pi*angvar)

        r3 = uniform(target_side_dist * (1-segvar_pc),
                     target_side_dist * (1+segvar_pc))
        a3 = uniform(-angvar*math.pi, angvar*math.pi)
        r4 = uniform(target_tab_len, target_tab_len * (1+2*segvar_pc))
        a4 = -uniform((math.pi-a3-target_tab_angle)-math.pi *
                      angvar, (math.pi-a3-target_tab_angle)+math.pi*angvar)

        # r3 = uniform(target_top_len * (1-segvar_pc),
        #                 target_top_len * (1+segvar_pc))
        # a3 = uniform(-angvar*math.pi, angvar*math.pi)
        # r4 = r2#target_tab_len#uniform(target_tab_len * (1-segvar_pc),target_tab_len * (1+segvar_pc))
        # a4 = -uniform((math.pi-a3-target_tab_angle)-math.pi *
        #                 angvar, (math.pi-a3-target_tab_angle)+math.pi*angvar)

        if invert:  # Randomly invert the tab
            a2 = -a2
            a4 = -a4
        self.points = [pp1, pp1 + Point(r=r1, a=a1), pp1 + Point(r=r1, a=a1)+Point(
            r=r2, a=a2), pp2-Point(r=r3, a=a3)-Point(r=r4, a=a4), pp2-Point(r=r3, a=a3), pp2]
        # self.points.append(pp1)
        # self.points.append(Point2D(r=r1, a=a1)+self.points[0])
        # self.points.append(Point2D(r=r2, a=a2)+self.points[1])
        # self.points.append(Point2D(r=r3, a=a3)+self.points[2])
        # self.points.append(Point2D(r=r4, a=a4)+self.points[3])
        # self.points.append(pp2)
        self.rotateandtranslate(pp1, angle, p1-pp1)
        self.points[0] = p1
        self.points[-1] = p2
        self.gap = False
        self.tabtype = TabType.JAGGED
        self._calc_segments()
        self._calc_centroid()

    def make_fracture(self, ndivs=5, jitter_pc=5):
        if ndivs == 0:
            self.make_line()
            return
        p1, p2 = self.points[0], self.points[-1]
        xs = np.linspace(p1.x, p2.x, ndivs)[1:-1]
        ys = np.linspace(p1.y, p2.y, ndivs)[1:-1]
        distance = (p2-p1).r
        xjitter = uniform(-distance*jitter_pc/100,
                          distance*jitter_pc/100, ndivs-2)
        yjitter = uniform(-distance*jitter_pc/100,
                          distance*jitter_pc/100, ndivs-2)
        pjitters = [Point(x+xj, y+yj)
                    for x, y, xj, yj in zip(xs, ys, xjitter, yjitter)]
        pjitters.insert(0, p1)
        pjitters.append(p2)
        self.points = pjitters
        self.gap = False
        self.tabtype = TabType.FRACTURE
        self._calc_segments()
        self._calc_centroid()
    
    def make_fromlib(self, prototype_points,tabtype,rj,aj):
        p1, p2 = self.points[0], self.points[-1]
        angle = (p2-p1).a
        span = (p2-p1).r
        self.points = [Point(r=p.r + uniform(-p.r,p.r)*rj/100, a=p.a)*span for p in prototype_points]
        self.rotateandtranslate(self.points[0], angle, p1-self.points[0])
        self.points[0] = p1
        self.points[-1] = p2
        self.gap = False
        self.tabtype = tabtype
        self._calc_segments()
        self._calc_centroid()


    def remake(self, min_cl=2.0, cl_frac=0.33, tl_frac=0.5, tab_rel_depth=0.2, segvar=5.0, angvar=0.05, invert=False):
        if self.tabtype is TabType.GAP:
            self.make_gap()
        elif self.tabtype is TabType.FRACTURE:
            self.make_fracture(jitter_pc=segvar)
        elif self.tabtype is TabType.JAGGED or self.tabtype is TabType.LINE:
            self.make_jagged(min_cl, cl_frac, tl_frac, tab_rel_depth, segvar, angvar, invert)

    def rotateandtranslate(self, rp, angle, tp):
        for p in self.points:
            p.rotate(rp, angle)
            # p.traslate(tp)
        for p in self.points:
            # p.rotate(rp,angle)
            p.traslate(tp)

    def flip(self):
        self.points[1:-1] = reversed([p.rotate(self.points[0], math.pi).traslate(
            self.points[-1]-self.points[0]) for p in self.points[1:-1]])
        self._calc_segments()
        self._calc_centroid()
        return self

    def _calc_centroid(self):
        self.centroid = Point(
            np.mean([p.x for p in self.points]), np.mean([p.y for p in self.points]))

    def _calc_segments(self):
        self.segments = [Segment(p1, p2)
                         for p1, p2 in zip(self.points, self.points[1:])]

    def self_intersects(self):
        if(len(self.segments) < 2):
            return False
        return any((not seg1.sharespointwith(seg2) and seg1.intersects(seg2)) for seg1, seg2 in itertools.combinations(self.segments, 2))

    def intersects(self, other):
        return any((not seg1.sharespointwith(seg2) and seg1.intersects(seg2)) for seg1, seg2 in itertools.product(self.segments, other.segments))

    def self_distance(self):
        if(len(self.segments) < 2):
            return self.segments[0].length()

        return min([seg1.dist2seg(seg2) for seg1, seg2 in itertools.combinations(self.segments, 2) if not seg1.sharespointwith(seg2)])

    def dist2tab(self, other, ignoreouter=False):
        segs1 = self.segments
        segs2 = other.segments
        if ignoreouter:
            if(self.intersects(other)):
                return 0
            if len(self.segments) > 2:
                segs1 = self.segments[1:-1]
            if len(other.segments) > 2:
                segs2 = other.segments[1:-1]

        return min([seg1.dist2seg(seg2) if not seg1.sharespointwith(seg2) else 1e10 for seg1, seg2 in itertools.product(segs1, segs2)])

    def angle2tab(self, other):
        segs1 = [self.segments[0], self.segments[-1]]
        segs2 = [other.segments[0], other.segments[-1]]
        seg1, seg2 = next(([seg1, seg2] for seg1, seg2 in itertools.product(
            segs1, segs2) if seg1.sharespointwith(seg2)))
        return seg1.angle2seg(seg2)

    def printtocanvas(self, canvas: tkinter.Canvas, color="black", width=1, tags="tab"):
        return [canvas.create_line(p1.x, p1.y, p2.x, p2.y, fill=color, width=width, tags=tags) for p1, p2 in zip(self.points, self.points[1:])]

    def endpoints(self):
        return [self.points[0], self.points[-1]]

    def sharespointwith(self, other):
        return any(p1 == p2 for p1, p2 in itertools.product(self.endpoints(), other.endpoints()))

    def span(self):
        return (self.points[-1]-self.points[0]).r

    def boundingbox(self):
        angle = (self.points[-1]-self.points[0]).a
        rpoints = [Point(p.x, p.y).rotate(self.points[0], -angle)
                   for p in self.points]
        miny = min([p.y for p in rpoints])
        maxy = max([p.y for p in rpoints])
        if abs(maxy - miny) < self.span()/10:
            maxy += self.span()/20
            miny -= self.span()/20
        pts = [Point(rpoints[0].x, maxy), Point(rpoints[-1].x, maxy),
               Point(rpoints[-1].x, miny), Point(rpoints[0].x, miny)]
        return map(lambda pt: pt.rotate(self.points[0], angle), pts)

    def setscaledlen(self, scaled_len):
        if scaled_len:
            self.scaled_length = min(self.span(), scaled_len)
        else:
            self.scaled_length = self.span()

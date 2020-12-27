# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import math
import tkinter
import itertools
from tab import Tab, TabType
from piece import Piece
from frame import RectangularFrame


class DRCChecker:
    @staticmethod
    def singletabckeck(tab: Tab, min_tab_length, frame: RectangularFrame):
        errs = [DRCShortTab.check(tab, min_tab_length,frame), DRCSelfIntersection.check(tab), DRCFrameIntersection.check(tab, frame)]
        return [e for e in errs if e]
    @staticmethod
    def tabtoframecheck(tab:Tab, min_seg_distance, frame:RectangularFrame):
        if len(tab.segments)> 2:
            dists = [seg1.dist2seg(seg2)  for seg1, seg2 in itertools.product(tab.segments[1:-1], frame.sides)]
            if len(dists) and 0< min(dists) < min_seg_distance:
                return DRCDistanceError(tab, frame, min(dists))
        return None
    @staticmethod
    def twotabckeck(tab1: Tab, tab2: Tab, min_seg_distance, min_ang, ndiv, checkextents=2):
        if tab1 and tab2 and not tab1.gap and not tab2.gap:
            if abs(tab1.rad_pos-tab2.rad_pos) <= checkextents and abs(tab1.ang_pos-tab2.ang_pos) % ndiv <= checkextents:
                dt = tab1.dist2tab(tab2, ignoreouter=True)
                if dt == 0:
                    return DRCIntersection(tab1, tab2)
                elif(dt < min_seg_distance) and ((tab1.tabtype is TabType.JAGGED) or (tab2.tabtype is TabType.JAGGED)):
                    return DRCDistanceError(tab1, tab2, dt)
                elif tab1.sharespointwith(tab2) and tab1.radial != tab2.radial and tab1.angle2tab(tab2) < min_ang:
                    return DRCAcute(tab1, tab2, tab1.angle2tab(tab2))


    @staticmethod
    def piececheck(piece: Piece):
        border = piece.border()
        jagsinborder = [tab for tab in border if tab.tabtype is TabType.JAGGED]
        if len(border) <= 2 and len(border) != len(jagsinborder):
            return DRCUnsupported(piece)
        elif len(border) <= 4 and len(jagsinborder) < 2:
            return DRCUnsupported(piece)
        elif len(border) > 4 and len(jagsinborder) < 3:
            return DRCUnsupported(piece)
        else:
            return None


class DRCError:
    def __init__(self, obj1, obj2):
        self.obj1 = obj1
        self.obj2 = obj2
        self.drawnobjects = []

    def unpaint(self, canvas: tkinter.Canvas):
        canvas.delete(self.drawnobjects)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (((self.obj1 is other.obj1) and (self.obj2 is other.obj2)) or ((self.obj1 is other.obj2) and (self.obj2 is other.obj1)))
        else:
            return False


class DRCShortTab(DRCError):
    def __init__(self, tab1: Tab):
        super().__init__(tab1, None)
        self.length = tab1.span()

    @staticmethod
    def check(tab: Tab, min_tab_length, frame=None):

        if tab and tab.rad_pos > 0 and (tab.span() < min_tab_length):
            if not frame or frame.ispointonborder(tab.points[0]) or frame.ispointonborder(tab.points[-1]):
                return DRCShortTab(tab)
        else:
            return None

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "shorttab"]):
        self.drawnobjects = self.obj1.printtocanvas(
            canvas, color="red", width=3, tags=tags)
        self.drawnobjects.append(canvas.create_text(self.obj1.centroid.x, self.obj1.centroid.y,
                                                    text='{:.1f}'.format(self.length), tags=tags))


class DRCSelfIntersection(DRCError):
    def __init__(self, tab1: Tab):
        super().__init__(tab1, None)

    @staticmethod
    def check(tab: Tab):
        if tab and tab.self_intersects():
            return DRCSelfIntersection(tab)
        else:
            return None

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "selfintersect"]):
        self.drawnobjects = self.obj1.printtocanvas(
            canvas, color="orange", width=3, tags=tags)


class DRCFrameIntersection(DRCError):
    def __init__(self, tab1: Tab):
        super().__init__(tab1, None)

    @staticmethod
    def check(tab: Tab, frame: RectangularFrame):
        if tab and frame and frame.intesercts(tab):
            return DRCFrameIntersection(tab)
        else:
            return None

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "frameintersect"]):
        self.drawnobjects = self.obj1.printtocanvas(
            canvas, color="blue", width=3, tags=tags)


class DRCIntersection(DRCError):
    def __init__(self, tab1: Tab, tab2: Tab):
        super().__init__(tab1, tab2)

    @staticmethod
    def check(tab: Tab, frame: RectangularFrame):
        if frame.intesercts(tab):
            return DRCFrameIntersection(tab)
        else:
            return None

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "intersect"]):
        self.drawnobjects = self.obj1.printtocanvas(
            canvas, color="yellow", width=3, tags=tags)
        self.drawnobjects.extend(self.obj2.printtocanvas(
            canvas, color="yellow", width=3, tags=tags))


class DRCDistanceError(DRCError):
    def __init__(self, tab1: Tab, obj2, min_distance):
        super().__init__(tab1, obj2)
        self.min_distance = min_distance

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "distance"]):
        self.drawnobjects = self.obj1.printtocanvas(canvas, color="violet", width=3, tags=tags)
        if type(self.obj2) == Tab:
            self.drawnobjects.extend(self.obj2.printtocanvas(canvas, color="violet", width=3, tags=tags))
            cx = (self.obj1.centroid.x + self.obj2.centroid.x)/2
            cy = (self.obj1.centroid.y + self.obj2.centroid.y)/2
            o2segs = self.obj2.segments
        else:
            cx= self.obj1.centroid.x
            cy= self.obj1.centroid.y
            o2segs = self.obj2.sides

        self.drawnobjects.append(canvas.create_text(cx, cy, text='{:.1f}'.format(self.min_distance), tags=tags))
        for p, seg in itertools.product(self.obj1.points, o2segs):
            if seg.dist2point(p) == self.min_distance:
                self.drawnobjects.append(canvas.create_line(
                    *p.xy(), *seg.pointprojection(p).xy(), fill="red", tags=tags))
        if type(self.obj2) == Tab:
            for p, seg in itertools.product(self.obj2.points, self.obj1.segments):
                if seg.dist2point(p) == self.min_distance:
                    self.drawnobjects.append(canvas.create_line(
                        *p.xy(), *seg.pointprojection(p).xy(), fill="red", tags=tags))


class DRCAcute(DRCError):
    def __init__(self, tab1: Tab, tab2: Tab, angle):
        super().__init__(tab1, tab2)
        self.angle = angle

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "distance"]):
        self.drawnobjects = self.obj1.printtocanvas(
            canvas, color="brown", width=3, tags=tags)
        self.drawnobjects.extend(self.obj2.printtocanvas(
            canvas, color="brown", width=3, tags=tags))
        cx = (self.obj1.centroid.x + self.obj2.centroid.x)/2
        cy = (self.obj1.centroid.y + self.obj2.centroid.y)/2
        self.drawnobjects.append(canvas.create_text(
            cx, cy, text='{:.1f}deg'.format(math.degrees(self.angle)), tags=tags))


class DRCUnsupported(DRCError):
    def __init__(self, piece: Piece):
        super().__init__(piece, None)

    def printtocanvas(self, canvas: tkinter.Canvas, tags=["drc", "distance"]):
        self.drawnobjects = [obj for tab in self.obj1.border(
        ) for obj in tab.printtocanvas(canvas, color="red", tags=tags)]

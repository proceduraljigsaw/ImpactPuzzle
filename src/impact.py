# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import tkinter
import itertools
import random
import svgwrite
import numpy as np
from point import Point
from numpy.random import *
from segment import Segment
from polyring import JaggedRing
from polyline import Polyline

from tab import Tab, TabType
from frame import RectangularFrame
from drcerror import *
from piece import Piece
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement


class Impact:

    @staticmethod
    def __tab_gen(frame, p1, p2, rad, ang, jagged, radial, scaled_length, cl_frac, tl_frac, tab_rel_depth, segvar, angvar, ndivs, p_gap, p_notjagged, tablib, p_tablib):
        if frame.ispointinside(p1) or frame.ispointinside(p2):
            # At least one point is inside the frame, get both inside and create the tab
            fp1 = frame.pointmovedtoborder(p1, p2)
            fp2 = frame.pointmovedtoborder(p2, p1)
            if(uniform() > p_gap):
                if (tablib and uniform() < p_tablib):
                    tab = Tab(TabType.GAP, fp1, fp2, rad, ang, radial, scaled_length)
                    prototab = choice(tablib)
                    tab.make_fromlib(prototab.points, prototab.tabtype,segvar,angvar)
                    if(uniform() > 0.5):
                        tab.flip()

                else:
                    if jagged and (uniform() > p_notjagged):
                        tab = Tab(TabType.JAGGED, fp1, fp2, rad, ang, radial, scaled_length, cl_frac=cl_frac, tl_frac=tl_frac,
                                tab_rel_depth=tab_rel_depth, segvar=segvar, angvar=angvar, invert=uniform() > 0.5)
                    else:
                        tab = Tab(TabType.FRACTURE, fp1, fp2, rad, ang,
                                radial, scaled_length, ndivs=ndivs, segvar=segvar)
            else:
                tab = Tab(TabType.GAP, fp1, fp2, rad,
                          ang, radial, scaled_length)
            return tab
        else:
            return None

    @staticmethod
    def __fill_tabs(matrix, frame, rings, cl_frac, tl_frac, tab_rel_depth, segvar, angvar, ndivs, p_agap, p_rgap, p_notjagged, tablib, p_tablib):
        max_rad, max_ang = 0, 0
        current_rad = len(rings)-1
        for r in reversed(rings):
            for i in range(0, len(r.points)-1):
                p1, p2 = r.points[i], r.points[(i+1) % len(r.points)]
                if r.inner_ring:
                    ip1, ip2 = r.inner_ring.points[i], r.inner_ring.points[(
                        i+1) % len(r.inner_ring.points)]
                    scaled_length = np.mean(
                        [(p2-p1).r, (p2-ip2).r, (p1-ip1).r, (ip2-ip1).r])
                    radt = Impact.__tab_gen(frame, ip1, p1, current_rad, i, True, True, scaled_length,
                                            cl_frac, tl_frac, tab_rel_depth, segvar, angvar, ndivs, p_rgap, p_notjagged, tablib, p_tablib)
                    matrix[i][current_rad-1][0] = radt
                    pg = p_agap
                    ptl = p_tablib
                else:
                    scaled_length = 0
                    radt = None
                    pg = 0
                    ptl = 0

                angt = Impact.__tab_gen(frame, p1, p2, current_rad, i, r.inner_ring, False, scaled_length,
                                        cl_frac, tl_frac, tab_rel_depth, segvar, angvar, ndivs, pg, p_notjagged, tablib, ptl)
                matrix[i][current_rad][1] = angt

                if(angt or radt):
                    max_rad = current_rad if current_rad > max_rad else max_rad
                    max_ang = i if i > max_ang else max_ang

            current_rad -= 1
        return max_rad, max_ang

    def __init__(self, frame, projectile, impact_pt, impact_radius, nrings, first_ring_delta, ndiv, ring_rj, ring_aj, skew_ang, max_skew, tab_rd, tab_tl, tab_bl, tab_rj, tab_aj, p_norad, p_noring, p_notab, tablib,p_tablib):
        radiuses = np.geomspace(min(impact_radius), max(impact_radius), nrings)
        distances = [radiuses[0]]
        extradistances = np.diff(radiuses)
        extradistances += (first_ring_delta)-np.min(extradistances)
        distances.extend(extradistances)

        rad_jitters = np.geomspace(ring_rj[0], ring_rj[1], nrings)
        ang_jitters = np.geomspace(ring_aj[0], ring_aj[1], nrings)
        rings = []
        self.ndiv = ndiv  # if not projectile else len(projectile.points)
        for rad, ring_rj, ring_aj in zip(distances, rad_jitters, ang_jitters):
            prev_ring = None if len(rings) == 0 else rings[-1]
            rings.append(JaggedRing(rad, self.ndiv, ring_aj, ring_rj,
                                    skew_angle=skew_ang, max_skew=max_skew, inner_ring=prev_ring, projectile=projectile))
        for r in rings:
            r.centeron(impact_pt)

        self.frame = frame
        self.tabmatrix = np.full((self.ndiv, nrings, 2), None)
        self.drcerrors = []
        # Fill tab matrix
        max_rad, max_ang = Impact.__fill_tabs(self.tabmatrix, frame, rings, cl_frac=tab_bl, tl_frac=tab_tl,
                                              tab_rel_depth=tab_rd, segvar=tab_rj, angvar=tab_aj, ndivs=5, p_agap=p_noring, p_rgap=p_norad, p_notjagged=p_notab, tablib= tablib, p_tablib=p_tablib)
        self.tabmatrix = self.tabmatrix[0:max_ang+1, 0:max_rad+1, :]
        self._calc_pieces()

    def getpiececount(self):
        #ngaps = len([tab for tab in self.tabmatrix.flat if tab and (tab.tabtype is TabType.GAP)])
        self._calc_pieces()
        return len(self.pieces)

    def topolylines(self):
        polylines = []
        poly = Polyline([])
        inpoly = False
        # Radials
        for i in range(0, self.tabmatrix.shape[0]):
            radialrow = self.tabmatrix[i, :, 0]
            for t in radialrow:
                if not t or t.gap:
                    if inpoly:
                        polylines.append(poly)
                        inpoly = False
                else:
                    if not inpoly:
                        poly = Polyline([])
                        inpoly = True
                    if not poly.add_points(t.points):
                        polylines.append(poly)
                        poly = Polyline(t.points)
            if inpoly:
                inpoly = False
                polylines.append(poly)
        # Angulars
        for i in range(0, self.tabmatrix.shape[1]):
            radialrow = self.tabmatrix[:, i, 1]
            for t in radialrow:
                if not t or t.gap:
                    if inpoly:
                        polylines.append(poly)
                        inpoly = False
                else:
                    if not inpoly:
                        poly = Polyline([])
                        inpoly = True
                    if not poly.add_points(t.points):
                        polylines.append(poly)
                        poly = Polyline(t.points)
            if inpoly:
                inpoly = False
                polylines.append(poly)
        return polylines

    def drc(self, min_seg_distance, min_tab_length, min_ang):
        # first check for tab self-intersection and short tabs
        self.drcerrors = []

        for tab in self.tabmatrix.flat:
            if tab and not tab.gap:
                self.drcerrors.extend(DRCChecker.singletabckeck(tab, min_tab_length, self.frame))
                err =DRCChecker.tabtoframecheck(tab, min_seg_distance, self.frame)
                if err:
                    self.drcerrors.append(err)
                
        for tab1, tab2 in itertools.combinations(self.tabmatrix.flat, 2):
            err = DRCChecker.twotabckeck(
                tab1, tab2, min_seg_distance, min_ang, self.ndiv, 2)
            if err:
                self.drcerrors.append(err)

        self._calc_pieces()

        for pc in self.pieces:
            err = DRCChecker.piececheck(pc)
            if err:
                self.drcerrors.append(err)

    @staticmethod
    def __buildpiece(i, j, visitmatrix, tabmatrix, pieces, piece):
        nr = tabmatrix.shape[0]
        nc = tabmatrix.shape[1]
        #bottom, left, up, right, up
        if j >= nc or visitmatrix[i][j]:
            return piece
        else:
            visitmatrix[i][j] = True
        cand_neigbors = []
        tabindexes = [(i, j, 1), (i, j, 0), (i, (j+1), 1), ((i+1) % nr, j, 0)]
        nextpcvisit = [(i, (j-1)), ((i-1) % nr, j),
                       (i, (j+1)), ((i+1) % nr, j)]
        for ti, npc in zip(tabindexes, nextpcvisit):
            if ti[1] < nc and tabmatrix[ti]:
                if tabmatrix[ti].gap:
                    piece = Impact.__buildpiece(
                        npc[0], npc[1], visitmatrix, tabmatrix, pieces, piece)
                else:
                    cand_neigbors.append(npc)
                    if piece:
                        piece.addtab(tabmatrix[ti])
                        pieces[i][j] = piece
                    else:
                        pieces[i][j] = Piece([tabmatrix[ti]])
                        piece = pieces[i][j]

        for cn in cand_neigbors:
            cand_neigbor = pieces[cn]
            if cand_neigbor and not piece is cand_neigbor:
                piece.addneighbor(cand_neigbor)
                cand_neigbor.addneighbor(piece)

        return piece

    def clear_drc(self):
        self.drcerrors = []
        
    def _calc_pieces(self):
        nr = self.tabmatrix.shape[0]
        nc = self.tabmatrix.shape[1]
        piecematrix = np.full((nr, nc), None)
        visitmatrix = np.full((nr, nc), False)

        self.pieces = [pc for i, j in itertools.product(range(0, nr), range(0, nc)) for pc in [
            Impact.__buildpiece(i, j, visitmatrix, self.tabmatrix, piecematrix, None)] if pc]

    def flipintersecting(self):
        for error in self.drcerrors:
            if isinstance(error, DRCIntersection):
                error.obj1.flip()
                error.obj2.flip()
                self.drcerrors.remove(error)

    def cleartaberrors(self, tab):
        for error in self.drcerrors:
            if (tab is error.obj1) or (tab is error.obj2):
                self.drcerrors.remove(error)

    def fliptab(self, tab):
        for error in self.drcerrors:
            if (tab is error.obj1) or (tab is error.obj2):
                self.drcerrors.remove(error)
        tab.flip()

    def printtocanvas(self, canvas: tkinter.Canvas):
        for tab in self.tabmatrix.flat:
            if tab and not tab.gap:
                tab.printtocanvas(canvas, tags="impactlines")

    def printtocanvass(self, canvas: tkinter.Canvas):
        for line in self.topolylines():
            line.printtocanvas(canvas, tags="impactlines")

    def toxml(self):
        impact = Element('impact', version='1.0', ndiv=str(self.ndiv))
        SubElement(impact, 'frame', type='rectangular', corners='{} {} {} {}'.format(
            *self.frame.ulc.xy(), *self.frame.lrc.xy()))
        tabmatrix = SubElement(impact, 'tabmatrix', rows=str(
            self.tabmatrix.shape[0]), columns=str(self.tabmatrix.shape[1]))
        for index, tab in np.ndenumerate(self.tabmatrix):
            if tab:
                SubElement(tabmatrix, 'tab', pos='{} {} {}'.format(*index), tabtype=tab.tabtype.name, scaledlen=str(
                    tab.scaled_length), pts=' '.join(map(str, [c for p in tab.points for c in p.xy()])))
        return ElementTree.tostring(impact)

    @classmethod
    def fromxml(cls, xmlfile):
        try:
            xmldoc = ElementTree.parse(xmlfile)
            impactroot = xmldoc.getroot()
            if impactroot.attrib['version'] == '1.0':
                ndiv = int(impactroot.attrib['ndiv'])
                framex = xmldoc.find('frame')
                if framex.attrib['type'] == 'rectangular':
                    coords = list(map(float, framex.attrib['corners'].split()))
                    frame = RectangularFrame(
                        Point(coords[0], coords[1]), Point(coords[2], coords[3]))
                matrix = xmldoc.find('tabmatrix')
                tabmatrix = np.full(
                    (int(matrix.attrib['rows']), int(matrix.attrib['columns']), 2), None)
                for tab in xmldoc.findall('tabmatrix/tab'):
                    tps = [Point(x, y) for x, y in zip(
                        *[iter(list(map(float, tab.attrib['pts'].split())))]*2)]
                    tpos = tuple(map(int, tab.attrib['pos'].split()))
                    ttype = TabType[tab.attrib['tabtype']]
                    slen = float(tab.attrib['scaledlen'])
                    tabmatrix[tpos] = Tab.from_points(
                        ttype, tps, tpos[1], tpos[0], not tpos[2], slen)
            else:
                print("Wrong Impact version")
                return None

            self = cls.__new__(cls)
            self.frame = frame
            self.ndiv = ndiv
            self.tabmatrix = tabmatrix
            self.drcerrors = []
            self._calc_pieces()
            return self
        except Exception as e:
            print(e)
            return None

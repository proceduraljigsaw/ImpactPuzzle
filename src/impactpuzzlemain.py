# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import random
import os
import sys
import math
import tkinter as tk
import svgwrite
import itertools
import numpy as np
from numpy.random import uniform
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from tkinter import filedialog
from point import Point
from polyring import JaggedRing
from impact import Impact
from frame import RectangularFrame
from projectile import Projectile
from drcerror import *
from projectile import ProjectileGUI
from segment import Segment
from tabeditor import TabPrototype, TabEditor
from tab import Tab


class SliderDesc():
    def __init__(self, text, minv, maxv, res, col, var, colspan=None):
        self.text = text
        self.min = minv
        self.max = maxv
        self.res = res
        self.col = col
        self.var = var
        self.colspan = colspan


class ButtonDesc():
    def __init__(self, text, command, col, textvar=None, colspan=None):
        self.text = text
        self.command = command
        self.textvar = textvar
        self.col = col
        self.colspan = colspan

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ShardGui():
    def __init__(self, root):
        self.root = root
        self.dframe = tk.Frame(self.root, width=1200, height=1000)
        self.aframe = tk.Frame(self.root, height=1000)
        self.aframe.pack(side="left")
        self.sframe = tk.Frame(self.root, width=250, height=1000)
        self.sframe.pack(side="right")
        self.canvas = tk.Canvas(self.dframe, bg="white", width=1200,
                                height=1000, cursor="tcross")

        self.rads = tk.IntVar(value=20)  # Impact Radius
        self.radf = tk.IntVar(value=500)  # Final Radius
        self.frs = tk.IntVar(value=15)  # Minimum first ring crown
        self.nrs = tk.IntVar(value=10)  # Number of rings
        self.nas = tk.IntVar(value=24)  # No. of angular divisions
        self.irjs = tk.DoubleVar(value=20)  # Initial Ring radius jitter %
        self.frjs = tk.DoubleVar(value=10)  # Final Ring radius jitter %
        self.iajs = tk.DoubleVar(value=20)  # Initial Ring angle jitter %
        self.fajs = tk.DoubleVar(value=10)  # Final Ring angle jitter %
        self.rtds = tk.DoubleVar(value=10)  # Relative tab depth %
        self.rtts = tk.DoubleVar(value=50)  # Relative tab top length %
        self.rtbs = tk.DoubleVar(value=33)  # Relative tab bottom length %
        self.trjs = tk.DoubleVar(value=10)  # Tab segment jitter %
        self.tajs = tk.DoubleVar(value=3)  # Tab angle jitter degrees
        self.pros = tk.DoubleVar(value=5)  # Prob. of no radial segment %
        self.paos = tk.DoubleVar(value=5)  # Prob. of no ring segment %
        self.pnjs = tk.DoubleVar(value=5)  # Probability of tab not jagged %
        self.ptfl = tk.DoubleVar(value=10)  # Probability of using a tab from the library
        self.drcs = tk.DoubleVar(value=2)  # Minimum distance for DRC
        self.drca = tk.DoubleVar(value=20)  # Minimum angle for DRC
        self.drced = tk.DoubleVar(value=6)  # Minimum edge-cutting tab length
        self.editbtext = tk.StringVar()
        self.editbtext.set("Set Edit Mode")

        impact_sliders = [SliderDesc("Impact Radius", 5, 100, 1, 0, self.rads),
                          SliderDesc("Final Radius", 100,
                                     2000, 1, 1, self.radf),
                          SliderDesc("Minimum first ring crown",
                                     5, 50, 1, 0, self.frs, 2),
                          SliderDesc("Number of rings", 2,
                                     50, 1, 0, self.nrs),
                          SliderDesc("No. of angular divisions",
                                     6, 50, 1, 1, self.nas),
                          SliderDesc("Initial Ring radius jitter %",
                                     1, 100, 1, 0, self.irjs),
                          SliderDesc("Final Ring radius jitter %",
                                     1, 100, 1, 1, self.frjs),
                          SliderDesc("Initial Ring angle jitter %",
                                     1, 100, 1, 0, self.iajs),
                          SliderDesc("Final Ring angle jitter %", 1, 100, 1, 1, self.fajs)]

        tab_sliders = [SliderDesc("Relative tab top length %", 0, 100, 1, 0, self.rtts),
                       SliderDesc("Relative tab bottom length %",
                                  0, 100, 1, 1, self.rtbs),
                       SliderDesc("Relative tab depth %", 0,
                                  100, 1, 0, self.rtds, 2),
                       SliderDesc("Tab segment jitter %",
                                  0, 100, 1, 0, self.trjs),
                       SliderDesc("Tab angle jitter degrees", 0, 20, 0.1, 1, self.tajs)]

        prob_sliders = [SliderDesc("Prob. of no radial seg %", 0, 100, 1, 0, self.pros),
                        SliderDesc("Prob. of no ring segment %", 0, 100, 1, 1, self.paos),
                        SliderDesc("Prob. of tab not jagged %", 0, 100, 1, 0, self.pnjs),
                        SliderDesc("Prob. of tab from library", 0, 100, 1, 1, self.ptfl)
                        ]

        drc_sliders = [SliderDesc("Minimum distance for DRC", 0.1, 10, 0.1, 0, self.drcs, 2),
                       SliderDesc("Minimum angle for DRC", 1, 45, 1, 0, self.drca, 2),
                       SliderDesc("Minimum tab length on edge", 1, 20, 0.1, 0, self.drced, 2)]

        mode_btns = [ButtonDesc(None, self.switchmode,
                                0, self.editbtext, colspan=2)]

        edit_btns = [ButtonDesc("Error Check", self.dodrc, 0),
                     ButtonDesc("Fix issues", self.fixissues, 1),
                     ButtonDesc("Delete Tab", self.deltab, 0),
                     ButtonDesc("Flip tab", self.fliptab, 1),
                     ButtonDesc("Make jagged tab", self.makejagged, 0,colspan=2),
                     ButtonDesc("Make fracture tab", self.makefracture, 0,colspan=2),
                     ButtonDesc("Regenerate all tabs", self.regentabs, 0,colspan=2)]

        loadsave_btns = [ButtonDesc("Load projectile", self.loadprojectile, 0),
                         ButtonDesc("Load Impact", self.loadimpact, 1),
                         ButtonDesc("Save Impact", self.saveimpact, 0),
                         ButtonDesc("Export SVG", self.exportsvg, 1),
                         ButtonDesc("Projectile Editor", self.openprojectile, 0, colspan=2),
                         ButtonDesc("Tab Creator", self.opentabeditor, 0, colspan=2),
                         ButtonDesc("Load tab library", self.loadtablibrary, 0, colspan=2),
                         ButtonDesc("Load settings", self.loadsettings, 0),
                         ButtonDesc("Save settings", self.savesettings, 1)]


        # Left side area

        l = tk.LabelFrame(self.aframe, text="Frame settings")
        l.grid(sticky='WE', padx=5, pady=5, column=0, columnspan=2)
        l.grid_columnconfigure(0,minsize=200)
        l.grid_columnconfigure(1,minsize=200)
        cur_row = 0
        la = tk.Label(l, text="Width")
        la.grid(row=cur_row, column=0, sticky='WE')
        la = tk.Label(l, text="Height")
        la.grid(row=cur_row, column=1, sticky='WE')
        cur_row += 1
        self.went = tk.Entry(l, width=4, justify='center')
        self.went.insert(0, "600")
        self.went.grid(row=cur_row, column=0, sticky='WE', padx=5, pady=5)
        self.hent = tk.Entry(l, width=4, justify='center')
        self.hent.insert(0, "400")
        self.hent.grid(row=cur_row, column=1, sticky='WE', padx=5, pady=5)
        cur_row += 1
        bt = tk.Button(l, text="Change frame size", command=self.setframesize)
        bt.grid(row=cur_row, column=0, columnspan=2,
                sticky='WE', padx=5, pady=5)

        self.impact_scales, _ = self.__scale_layout_group("Impact shape settings", self.aframe, 200, impact_sliders)
        self.impact_prob_scales, _ = self.__scale_layout_group("Impact probability settings", self.aframe, 200, prob_sliders)
        self.impact_tab_scales, tabgroup = self.__scale_layout_group("Tab settings", self.aframe, 200, tab_sliders, command=self.tab_preview)

        self.tabcanvas = tk.Canvas(tabgroup, bg="white", width=300, height=150)
        self.tabcanvas.grid(columnspan=2)


        # Right side area

        self.mode_buttons, _ = self.__button_layout_group( "Mode change", self.sframe, 100, mode_btns)
        self.drc_slides, _ = self.__scale_layout_group("Error check settings", self.sframe, 200, drc_sliders)
        self.edit_buttons, _ = self.__button_layout_group("Edit buttons", self.sframe, 100, edit_btns)
        self.loadsave_buttons, _ = self.__button_layout_group("Load and save", self.sframe, 100, loadsave_btns)

        self.infotxt = tk.Text(self.sframe, height=10, width=25)
        self.infotxt.grid(sticky='WE',padx=5, pady=5)

        self.dframe.pack(side="right")
        self.canvas.grid()
        self.canvas.focus_set()
        self.impact = None
        self.framesize = (600, 400)
        self.frame = RectangularFrame(Point((1200-self.framesize[0])/2, (1000-self.framesize[1])/2), Point(
            (1200-self.framesize[0])/2+self.framesize[0], (1000-self.framesize[1])/2+self.framesize[1]))
        self.arrow = None
        self.tabcentroids = None
        self.selectedtab = None
        self.selectedpiece = None
        self.selectedtablines = None
        self.editmode = True
        self.projectile = None
        self.draggingpoint = None
        self.draggingborderpoint = False
        self.undrag_fcid = None
        self.dragclick_fcid = None
        self.switchmode()
        self.frame.printtocanvas(self.canvas)
        self.referencecoords = self.get_current_frameref_coords()
        self.tab_preview(None)
        self.prototabs =[]

    def openprojectile(self):
        projectileGUIWindow = tk.Toplevel(self.root)
        if ( sys.platform.startswith('win')):
            projectileGUIWindow.iconbitmap(resource_path('assets/Shard.ico'))
        ProjectileGUI(projectileGUIWindow)

    def opentabeditor(self):
        tabEditorWindow = tk.Toplevel(self.root)
        if ( sys.platform.startswith('win')):
            tabEditorWindow.iconbitmap(resource_path('assets/Shard.ico'))
        TabEditor(tabEditorWindow)

    def loadtablibrary(self):
        self.root.filename = filedialog.askdirectory(title="Tab lib directory prototype")
        if self.root.filename:
            self.prototabs=[]
            for root,dirs,files in os.walk(self.root.filename):
                for file in files:
                    if file.endswith(".tab"):
                        print(file)
                        ptab = TabPrototype.fromxml(os.path.join(root,file))
                        if ptab:
                            self.prototabs.append(ptab)
        print(self.prototabs)

    def __button_layout_group(self, groupname, frame, length, descriptors):

        l = tk.LabelFrame(frame, text=groupname)
        l.grid(sticky='WE', padx=5, pady=5, columnspan=2)
        l.grid_columnconfigure(0,minsize=length)
        l.grid_columnconfigure(1,minsize=length)
        cur_row = 0
        groupitems = []
        for bt in descriptors:
            sc = tk.Button(l, text=bt.text,
                           textvariable=bt.textvar, command=bt.command)
            if not bt.col:
                cur_row += 1
            sc.grid(row=cur_row, column=bt.col, columnspan=bt.colspan,
                    sticky='WE', padx=5, pady=5),
            groupitems.append(sc)
        return groupitems, l

    def __scale_layout_group(self, groupname, frame, length, descriptors, command=None):
        l = tk.LabelFrame(frame, text=groupname)
        l.grid(sticky='WE', padx=5, pady=5, columnspan=2)
        cur_row = 0
        groupitems = []
        for sl in descriptors:
            sc = tk.Scale(l, length=length, label=sl.text, from_=sl.min, to=sl.max, resolution=sl.res,
                          variable=sl.var, orient=tk.HORIZONTAL, command=command if command else None)
            if not sl.col:
                cur_row += 1
            sc.grid(row=cur_row, column=sl.col, columnspan=sl.colspan)
            groupitems.append(sc)
        return groupitems, l

    def setframesize(self):
        try:
            width = int(self.went.get())
            height = int(self.hent.get())
            if (self.editmode):
                self.switchmode()
            self.framesize = (width, height)
            self.frame = RectangularFrame(Point((1200-self.framesize[0])/2, (1000-self.framesize[1])/2), Point(
                (1200-self.framesize[0])/2+self.framesize[0], (1000-self.framesize[1])/2+self.framesize[1]))
            self.impact = None
            self.reprint_impact()
            self.referencecoords = self.get_current_frameref_coords()
        except:
            pass

    def get_offs_and_scale(self):
        currentcoords = self.get_current_frameref_coords()
        scale = (currentcoords[2]-currentcoords[0]) / \
            (self.referencecoords[2]-self.referencecoords[0])
        if scale == 1:
            ox = 0
            oy = 0
        else:
            ox = (currentcoords[0]-self.referencecoords[0]*scale)/(1-scale)
            oy = (currentcoords[1]-self.referencecoords[1]*scale)/(1-scale)
        offs = [ox, oy]
        return offs, scale

    def get_current_frameref_coords(self):
        return self.canvas.coords(self.canvas.find_withtag("frame")[0])

    def switchmode(self):
        self.editmode = not self.editmode
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Button-3>")
        self.canvas.unbind("<ButtonRelease-3>")
        self.canvas.unbind("<B3-Motion>")
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        if self.editmode:
            self.unbindprojectile()
            self.canvas.delete("projectile")
            self.editbtext.set("Set Draw Mode")
            self.canvas.bind("<Button-3>", self.startmoving)
            self.canvas.bind("<B3-Motion>", self.move)
            self.canvas.bind("<ButtonRelease-3>", self.stopmoving)
            self.canvas.bind("<MouseWheel>", self.mouse_wheel)
            # with Linux OS
            self.canvas.bind("<Button-4>", self.mouse_wheel)
            self.canvas.bind("<Button-5>", self.mouse_wheel)
            for sl in self.impact_scales + self.impact_prob_scales:
                sl.config(state=tk.DISABLED)
                sl.config(fg="gray")
            for bt in self.edit_buttons:
                bt.config(state=tk.NORMAL)
            self.painttabselectors()

        else:
            for sl in self.impact_scales + self.impact_prob_scales:
                sl.config(state=tk.NORMAL)
                sl.config(fg="black")
            for bt in self.edit_buttons:
                bt.config(state=tk.DISABLED)
            self.canvas.bind("<Button-1>", self.touchpoint)
            self.canvas.bind("<B1-Motion>", self.movepoint)
            self.canvas.bind("<ButtonRelease-1>", self.paintcrash)
            self.editbtext.set("Set Edit Mode")
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.canvas.delete("all")
            self.frame.printtocanvas(self.canvas)
            if(self.impact):
                self.impact.printtocanvas(self.canvas)
                self.impact.clear_drc()
                self.printpiececount()
            if self.projectile:
                self.bindprojectile()

    def tab_preview(self, event):
        colors = ['gray64', 'gray65',
                  'gray66', 'gray67', 'gray68', 'gray69', 'gray70', 'gray71', 'gray72', 'gray73', 'gray74',
                  'gray75', 'gray76', 'gray77', 'gray78', 'gray79', 'gray80', 'gray81', 'gray82', 'gray83',
                  'gray84', 'gray85', 'gray86', 'gray87', 'gray88', 'gray89', 'gray90', 'gray91', 'gray92',
                  'gray93', 'gray94', 'gray95', 'gray97', 'gray98', 'gray99']
        self.tabcanvas.delete("all")
        for color in reversed(colors):
            ptab = Tab(TabType.JAGGED, Point(10, 100),  Point(290, 100), 0, 0, False, 0, cl_frac=self.rtbs.get()/100, tl_frac=self.rtts.get() /
                       100, tab_rel_depth=self.rtds.get()/100, segvar=self.trjs.get(), angvar=np.deg2rad(self.tajs.get()), invert=True)
            ptab.printtocanvas(self.tabcanvas, color=color)
        ptab = Tab(TabType.JAGGED, Point(10, 100),  Point(290, 100), 0, 0, False, 0, cl_frac=self.rtbs.get(
        )/100, tl_frac=self.rtts.get()/100, tab_rel_depth=self.rtds.get()/100, segvar=0, angvar=0, invert=True)
        ptab.printtocanvas(self.tabcanvas, width=2)

    def unbindprojectile(self):
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<MouseWheel>")
        # with Linux OS
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.canvas.unbind("<Key>")

    def bindprojectile(self):
        self.canvas.bind("<Motion>", self.paintprojectile)
        self.canvas.bind("<MouseWheel>", self.scaleprojectile)
        # with Linux OS
        self.canvas.bind("<Button-4>", self.scaleprojectile)
        self.canvas.bind("<Button-5>", self.scaleprojectile)
        self.canvas.bind("<Key>", self.rotateprojectile)

    def rotateprojectile(self, event):
        if(event.keysym in ('q', 'Q')):
            self.projectile.rotate(-math.pi/180)
            self.paintprojectile(event)
        if(event.keysym in ('e', 'E')):
            self.projectile.rotate(math.pi/180)
            self.paintprojectile(event)

    def scaleprojectile(self, event):
        if event.num == 5 or event.delta == -120:
            self.projectile.scale(0.9)
        if event.num == 4 or event.delta == 120:
            self.projectile.scale(1.1)
        self.paintprojectile(event)

    def touchpoint(self, event):
        if self.arrow:
            self.canvas.delete(self.arrow)
        self.arrow = self.canvas.create_line(self.canvas.canvasx(event.x), self.canvas.canvasy(
            event.y), self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), fill="red", width=2, arrow=tk.LAST)

    def movepoint(self, event):
        if self.arrow:
            cc = self.canvas.coords(self.arrow)
            self.canvas.coords(self.arrow, cc[0], cc[1], self.canvas.canvasx(
                event.x), self.canvas.canvasy(event.y))

    def paintprojectile(self, event):
        self.canvas.delete("projectile")
        if self.projectile:
            self.projectile.printtocanvas(self.canvas, offset=Point(
                self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)), tags="projectile")

    def undrag(self, event):
        self.draggingpoint = None
        self.canvas.delete("draglines")
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Button-3>", self.undrag_fcid)
        self.canvas.bind("<Button-3>", self.startmoving)
        self.canvas.unbind("<Button-1>", self.dragclick_fcid)
        self.canvas.unbind("<ButtonRelease-1>")

    def modpoint(self, event, pos, borderdrag):
        self.draggingpoint = pos
        self.draggingborderpoint = borderdrag
        self.canvas.bind("<Motion>", self.dragpoint)
        self.canvas.unbind("<Button-3>")
        self.undrag_fcid = self.canvas.bind("<Button-3>", self.undrag)
        self.canvas.bind("<ButtonRelease-1>", self.modpoint_onrelease)

    def modpoint_onrelease(self, event):
        self.dragclick_fcid = self.canvas.bind("<Button-1>", self.setnewpoint)

    def dragpoint(self, event):
        self.canvas.delete("draglines")
        offs, scale = self.get_offs_and_scale()
        if self.impact and self.draggingpoint:
            i = self.draggingpoint[0]
            j = self.draggingpoint[1]
            nr = self.impact.tabmatrix.shape[0]
            tabindexes = [((i, j, 1), -1), ((i, j, 0), -1),
                          ((i, (j-1), 0), 0), (((i-1) % nr, j, 1), 0)]
            pts = [self.impact.tabmatrix[idx[0]].points[idx[1]]
                   for idx in tabindexes if idx[0][1] >= 0 and idx[0][0] < nr and self.impact.tabmatrix[idx[0]]]
            newpt = Point((self.canvas.canvasx(
                event.x)-offs[0])/scale+offs[0], (self.canvas.canvasy(event.y)-offs[1])/scale+offs[1])
            # # self.draggingborderpoint = self.draggingborderpoint and len(pts)<4
            dragok = not self.draggingborderpoint or self.frame.ispointonborder(
                self.frame.pointmovedtoborder(newpt, pts[0]))
            for p in pts:
                self.canvas.create_line(self.canvas.canvasx(event.x), self.canvas.canvasy(
                    event.y), (p.x-offs[0])*scale+offs[0], (p.y-offs[1])*scale+offs[1], fill="blue" if dragok else "red", tags="draglines")

    def setnewpoint(self, event):
        if self.impact and self.draggingpoint:
            offs, scale = self.get_offs_and_scale()
            i = self.draggingpoint[0]
            j = self.draggingpoint[1]
            self.undrag(None)
            nr = self.impact.tabmatrix.shape[0]
            nc = self.impact.tabmatrix.shape[0]
            tabindexes = [((i, j, 1), -0), ((i, j, 0), -0),
                          ((i, (j-1), 0), -1), (((i-1) % nr, j, 1), -1)]
            newpt = Point((self.canvas.canvasx(
                event.x)-offs[0])/scale+offs[0], (self.canvas.canvasy(event.y)-offs[1])/scale+offs[1])

            tabs = []
            # First we modify the endpoint
            for idx in tabindexes:
                if idx[0][1] >= 0 and idx[0][0] < nr and self.impact.tabmatrix[idx[0]]:
                    tabs.append(self.impact.tabmatrix[idx[0]])
                    pt = self.frame.pointmovedtoborder(
                        newpt, self.impact.tabmatrix[idx[0]].points[-(idx[1]+1)])
                    if self.draggingborderpoint and not self.frame.ispointonborder(pt):
                        return
                    self.impact.tabmatrix[idx[0]].points[idx[1]] = pt
                    if not self.frame.ispointinside(self.impact.tabmatrix[idx[0]].points[0], True) and not self.frame.ispointinside(self.impact.tabmatrix[idx[0]].points[-1], True):
                        self.impact.tabmatrix[idx[0]] = None
            # Now recalculate the scaled distance and redraw
            for idx in tabindexes:
                if idx[0][1] >= 0 and idx[0][0] < nr and self.impact.tabmatrix[idx[0]]:
                    ni = idx[0][0]
                    nj = idx[0][1]
                    pindexes = [(ni, nj, 1), (ni, nj-1, 1), (ni, nj-1, 0), ((ni+1) % nr, nj-1, 0)] if idx[0][2] else [(ni, nj, 0), (ni, nj, 1), ((ni+1) % nr, nj, 0), (ni, (nj+1), 1)]
                    scaledlen = np.mean([self.impact.tabmatrix[pidx].span() for pidx in pindexes if pidx[1] >= 0 and pidx[1] < nc and self.impact.tabmatrix[pidx]])
                    self.impact.tabmatrix[idx[0]].setscaledlen(scaledlen)
                    self.impact.tabmatrix[idx[0]].remake(cl_frac=self.rtbs.get()/100, tl_frac=self.rtts.get()/100, tab_rel_depth=self.rtds.get()/100, segvar=self.trjs.get(), angvar=np.deg2rad(self.tajs.get()), invert=uniform() > 0.5)
            self._post_tabmod(tabs)

    def painttabselectors(self):
        offs, scale = self.get_offs_and_scale()
        self.canvas.delete("selector")
        if self.impact:
            for tab in self.impact.tabmatrix.flat:
                if tab:
                    coords = [(p.xy()) for p in tab.boundingbox()]
                    if tab.gap:
                        self.canvas.create_line(
                            *tab.points[0].xy(), *tab.points[-1].xy(), fill="red", dash=(3, 3), tags='selector')
                    self.canvas.tag_bind(self.canvas.create_polygon(*coords, outline="", activeoutline="red", fill="green", width=1,
                                                                    stipple="@"+resource_path("assets/transparent.xbm"), tags="selector"), "<Button-1>", lambda event, tab=tab: self.selectTab(tab))
            for i, j in itertools.product(range(0, self.impact.tabmatrix.shape[0]), range(0, self.impact.tabmatrix.shape[1])):
                tab = self.impact.tabmatrix[i][j][0]
                tab2 = self.impact.tabmatrix[i][j][1]
                pt = tab.points[0] if tab else tab2.points[0] if tab2 else None
                rads = [t.scaled_length/30 for t in [tab,tab2] if t]
                rad = max(rads) if rads else None
                # if tab:
                #     self.canvas.create_text(
                #         tab.centroid.x, tab.centroid.y, text="{},{},{}".format(i, j, 0), tags="selector")
                # if tab2:
                #     self.canvas.create_text(
                #         tab2.centroid.x, tab2.centroid.y, text="{},{},{}".format(i, j, 1), tags="selector")
                if pt:
                    self.canvas.tag_bind(self.canvas.create_oval(pt.x-rad, pt.y-rad, pt.x+rad, pt.y+rad, outline="blue", activefill="green",
                                                                 fill="blue", width=1, tags="selector"), "<Button-1>", lambda event, bd=self.frame.ispointonborder(pt), pos=(i, j): self.modpoint(event, pos, bd))
                if tab and not self.frame.ispointinside(tab.points[-1], True):
                    self.canvas.tag_bind(self.canvas.create_oval(tab.points[-1].x-rad, tab.points[-1].y-rad, tab.points[-1].x+rad, tab.points[-1].y+rad, outline="blue",
                                                                 activefill="green", fill="blue", width=1, tags="selector"), "<Button-1>", lambda event, bd=True, pos=(i, j+1): self.modpoint(event, pos, bd))
                if tab2 and not self.frame.ispointinside(tab2.points[-1], True):
                    self.canvas.tag_bind(self.canvas.create_oval(tab2.points[-1].x-rad, tab2.points[-1].y-rad, tab2.points[-1].x+rad, tab2.points[-1].y+rad,
                                                                 outline="blue", activefill="green", fill="blue", width=1, tags="selector"), "<Button-1>", lambda event, bd=True, pos=(i+1, j): self.modpoint(event, pos, bd))

        self.canvas.scale("selector", offs[0], offs[1], scale, scale)

    def paintpieceselectors(self):
        offs, scale = self.get_offs_and_scale()
        self.canvas.delete("selector")
        if self.impact:
            i = 0
            for pc in self.impact.pieces:
                cp = pc.centroid
                radius = 3
                self.canvas.tag_bind(self.canvas.create_rectangle(cp.x-radius, cp.y-radius, cp.x + radius, cp.y+radius,
                                                                  outline="red", fill="green", width=1, stipple="@"+resource_path("assets/transparent.xbm"), tags="selector"), "<Button-1>", lambda event, pc=pc: self.selectPiece(pc))
                self.canvas.create_text(
                    cp.x, cp.y, text=str(i), tags="selector")
                i = i+1
        self.canvas.scale("selector", offs[0], offs[1], scale, scale)
    
    def printpiececount(self):
        drctext = 'Pieces: {}\n'
        self.infotxt.delete(1.0, tk.END)
        self.infotxt.insert(tk.END, drctext.format(self.impact.getpiececount()))

    def paintcrash(self, event):

        cc = self.canvas.coords(self.arrow)
        impactpt = Point(cc[0], cc[1])
        drag = Point(cc[2], cc[3])
        skew_ang = (drag-impactpt).a
        max_skew = (((drag-impactpt).r / 1000) * 5)+1
        self.impact = Impact(self.frame, self.projectile, impactpt, (self.rads.get(), self.radf.get()), self.nrs.get(), self.frs.get(), self.nas.get(), (self.irjs.get(), self.frjs.get()), (self.iajs.get(), self.fajs.get(
        )), skew_ang, max_skew, self.rtds.get()/100, self.rtts.get()/100, self.rtbs.get()/100, self.trjs.get(), np.deg2rad(self.tajs.get()), self.pros.get()/100, self.paos.get()/100, self.pnjs.get()/100, self.prototabs, self.ptfl.get()/100)
        self.printpiececount()
        self.selectedtab = None
        self.reprint_impact()

    def exportsvg(self):
        if self.impact:
            xs = [p.x for tab in self.impact.tabmatrix.flat if tab and not tab.gap for p in tab.points]
            ys = [p.y for tab in self.impact.tabmatrix.flat if tab and not tab.gap for p in tab.points]
            minx = min(min(xs),self.frame.ulc.x)
            miny = min(min(ys),self.frame.ulc.y)
            maxx = max(max(xs),self.frame.lrc.x)
            maxy = max(max(ys),self.frame.lrc.y)
            width = maxx-minx
            height = maxy-miny
            offset = Point(minx, miny)

            self.root.filename = filedialog.asksaveasfilename(
                title="Save SVG", filetypes=(("svg files", "*.svg"), ("all files", "*.*")))
            if self.root.filename:
                if not self.root.filename.endswith(".svg"):
                    self.root.filename += ".svg"

                dwg = svgwrite.Drawing(self.root.filename, size=(
                    str(width)+'mm', str(height)+'mm'), viewBox=('0 0 {} {}'.format(width, height)))

                for polyline in self.impact.topolylines():
                    polyline.printtosvg(dwg, offset)
                self.frame.printtosvg(dwg, offset)
                dwg.save()
    def savesettings(self):
        savevars =[ ("rads",self.rads),
                    ("radf",self.radf),
                    ("frs",self.frs),
                    ("nrs",self.nrs),
                    ("nas",self.nas),
                    ("irjs",self.irjs),
                    ("frjs",self.frjs),
                    ("iajs",self.iajs),
                    ("fajs",self.fajs),
                    ("rtds",self.rtds),
                    ("rtts",self.rtts),
                    ("rtbs",self.rtbs),
                    ("trjs",self.trjs),
                    ("tajs",self.tajs),
                    ("pros",self.pros),
                    ("paos",self.paos),
                    ("pnjs",self.pnjs),
                    ("ptfl",self.ptfl),
                    ("drcs",self.drcs),
                    ("drca",self.drca),
                    ("drced",self.drced)]

        self.root.filename = filedialog.asksaveasfilename(title="Save Settings", filetypes=(("Settings Files", "*.set"), ("all files", "*.*")))
        if(self.root.filename):
            if not self.root.filename.endswith(".set"):
                self.root.filename += ".set"     
            settings = Element('impactsettings', version='1.1')
            for var in savevars:
                SubElement(settings, var[0],val=str(var[1].get()))
            filecontent= ElementTree.tostring(settings)
            with open(self.root.filename, 'wb') as settingsfile:
                settingsfile.write(filecontent)


    def loadsettings(self):
        savevars =[ ("rads",self.rads),
            ("radf",self.radf),
            ("frs",self.frs),
            ("nrs",self.nrs),
            ("nas",self.nas),
            ("irjs",self.irjs),
            ("frjs",self.frjs),
            ("iajs",self.iajs),
            ("fajs",self.fajs),
            ("rtds",self.rtds),
            ("rtts",self.rtts),
            ("rtbs",self.rtbs),
            ("trjs",self.trjs),
            ("tajs",self.tajs),
            ("pros",self.pros),
            ("paos",self.paos),
            ("pnjs",self.pnjs),
            ("ptfl",self.ptfl),
            ("drcs",self.drcs),
            ("drca",self.drca),
            ("drced",self.drced)]
        self.root.filename = filedialog.askopenfilename(title="Load Settings", filetypes=(("Settings Files", "*.set"), ("all files", "*.*")))
        if(self.root.filename):
            try:
                xmldoc = ElementTree.parse(self.root.filename)
                impactroot = xmldoc.getroot()
                if impactroot.attrib['version'] == '1.1':
                    for var in savevars:
                        entry = xmldoc.find(var[0])
                        if not entry==None and not entry.attrib['val'] == None:
                            var[1].set(float(entry.attrib['val']))
  
                else:
                    print("Wrong Settings version")
     
            except Exception as e:
                print(e)
            self.tab_preview(None)


    def saveimpact(self):
        if self.impact:
            self.root.filename = filedialog.asksaveasfilename(
                title="Save Impact", filetypes=(("Impact Files", "*.imp"), ("all files", "*.*")))
            if not self.root.filename.endswith(".imp"):
                self.root.filename += ".imp"
            with open(self.root.filename, 'wb') as impactfile:
                impactfile.write(self.impact.toxml())

    def loadimpact(self):
        self.root.filename = filedialog.askopenfilename(
            title="Load Impact", filetypes=(("Impact Files", "*.imp"), ("all files", "*.*")))
        newimpact = Impact.fromxml(self.root.filename)
        if(newimpact):
            self.impact = newimpact
            self.frame = newimpact.frame
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.canvas.delete("all")
            self.frame.printtocanvas(self.canvas)
            self.referencecoords = self.get_current_frameref_coords()
            self.impact.printtocanvas(self.canvas)
            self.printpiececount()
            self.selectedtab = None
            if self.editmode:
                self.painttabselectors()
            else:
                self.switchmode()

    def loadprojectile(self):
        self.root.filename = filedialog.askopenfilename(title="Load Projectile", filetypes=(
            ("Projectile Files", "*.pro"), ("all files", "*.*")))
        if(self.root.filename):
            newproj = Projectile.fromxml(self.root.filename)
            if(newproj):
                self.projectile = newproj
                if not self.editmode:
                    self.bindprojectile()
        else:
            if not self.editmode:
                self.unbindprojectile()
            self.projectile = None
            self.paintprojectile(None)

    def print_selected_tab(self):
        self.canvas.delete("selected_tab")
        if(self.selectedtab):
            offs, scale = self.get_offs_and_scale()
            self.selectedtab.printtocanvas(
                self.canvas, color="green", width=3, tags="selected_tab")
            self.canvas.scale("selected_tab", offs[0], offs[1], scale, scale)

    def print_selected_piece(self):
        self.canvas.delete("selected_piece")
        offs, scale = self.get_offs_and_scale()
        i = 0
        for piece in self.selectedpiece.neigbors:
            for tab in piece.tabs:
                tab.printtocanvas(
                    self.canvas, color="red", width=3, tags="selected_piece")
        for tab in self.selectedpiece.tabs:
            tab.printtocanvas(
                self.canvas, color="green", width=3, tags="selected_piece")
            # self.canvas.create_text(
            #     tab.centroid.x, tab.centroid.y, text=str(i), tags="selected_piece")
            # i = i+1

        for tab in self.selectedpiece.border():
            tab.printtocanvas(
                self.canvas, color="blue", width=3, tags="selected_piece")
            self.canvas.create_text(
                tab.centroid.x, tab.centroid.y, text=str(i), tags="selected_piece")
            i = i+1
        self.canvas.scale("selected_piece", offs[0], offs[1], scale, scale)

    def selectTab(self, tab):
        self.canvas.delete("selected_tab")
        if tab is self.selectedtab:
            self.selectedtab = None
        else:
            self.selectedtab = tab
            self.print_selected_tab()

    def selectPiece(self, pc):
        self.canvas.delete("selected_piece")
        if pc is self.selectedpiece:
            self.selectedpiece = None
        else:
            self.selectedpiece = pc
            self.print_selected_piece()

    def _post_tabmod(self, tabs):
        for tab in tabs:
            self.impact.cleartaberrors(tab)
        self.reprint_impact()
        self.paintdrc()
        self.painttabselectors()
        self.print_selected_tab()

    def fliptab(self):
        if(self.impact and self.selectedtab):
            self.selectedtab.flip()
            self._post_tabmod([self.selectedtab])

    def deltab(self):
        if self.selectedtab:
            self.selectedtab.make_gap()
            self._post_tabmod([self.selectedtab])

    def makejagged(self):
        if self.selectedtab:
            self.selectedtab.make_jagged(cl_frac=self.rtbs.get()/100, tl_frac=self.rtts.get(
            )/100, tab_rel_depth=self.rtds.get()/100, segvar=self.trjs.get(), angvar=np.deg2rad(self.tajs.get()))
            self._post_tabmod([self.selectedtab])

    def makefracture(self):
        if self.selectedtab:
            self.selectedtab.make_fracture(jitter_pc=self.trjs.get())
            self._post_tabmod([self.selectedtab])
    
    def regentabs(self):
        for t in self.impact.tabmatrix.flatten():
            if t:
                if t.tabtype is TabType.FRACTURE:
                    t.make_fracture(jitter_pc=self.trjs.get())
                elif t.tabtype is TabType.JAGGED or t.tabtype is TabType.LINE:
                    t.make_jagged(cl_frac=self.rtbs.get()/100, tl_frac=self.rtts.get()/100, tab_rel_depth=self.rtds.get()/100, segvar=self.trjs.get(), angvar=np.deg2rad(self.tajs.get()))
        self.impact.clear_drc()
        self._post_tabmod([])

    def fixissues(self):
        tabstodelete = set([])
        tabstoflip = set([])
        tabstoreduce = set([])
        tabstodejitter = set([])
        shorttabsonedge = set([])
        for err in self.impact.drcerrors:
            if isinstance(err, DRCFrameIntersection):
                tabstodelete.add(err.obj1)
            if isinstance(err, DRCShortTab) and self.impact.frame.intersects_strict(err.obj1):
                shorttabsonedge.add(err.obj1)
            if isinstance(err, DRCSelfIntersection):
                tabstodejitter.add(err.obj1)
            if isinstance(err, DRCAcute):
                if(uniform() > 0.5 or err.obj1.tabtype is TabType.FRACTURE):
                    tabstodelete.add(err.obj1)
                else:
                    tabstodelete.add(err.obj2)
            if isinstance(err, DRCIntersection) or isinstance(err, DRCDistanceError):
                if type(err.obj2) != Tab:
                    tabstodelete.add(err.obj1)
                elif err.obj1.tabtype is TabType.FRACTURE:
                    tabstoflip.add(err.obj2)
                elif err.obj1.tabtype is TabType.FRACTURE:
                    tabstoflip.add(err.obj1)
                elif(uniform() > 0.5):
                    tabstoflip.add(err.obj1)
                    tabstoreduce.add(err.obj2)
                else:
                    tabstoflip.add(err.obj2)
                    tabstoreduce.add(err.obj1)

        for tab in tabstodelete:
            if tab.rad_pos > 0:  # Don't delete tabs from the first ring
                tab.make_gap()
                self.impact.cleartaberrors(tab)

        for tab in tabstoflip:
            self.impact.fliptab(tab)

        for tab in tabstoreduce:
            if tab.tabtype is TabType.JAGGED:
                tab.make_jagged(cl_frac=self.rtbs.get()/200, tl_frac=self.rtts.get()/200, tab_rel_depth=self.rtds.get(
                )/200, segvar=self.trjs.get()/2, angvar=np.deg2rad(self.tajs.get()/2))
                self.impact.cleartaberrors(tab)

        for tab in tabstodejitter:
            if tab.tabtype is TabType.JAGGED:
                tab.make_jagged(cl_frac=self.rtbs.get()/100, tl_frac=self.rtts.get() /
                                100, tab_rel_depth=self.rtds.get()/100, segvar=0, angvar=0)
                self.impact.cleartaberrors(tab)

        self.reprint_impact()
        self.painttabselectors()
        # for tab in tabstoreduce:
        #     tab.printtocanvas(self.canvas,color="green",width="3",tags=["tab","reduced"])
        # offs,scale = self.get_offs_and_scale()
        # self.canvas.scale("reduced", offs[0], offs[1], scale, scale)
        # impact.printcorners(canvas)

    def reprint_impact(self):
        offs, scale = self.get_offs_and_scale()
        self.canvas.delete("all")
        self.frame.printtocanvas(self.canvas)
        if(self.impact):
            self.impact.printtocanvas(self.canvas)

        self.canvas.scale("all", offs[0], offs[1], scale, scale)

    def paintdrc(self):
        offs, scale = self.get_offs_and_scale()
        self.canvas.delete("drc")
        for error in self.impact.drcerrors:
            error.printtocanvas(self.canvas)
        self.canvas.scale("drc", offs[0], offs[1], scale, scale)

    def dodrc(self):
        if self.impact:
            self.impact.drc(self.drcs.get(), self.drced.get(), math.radians(self.drca.get()))
            self.paintdrc()
            self.painttabselectors()
            drctext = ('Short Tabs on edge:{}\n'
                       'Self-Intersections:{}\n'
                       'Tab-tab Intersections:{}\n'
                       'Frame Intersections:{}\n'
                       'Small Distance:{}\n'
                       'Acute Angle:{}\n'
                       'Unsupported Pieces:{}\n'
                       'Total errors:{}\n')
            st = sum(isinstance(err, DRCShortTab)
                     for err in self.impact.drcerrors)
            si = sum(isinstance(err, DRCSelfIntersection)
                     for err in self.impact.drcerrors)
            ti = sum(isinstance(err, DRCIntersection)
                     for err in self.impact.drcerrors)
            fi = sum(isinstance(err, DRCFrameIntersection)
                     for err in self.impact.drcerrors)
            di = sum(isinstance(err, DRCDistanceError)
                     for err in self.impact.drcerrors)
            aa = sum(isinstance(err, DRCAcute)
                     for err in self.impact.drcerrors)
            up = sum(isinstance(err, DRCUnsupported)
                     for err in self.impact.drcerrors)
            self.infotxt.delete(1.0, tk.END)
            self.infotxt.insert(tk.END, drctext.format(
                st, si, ti, fi, di, aa, up, len(self.impact.drcerrors)))

    def mouse_wheel(self, event):
        # respond to Linux or Windows wheel event
        if event.num == 5 or event.delta == -120:
            self.canvas.scale("all", self.canvas.canvasx(
                event.x), self.canvas.canvasy(event.y), 0.8, 0.8)
        if event.num == 4 or event.delta == 120:
            self.canvas.scale("all", self.canvas.canvasx(
                event.x), self.canvas.canvasy(event.y), 1.25, 1.25)

    def startmoving(self, event):
        self.canvas.configure(cursor="fleur")
        self.canvas.scan_mark(event.x, event.y)

    def move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def stopmoving(self, event):
        self.canvas.configure(cursor="tcross")


def main():
    root = tk.Tk()
    root.title("Impact Puzzle Generator")
    root.minsize(1600,1000)
    if ( sys.platform.startswith('win')):
        root.iconbitmap(resource_path('assets/Shard.ico'))
    app = ShardGui(root)
    root.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()

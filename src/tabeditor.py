# Copyright (c) 2020 ProceduralJigsaw
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import math
import tkinter as tk
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from segment import Segment
from tab import Tab, TabType
from tkinter import filedialog
from point import Point

class TabPrototype():
    def __init__(self, points, tabtype:TabType):
        span = (points[-1]-points[0]).r
        self.points = [(p-points[0])*(1/span) for p in points]
        self.tabtype = tabtype
        self.__calc_mindist()

    def __calc_mindist(self):
        t = Tab(TabType.GAP,self.points[0],self.points[-1],0,0,False,0)
        t.make_fromlib(self.points,self.tabtype,0,0)
        self.mindist = t.self_distance()

    def segments(self):
        return [Segment(p1, p2) for p1, p2 in zip(self.points, self.points[1:]+[self.points[0]])]

    def toxml(self):
        tabproto = Element('tabprototype', version='1.0', tabtype=self.tabtype.name, pts=' '.join(
            map(str, [c for p in self.points for c in p.xy()])))
        return ElementTree.tostring(tabproto)

    def printtocanvas(self, canvas, p1,p2, color="black", width=1, tags="projectile"):
        t = Tab(TabType.GAP,p1,p2,0,0,False,0)
        t.make_fromlib(self.points,self.tabtype,0,0)
        t.printtocanvas(canvas,color=color,tags=tags,width=width)

    @classmethod
    def fromxml(cls, xmlfile):
        try:
            xmldoc = ElementTree.parse(xmlfile)
            projroot = xmldoc.getroot()
            if projroot.attrib['version'] == '1.0':
                ttype = TabType[projroot.attrib['tabtype']]
                pps = [Point(x, y) for x, y in zip(
                    *[iter(list(map(float, projroot.attrib['pts'].split())))]*2)]
            else:
                print("Wrong TabPrototype version")
                return None
            return TabPrototype(pps,ttype)
        except Exception as e:
            print(e)
            return None


class TabEditor():
    def __init__(self, root):
        self.root = root
        self.dframe = tk.Frame(self.root, width=800, height=600)
        self.canvas = tk.Canvas(self.dframe, width=800,
                                height=600, cursor="tcross")

        self.savb = tk.Button(self.dframe, text="Save Tab",
                              command=self.savetab)
                              
        self.resb = tk.Button(self.dframe, text="Reset",
                              command=self.initcanvas)
        self.pickedpoints = []
        self.drawnelements = []
        self.initcanvas()
        self.savb.pack()
        self.resb.pack()
        self.dframe.pack()
        self.canvas.pack()
    def initcanvas(self):
        self.canvas.delete("all")
        self.pickedpoints = [Point(100,300),Point(100,300)]
        self.drawnelements = []
        self.canvas.create_oval(100-3, 300-3, 100 + 3, 300+3, fill="red", width=1, tags="anchor")
        self.canvas.create_oval(700-3, 300-3, 700 + 3, 300+3, fill="red", width=1, tags="anchor")


        self.canvas.bind("<Button-3>", self.undo)
        self.canvas.bind("<Motion>", self.dragpoint)
        self.canvas.bind("<ButtonRelease-1>", self.pickpoint)
        self.canvas.bind("<Double-Button-1>", self.closeloop)

    def savetab(self):
        if self.tabproto:
            self.root.filename = filedialog.asksaveasfilename(title="Save tab prototype", filetypes=(
                ("Tabproto Files", "*.tab"), ("all files", "*.*")))
            if not self.root.filename.endswith(".tab"):
                self.root.filename += ".tab"
            with open(self.root.filename, 'wb') as tabprotofile:
                tabprotofile.write(self.tabproto.toxml())

    def tentativepoint(self, event):
        p = Point(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.pickedpoints.append(p)
        self.canvas.create_oval(p.x-3, p.y-3, p.x + 3,
                                p.y+3, fill="blue", width=1, tags="tentative")
        if len(self.pickedpoints) > 1:
            self.canvas.create_line(self.pickedpoints[-2].x, self.pickedpoints[-2].y,
                                    self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tentative")

    def dragpoint(self, event):
        self.pickedpoints[-1].setxy(self.canvas.canvasx(event.x),
                                        self.canvas.canvasy(event.y))
        self.canvas.delete("tentative")
        self.canvas.create_oval(self.pickedpoints[-1].x-3, self.pickedpoints[-1].y-3,
                                self.pickedpoints[-1].x + 3, self.pickedpoints[-1].y+3, fill="blue", width=1, tags="tentative")
        if len(self.pickedpoints) > 1:
            self.canvas.create_line(self.pickedpoints[-2].x, self.pickedpoints[-2].y,
                                    self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tentative")

    def pickpoint(self, event):
        self.drawnelements.append(self.canvas.create_oval(
            self.pickedpoints[-1].x-3, self.pickedpoints[-1].y-3, self.pickedpoints[-1].x + 3, self.pickedpoints[-1].y+3, fill="blue", width=1, tags="tabproto"))
        if len(self.pickedpoints) > 1:
            self.drawnelements.append(self.canvas.create_line(
                self.pickedpoints[-2].x, self.pickedpoints[-2].y, self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tabproto"))
        if len(self.pickedpoints):
            self.tentativepoint(event)
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.bind("<Motion>", self.dragpoint)
            self.canvas.bind("<ButtonRelease-1>", self.pickpoint)

    def undo(self, event):
        if len(self.pickedpoints)>2:
            self.canvas.delete(self.drawnelements[-1])
            self.drawnelements.pop()
            if len(self.drawnelements) > 0:
                self.canvas.delete(self.drawnelements[-1])
                self.drawnelements.pop()
            self.pickedpoints.pop()
            self.dragpoint(event)

    def closeloop(self, event):
        if len(self.pickedpoints) > 2:
            self.pickedpoints.pop()
            self.pickedpoints.pop()
            self.pickedpoints.append(Point(700,300))
            if all(p.y == 300 for p in self.pickedpoints):
                ttype = TabType.LINE
            elif any((p.x > q.x) for p,q in zip(self.pickedpoints,self.pickedpoints[1:])):
                ttype = TabType.JAGGED
            else:
                ttype = TabType.FRACTURE
            self.tabproto = TabPrototype(self.pickedpoints,ttype)
            self.canvas.delete("all")
            self.tabproto.printtocanvas(self.canvas,Point(100,300),Point(700,300))
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.unbind("<Button-3>")
            self.canvas.unbind("<Motion>")
            self.canvas.bind("<MouseWheel>", self.scaletabproto)
            # with Linux OS
            self.canvas.bind("<Button-4>", self.scaletabproto)
            self.canvas.bind("<Button-5>", self.scaletabproto)
            self.canvas.bind("<Key>", self.rotatetabproto)

    def rotatetabproto(self, event):
        if(event.keysym in ('q', 'Q')):
            self.tabproto.rotate(-math.pi/180)
            self.canvas.delete("all")
            self.tabproto.printtocanvas(self.canvas)
        if(event.keysym in ('e', 'E')):
            self.tabproto.rotate(math.pi/180)
            self.canvas.delete("all")
            self.tabproto.printtocanvas(self.canvas)

    def scaletabproto(self, event):
        if event.num == 5 or event.delta == -120:
            self.tabproto.scale(0.9)
        if event.num == 4 or event.delta == 120:
            self.tabproto.scale(1.1)
        self.canvas.delete("all")
        self.tabproto.printtocanvas(self.canvas)


class TabLibManager():
    def __init__(self, root):
        self.root = root
        self.root.directory = filedialog.askdirectory()


        self.dframe = tk.Frame(self.root, width=800, height=600)
        self.bframe = tk.Frame(self.root,width =400)
        self.dframe.pack()
        self.bframe.pack(side= tk.RIGHT)
        self.scrollbar = tk.Scrollbar(self.dframe)
        self.scrollbar.pack( side = tk.RIGHT, fill = tk.Y )

        self.mylist = tk.Listbox(self.dframe, yscrollcommand = self.scrollbar.set )
        for line in range(100):
            self.mylist.insert(tk.END, "This is line number " + str(line))

        self.mylist.pack( side = tk.LEFT, fill = tk.BOTH )
        self.scrollbar.config( command = self.mylist.yview )
        self.loadb = tk.Button(self.bframe, text="Save Tab",
                              command=self.loadlib)
        self.loadb.pack()
    def loadlib(self):
        print("kk")
    # def initcanvas(self):
    #     self.canvas.delete("all")
    #     self.pickedpoints = [Point(100,300),Point(100,300)]
    #     self.drawnelements = []
    #     self.canvas.create_oval(100-3, 300-3, 100 + 3, 300+3, fill="red", width=1, tags="anchor")
    #     self.canvas.create_oval(700-3, 300-3, 700 + 3, 300+3, fill="red", width=1, tags="anchor")


    #     self.canvas.bind("<Button-3>", self.undo)
    #     self.canvas.bind("<Motion>", self.dragpoint)
    #     self.canvas.bind("<ButtonRelease-1>", self.pickpoint)
    #     self.canvas.bind("<Double-Button-1>", self.closeloop)

    # def savetab(self):
    #     if self.tabproto:
    #         self.root.filename = filedialog.asksaveasfilename(title="Save tab prototype", filetypes=(
    #             ("Tabproto Files", "*.tab"), ("all files", "*.*")))
    #         if not self.root.filename.endswith(".tab"):
    #             self.root.filename += ".tab"
    #         with open(self.root.filename, 'wb') as tabprotofile:
    #             tabprotofile.write(self.tabproto.toxml())

    # def tentativepoint(self, event):
    #     p = Point(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    #     self.pickedpoints.append(p)
    #     self.canvas.create_oval(p.x-3, p.y-3, p.x + 3,
    #                             p.y+3, fill="blue", width=1, tags="tentative")
    #     if len(self.pickedpoints) > 1:
    #         self.canvas.create_line(self.pickedpoints[-2].x, self.pickedpoints[-2].y,
    #                                 self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tentative")

    # def dragpoint(self, event):
    #     self.pickedpoints[-1].setxy(self.canvas.canvasx(event.x),
    #                                     self.canvas.canvasy(event.y))
    #     self.canvas.delete("tentative")
    #     self.canvas.create_oval(self.pickedpoints[-1].x-3, self.pickedpoints[-1].y-3,
    #                             self.pickedpoints[-1].x + 3, self.pickedpoints[-1].y+3, fill="blue", width=1, tags="tentative")
    #     if len(self.pickedpoints) > 1:
    #         self.canvas.create_line(self.pickedpoints[-2].x, self.pickedpoints[-2].y,
    #                                 self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tentative")

    # def pickpoint(self, event):
    #     self.drawnelements.append(self.canvas.create_oval(
    #         self.pickedpoints[-1].x-3, self.pickedpoints[-1].y-3, self.pickedpoints[-1].x + 3, self.pickedpoints[-1].y+3, fill="blue", width=1, tags="tabproto"))
    #     if len(self.pickedpoints) > 1:
    #         self.drawnelements.append(self.canvas.create_line(
    #             self.pickedpoints[-2].x, self.pickedpoints[-2].y, self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="tabproto"))
    #     if len(self.pickedpoints):
    #         self.tentativepoint(event)
    #         self.canvas.unbind("<Button-1>")
    #         self.canvas.unbind("<B1-Motion>")
    #         self.canvas.bind("<Motion>", self.dragpoint)
    #         self.canvas.bind("<ButtonRelease-1>", self.pickpoint)

    # def undo(self, event):
    #     if len(self.pickedpoints)>2:
    #         self.canvas.delete(self.drawnelements[-1])
    #         self.drawnelements.pop()
    #         if len(self.drawnelements) > 0:
    #             self.canvas.delete(self.drawnelements[-1])
    #             self.drawnelements.pop()
    #         self.pickedpoints.pop()
    #         self.dragpoint(event)

    # def closeloop(self, event):
    #     if len(self.pickedpoints) > 2:
    #         self.pickedpoints.pop()
    #         self.pickedpoints.pop()
    #         self.pickedpoints.append(Point(700,300))
    #         if all(p.y == 300 for p in self.pickedpoints):
    #             ttype = TabType.LINE
    #         elif any((p.x > q.x) for p,q in zip(self.pickedpoints,self.pickedpoints[1:])):
    #             ttype = TabType.JAGGED
    #         else:
    #             ttype = TabType.FRACTURE
    #         self.tabproto = TabPrototype(self.pickedpoints,ttype)
    #         self.canvas.delete("all")
    #         self.tabproto.printtocanvas(self.canvas,Point(100,300),Point(700,300))
    #         self.canvas.unbind("<Button-1>")
    #         self.canvas.unbind("<B1-Motion>")
    #         self.canvas.unbind("<ButtonRelease-1>")
    #         self.canvas.unbind("<Button-3>")
    #         self.canvas.unbind("<Motion>")
    #         self.canvas.bind("<MouseWheel>", self.scaletabproto)
    #         # with Linux OS
    #         self.canvas.bind("<Button-4>", self.scaletabproto)
    #         self.canvas.bind("<Button-5>", self.scaletabproto)
    #         self.canvas.bind("<Key>", self.rotatetabproto)

    # def rotatetabproto(self, event):
    #     if(event.keysym in ('q', 'Q')):
    #         self.tabproto.rotate(-math.pi/180)
    #         self.canvas.delete("all")
    #         self.tabproto.printtocanvas(self.canvas)
    #     if(event.keysym in ('e', 'E')):
    #         self.tabproto.rotate(math.pi/180)
    #         self.canvas.delete("all")
    #         self.tabproto.printtocanvas(self.canvas)

    # def scaletabproto(self, event):
    #     if event.num == 5 or event.delta == -120:
    #         self.tabproto.scale(0.9)
    #     if event.num == 4 or event.delta == 120:
    #         self.tabproto.scale(1.1)
    #     self.canvas.delete("all")
    #     self.tabproto.printtocanvas(self.canvas)


def main():
    root = tk.Tk()
    app = TabLibManager(root)
    root.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()

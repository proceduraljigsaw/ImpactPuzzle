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
from tab import Tab
from tkinter import filedialog
from point import Point


class Projectile():
    def __init__(self, points):
        signed_area = 0.5 * \
            sum([p1.x*p2.y - p2.x*p1.y for p1,
                 p2 in zip(points, points[1:]+[points[0]])])
        cx = 1/(6*signed_area)*sum([(p1.x+p2.x)*(p1.x*p2.y - p2.x*p1.y)
                                    for p1, p2 in zip(points, points[1:]+[points[0]])])
        cy = 1/(6*signed_area)*sum([(p1.y+p2.y)*(p1.x*p2.y - p2.x*p1.y)
                                    for p1, p2 in zip(points, points[1:]+[points[0]])])
        centroid = Point(cx, cy)
        self.points = [p-centroid for p in points]
        self.radius = max(p.r for p in self.points)

    def rotate(self, angle):
        self.points = [p.rotate(Point(0, 0), angle) for p in self.points]

    def scale(self, scale):
        self.points = [p*scale for p in self.points]
        self.radius *= scale

    def segments(self):
        return [Segment(p1, p2) for p1, p2 in zip(self.points, self.points[1:]+[self.points[0]])]

    def toxml(self):
        projectile = Element('projectile', version='1.0', pts=' '.join(
            map(str, [c for p in self.points for c in p.xy()])))
        return ElementTree.tostring(projectile)

    @classmethod
    def fromxml(cls, xmlfile):
        try:
            xmldoc = ElementTree.parse(xmlfile)
            projroot = xmldoc.getroot()
            if projroot.attrib['version'] == '1.0':
                pps = [Point(x, y) for x, y in zip(
                    *[iter(list(map(float, projroot.attrib['pts'].split())))]*2)]
            else:
                print("Wrong Impact version")
                return None
            return Projectile(pps)
        except Exception as e:
            print(e)
            return None

    def printtocanvas(self, canvas, color="black", offset=Point(400, 400), width=1, tags="projectile"):
        np = [(p+offset) for p in self.points]
        for p1, p2 in zip(np, np[1:]):
            canvas.create_line(p1.x, p1.y, p2.x, p2.y,
                               fill=color, width=width, tags=tags)
        canvas.create_line(np[-1].x, np[-1].y, np[0].x,
                           np[0].y, fill=color, width=width, tags=tags)
        canvas.create_oval(offset.x-3, offset.y-3, offset.x + 3,
                           offset.y+3, fill="blue", width=1, tags="projectile")
        canvas.create_oval(offset.x-self.radius, offset.y-self.radius, offset.x +
                           self.radius, offset.y+self.radius, outline="blue", width=1, tags="projectile")


class ProjectileGUI():
    def __init__(self, root):
        self.root = root
        self.dframe = tk.Frame(self.root, width=800, height=800)
        self.canvas = tk.Canvas(self.dframe, width=800,
                                height=800, cursor="tcross")
        self.pickedpoints = []
        self.drawnelements = []
        self.canvas.bind("<Button-1>", self.tentativepoint)
        self.canvas.bind("<Button-3>", self.undo)
        self.canvas.bind("<B1-Motion>", self.dragpoint)
        self.canvas.bind("<ButtonRelease-1>", self.pickpoint)
        self.canvas.bind("<Double-Button-1>", self.closeloop)
        self.savb = tk.Button(self.dframe, text="Save Projectile",
                              command=self.saveproj)
        self.savb.pack()
        self.dframe.pack()
        self.canvas.pack()
        self.canvas.focus_set()

    def saveproj(self):
        if self.projectile:
            self.root.filename = filedialog.asksaveasfilename(title="Save Projectiles", filetypes=(
                ("Projectile Files", "*.pro"), ("all files", "*.*")))
            if not self.root.filename.endswith(".pro"):
                self.root.filename += ".pro"
            with open(self.root.filename, 'wb') as projectilefile:
                projectilefile.write(self.projectile.toxml())

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
            self.pickedpoints[-1].x-3, self.pickedpoints[-1].y-3, self.pickedpoints[-1].x + 3, self.pickedpoints[-1].y+3, fill="blue", width=1, tags="projectile"))
        if len(self.pickedpoints) > 1:
            self.drawnelements.append(self.canvas.create_line(
                self.pickedpoints[-2].x, self.pickedpoints[-2].y, self.pickedpoints[-1].x, self.pickedpoints[-1].y, width=1, tags="projectile"))
        if len(self.pickedpoints):
            self.tentativepoint(event)
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.bind("<Motion>", self.dragpoint)
            self.canvas.bind("<ButtonRelease-1>", self.pickpoint)

    def undo(self, event):
        self.canvas.delete(self.drawnelements[-1])
        self.drawnelements.pop()
        if len(self.drawnelements) > 1:
            self.canvas.delete(self.drawnelements[-1])
            self.drawnelements.pop()
        self.pickedpoints.pop()
        self.dragpoint(event)

    def closeloop(self, event):
        if len(self.pickedpoints) > 2:
            self.projectile = Projectile(self.pickedpoints[:-1])
            self.canvas.delete("all")
            self.projectile.printtocanvas(self.canvas)
            self.pickedpoints = []
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.unbind("<Button-3>")
            self.canvas.unbind("<Motion>")
            self.canvas.bind("<MouseWheel>", self.scaleprojectile)
            # with Linux OS
            self.canvas.bind("<Button-4>", self.scaleprojectile)
            self.canvas.bind("<Button-5>", self.scaleprojectile)
            self.canvas.bind("<Key>", self.rotateprojectile)

    def rotateprojectile(self, event):
        if(event.keysym in ('q', 'Q')):
            self.projectile.rotate(-math.pi/180)
            self.canvas.delete("all")
            self.projectile.printtocanvas(self.canvas)
        if(event.keysym in ('e', 'E')):
            self.projectile.rotate(math.pi/180)
            self.canvas.delete("all")
            self.projectile.printtocanvas(self.canvas)

    def scaleprojectile(self, event):
        if event.num == 5 or event.delta == -120:
            self.projectile.scale(0.9)
        if event.num == 4 or event.delta == 120:
            self.projectile.scale(1.1)
        self.canvas.delete("all")
        self.projectile.printtocanvas(self.canvas)


def main():
    root = tk.Tk()
    app = ProjectileGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()

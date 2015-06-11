# =========================================================================
#
# Copyright (c) 2000 Atamai, Inc.
#
# Use, modification and redistribution of the software, in source or
# binary forms, are permitted provided that the following terms and
# conditions are met:
#
# 1) Redistribution of the source code, in verbatim or modified
#    form, must retain the above copyright notice, this license,
#    the following disclaimer, and any notices that refer to this
#    license and/or the following disclaimer.
#
# 2) Redistribution in binary form must include the above copyright
#    notice, a copy of this license and the following disclaimer
#    in the documentation or with other materials provided with the
#    distribution.
#
# 3) Modified copies of the source code must be clearly marked as such,
#    and must not be misrepresented as verbatim copies of the source code.
#
# THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE SOFTWARE "AS IS"
# WITHOUT EXPRESSED OR IMPLIED WARRANTY INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE.  IN NO EVENT SHALL ANY COPYRIGHT HOLDER OR OTHER PARTY WHO MAY
# MODIFY AND/OR REDISTRIBUTE THE SOFTWARE UNDER THE TERMS OF THIS LICENSE
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, LOSS OF DATA OR DATA BECOMING INACCURATE
# OR LOSS OF PROFIT OR BUSINESS INTERRUPTION) ARISING IN ANY WAY OUT OF
# THE USE OR INABILITY TO USE THE SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGES.
#
# =========================================================================

#
# This file represents a derivative work by Parallax Innovations Inc.
#

__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: RulerFactory.py,v $',
    'creator': 'Hua Qian <hqian@irus.rri.ca>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
    'author': '$Author: jeremy_gill $',
    'version': '$Revision: 1.2 $',
    'date': '$Date: 2006/06/06 16:59:29 $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
RulerFactory - a ruler for measuring the distance between two points

  This factory produces a ruler which shows the distance
  between two marks. The ruler can also be used as a pointer
  for landmark registration.

Dereived from:

  ActorFactory

Public Methods:

  SetInput(*input*) -- The input is used only for Extent, Origin and Spacing.
   This method must be called right after the Actor was made.

  AddSlicePlane(*plane*) -- Add the plane to the plane list which can access
   by two end marks of the ruler.

  SetOrthoPlanes(*orthPlanes*) -- Add a set of ortho planes for the marks
   to drag around. This method or AddSlicePlane must be called for the mouse
   interaction to work properly.

  Add2DTextToRender(*renderer*) -- Draw the 2D text in this renderer.

  GetDistance() -- Get the Distance between two marks.

  SetColor(*r*,*g*,*b*) -- Set the color of the line.

  SetTextColor(*r*,*g*,*b*) -- Set the color of the 2D text showing
    positions and distance of the two marks.

  RulerModeOn() -- Make the planes in the plane list not pickable,
    so that only the ruler can be picked.

  RulerModeOff() -- Turn off ruler mode.

  RegisterModeOn() -- RulerModeOn, and a dummy mark is displayed on
    current picked position.

  RegisterModeOff() -- Turn off ruler mode.

  PutMark(*size*, *color*) -- Put a mark at current picked position.

  DeleteLastMark() -- Delete the last mark.

  DeleteAllMarks() -- Delete all the marks.

  GetTagList() -- Get a list of marks positions, which can be used for
    landmark registration.

To Do:

  For marks: add points to a vtkPolyData, and then use vtkGlyph3D to place
  spheres around the points.

"""

from ActorFactory import *
from ConeMarkerFactory import *
from SphereMarkFactory import *
import math


class RulerFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        # two marks
        self._mark1 = ConeMarkerFactory()
        self._mark1.SetColor(1, 0, 0)
        self._mark2 = ConeMarkerFactory()
        self._mark2.SetColor(0, 1, 0)
        self.AddChild(self._mark1)
        self.AddChild(self._mark2)

        # A line connecting the two marks
        self._Line = vtk.vtkLineSource()
        self._CurrentPosition = (0, 0, 0)

        # 2D Text
        self._Distance = 0.0
        self.MakeText2D()

        # OrthoPlanes for Marks to move on
        # self._OrthoPlanes = None

        # Picked Mark
        self._Mark = None
        self._markSize = 40

        # Slice plane list
        self._Planes = []

        # Ruler Mode: only ruler is pickable
        self._RulerMode = 0

        # Register Mode:
        # current position will be displayed by a mark
        self._RegisterMode = 0

        self._Visibility = {}

        # Cones point to each other, defaut is not.
        self._ConesInward = 0

        # Landmark Initialize
        self._LandMarkInit()

        # shared property
        self._Property = vtk.vtkProperty()

        self.BindEvent("<ButtonPress>", self.StartMoveMark)
        self.BindEvent("<ButtonRelease>", self.StopMoveMark)
        self.BindEvent("<B2-Motion>", self.DoMoveMark)
        self.BindEvent("<B1-Motion>", self.DoMoveMark)

    def StartMoveMark(self, event):
        self._WindowSize = event.renderer.GetRenderWindow().GetSize()
        for mark in [self._mark1, self._mark2]:
            if event.actor in mark.GetActors(event.renderer):
                self._LastX = event.x
                self._LastY = event.y
                self._Mark = mark
                break
        for actor in self._mark1.GetActors(event.renderer):
            actor.PickableOff()
        for actor in self._mark2.GetActors(event.renderer):
            actor.PickableOff()

        # turn on pickable for planes
        self._PlanesPickableOn()

        # Dummy Mark is used for rigister mode, hide it when move ruler around
        self._DummyMark.SetVisibility(event.renderer, 0)

    def StopMoveMark(self, event):
        self._CurrentPosition = self._Mark.GetPosition()
        self._Marked = 0  # new mark position
        self._Mark = None
        for actor in self._mark1.GetActors(event.renderer):
            actor.PickableOn()
        for actor in self._mark2.GetActors(event.renderer):
            actor.PickableOn()

        # turn off picakable for planes if in Ruler Only Mode
        if self._RulerMode:
            self._PlanesPickableOff()

        # put a sphere mark at current position if Register Mode is on
        if self._RegisterMode:
            self._DummyMark.SetPosition(self._CurrentPosition)
            self._DummyMark.SetVisibility(event.renderer, 1)
            self._DummyMark.Modified()

    def DoMoveMark(self, event):
        if (self._Mark == None):
            return
        if (self._Planes[0] == None):
            print "Warning: No Slice Planes have been set for RulerFactory."
            return

        picker = event.picker
        picker.Pick(event.x,
                    event.y,
                    0.0,
                    event.renderer)

        position = None
        for plane in self._Planes:
            if picker.GetActor() in plane.GetActors(event.renderer):
                position = picker.GetPickPosition()

        if (position == None):
            return

        self._Mark.SetPosition(position)
        self.UpdateRuler()
        # set the new positions for picked mark and
        # the end point of the line
        """
        mark = self._Mark
        mark.SetPosition(position)
        [mx, my, mz] = position

        if (self._Mark is self._mark1):
            self._Line.SetPoint1(mx, my, mz)
            mark2 = self._mark2
        else:
            self._Line.SetPoint2(mx, my, mz)
            mark2 = self._mark1

        [mx2, my2, mz2] = mark2.GetPosition()

        dmx = mx2 -mx
        dmy = my2 -my
        dmz = mz2 -mz

        self._Distance = math.sqrt(dmx*dmx + dmy*dmy + dmz*dmz)

        if self._ConesInward :
            cone1Normal = [dmx, dmy, dmz]
            cone2Normal = [-dmx, -dmy, -dmz]
        else:
            if self._Distance > 2 * self._markSize:  # * self._ConePitch:
                cone1Normal = [-dmx, -dmy, -dmz]
                cone2Normal = [dmx, dmy, dmz]
            else:
                cone1Normal = [dmx, dmy, dmz]
                cone2Normal = [-dmx, -dmy, -dmz]

        # update the normals of the marks
        mark.SetNormal(cone1Normal)
        mark2.SetNormal(cone2Normal)

        if (mark is  self._mark1):
            disp = "P1: (%6.2f,%6.2f,%6.2f)\nP2: (%6.2f,%6.2f,%6.2f)\nDistance: %6.2f" % \
                   (mx,my,mz,mx2,my2,mz2,self._Distance)
        else:
            disp = "P1: (%6.2f,%6.2f,%6.2f)\nP2: (%6.2f,%6.2f,%6.2f)\nDistance: %6.2f" % \
                   (mx2,my2,mz2,mx,my,mz,self._Distance)

        # self._TextMapper.SetInput(disp)
        self.SetText(disp)
        self.Modified()
        """

    def SetMark1Position(self, position):
        self._mark1.SetPosition(position)
        self.UpdateRuler()
        self._CurrentPosition = position
        self._Marked = 0

    def SetMark2Position(self, position):
        self._mark2.SetPosition(position)
        self.UpdateRuler()
        self._CurrentPosition = position
        self._Marked = 0

    def UpdateRuler(self):
        x1, y1, z1 = self._mark1.GetPosition()
        x2, y2, z2 = self._mark2.GetPosition()
        self._Line.SetPoint1(x1, y1, z1)
        self._Line.SetPoint2(x2, y2, z2)
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        self._Distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        if self._ConesInward:
            cone1Normal = [dx, dy, dz]
            cone2Normal = [-dx, -dy, -dz]
        else:
            if self._Distance > 2 * self._markSize:  # * self._ConePitch:
                cone1Normal = [-dx, -dy, -dz]
                cone2Normal = [dx, dy, dz]
            else:
                cone1Normal = [dx, dy, dz]
                cone2Normal = [-dx, -dy, -dz]

        # update the normals of the marks
        self._mark1.SetNormal(cone1Normal)
        self._mark2.SetNormal(cone2Normal)

        disp = "P1: (%6.2f,%6.2f,%6.2f)\nP2: (%6.2f,%6.2f,%6.2f)\nDistance: %6.2f" % \
               (x1, y1, z1, x2, y2, z2, self._Distance)

        # self._TextMapper.SetInput(disp)
        self.SetText(disp)
        self.Modified()

    def SetInput(self, input):
        pass
        # don't need this anymore
        """
        # get extend, origin and spacing from input
        extent = input.GetWholeExtent()
        origin = input.GetOrigin()
        spacing = input.GetSpacing()
        bound = [origin[0]+spacing[0]*(extent[0]-0.5),
                 origin[0]+spacing[0]*(extent[1]+0.5),
                 origin[1]+spacing[1]*(extent[2]-0.5),
                 origin[1]+spacing[1]*(extent[3]+0.5),
                 origin[2]+spacing[2]*(extent[4]-0.5),
                 origin[2]+spacing[2]*(extent[5]+0.5)]
        # swap if neccesary
        for i in range(3):
            if bound[i*2] > bound[i*2+1]:
                bound[i*2],bound[i*2+1] = bound[i*2+1],bound[i*2]

        xSize = bound[1] - bound[0]
        ySize = bound[3] - bound[2]
        zSize = bound[5] - bound[4]
        # self._markSize = 0.05 * max([xSize,ySize,zSize])
        # self._markSize = max([xSize,ySize,zSize])
        self._Sizes = (xSize, ySize, zSize)

        # set the positions and colors of the marks
        # moved to AddToRenderer()
        """
    # Make the line actor

    def _MakeActors(self):
        actor = self._NewActor()
        actor.SetProperty(self._Property)
        actor.PickableOff()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(self._Line.GetOutput())
        actor.SetMapper(mapper)
        return [actor]

    def AddToRenderer(self, renderer):
        ActorFactory.AddToRenderer(self, renderer)
        self.PutAsideRuler(renderer)
        renderer.AddObserver('StartEvent', self.OnRenderEvent)

    def OnRenderEvent(self, renderer, event):
        # Update scale for cones
        matrix = self._Transform.GetMatrix()
        x = matrix.GetElement(0, 3)
        y = matrix.GetElement(1, 3)
        z = matrix.GetElement(2, 3)
        camera = renderer.GetActiveCamera()
        if camera.GetParallelProjection():
            worldsize = camera.GetParallelScale()
        else:
            cx, cy, cz = camera.GetPosition()
            worldsize = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 +
                                  (z - cz) ** 2) * \
                math.tan(0.5 * camera.GetViewAngle() / 57.296)
        pitch = worldsize / math.sqrt(renderer.GetSize()[0] *
                                      renderer.GetSize()[1])
        # self._ConePitch = pitch

        for child in self.GetChildren():
            for actor in child._ActorDict[renderer]:
                actor.SetScale(pitch)

        # for actor in self._mark1.GetActors(renderer):
            # actor.SetScale(pitch)

        # for actor in self._mark2.GetActors(renderer):
           #  actor.SetScale(pitch)

    def PutAsideRuler(self, renderer):
        # set the positions and colors of the marks
        # and put the ruler in a handy location,
        # near the right edge of the window.

        renderer.SetWorldPoint(0, 0, 0, 1.0)
        renderer.WorldToDisplay()
        z = renderer.GetDisplayPoint()[2]
        width, height = renderer.GetSize()

        renderer.SetDisplayPoint(width * 0.9, height * 0.3, z)
        renderer.DisplayToWorld()
        wx, wy, wz, w = renderer.GetWorldPoint()
        p1 = (wx / w, wy / w, wz / w + 0.0001)

        renderer.SetDisplayPoint(width * 0.9, height * 0.7, z)
        renderer.DisplayToWorld()
        wx, wy, wz, w = renderer.GetWorldPoint()
        p2 = (wx / w, wy / w, wz / w + 0.0001)

        if self._ConesInward:
            n1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            n2 = (-n1[0], -n1[1], -n1[2])
        else:
            n1 = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
            n2 = (-n1[0], -n1[1], -n1[2])

        self._mark1.SetSize(self._markSize)
        self._mark1.SetPosition(p1)
        self._mark1.SetNormal(n1)

        self._mark2.SetSize(self._markSize)
        self._mark2.SetPosition(p2)
        self._mark2.SetNormal(n2)

        self._CurrentPosition = p2
        self._DummyMark.SetSize(0.3 * self._markSize)
        self._DummyMark.SetVisibility(renderer, 0)
        self._DummyMark.SetPosition(p2)
        self._DummyMark.SetColor(1, 1, 0)

        self._Line.SetResolution(10)
        self._Line.SetPoint1(p1)
        self._Line.SetPoint2(p2)

    def SetColor(self, *args):
        apply(self._Property.SetColor, args)

    def SetConesInward(self, yesno):
        self._ConesInward = yesno

    def GetDistance(self):
        return self._Distance

    def SetVisibility(self, ren, yesno):
        self._Visibility[ren] = yesno
        for actor in self.GetActors(ren):
            actor.SetVisibility(yesno)
        self.Modified()

    def GetVisibility(self, ren):
        return self._Visibility[ren]

    def MakeText2D(self):
        textMapper = vtk.vtkTextMapper()
        textMapper.SetInput(" ")
        try:
            textProperty = textMapper.GetTextProperty()
        except AttributeError:
            textProperty = textMapper
        # textProperty.SetFontSize(16)
        textProperty.SetFontFamilyToCourier()
        # textProperty.SetJustificationToCentered()
        # textProperty.BoldOn()
        # textProperty.ItalicOn()
        textProperty.ShadowOn()

        # textActor = vtk.vtkScaledTextActor()
        textActor = vtk.vtkActor2D()
        textActor.SetMapper(textMapper)
        textActor.GetProperty().SetColor(1, 1, 1)
        textActor.SetPosition([5, 5])

        self._TextMapper = textMapper
        self._TextActor = textActor

    def SetText(self, text):
        self._TextMapper.SetInput(text)
        try:
            textProperty = self._TextMapper.GetTextProperty()
        except AttributeError:
            textProperty = textMapper
        textProperty.SetFontSize(14)
        self._TextMapper.Modified()

    def SetTextColor(self, *args):
        apply(self._TextActor.GetProperty().SetColor, args)

    def Add2DTextToRender(self, ren):
        ren.AddActor2D(self._TextActor)

    def Remove2DText(self, ren):
        ren.RemoveActor2D(self._TextActor)

    def SetOrthoPlanes(self, orthoPlanes):
        for plane in orthoPlanes.GetPlanes():
            self._Planes.append(plane)
        del plane

    def AddSlicePlane(self, slicePlane):
        self._Planes.append(slicePlane)

    def _PlanesPickableOff(self):
        for render in self._Renderers:
            for plane in self._Planes:
                for actor in plane._ActorDict[render]:
                    # actor = plane._ActorDict[render][0]
                    actor.PickableOff()

    def _PlanesPickableOn(self):
        for render in self._Renderers:
            for plane in self._Planes:
                for actor in plane._ActorDict[render]:
                    # actor = plane._ActorDict[render][0]
                    actor.PickableOn()

    def RulerModeOn(self):
        self._RulerMode = 1
        self._PlanesPickableOff()

    def RulerModeOff(self):
        self._RulerMode = 0
        self._PlanesPickableOn()

    def RegisterModeOn(self):
        self._RegisterMode = 1
        self.RulerModeOn()
        # self._DummyMark.SetVisibility(1)

    def RegisterModeOff(self):
        self._RegisterMode = 0
        self.RulerModeOff()
        # self._DummyMark.SetVisibility(0)

    def _LandMarkInit(self):
        self._TagList = []
        self._MarkList = []
        self._Marked = 0
        self._DummyMark = SphereMarkFactory()
        #
        # self._DummyMark.SetPosition(self._CurrentPosition)
        # self._DummyMark.SetColor(1,1,0)
        # self._DummyMark.SetOpacity(0)
        self.AddChild(self._DummyMark)

    def PutMark(self, size=1, color=[1, 0, 0]):
        # check if mark has been put already
        if self._Marked:
            return
        mark = SphereMarkFactory()

        self.AddChild(mark)
        # important add child first, then
        # set the position and properties
        mark.SetColor(color[0], color[1], color[2])
        # mark.SetOpacity(0.6)
        mark.SetSize(0.3 * size * self._markSize)
        mark.SetPosition(self._CurrentPosition)

        self._MarkList.append(mark)
        self._TagList.append(self._CurrentPosition)
        self._Marked = 1
        self.Modified()

    def DeleteLastMark(self):
        if self._MarkList[0:]:
            self.RemoveChild(self._MarkList[len(self._MarkList) - 1])
            self._MarkList.pop(len(self._MarkList) - 1)
            self._TagList.pop(len(self._TagList) - 1)
        self._Marked = 0
        self.Modified()

    def DeleteAllMarks(self):
        for mark in self._MarkList:
            self.RemoveChild(mark)
        self._MarkList = []
        self._TagList = []
        self.Modified()

    def GetCurrentTag(self):
        return self._TagList[len(self._TagList) - 1]

    def GetCurrentMark(self):
        return self._MarkList[len(self._MarkList) - 1]

    def GetTagList(self):
        return self._TagList

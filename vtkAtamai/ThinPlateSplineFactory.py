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
    'module_name': '$RCSfile: ThinPlateSplineFactory.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
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
ThinPlateSplineFactory - tag points for a thin plate spline transformation

  This class draws a set of spherical tag points that are used a control
  points for a thin plate spline transformation.  The resulting transformation
  can be applied to an image via the SetImageTransform() method of
  the OrthoPlanesFactory, or to a polydata mesh via the
  vtkTransformPolyDataFilter().

  The spheres are drawn in the "target" coordinate system.  This is because
  it is expected that whichever data set is being transformed is also going
  to be rendered in the "target" coordinate system.

Derived From:

  ActorFactory

See Also:

  SlicePlaneFactory, OrthoPlanesFactory

Initialization:

  ThinPlateSplineFactory()

Public Methods:

  AddPoint(*coord*) -- Add a new control point by specifying the (*x*,*y*,*z*)
                       coordinates in the "target" coordinate system.  The
                       coordinates in the "source" coordinate system are
                       automatically calculated by passing (*x*,*y*,*z*)
                       backwards through the transformation.

  RemovePoint(*coord*) -- Remove the control point whose location in
                       the "target" cordinate system is (*x*,*y*,*z*).

  MovePoint(*coord*,*coord*) -- Move the "target" coordinates of the control
                       point while holding the "source" coordinates fixed.

  GetResultTransform() -- Get the vtkThinPlateSplineTransform.

"""

from ActorFactory import *


class ThinPlateSplineFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)
        self._ResultTransform = vtk.vtkThinPlateSplineTransform()
        # self._ResultTransform = vtk.vtkLandmarkTransform()
        self._SourceLandmarks = []
        self._TargetLandmarks = []
        self._Spheres = []

        self._CurrentLandmark = None
        self._DragOffset = (0.0, 0.0, 0.0)

        self.BindEvent("<ButtonPress>", self.DoSelect)
        self.BindEvent("<ButtonRelease>", self.DoRelease)
        self.BindEvent("<Motion>", self.DoMotion)
        self.BindEvent("<Shift-ButtonPress>", self.DoDelete)

    def DoDelete(self, event):
        actors = self._ActorDict[event.renderer]
        self.RemovePoint(self._TargetLandmarks[actors.index(event.actor)])
        self.Modified()

    def DoAddPoint(self, event):
        event.picker.Pick(event.x, event.y, 0, event.renderer)
        thin.AddPoint(event.picker.GetPickPosition())
        self.Modified()

    def DoSelect(self, event):
        actors = self._ActorDict[event.renderer]
        for actor in actors:
            actor.PickableOff()
        self._CurrentLandmark = actors.index(event.actor)
        event.actor.GetProperty().SetColor(1.0, 1.0, 0.0)

        event.picker.Pick(event.x, event.y, 0, event.renderer)
        x, y, z = event.picker.GetPickPosition()
        u, v, w = self._TargetLandmarks[self._CurrentLandmark]
        self._DragOffset = (u - x, v - y, w - z)

        self.Modified()

    def DoRelease(self, event):
        actors = self._ActorDict[event.renderer]
        for actor in actors:
            actor.PickableOn()
        self._CurrentLandmark = None
        event.actor.GetProperty().SetColor(1.0, 0.0, 0.0)
        self.Modified()

    def DoMotion(self, event):
        # Prevent DoMotion from executing during point deletion
        if self._CurrentLandmark is None:
            return

        event.picker.Pick(event.x, event.y, 0, event.renderer)
        x, y, z = event.picker.GetPickPosition()
        x = x + self._DragOffset[0]
        y = y + self._DragOffset[1]
        z = z + self._DragOffset[2]
        # for a little stability, never drag too far
        u, v, w = self._TargetLandmarks[self._CurrentLandmark]
        if ((u - x) ** 2 + (v - y) ** 2 + (w - z) ** 2) < 500:
            self.MovePoint((u, v, w), (x, y, z))
            self.Modified()

    def GetResultTransform(self):
        return self._ResultTransform

    def AddPoint(self, *coord):
        if len(coord) == 1:
            coord = coord[0]
        coord = tuple(coord)
        self._TargetLandmarks.append(coord)
        self._SourceLandmarks.append(
            self._ResultTransform.GetInverse().TransformPoint(coord))
        sphere1 = vtk.vtkSphereSource()
        sphere1.SetRadius(2)
        sphere1.SetCenter(self._TargetLandmarks[-1])
        self._Spheres.append(sphere1)
        for renderer in self._Renderers:
            actor = self._NewActor()
            actor.SetProperty(vtkProperty())
            actor.GetProperty().SetOpacity(1.0)
            actor.GetProperty().SetColor(1.0, 0.0, 0.0)
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInput(sphere1.GetOutput())
            actor.SetMapper(mapper)
            self._ActorDict[renderer].append(actor)
            renderer.AddActor(actor)
        # if there are not enough points, updating the transform
        #  might lead to an singular matrix in the TPS.
        # self._UpdateTransform()

    def RemovePoint(self, *coord):
        if len(coord) == 1:
            coord = coord[0]
        coord = tuple(coord)
        if not coord in self._TargetLandmarks:
            return

        i = self._TargetLandmarks.index(coord)
        actors = self._ActorDict
        for renderer in self._Renderers:
            actor = actors[renderer][i]
            renderer.RemoveActor(actor)
            del actors[renderer][i]
        del self._TargetLandmarks[i]
        del self._SourceLandmarks[i]
        del self._Spheres[i]
        self._UpdateTransform()
        self.Modified()

    def MovePoint(self, coord1, coord2):
        coord1 = tuple(coord1)
        coord2 = tuple(coord2)
        if not (coord1 in self._TargetLandmarks):
            return

        i = self._TargetLandmarks.index(coord1)
        self._TargetLandmarks[i] = coord2
        self._Spheres[i].SetCenter(coord2)
        self._UpdateTransform()
        self.Modified()

    def _UpdateTransform(self):
        n = len(self._SourceLandmarks)
        spoints = vtk.vtkPoints()
        tpoints = vtk.vtkPoints()
        spoints.SetNumberOfPoints(n)
        tpoints.SetNumberOfPoints(n)
        for i in range(n):
            apply(spoints.SetPoint, (i,) + tuple(self._SourceLandmarks[i]))
            apply(tpoints.SetPoint, (i,) + tuple(self._TargetLandmarks[i]))
        self._ResultTransform.SetSourceLandmarks(spoints)
        self._ResultTransform.SetTargetLandmarks(tpoints)

    def _MakeActors(self):
        actors = []
        for i in range(len(self._Spheres)):
            sphere = self._Spheres[i]
            actor = self._NewActor()
            actor.SetProperty(vtkProperty())
            actor.GetProperty().SetOpacity(0.4)
            actor.GetProperty().SetColor(1.0, 0.0, 0.0)
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInput(sphere.GetOutput())
            actor.SetMapper(mapper)
            actors.append(actor)
        return actors

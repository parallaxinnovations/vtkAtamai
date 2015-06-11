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
    'module_name': '$RCSfile: SphereMarkerFactory.py,v $',
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
SphereMarkerFactory - draw a sphere for every point in a vtkPolyData dataset

  SphereMarkerFactory uses vtkGlyph3D to display a list of sphere marks.
  Call function AddPoint to add a mark to the vtkGlyph3D input poly data.
  The vtkGlyph3D doesn't like empty data set, it gives warning.

Derived From:

  ActorFactory

Public Methods:

  AddPoint(*point*)

  RemovePoint(*id*)

  RemoveLastPoint(*id*)

  RemoveAllPoints(*id*)

  SetSize(*size*) -- Set mark size in world dimensions

  SetColor(*r,*g*,*b*) -- set mark color

  SetOpacity(*alpha*) -- set mark opacity

"""

from ActorFactory import *
from math import *


class SphereMarkerFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self._property = vtk.vtkProperty()
        self._sphereSource = vtk.vtkSphereSource()
        self._sphereSource.SetRadius(5)
        self._markPoints = vtk.vtkPoints()
        self._polyData = vtk.vtkPolyData()
        self._polyData.SetPoints(self._markPoints)
        self._glyph = vtk.vtkGlyph3D()
        self._glyph.SetInput(self._polyData)
        self._glyph.SetSource(self._sphereSource.GetOutput())

    def AddPoint(self, point):
        self._markPoints.InsertNextPoint(point[0], point[1], point[2])

        # change the actor scale to suit the renderer
        x = point[0]
        y = point[1]
        z = point[2]
        for ren in self._Renderers:
            camera = ren.GetActiveCamera()
            if camera.GetParallelProjection():
                worldsize = camera.GetParallelScale()
            else:
                cx, cy, cz = camera.GetPosition()
                worldsize = sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) * \
                    tan(0.5 * camera.GetViewAngle() / 57.296)
            pitch = worldsize / sqrt(ren.GetSize()[0] * ren.GetSize()[1])
            # print pitch
            self.SetSize(10 * pitch)

        self._markPoints.Modified()
        self.Render()

    def RemovePoint(self, id):
        # Remove the point from list at id
        n = self._markPoints.GetNumberOfPoints()
        if id < n:
            for i in range(id, n):
                self._markPoints.SetPoint(i, self._markPoints.GetPoint(i + 1))
            self._markPoints.SetNumberOfPoints(n - 1)
        self._markPoints.Modified()

    def RemoveLastPoint(self):
        self._markPoints.SetNumberOfPoints(
            self._markPoints.GetNumberOfPoints() - 1)
        self._markPoints.Modified()

    def RemoveAllPoints(self):
        self._markPoints.SetNumberOfPoints(0)

    def SetSize(self, size):
        self._sphereSource.SetRadius(0.5 * size)
        self._sphereSource.Update()
        # self._sphere.SetResolution(10)

    def SetOpacity(self, theOpacity):
        self._property.SetOpacity(theOpacity)

    def SetColor(self, *args):
        apply(self._property.SetColor, args)

    def GetColor(self):
        return self._property.GetColor()

    def GetActor(self):
        return self._Actor

    def _MakeActors(self):
        actor = self._NewActor()
        actor.SetProperty(self._property)
        actor.PickableOff()

        self._mapper = vtk.vtkPolyDataMapper()
        self._mapper.SetInputConnection(self._glyph.GetOutputPort())
        actor.SetMapper(self._mapper)
        return [actor]

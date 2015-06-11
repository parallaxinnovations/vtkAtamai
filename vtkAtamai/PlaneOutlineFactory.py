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
    'module_name': '$RCSfile: PlaneOutlineFactory.py,v $',
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
PlaneOutlineFactory - draw an outline around a plane

  The PlaneOutlineFactory produces a '#' shape outline on a plane of
  SlicePlaneFactory. This factory is used by OrthoPlaneFactory
  for highlighting the "action" zones.

  This is helper class for OrthoPlaneFactory. It assumes the margins
  is 0.05 of the size of the corresponding dimension.

Derived From:

  ActorFactory

Public Methods:

  SetPlane(*plane*)  -- set the SlicePlaneFactory to use

  GetPlane()         -- get the plane

  SetColor(*color*)  -- specify the color of the lines in RGB

  GetColor()         -- get the color

"""
#======================================
from ActorFactory import *
import vtk
import math

#======================================


class PlaneOutlineFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)
        self._Property = vtk.vtkProperty()
        self._Plane = None
        self._Line = []
        for i in range(4):
            self._Line.append(vtk.vtkLineSource())

    def SetPlane(self, plane):
        if plane is None:
            return

        self._Plane = plane

        s = 0.05
        t = 0.05

        p0 = self._Plane.GetOrigin()
        p1 = self._Plane.GetPoint1()
        p2 = self._Plane.GetPoint2()

        v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])

        p11 = (p0[0] + v1[0] * s,     p0[1] + v1[1] * s,     p0[2] + v1[2] * s)
        p12 = (p2[0] + v1[0] * s,     p2[1] + v1[1] * s,     p2[2] + v1[2] * s)
        p13 = (p0[0] + v1[0] * (1 - s), p0[1] + v1[1]
               * (1 - s), p0[2] + v1[2] * (1 - s))
        p14 = (p2[0] + v1[0] * (1 - s), p2[1] + v1[1]
               * (1 - s), p2[2] + v1[2] * (1 - s))

        p21 = (p0[0] + v2[0] * t,     p0[1] + v2[1] * t,     p0[2] + v2[2] * t)
        p22 = (p1[0] + v2[0] * t,     p1[1] + v2[1] * t,     p1[2] + v2[2] * t)
        p23 = (p0[0] + v2[0] * (1 - t), p0[1] + v2[1]
               * (1 - t), p0[2] + v2[2] * (1 - t))
        p24 = (p1[0] + v2[0] * (1 - t), p1[1] + v2[1]
               * (1 - t), p1[2] + v2[2] * (1 - t))

        self._Line[0].SetPoint1(p11)
        self._Line[0].SetPoint2(p12)
        self._Line[1].SetPoint1(p13)
        self._Line[1].SetPoint2(p14)
        self._Line[2].SetPoint1(p21)
        self._Line[2].SetPoint2(p22)
        self._Line[3].SetPoint1(p23)
        self._Line[3].SetPoint2(p24)

        self.Modified()

    def AddToRenderer(self, ren):
        ActorFactory.AddToRenderer(self, ren)
        try:
            ren.AddObserver('StartEvent', self.OnRenderEvent)
        except:
            pass

    def OnRenderEvent(self, ren, event):
        if self._Property.GetOpacity() == 0.0:
            return

        self.SetPlane(self._Plane)

        camera = ren.GetActiveCamera()
        v = camera.GetViewPlaneNormal()

        if camera.GetParallelProjection():
            d = camera.GetParallelScale() / 100
        else:
            d = camera.GetDistance() * \
                math.sin(camera.GetViewAngle() / 360.0 * math.pi) / 100

        v = self._Transform.GetInverse().TransformVector(
            v[0] * d, v[1] * d, v[2] * d)
        for actor in self._ActorDict[ren]:
            actor.SetPosition(v)

        self._RenderTime.Modified()

    def GetPlane(self):
        return self._Plane

    def SetColor(self, *args):
        if len(args) == 1:
            args = args[0]
        apply(self._Property.SetColor, args)

    def GetColor(self):
        return self._Property.GetColor()

    def SetVisibility(self, i, renderer=None):
        if renderer is None:
            renderers = self._Renderers
        else:
            renderers = [renderer]

        for renderer in renderers:
            for actor in self._ActorDict[renderer]:
                actor.SetVisibility(i)

    def HasChangedSince(self, sinceMTime):
        if ActorFactory.HasChangedSince(self, sinceMTime):
            return 1
        if self._Plane and self._Plane.HasChangedSince(sinceMTime):
            return 1
        if self._Property and self._Property.GetMTime() > sinceMTime:
            return 1
        return 0

    def _MakeActors(self):
        actors = []
        for i in range(4):
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(self._Line[i].GetOutputPort())
            actor = self._NewActor()
            actor.VisibilityOff()
            actor.PickableOff()
            actor.SetProperty(self._Property)
            actor.SetMapper(mapper)
            actors.append(actor)
        return actors

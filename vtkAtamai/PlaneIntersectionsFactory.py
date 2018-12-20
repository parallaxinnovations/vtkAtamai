from __future__ import division
from __future__ import absolute_import
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

from builtins import range
from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: PlaneIntersectionsFactory.py,v $',
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
PlaneIntersectionsFactory - draw lines at the plane intersections

  This factory is meant to be used with a set of SlicePlaneFactories.
  It generates a set of lines at the intersections of the planes.

Derived From:

  ActorFactory

See Also:

  OrthoPlanesFactory, SlicePlaneFactory

Initialization:

  PlaneIntersectionsFactory()

Public Methods:

  SetPlanes(*planes*) -- set the SlicePlaneFactories to use

  GetPlanes()         -- get the planes

  SetColor(*color*)  -- specify the color of the lines in RGB

  GetColor()         -- get the color

"""

#======================================
from .ActorFactory import *
import math


#======================================
class PlaneIntersectionsFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self._Property = vtk.vtkProperty()
        self._Property.SetColor(1, 0, 0)
        self._Property.SetAmbient(1.0)

        self._Planes = []
        self._Cutters = []

        self._Append = vtk.vtkAppendPolyData()

    def SetColor(self, *args):
        self._Property.SetColor(*args)

    def GetColor(self):
        return self._Property.GetColor()

    def HasChangedSince(self, sinceMTime):
        if ActorFactory.HasChangedSince(self, sinceMTime):
            return 1
        for plane in self._Planes:
            if plane.HasChangedSince(sinceMTime):
                return 1
        if self._Property.GetMTime() > sinceMTime:
            return 1
        return 0

    def SetPlanes(self, planes):
        self._Planes = list(planes)
        planes = list(planes)
        done = []

        for cutter in self._Cutters:
            self._Append.RemoveInput(cutter.GetOutput())

        self._Cutters = []
        for i in range(len(self._Planes)):
            for j in range(i + 1, len(self._Planes)):
                cutter = vtk.vtkCutter()
                cutter.SetInput(self._Planes[i].GetPolyData())
                cutter.SetCutFunction(self._Planes[j].GetPlaneEquation())
                self._Cutters.append(cutter)
                self._Append.AddInput(cutter.GetOutput())

    def GetPlanes(self):
        return self._Planes

    def SetVisibility(self, yesno, renderer=None):
        if renderer is None:
            renderers = self._Renderers
        else:
            renderers = [renderer, ]

        for ren in renderers:
            for actor in self._ActorDict[ren]:
                actor.SetVisibility(yesno)

    def GetProperty(self):
        return self._Property

    def AddToRenderer(self, ren):
        ActorFactory.AddToRenderer(self, ren)
        try:
            ren.AddObserver('StartEvent', self.OnRenderEvent)
        except:
            pass

    def OnRenderEvent(self, ren, event):
        camera = ren.GetActiveCamera()
        v = camera.GetViewPlaneNormal()

        if camera.GetParallelProjection():
            d = old_div(camera.GetParallelScale(), 100)
        else:
            d = camera.GetDistance() * \
                math.sin(camera.GetViewAngle() / 360.0 * math.pi) / \
                100

        v = self._Transform.GetInverse().TransformVector(
            v[0] * d, v[1] * d, v[2] * d)
        for actor in self._ActorDict[ren]:
            actor.SetPosition(v[0], v[1], v[2])

    def _MakeActors(self):
        actors = []

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self._Append.GetOutputPort())
        actor = self._NewActor()
        actor.SetProperty(self._Property)
        actor.SetMapper(mapper)
        actors.append(actor)

        return actors

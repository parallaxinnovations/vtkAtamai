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
    'module_name': '$RCSfile: SphereMarkFactory.py,v $',
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
SphereMarkFactory - a spherical annotation marker

  The SphereMarkFactory is a spherical actor that is not
  pickable and that automatically scales itself such that
  its size is relative to display coordinates, rather than
  world coordinates.

  It is meant to be used as a simple annotation marker.

Derived From:

  ActorFactory

Public Methods:

  SetSize(*size*) -- set mark size in world dimensions

  SetColor(*r*,*g*,*b*) -- set mark color

  SetOpacity(*alpha*) -- set mark opacity

  SetPosition(position) -- set mark position

"""

from ActorFactory import *
import math


class SphereMarkFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self.__sphere = vtk.vtkSphereSource()
        self.__transform = vtk.vtkTransform()
        self.__position = (0.0, 0.0, 0.0)
        self.__radius = 1.0
        self.__property = vtk.vtkProperty()

    def SetSize(self, size):
        self.SetRadius(0.5 * size)
        self.__sphere.Update()

    def SetRadius(self, r):
        self.__radius = r
        self.__sphere.SetRadius(r)

    def SetTransform(self, trans):
        self.__transform = trans

    def GetTransform(self):
        return self.__transform

    def GetRadius(self):
        return self.__radius

    def SetPosition(self, position):
        self.__position = position
        for renderer in self._Renderers:
            for actor in self._ActorDict[renderer]:
                # differentiate between 2D actor (caption) and 3D actor
                # (sphere)
                if actor.IsA('vtkActor2D'):
                    actor.SetAttachmentPoint(position)
                else:
                    actor.SetPosition(position)

    def GetPosition(self):
        return self.__position

    def SetOpacity(self, theOpacity):
        self.__property.SetOpacity(theOpacity)

    def GetOpacity(self):
        return self.__property.GetOpacity()

    def SetVisibility(self, renderer, yesno):
        for actor in self._ActorDict[renderer]:
            actor.SetVisibility(yesno)

    def SetColor(self, *args):
        apply(self.__property.SetColor, args)

    def GetColor(self):
        return self.__property.GetColor()

    def _MakeActors(self):
        actor = self._NewActor()
        actor.SetProperty(self.__property)
        return [actor]

    def _NewActor(self):
        actor = ActorFactory._NewActor(self)
        actor.PickableOff()
        actor.SetUserTransform(self.GetTransform())
        actor.SetPosition(self.GetPosition())
        self.SetRadius(self.GetRadius())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.__sphere.GetOutputPort())
        actor.SetMapper(mapper)
        return actor

    def AddToRenderer(self, renderer):
        ActorFactory.AddToRenderer(self, renderer)
        renderer.AddObserver('StartEvent', self.OnRenderEvent)

    def OnRenderEvent(self, renderer, event):

        x, y, z = self.GetPosition()

        if renderer not in self._ActorDict:
            return

        actors = self._ActorDict[renderer]
        if actors:
            camera = renderer.GetActiveCamera()
            if camera.GetParallelProjection():
                worldsize = camera.GetParallelScale()
            else:
                cx, cy, cz = camera.GetPosition()
                worldsize = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 +
                                      (z - cz) ** 2) * \
                    math.tan(0.5 * camera.GetViewAngle() / 57.296)
            windowWidth, windowHeight = renderer.GetSize()
            if windowWidth > 0 and windowHeight > 0:
                pitch = worldsize / windowHeight
                for actor in actors:
                    # ignore resize of caption
                    if not actor.IsA('vtkCaptionActor2D'):
                        actor.SetScale(pitch)

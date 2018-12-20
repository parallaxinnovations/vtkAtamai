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

from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: CursorFactory.py,v $',
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
CursorFactory - a 3D cursor that follows the mouse

  The CursorFactory provides a 3D cursor that follows the mouse
  in the RenderPane.

  The RenderPane and ActorFactory have code that is specific to
  the cursor.  The cursor position is used for doing picks and for
  converting 2D mouse coordinates into 3D scene coordinates.

Derived From:

  ActorFactory

See Also:

  RenderPane, ConeCursorFactory, CrossCursorFactory

Initialization:

  CursorFactory()

Public Methods:

  General Use:

    SetInput(*data*)      -- set the polydata to use as a cursor (the polydata
                             should be 1 unit length across)

    AddListenerMethod(*method*) -- set a method that will be called whenever
                                 the cursor is Updated, the method will be
                                 called with a vtkTransform as the first
                                 argument

    RemoveListenerMethod(*method*) -- remove a listener method

  Reserved for RenderPane:

    Update(*renderer*)      -- update the cursor (prior to rendering)

    SetVisibility(*renderer*,*bool*) -- specify whether to draw the
                               cursor in the specified renderer

Protected Attributes:

   _CursorSize      -- size of cursor in pixels

   _TopProperty     -- property of Top actor, default red

   _BotProperty     -- property of Bot actor, default green

"""

#======================================
from .ActorFactory import *
import math

#======================================


class CursorFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        # cursor size in pixels
        self._CursorSize = 20.0

        # get the data from overloaded method
        self._Input = self._CreateCursorData()

        # the listener methods
        self._ListenerMethods = []

        # visibility in each of the renderers
        self._Visibility = {}

        # cut the data in half
        plane = vtk.vtkPlane()
        plane.SetNormal(1.0, 0.0, 0.0)
        plane.SetOrigin(0.0, 0.0, 0.0)

        self._Split = vtk.vtkClipPolyData()
        self._Split.SetClipFunction(plane)
        self._Split.GenerateClipScalarsOff()
        self._Split.GenerateClippedOutputOn()
        self._Split.SetInput(self._Input)

        self._TopCursorData = self._Split.GetOutput()
        self._BotCursorData = self._Split.GetClippedOutput()

        self._TopProperty = vtk.vtkProperty()
        self._TopProperty.SetColor(1.0, 0.0, 0.0)

        self._BotProperty = vtk.vtkProperty()
        self._BotProperty.SetColor(0.0, 1.0, 0.0)

        """
        self._2DActors = {}
        """

        # make the text
        self._TextPosition = (10, 10)
        self._TextColor = (0.0, 1.0, 0.0)
        self._TextSize = 15
        self._TextFormat = "%+7.2f %+7.2f %+7.2f"

        self._MakeText()

    def _CreateCursorData(self):
        # create the data for the two cones
        a = self._CursorSize

        self.__CursorSource = vtk.vtkCursor3D()
        self.__CursorSource.SetModelBounds(-a, a, -a, a, -a, a)

        return self.__CursorSource.GetOutput()

    def SetInput(self, input):
        if self._Input == input:
            return
        self._Input = input
        self._Split.SetInput(input)
        self.Modified()

    def GetInput(self):
        return self._Input

    def AddListenerMethod(self, method):
        self._ListenerMethods.append(method)

    def RemoveListenerMethod(self, method):
        self._ListenerMethods.remove(method)

    def SetVisibility(self, ren, visibility):
        self._Visibility[ren] = visibility
        for actor in self._ActorDict[ren]:
            actor.SetVisibility(visibility)

    def GetVisibility(self, ren):
        return self._Visibility[ren]

    def Update(self, renderer):
        # change the actor scale to suit the renderer
        matrix = self._Transform.GetMatrix()
        x = matrix.GetElement(0, 3)
        y = matrix.GetElement(1, 3)
        z = matrix.GetElement(2, 3)
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
                pitch = old_div(worldsize, windowHeight)
                for actor in actors:
                    actor.SetScale(pitch)

        for meth in self._ListenerMethods:
            meth(self._Transform)

        """
        self._TextMapper.SetInput(self._TextFormat % (x,y,z))
        """

    def AddToRenderer(self, renderer):
        ActorFactory.AddToRenderer(self, renderer)
        self._Visibility[renderer] = 1
        actors = self._Make2DActors()
        """
        self._2DActors[renderer] = actors
        for actor in actors:
            renderer.AddActor2D(actor)
        """
        self.Update(renderer)

    def RemoveFromRenderer(self, renderer):
        del self._Visibility[renderer]
        """
        for actor in self._2DActors[renderer]:
            renderer.RemoveActor2D(actor)
        del self._2DActors[renderer]
        """
        ActorFactory.RemoveFromRenderer(self, renderer)

    def GetCursorPosition(self):
        matrix = self._Transform.GetMatrix()

        position = (matrix.GetElement(0, 3),
                    matrix.GetElement(1, 3),
                    matrix.GetElement(2, 3))

        return position

    def _MakeActors(self):
        topActor = self._NewActor()
        topMapper = vtk.vtkPolyDataMapper()
        topMapper.SetInput(self._TopCursorData)
        topActor.SetMapper(topMapper)
        topActor.SetProperty(self._TopProperty)

        botActor = self._NewActor()
        botMapper = vtk.vtkPolyDataMapper()
        botMapper.SetInput(self._BotCursorData)
        botActor.SetMapper(botMapper)
        botActor.SetProperty(self._BotProperty)

        return [topActor, botActor]

    def _NewActor(self):
        actor = ActorFactory._NewActor(self)
        actor.PickableOff()
        return actor

    def _MakeText(self):
        mapper = vtk.vtkTextMapper()
        mapper.SetInput("")
        try:
            property = mapper.GetTextProperty()
        except AttributeError:
            property = mapper
        property.SetFontSize(self._TextSize)
        # property.SetFontFamilyToCourier()
        # property.BoldOn()
        self._TextMapper = mapper

    def _Make2DActors(self):
        actor = vtk.vtkActor2D()
        actor.GetProperty().SetColor(self._TextColor)
        actor.SetMapper(self._TextMapper)
        actor.SetPosition(self._TextPosition)

        return (actor,)

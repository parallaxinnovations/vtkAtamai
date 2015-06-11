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
    'module_name': '$RCSfile: OutlineFactory.py,v $',
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
OutlineFactory - a wireframe outline around a data set

  This factory is used to draw a box around a data set.
  It uses the vtkOutlineFilter.

Derived From:

  ActorFactory

See Also:

  AnatomicalLabelsFactory

Initialization:

  OutlineFactory()

PublicMethods:

  SetInput(*data*)   -- set the data set to generate a frame for

  GetInput()         -- get the input

  SetColor(*color*)  -- specify the color of the frame in RGB

  GetColor()         -- get the color

"""
#======================================
import ActorFactory
import math
import vtk

#======================================


class OutlineFactory(ActorFactory.ActorFactory):

    def __init__(self):

        ActorFactory.ActorFactory.__init__(self)
        self._OutlineFilter = vtk.vtkOutlineFilter()
        self._Property = vtk.vtkProperty()
        self._Input = None

    def SetInputData(self, input):
        self._Input = input
        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            self._OutlineFilter.SetInputData(input)
        else:
            self._OutlineFilter.SetInput(input)
        self.Modified()

    def GetInput(self):
        return self._Input

    def SetColor(self, *args):

        if len(args) == 1:
            args = args[0]
        self._Property.SetColor(args[0], args[1], args[2])
        self.Modified()

    def GetColor(self):
        return self._Property.GetColor()

    def SetVisibility(self, yesno, renderer=None):

        if renderer is None:
            renderers = self._Renderers
        else:
            renderers = [renderer, ]

        for ren in renderers:
            for actor in self._ActorDict[ren]:
                actor.SetVisibility(yesno)

    def HasChangedSince(self, sinceMTime):

        if (ActorFactory.ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        if (self._Input and self._Input.GetMTime() > sinceMTime):
            return 1
        return 0

#    def AddToRenderer(self, ren):
#        ActorFactory.ActorFactory.AddToRenderer(self, ren)
#        ren.AddObserver('StartEvent', self.OnRenderEvent)

#    def OnRenderEvent(self, ren, event):
#
#        camera = ren.GetActiveCamera()
#        v = camera.GetViewPlaneNormal()
#
#        if camera.GetParallelProjection():
#            d = camera.GetParallelScale()/100.0
#        else:
#            d = camera.GetDistance() * \
#                math.sin(camera.GetViewAngle()/360.0*math.pi) / \
#                100.0
#        for actor in self._ActorDict[ren]:
#            actor.SetPosition(self._Transform.GetInverse().TransformVector(
#                v[0]*d, v[1]*d, v[2]*d))

    def _MakeActors(self):
        actor = self._NewActor()
        actor.SetProperty(self._Property)
        actor.PickableOff()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self._OutlineFilter.GetOutputPort())
        actor.SetMapper(mapper)
        return [actor]

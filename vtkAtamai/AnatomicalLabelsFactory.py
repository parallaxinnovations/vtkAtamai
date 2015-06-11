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
    'module_name': '$RCSfile: AnatomicalLabelsFactory.py,v $',
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
AnatomicalLabelsFactory - AP SI LR labels for a data set

  Create a set of labels that mark the anatomically significant directions
  in a medical data set, that is:

 - L Left:      -x

 - R Right:     +x

 - A Anterior:  +y

 - P Posterior: -y

 - I Inferior:  -z

 - S Superior:  +z

Derived From:

  ActorFactory

See Also:

  OutlineFactory

Initialization:

  AnatomicalLabelsFactory(*labels*=["L","R","P","A","I","S"])

  *labels* - specify the labels to use

Public Methods:

  SetInput(*imagedata*)  -- set the medical data set, which is
                            used to determine the positions of
                            the labels

"""

#======================================
from ActorFactory import *
import math

#======================================


class AnatomicalLabelsFactory(ActorFactory):

    def __init__(self, labels=['L', 'R', 'P', 'A', 'I', 'S']):
        ActorFactory.__init__(self)

        self._Input = None

        self._PositiveProperty = vtk.vtkProperty()
        self._PositiveProperty.SetColor(0.0, 1.0, 0.0)

        self._NegativeProperty = vtk.vtkProperty()
        self._NegativeProperty.SetColor(1.0, 0.0, 0.0)
        self._Labels = labels
        self._Scale = 6.0     # scale for label text
        self._bounds = (-1, 1, -1, 1, -1, 1)
        self._offset = 0.
        self._volumeCenter = (0, 0, 0)

    def SetScale(self, scale):
        self._Scale = scale

    def GetScale(self):
        return self._Scale

    def SetInputData(self, input):
        self._Input = input

        # TODO: port to VTK6
        # input.UpdateInformation()

        # scale
        e = input.GetExtent()
        size1 = (e[1] - e[0] + e[3] - e[2]) * 0.5
        self._Scale = size1 * 0.05
        if e[5] - e[4] > 0:
            self._Scale = self._Scale * size1 / (e[5] - e[4])
        if self._Scale > 5:
            self._Scale = 5

        self._Scale = 6.0

        spacing = input.GetSpacing()
        xmin, ymin, zmin = input.GetOrigin()
        xmax, ymax, zmax = xmin + e[1] * spacing[0], ymin + e[
            3] * spacing[1], zmin + e[5] * spacing[2]

        size = ((xmax - xmin) + (ymax - ymin)) * 0.5
        offset = 0.1 * size

        xc = (xmin + xmax) * 0.5
        yc = (ymin + ymax) * 0.5
        zc = (zmin + zmax) * 0.5

        for renderer in self._Renderers:
            actors = self._ActorDict[renderer]

            for actor in actors:
                # actor.SetOrigin(self._Origin)
                actor.SetScale(self._Scale)

            actors[0].SetPosition(xmin - offset, yc, zc)
            actors[1].SetPosition(xmax + offset, yc, zc)
            actors[2].SetPosition(xc, ymin - offset, zc)
            actors[3].SetPosition(xc, ymax + offset, zc)
            actors[4].SetPosition(xc, yc, zmin - offset)
            actors[5].SetPosition(xc, yc, zmax + offset)

        self._offset = offset
        self._volumeCenter = (xc, yc, zc)
        self._bounds = (xmin, xmax, ymin, ymax, zmin, zmax)

    def SetVisibility(self, status=0, label=None):
        if label is None:
            for renderer in self._Renderers:
                for actor in self.GetActors(renderer):
                    actor.SetVisibility(status)
        else:
            n = self._Labels.index(label)
            for renderer in self._Renderers:
                actor = self.GetActors(renderer)[n]
                actor.SetVisibility(status)

        self.Modified()
        # self.Render()

    def GetInput(self):
        return self._Input

    def HasChangedSince(self, sinceMTime):
        if (ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        if (self._Input and self._Input.GetMTime() > sinceMTime):
            return 1
        return 0

    def _MakeActors(self):
        xmin, xmax, ymin, ymax, zmin, zmax = self._bounds
        offset = self._offset
        xc, yc, zc = self._volumeCenter
        scale = self._Scale

        return [self._NewActor(self._Labels[0], (xmin - offset, yc, zc),
                               scale, direction='negative'),
                self._NewActor(self._Labels[1], (xmax + offset, yc, zc),
                               scale, direction='positive'),
                self._NewActor(self._Labels[2], (xc, ymin - offset, zc),
                               scale, direction='negative'),
                self._NewActor(self._Labels[3], (xc, ymax + offset, zc),
                               scale, direction='positive'),
                self._NewActor(self._Labels[4], (xc, yc, zmin - offset),
                               scale, direction='negative'),
                self._NewActor(self._Labels[5], (xc, yc, zmax + offset),
                               scale, direction='positive')]

    def _NewActor(self, label, point, scale, direction='positive'):
        # have to completely override ActorFactory._NewActor to create
        # a follower instead of an actor
        actor = ActorFactory._NewActor(self)
        actor.PickableOff()
        if direction == 'positive':
            actor.SetProperty(self._PositiveProperty)
        else:
            actor.SetProperty(self._NegativeProperty)

        vectorText = vtk.vtkVectorText()
        vectorText.SetText(label)

        textMapper = vtk.vtkPolyDataMapper()
        textMapper.SetInput(vectorText.GetOutput())

        actor.SetMapper(textMapper)
        actor.SetOrigin(0., 0., 0.)
        actor.SetPosition(point[0], point[1], point[2])
        actor.SetScale(scale)

        return actor

    def AddToRenderer(self, renderer):
        ActorFactory.AddToRenderer(self, renderer)
        try:
            renderer.AddObserver('StartEvent', self.OnRenderEvent)
        except AttributeError:
            pass

    def OnRenderEvent(self, renderer, event):
        actors = self._ActorDict[renderer]
        xmin, xmax, ymin, ymax, zmin, zmax = self._bounds
        offset = self._offset
        xc, yc, zc = self._volumeCenter
        scale = self._Scale

        # permute actor positions according to transform
        transform = self._Transform.GetInverse()
        vec = list(transform.TransformVector(1, 0, 0))
        avec = map(abs, vec)
        i = avec.index(max(avec))
        isign = int(avec[i] / vec[i])
        vec = list(transform.TransformVector(0, 1, 0))
        vec[i] = 0.0
        avec = map(abs, vec)
        j = avec.index(max(avec))
        jsign = int(avec[j] / vec[j])
        vec = list(transform.TransformVector(0, 0, 1))
        vec[i] = 0.0
        vec[j] = 0.0
        avec = map(abs, vec)
        k = avec.index(max(avec))
        ksign = int(avec[k] / vec[k])

        coords = [(xmin - offset, yc,  zc),
                  (xmax + offset, yc,  zc),
                  (xc,  ymin - offset, zc),
                  (xc,  ymax + offset, zc),
                  (xc,  yc,  zmin - offset),
                  (xc,  yc,  zmax + offset)]

        actors[0].SetPosition(coords[2 * i + (1 - isign) / 2])
        actors[1].SetPosition(coords[2 * i + (1 + isign) / 2])
        actors[2].SetPosition(coords[2 * j + (1 - jsign) / 2])
        actors[3].SetPosition(coords[2 * j + (1 + jsign) / 2])
        actors[4].SetPosition(coords[2 * k + (1 - ksign) / 2])
        actors[5].SetPosition(coords[2 * k + (1 + ksign) / 2])

        width, height = renderer.GetSize()
        if height > 0:
            matrix = self._Transform.GetMatrix()
            # x = matrix.GetElement(0,3)
            # y = matrix.GetElement(1,3)
            # z = matrix.GetElement(2,3)
            x = xc
            y = yc
            z = zc
            camera = renderer.GetActiveCamera()
            if camera.GetParallelProjection():
                worldsize = camera.GetParallelScale()
            else:
                cx, cy, cz = camera.GetPosition()
                worldsize = math.sqrt((x - cx) ** 2 +
                                      (y - cy) ** 2 +
                                      (z - cz) ** 2)

            transform = vtk.vtkTransform()
            transform.Concatenate(camera.GetViewTransformMatrix())
            transform.Concatenate(matrix)
            rx, ry, rz = transform.GetInverse().GetOrientation()

            for actor in actors:
                actor.SetOrientation(rx, ry, rz)

            pitch = scale * worldsize / height

            for actor in actors:
                actor.SetScale(pitch)

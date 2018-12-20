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
from builtins import map
from builtins import range
from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: VolumePlanesFactory.py,v $',
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
VolumePlanesFactory - accelerated volume rendering with texture maps

  The VolumePlanesFactory uses a set of texture maps to do non-specular
  volume rendering.  For even for a moderately small volume a large
  amount of texture map memory is required, e.g. 20MB for a 128x128x128
  volume.  The volume is automatically subsampled to a power of two in
  each dimension to increase performance.

  Interaction with the planes (i.e. slicing into the planes) is done
  via the ClippingCubeFactory.


Derived From:

  ActorFactory

See Also:

  ClippingCubeFactory

Initialization:

  VolumePlanesFactory()

Public Methods:

  SetInput()             -- set a vtkImageData as input

  GetInput()             -- get the input

  SetLookupTable()       -- set the lookup table for the volume rendering

  GetLookupTable()       -- get the lookup table

  SetVolumeResolution(*x*,*y,*z*) -- resample the volume to a size of
                                     (*x*,*y*,*z*) before converting to
                                     textures (must be powers of two)

  GetVolumeResolution()  -- get the texture resolution

  SetVolumeBounds(*xl*,*xh*,*yl*,*yh*,*zl*,*zh*) -- specify a bounding box,
                            only the portions of the vtkImageData that lie
                            inside the box will be volume renderered

  GetVolumeBounds()      -- get the bounding box

  SetPickThreshold(*t*)  -- set the opacity value for the volume that will
                            be considered "solid" when picking is done.

  GetPickThreshold()     -- get the pick threshold

  GetClippingCube()      -- get the ClippingCubeFactory used to clip into
                            the volume

  SetOrthoPlanes(*p*)    -- use a set of OrthoPlanes to clip into the data,
                            the OrthoPlanes will also be texture-mapped
                            onto these clipping planes

  GetOrthoPlanes()       -- get the OrthoPlanes for this volume

  SetShowOrthoPlanes(*bool*)  -- specify whether to show the ortho planes

  ShowOrthoPlanesOn()    -- turn on ortho planes

  ShowOrthoPlanesOff()   -- turn off ortho planes

  GetShowOrthoPlanes()   -- get whether ortho planes are shown

  SetShowVolume(*bool*)  -- specify whether to show the volume

  ShowVolumeOn()         -- show the volume

  ShowVolumeOff()        -- don't show the volume

  GetShowVolume()        -- get whether the volume is shown

"""

#======================================
from . import ActorFactory
from . import ClippingCubeFactory
from . import PaneFrame
import math
import vtk

#======================================


class VolumePlanesFactory(ActorFactory.ActorFactory):

    def __init__(self):
        ActorFactory.ActorFactory.__init__(self)

        # whether to display the volume
        self._ShowVolume = 1
        self._StatusChange = 0

        # create a clipping cube to go with the volume
        self._ClippingCube = ClippingCubeFactory.ClippingCubeFactory()
        self.AddChild(self._ClippingCube)
        self._CubeClippingPlanes = vtk.vtkPlaneCollection()
        for i in range(6):
            self._CubeClippingPlanes.AddItem(vtk.vtkPlane())

        # for if we clip in with OrthoPlanes
        self._OrthoPlanes = None
        self._ShowOrthoPlanes = 1
        self._OrthoPlanesLookupTables = {}
        self._OrthoPickThreshold = 0.0025

        # corner clipping planes, in pairs with opposite normals
        self._CornerClippingPlanes = vtk.vtkPlaneCollection()
        for i in range(6):
            self._CornerClippingPlanes.AddItem(vtk.vtkPlane())

        # clipping planes for the volume, sorted for the
        # three chunks that will make up the final volume
        self._ClippingPlanes = [vtk.vtkPlaneCollection(),
                                vtk.vtkPlaneCollection(),
                                vtk.vtkPlaneCollection()]

        for i in range(3):
            planes = self._ClippingPlanes[i]
            cplanes = self._CornerClippingPlanes
            bplanes = self._CubeClippingPlanes
            if i == 0:
                planes.AddItem(cplanes.GetItemAsObject(0))
                planes.AddItem(bplanes.GetItemAsObject(1))
                planes.AddItem(bplanes.GetItemAsObject(2))
                planes.AddItem(bplanes.GetItemAsObject(3))
                planes.AddItem(bplanes.GetItemAsObject(4))
                planes.AddItem(bplanes.GetItemAsObject(5))
            else:
                planes.AddItem(bplanes.GetItemAsObject(0))
                planes.AddItem(cplanes.GetItemAsObject(1))
                if i == 1:
                    planes.AddItem(cplanes.GetItemAsObject(2))
                    planes.AddItem(bplanes.GetItemAsObject(3))
                    planes.AddItem(bplanes.GetItemAsObject(4))
                    planes.AddItem(bplanes.GetItemAsObject(5))
                else:
                    planes.AddItem(bplanes.GetItemAsObject(2))
                    planes.AddItem(cplanes.GetItemAsObject(3))
                    if i == 2:
                        planes.AddItem(cplanes.GetItemAsObject(4))
                        planes.AddItem(bplanes.GetItemAsObject(5))
                    else:
                        planes.AddItem(bplanes.GetItemAsObject(4))
                        planes.AddItem(bplanes.GetItemAsObject(5))

        self._Input = None

        # generate the pipeline
        self._ImagePrefilter = vtk.vtkImageShrink3D()

        self._ImageReslice = vtk.vtkImageReslice()
        self._ImageReslice.SetInterpolationModeToLinear()

        self._ImageMapToColors = vtk.vtkImageMapToColors()
        self._ImageMapToColors.SetOutputFormatToRGBA()

        self._ImageToStructuredPoints = vtk.vtkImageToStructuredPoints()

        self._ImageClipsXY = []
        self._PlanesXY = []
        self._ActorsXY = []
        self._PropertyXY = vtk.vtkProperty()
        self._PropertyXY.SetDiffuse(0)
        self._PropertyXY.SetAmbient(1)

        self._ImageClipsYZ = []
        self._PlanesYZ = []
        self._ActorsYZ = []
        self._PropertyYZ = vtk.vtkProperty()
        self._PropertyYZ.SetDiffuse(0)
        self._PropertyYZ.SetAmbient(1)

        self._ImageClipsZX = []
        self._PlanesZX = []
        self._ActorsZX = []
        self._PropertyZX = vtk.vtkProperty()
        self._PropertyZX.SetDiffuse(0)
        self._PropertyZX.SetAmbient(1)

        # a list of the renderer info
        self._RendererCurrentIndex = {}
        self._RendererActorList = {}
        self._RendererObserverList = {}

        # a transform to apply to the image
        self._ImageTransform = None
        self._TransformToGrid = vtk.vtkTransformToGrid()

        # the alpha pick threshold for the volume
        self._PickThreshold = 0.25
        # the implicit volume for finding the gradient
        self._ImplicitVolume = vtk.vtkImplicitVolume()

        # the extent of the texture maps
        self._VolumeResolution = (64, 64, 64)

        # the bounds of the volume
        self._VolumeBounds = None

    def HandleEvent(self, event):
        if self._OrthoPlanes and \
                event.actor in self._OrthoPlanes.GetActors(event.renderer):
            self._OrthoPlanes.HandleEvent(event)
        else:
            self._ClippingCube.HandleEvent(event)

    def SetVisibility(self, renderer, i):
        for actors in self._RendererActorList[renderer]:
            for actor in actors:
                actor.SetVisibility(i)
                self._ClippingCube.SetPickable(i)

        if i == 0:
            self._PickThreshold = 0.0
        else:
            self._PickThreshold = 0.25
        self.Modified()

    # add the volume rendering mechanism to a renderer
    def AddToRenderer(self, renderer):
        ActorFactory.ActorFactory.AddToRenderer(self, renderer)
        actorList = self._MakeAllActors()
        self._RendererActorList[renderer] = actorList
        self._RendererCurrentIndex[renderer] = 5
        # force update of these
        # self._ImageReslice.UpdateWholeExtent()
        self._ImageMapToColors.UpdateWholeExtent()
        self._ImageToStructuredPoints.UpdateWholeExtent()
        for actors in actorList[0:3]:
            i = 0
            for actor in actors:
                if i % 3 == 0:
                    actor.GetTexture().Render(renderer)
                    actor.GetTexture().GetInput().ReleaseData()
                actor.RenderOpaqueGeometry(renderer)
                actor.RenderTranslucentGeometry(renderer)
                i = i + 1

        try:  # new way of adding render callback
            self._RendererObserverList[renderer] = \
                renderer.AddObserver('StartEvent', self.OnRenderEvent)
        except:
            renderer.SetStartRenderMethod(lambda s=self, r=renderer:
                                          s._OnRenderEvent(r, 'StartEvent'))

    # remove volume from renderer and free resources
    def RemoveFromRenderer(self, renderer):
        actorList = self._RendererActorList[renderer]
        index = self._RendererCurrentIndex[renderer]

        del self._RendererActorList[renderer]
        del self._RendererCurrentIndex[renderer]
        try:
            renderer.RemoveObserver(self._RendererObserverList[renderer])
            del self._RendererObserverList[renderer]
        except:
            done = 0
            for frame in PaneFrame.AllPaneFrames:
                for pane in frame.GetRenderPanes():
                    if pane.GetRenderer() == renderer:
                        renderer.SetStartRenderMethod(pane.StartRender)
                        done = 1
                        break
                if done:
                    break
            if not done:
                try:
                    renderer.SetStartRenderMethod(None)
                except:
                    renderer.SetStartRenderMethod(lambda: None)

        for actor in actorList[index]:
            renderer.RemoveActor(actor)

        clips = (self._ImageClipsXY, self._ImageClipsYZ, self._ImageClipsZX)
        planes = (self._PlanesXY, self._PlanesYZ, self._PlanesZX)
        actorlist = (self._ActorsXY, self._ActorsYZ, self._ActorsZX)

        for i in range(6):
            for actor in actorList[i]:
                for j in range(3):
                    if actor in actorlist[j]:
                        k = actorlist[j].index(actor)
                        del actorlist[j][k]
                        del clips[j][k]
                        del planes[j][k]

        ActorFactory.ActorFactory.RemoveFromRenderer(self, renderer)

    # like OnRenderEvent, but for VTK 3.2 backwards compatibility
    def _OnRenderEvent(self, renderer, vtkevent):
        # because we have pre-empted the RenderPane's StartRender
        #  method, we have to find the pane that belongs to the
        #  renderer and call the method ourselves
        done = 0
        for frame in PaneFrame.AllPaneFrames:
            for pane in frame.GetRenderPanes():
                if pane.GetRenderer() == renderer:
                    pane.StartRender()
                    done = 1
                    break
            if done:
                break
        # do the usual
        self.OnRenderEvent(renderer, vtkevent)

    # call when orientation changes
    def OnRenderEvent(self, renderer, vtkevent):
        VPN = renderer.GetActiveCamera().GetViewPlaneNormal()
        absVPN = list(map(abs, VPN))
        planeIndex = absVPN.index(max(absVPN))
        oldPlaneIndex = self._RendererCurrentIndex[renderer]
        if VPN[planeIndex] < 0:
            planeIndex = planeIndex + 3
        if planeIndex != oldPlaneIndex or self._StatusChange:
            allPlanes = self._RendererActorList[renderer]
            if oldPlaneIndex >= 0 and oldPlaneIndex < 6:
                for actor in allPlanes[oldPlaneIndex]:
                    renderer.RemoveActor(actor)

            # the OrthoPlane actors
            if self._OrthoPlanes:
                for plane in self._OrthoPlanes.GetPlanes():
                    for actor in plane.GetActors(renderer):
                        if actor.GetTexture():
                            renderer.RemoveActor(actor)

            # make a list of all the other actors
            allActorsList = []
            allActors = renderer.GetActors()
            allActors.InitTraversal()
            while 1:
                actor = allActors.GetNextItem()
                if actor is None:
                    break
                if actor.GetProperty().GetOpacity() < 1.0:
                    allActorsList.append(actor)
            for actor in allActorsList:
                renderer.RemoveActor(actor)

            i = 0
            for actor in allPlanes[planeIndex]:
                if (i % 3 == 0 or (self._OrthoPlanes and self._ShowOrthoPlanes)) and \
                        self._ShowVolume:
                    renderer.AddActor(actor)
                i = i + 1

        self._RendererCurrentIndex[renderer] = planeIndex

        if self._LookupTable.GetMTime() > self._RenderTime.GetMTime():
            self._ImageMapToColors.UpdateWholeExtent()
            self._ImageToStructuredPoints.UpdateWholeExtent()
            i = 0
            for actor in self._RendererActorList[renderer][planeIndex]:
                if i % 3 == 0:
                    actor.GetTexture().Render(renderer)
                    actor.GetTexture().GetInput().ReleaseData()
                i = i + 1

        if not (self._OrthoPlanes and self._ShowOrthoPlanes):
            transform = self._ClippingCube.GetTransform()
            cplanes = self._CornerClippingPlanes
            bplanes = self._CubeClippingPlanes
            cplanes.InitTraversal()
            bplanes.InitTraversal()
            for p in self._ClippingCube.GetPlanes():
                bplane = bplanes.GetNextItem()
                bplane.SetNormal(transform.TransformNormal(p.GetNormal()))
                bplane.SetOrigin(transform.TransformPoint(p.GetCenter()))
                cplane = cplanes.GetNextItem()
                cplane.SetNormal(transform.TransformNormal(p.GetNormal()))
                cplane.SetOrigin(transform.TransformPoint(p.GetCenter()))

        else:
            for i in range(self._OrthoPlanes.GetNumberOfInputs()):
                needupdate = 0
                try:
                    table = self._OrthoPlanesLookupTables[i]
                except KeyError:
                    table = vtk.vtkLookupTable()
                    self._OrthoPlanesLookupTables[i] = table
                    needupdate = 1

                oldtable = self._OrthoPlanes.GetLookupTable(i)
                vtable = self._LookupTable
                if (oldtable.GetMTime() > table.GetMTime() or
                        vtable.GetMTime() > table.GetMTime() or needupdate):
                    # map everything with alpha below threshold to transparent
                    trange = oldtable.GetTableRange()
                    vrange = vtable.GetTableRange()
                    n = oldtable.GetNumberOfColors()
                    m = vtable.GetNumberOfColors()
                    table.SetTableRange(trange[0], trange[1])
                    table.SetNumberOfColors(n)
                    for j in range(n):
                        r, g, b, a = oldtable.GetTableValue(j)
                        v = trange[0] + j / (n - 1.0) * (trange[1] - trange[0])
                        idx = int((v - vrange[0]) / (vrange[
                                  1] - vrange[0]) * (m - 1.0) + 0.5)
                        if idx < 0:
                            idx = 0
                        if idx > m - 1:
                            idx = m - 1
                        vr, vg, vb, va = vtable.GetTableValue(idx)
                        # vr,vg,vb,va = vtable.GetColor(v)
                        if va < self._OrthoPickThreshold or j == 0:
                            table.SetTableValue(j, r, g, b, 0)
                        else:
                            table.SetTableValue(j, r, g, b, a)

            transform = self._OrthoPlanes.GetTransform()
            pos = transform.TransformPoint(self._OrthoPlanes.GetOrthoCenter())
            cpos = renderer.GetActiveCamera().GetPosition()
            cnorm = (cpos[0] - pos[0], cpos[1] - pos[1], cpos[2] - pos[2])
            n = math.sqrt(cnorm[0] ** 2 + cnorm[1] ** 2 + cnorm[2] ** 2)
            cnorm = (old_div(cnorm[0], n), old_div(cnorm[1], n), old_div(cnorm[2], n))

            origins = []
            normals = []

            cplanes = self._CornerClippingPlanes
            bplanes = self._CubeClippingPlanes
            cplanes.InitTraversal()
            bplanes.InitTraversal()
            for plane in self._OrthoPlanes.GetPlanes():
                origin = plane.GetOrigin()
                normal = plane.GetNormal()
                originw = transform.TransformPoint(origin)
                normalw = transform.TransformNormal(normal)
                if (cnorm[0] * normalw[0] + cnorm[1] * normalw[1] + cnorm[2] * normalw[2] > 0):
                    normalw = (-normalw[0], -normalw[1], -normalw[2])
                else:
                    normal = (-normal[0], -normal[1], -normal[2])
                origins.append(origin)
                normals.append(normal)
                # this is a brute-force way of matching the planes
                cplane = cplanes.GetNextItem()
                cplane.SetOrigin(originw)
                cplane.SetNormal(normalw)
                for p in self._ClippingCube.GetPlanes():
                    if (-normal[0], -normal[1], -normal[2]) == p.GetNormal():
                        bplane = bplanes.GetNextItem()
                        bplane.SetNormal(normalw[0], normalw[1], normalw[2])
                        bplane.SetOrigin(
                            transform.TransformPoint(p.GetCenter()))
                        if bplane.EvaluateFunction(*cplane.GetOrigin()) < 0:
                            cplane.SetOrigin(bplane.GetOrigin())
                        break
                cplane = cplanes.GetNextItem()
                cplane.SetOrigin(originw)
                cplane.SetNormal(-normalw[0], -normalw[1], -normalw[2])
                for p in self._ClippingCube.GetPlanes():
                    if normal == p.GetNormal():
                        bplane = bplanes.GetNextItem()
                        bplane.SetNormal(-normalw[0], -normalw[1], -normalw[2])
                        bplane.SetOrigin(
                            transform.TransformPoint(p.GetCenter()))
                        if bplane.EvaluateFunction(*cplane.GetOrigin()) < 0:
                            cplane.SetOrigin(bplane.GetOrigin())
                        break

            # make sure orthoplanes are drawn after the volume
            k = 0
            for plane in self._OrthoPlanes.GetPlanes():
                i = 0
                for actor in plane.GetActors(renderer):
                    texture = actor.GetTexture()
                    if not texture:
                        continue
                    if texture.GetLookupTable() != self._OrthoPlanesLookupTables[i]:
                        texture.SetLookupTable(
                            self._OrthoPlanesLookupTables[i])
                        texture.MapColorScalarsThroughLookupTableOn()
                        # these next three lines are a real hack to force the
                        # color mapping to be done by the texture, not by
                        # vtkImageMapToColors
                        source = texture.GetInput().GetSource()
                        while not source.IsA("vtkImageReslice"):
                            source = source.GetInput().GetSource()
                        texture.SetInput(source.GetOutput())
                    if actor.GetProperty().GetOpacity() != 0.999:
                        property = vtk.vtkProperty()
                        actor.GetProperty().DeepCopy(property)
                        actor.SetProperty(property)
                        actor.GetProperty().SetOpacity(0.999)
                    mapper = actor.GetMapper()
                    planes = mapper.GetClippingPlanes()
                    if not planes or planes.GetNumberOfItems() != 6:
                        planes = vtk.vtkPlaneCollection()
                        for j in range(6):
                            planes.AddItem(vtk.vtkPlane())
                        mapper.SetClippingPlanes(planes)
                    planes.InitTraversal()
                    bplanes.InitTraversal()
                    for j in range(6):
                        np = planes.GetNextItem()
                        bplane = bplanes.GetNextItem()
                        # an ugly hack to ensure exact rounding for comparison
                        np.SetNormal(transform.TransformNormal(normals[old_div(j, 2)]))
                        if old_div(j, 2) != k and bplane.GetNormal() == np.GetNormal() and \
                                bplane.EvaluateFunction(*origins[old_div(j, 2)]) > 0:
                            np.SetOrigin(origins[old_div(j, 2)])
                            np.SetNormal(normals[old_div(j, 2)])
                        else:
                            np.SetOrigin(transform.GetInverse().
                                         TransformPoint(bplane.GetOrigin()))
                            np.SetNormal(transform.GetInverse().
                                         TransformNormal(bplane.GetNormal()))
                    i = i + 1
                    if planeIndex != oldPlaneIndex or self._StatusChange:
                        renderer.AddActor(actor)
                k = k + 1

        # put all the other actors back
        if planeIndex != oldPlaneIndex or self._StatusChange:
            for actor in allActorsList:
                renderer.AddActor(actor)

        self._StatusChange = 0
        self._RenderTime.Modified()

    def SetImageTransform(self, transform):
        self._ImageTransform = transform
        if not transform:
            self._ImageReslice.SetResliceTransform(None)
        elif transform.IsA('vtkLinearTransform'):
            self._ImageReslice.SetResliceTransform(
                transform.GetLinearInverse())
        elif transform.IsA('vtkHomogeneousTransform'):
            self._ImageReslice.SetResliceTransform(
                transform.GetHomogeneousInverse())
        else:
            tgrid = self._TransformToGrid
            tgrid.SetInput(transform.GetInverse())
            gridt = vtk.vtkGridTransform()
            gridt.SetInterpolationModeToCubic()
            gridt.SetDisplacementGrid(tgrid.GetOutput())
            self._ImageReslice.SetResliceTransform(transform.GetInverse())

        self._ImplicitVolume.SetTransform(
            self._ImageReslice.GetResliceTransform())

    def GetImageTransform(self, transform):
        return self._ImageTransform

    def SetInput(self, input):
        # the input is the image data to slice through
        input.UpdateInformation()
        extent = input.GetExtent()  # VTK 6
        origin = input.GetOrigin()
        spacing = input.GetSpacing()
        if self._VolumeBounds:
            bounds = self._VolumeBounds
        else:
            bounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                      origin[0] + spacing[0] * (extent[1] + 0.5),
                      origin[1] + spacing[1] * (extent[2] - 0.5),
                      origin[1] + spacing[1] * (extent[3] + 0.5),
                      origin[2] + spacing[2] * (extent[4] - 0.5),
                      origin[2] + spacing[2] * (extent[5] + 0.5)]

        resliceExtent = [0, self._VolumeResolution[0] - 1,
                         0, self._VolumeResolution[1] - 1,
                         0, self._VolumeResolution[2] - 1]

        resliceSpacing = (old_div((bounds[1] - bounds[0]), resliceExtent[1]),
                          old_div((bounds[3] - bounds[2]), resliceExtent[3]),
                          old_div((bounds[5] - bounds[4]), resliceExtent[5]))

        resliceOrigin = (bounds[0] + 0.5 * resliceSpacing[0],
                         bounds[2] + 0.5 * resliceSpacing[1],
                         bounds[4] + 0.5 * resliceSpacing[2])

        # first shrink the image & antialias
        shrink = [1.0, 1.0, 1.0]
        for i in range(3):
            s = abs(old_div(resliceSpacing[i], spacing[i]))
            if s > 1.0:
                shrink[i] = s

        self._ImagePrefilter.SetInput(input)
        self._ImagePrefilter.SetShrinkFactors(shrink)
        self._ImagePrefilter.MeanOn()
        self._ImagePrefilter.ReleaseDataFlagOn()

        # need to shift to correct the error in vtkImageShrink3D...
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy((1.0, 0.0, 0.0, 0.5 * (spacing[0] - resliceSpacing[0]),
                         0.0, 1.0, 0.0, 0.5 * (spacing[1] - resliceSpacing[1]),
                         0.0, 0.0, 1.0, 0.5 * (spacing[2] - resliceSpacing[2]),
                         0.0, 0.0, 0.0, 1.0))

        # apply the shift correction, resample to power of two
        # (if vtkImageReslice did antialiasing, there would be no need
        # for the vtkImageShrink3D)
        self._ImageReslice.SetInput(self._ImagePrefilter.GetOutput())
        self._ImageReslice.SetResliceAxes(matrix)
        self._ImageReslice.SetOutputExtent(resliceExtent)
        self._ImageReslice.SetOutputOrigin(resliceOrigin)
        self._ImageReslice.SetOutputSpacing(resliceSpacing)
        self._ImageReslice.ReleaseDataFlagOff()

        # apply the color table
        self._ImageMapToColors.SetInput(self._ImageReslice.GetOutput())
        self._ImageMapToColors.ReleaseDataFlagOff()

        # convert to structured points before chopping up and sending to
        # the textures
        self._ImageToStructuredPoints.SetInput(
            self._ImageMapToColors.GetOutput())
        self._ImageToStructuredPoints.ReleaseDataFlagOff()

        # this is for if we want to warp the volume before renderering
        self._TransformToGrid.SetGridSpacing(
            [4 * x for x in resliceSpacing])
        self._TransformToGrid.SetGridOrigin(resliceOrigin)
        self._TransformToGrid.SetGridExtent(
            [old_div(x, 4) for x in resliceExtent])

        # set opacity according to slice spacing (is this correct?)
        self._PropertyXY.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[2])))
        self._PropertyYZ.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[0])))
        self._PropertyZX.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[1])))

        # set clipping cube bounds
        if self._VolumeBounds:
            self._ClippingCube.SetBounds(self._VolumeBounds)
        else:
            self._ClippingCube.SetBounds(input.GetBounds())

        # set up implicit volume
        self._ImplicitVolume.SetTransform(
            self._ImageReslice.GetResliceTransform())
        self._ImplicitVolume.SetVolume(input)
        self._ImplicitVolume.GetVolume().Update()

        self._Input = input
        self.Modified()

    def GetInput(self):
        return self._Input

    def SetOrthoPlanes(self, planes):
        if planes == self._OrthoPlanes:
            return
        if self._OrthoPlanes:
            self.RemoveChild(self._OrthoPlanes)
        if planes:
            self.AddChild(planes)
            self._ClippingCube.GetTransform().SetInput(planes.GetTransform())
        self._OrthoPlanes = planes
        self._StatusChange = 1
        self.Modified()

    def GetOrthoPlanes(self):
        return self._OrthoPlanes

    def SetShowOrthoPlanes(self, i):
        if i == self._ShowOrthoPlanes:
            return
        self._StatusChange = 1
        self._ShowOrthoPlanes = i
        self.Modified()

    def GetShowOrthoPlanes(self):
        return self._ShowOrthoPlanes

    def ShowOrthoPlanesOn(self):
        self.SetShowOrthoPlanes(1)

    def ShowOrthoPlanesOff(self):
        self.SetShowOrthoPlanes(0)

    def SetShowVolume(self, i):
        if i == self._ShowVolume:
            return
        self._StatusChange = 1
        self._ShowVolume = i
        self.Modified()

    def GetShowVolume(self):
        return self._ShowVolume

    def ShowVolumeOn(self):
        self.SetShowVolume(1)

    def ShowVolumeOff(self):
        self.SetShowVolume(0)

    def SetClippingCube(self, cube):
        self.RemoveChild(self._ClippingCube)
        self._ClippingCube = cube

    def GetClippingCube(self):
        return self._ClippingCube

    def SetLookupTable(self, table):
        # the lookup table associated with the data
        self._LookupTable = table
        self._ImageMapToColors.SetLookupTable(table)
        self.Modified()

    def GetLookupTable(self):
        return self._LookupTable

    def SetVolumeBounds(self, *b):
        if len(b) == 0:
            b = b[0]
        self._VolumeBounds = tuple(map(float, b))
        renderers = self._Renderers
        for renderer in renderers:
            self.RemoveFromRenderer(renderer)
        if self._Input:
            self.SetInput(self._Input)
        for renderer in renderers:
            self.AddToRenderer(renderer)

    def GetVolumeBounds(self):
        return self._VolumeBounds

    def SetVolumeExtent(self, *r):
        self.SetVolumeResolution(*r)

    def SetVolumeResolution(self, *r):
        if len(r) == 1:
            r = r[0]
        renderers = list(self._Renderers)
        for renderer in renderers:
            self.RemoveFromRenderer(renderer)
        self._VolumeResolution = tuple(r)
        if self._Input:
            self.SetInput(self._Input)
        for renderer in renderers:
            self.AddToRenderer(renderer)

    def GetVolumeResolution(self):
        return self._VolumeResolution

    def HasChangedSince(self, sinceMTime):
        if (ActorFactory.ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        if (self._Input and self._Input.GetMTime() > sinceMTime):
            return 1
        if (self._LookupTable and self._LookupTable.GetMTime() > sinceMTime):
            return 1
        return 0

    def SetPickThreshold(self, thresh):
        self._PickThreshold = thresh

    def GetPickThreshold(self, thresh):
        return self._PickThreshold

    def GetPickList(self, event):
        # get a list of PickInformation objects, one for each picked actor

        # first query the clipping cube
        picklist = self._ClippingCube.GetPickList(event)

        if len(picklist) == 1:
            info = ActorFactory.PickInformation()
            event.renderer.SetDisplayPoint(event.x, event.y, 0.0)
            event.renderer.DisplayToWorld()
            info.position = event.renderer.GetWorldPoint()[0:3]
            info.normal = event.renderer.GetActiveCamera().GetViewPlaneNormal()
            info.vector = event.renderer.GetActiveCamera().GetViewUp()
            picklist.append(info)

        # if we have entrance and exit points,
        if len(picklist) == 2:
            discardedinfo = None
            if self._OrthoPlanes and self._ShowOrthoPlanes:
                cpos = event.renderer.GetActiveCamera().GetPosition()
                picklist2 = []
                for plane in self._OrthoPlanes.GetPlanes():
                    picklist2 = picklist2 + plane.GetPickList(event)

                for info in list(picklist2):
                    clipplanes = info.actor.GetMapper().GetClippingPlanes()
                    if clipplanes:
                        x, y, z = self._OrthoPlanes.GetTransform().GetInverse().\
                            TransformPoint(info.position)
                        clipplanes.InitTraversal()
                        plane = clipplanes.GetNextItem()
                        while (plane):
                            if plane.EvaluateFunction(x, y, z) < 0:
                                break
                            plane = clipplanes.GetNextItem()
                        if plane:
                            picklist2.remove(info)

                if picklist2:
                    for info in picklist + picklist2:
                        coord = info.position
                        info.distance = math.sqrt((coord[0] - cpos[0]) ** 2 +
                                                  (coord[1] - cpos[1]) ** 2 +
                                                  (coord[2] - cpos[2]) ** 2)

                    picklist.sort(lambda pn1, pn2: int(
                        pn1.distance - pn2.distance))
                    picklist2.sort(lambda pn1, pn2: int(
                        pn1.distance - pn2.distance))
                    if picklist2[0].distance > picklist[0].distance:
                        discardedinfo = picklist[0]
                        picklist[0] = picklist2[0]

            point1 = picklist[0].position
            point2 = picklist[1].position
            vec = (point2[0] - point1[0], point2[
                   1] - point1[1], point2[2] - point1[2])
            pathlength = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
            if pathlength < 1.0:
                hitVolume = 1
            else:
                hitVolume = 0
                if self._ClippingCube.ShowCubeWhenPicked == 1:
                        # otherwise, clip cube can disappear entirely if no textures
                        # are contained within it.
                    if pathlength < 100:
                        self._PickThreshold = 0.0
                    else:
                        self._PickThreshold = 0.25

            # set up an implicit function that we can query
            vol = self._ImplicitVolume
            vol.SetOutValue(self._LookupTable.GetTableRange()[0])

            if discardedinfo:
                table = self._OrthoPlanesLookupTables[0]
            else:
                table = self._LookupTable
            range = table.GetTableRange()
            maxidx = table.GetNumberOfColors() - 1

            if self._PickThreshold > 0.0 and not hitVolume:
                # cast a ray into the volume from one side

                # get mininum voxel spacing
                spacing = min(list(map(abs, self._Input.GetSpacing())))

                # get the number of steps required along the length
                N = int(math.ceil(abs(old_div(pathlength, spacing))))
                dx, dy, dz = (old_div(vec[0], N), old_div(vec[1], N), old_div(vec[2], N))
                x0, y0, z0 = point1
                for i in range(N):
                    x = x0 + i * dx
                    y = y0 + i * dy
                    z = z0 + i * dz
                    value = vol.FunctionValue(
                        x + old_div(dx, 2), y + old_div(dy, 2), z + old_div(dz, 2))
                    idx = int(round((value - range[
                              0]) / (range[1] - range[0]) * maxidx))
                    if idx < 0:
                        idx = 0
                    elif idx > maxidx:
                        idx = maxidx
                    alpha = table.GetTableValue(idx)[3]
                    # check if alpha is greater than threshold
                    if alpha > self._PickThreshold:
                        if i != 0:
                            picklist[0].position = (x, y, z)
                            gx, gy, gz = vol.FunctionGradient(x, y, z)
                            picklist[0].normal = (-gx, -gy, -gz)
                        hitVolume = 1
                        break
                    table = self._LookupTable
                    if discardedinfo:
                        picklist[0] = discardedinfo

                if hitVolume:
                    # cast a ray into the volume from the other side
                    x1, y1, z1 = point2
                    for i in range(N):
                        x = x1 - i * dx
                        y = y1 - i * dy
                        z = z1 - i * dz
                        value = vol.FunctionValue(
                            x - old_div(dx, 2), y - old_div(dy, 2), z - old_div(dz, 2))
                        idx = int(round((value - range[
                                  0]) / (range[1] - range[0]) * maxidx))
                        if idx < 0:
                            idx = 0
                        elif idx > maxidx:
                            idx = maxidx
                        alpha = table.GetTableValue(idx)[3]
                        if alpha > self._PickThreshold:
                            if i != 0:
                                picklist[1].position = (x, y, z)
                                gx, gy, gz = vol.FunctionGradient(x, y, z)
                                picklist[1].normal = (-gx, -gy, -gz)
                            break
                else:
                    # not tracking surface
                    picklist = []

        for child in self._Children:
            if child != self._ClippingCube and \
                    child != self._OrthoPlanes:  # already done it
                picklist = picklist + child.GetPickList(event)

        return picklist

    def _MakeXYActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutputExtent()
        origin = self._ImageReslice.GetOutputOrigin()
        spacing = self._ImageReslice.GetOutputSpacing()

        bounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                  origin[0] + spacing[0] * (extent[1] + 0.5),
                  origin[1] + spacing[1] * (extent[2] - 0.5),
                  origin[1] + spacing[1] * (extent[3] + 0.5),
                  origin[2] + spacing[2] * (extent[4] - 0.5),
                  origin[2] + spacing[2] * (extent[5] + 0.5)]

        for sliceNumber in range(extent[4], old_div((extent[5] + 1), reduce)):
            # the z position of the slice
            z = origin[2] + reduce * sliceNumber * spacing[2]

            plane = vtk.vtkPlaneSource()
            plane.SetXResolution(1)
            plane.SetYResolution(1)
            plane.SetOrigin(bounds[0], bounds[2], z)
            plane.SetPoint1(bounds[1], bounds[2], z)
            plane.SetPoint2(bounds[0], bounds[3], z)

            imageClip = vtk.vtkExtractVOI()
            imageClip.SetInput(self._ImageToStructuredPoints.GetOutput())
            imageClip.SetVOI(extent[0], extent[1],
                             extent[2], extent[3],
                             reduce * sliceNumber, reduce * sliceNumber)
            imageClip.ReleaseDataFlagOn()

            texture = vtk.vtkTexture()
            texture.SetQualityTo32Bit()
            texture.SetInput(imageClip.GetOutput())
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOff()

            for i in range(3):
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(plane.GetOutput())
                mapper.SetClippingPlanes(self._ClippingPlanes[i])

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.SetTexture(texture)
                actor.PickableOff()
                actor.SetProperty(self._PropertyXY)

                self._PlanesXY.append(plane)
                self._ImageClipsXY.append(imageClip)
                self._ActorsXY.append(actor)

        numberOfPlanes = (extent[5] - extent[4] + 1) / reduce * 3
        return self._ActorsXY[-numberOfPlanes:]

    def _MakeYZActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutputExtent()
        origin = self._ImageReslice.GetOutputOrigin()
        spacing = self._ImageReslice.GetOutputSpacing()

        bounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                  origin[0] + spacing[0] * (extent[1] + 0.5),
                  origin[1] + spacing[1] * (extent[2] - 0.5),
                  origin[1] + spacing[1] * (extent[3] + 0.5),
                  origin[2] + spacing[2] * (extent[4] - 0.5),
                  origin[2] + spacing[2] * (extent[5] + 0.5)]

        for sliceNumber in range(extent[0], old_div((extent[1] + 1), reduce)):
            # the z position of the slice
            x = origin[0] + reduce * sliceNumber * spacing[0]

            plane = vtk.vtkPlaneSource()
            plane.SetXResolution(1)
            plane.SetYResolution(1)
            plane.SetOrigin(x, bounds[2], bounds[4])
            plane.SetPoint1(x, bounds[3], bounds[4])
            plane.SetPoint2(x, bounds[2], bounds[5])

            imageClip = vtk.vtkExtractVOI()
            imageClip.SetInput(self._ImageToStructuredPoints.GetOutput())
            imageClip.SetVOI(reduce * sliceNumber, reduce * sliceNumber,
                             extent[2], extent[3],
                             extent[4], extent[5])
            imageClip.ReleaseDataFlagOn()

            texture = vtk.vtkTexture()
            texture.SetQualityTo32Bit()
            texture.SetInput(imageClip.GetOutput())
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOff()

            for i in range(3):
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(plane.GetOutput())
                mapper.SetClippingPlanes(self._ClippingPlanes[i])

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.SetTexture(texture)
                actor.PickableOff()
                actor.SetProperty(self._PropertyYZ)

                self._PlanesYZ.append(plane)
                self._ImageClipsYZ.append(imageClip)
                self._ActorsYZ.append(actor)

        numberOfPlanes = (extent[1] - extent[0] + 1) / reduce * 3
        return self._ActorsYZ[-numberOfPlanes:]

    def _MakeZXActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutputExtent()
        origin = self._ImageReslice.GetOutputOrigin()
        spacing = self._ImageReslice.GetOutputSpacing()

        bounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                  origin[0] + spacing[0] * (extent[1] + 0.5),
                  origin[1] + spacing[1] * (extent[2] - 0.5),
                  origin[1] + spacing[1] * (extent[3] + 0.5),
                  origin[2] + spacing[2] * (extent[4] - 0.5),
                  origin[2] + spacing[2] * (extent[5] + 0.5)]

        for sliceNumber in range(extent[2], old_div((extent[3] + 1), reduce)):
            # the y position of the slice
            y = origin[1] + reduce * sliceNumber * spacing[1]

            plane = vtk.vtkPlaneSource()
            plane.SetXResolution(1)
            plane.SetYResolution(1)
            plane.SetOrigin(bounds[0], y, bounds[4])
            plane.SetPoint1(bounds[1], y, bounds[4])
            plane.SetPoint2(bounds[0], y, bounds[5])

            imageClip = vtk.vtkExtractVOI()
            imageClip.SetInput(self._ImageToStructuredPoints.GetOutput())
            imageClip.SetVOI(extent[0], extent[1],
                             reduce * sliceNumber, reduce * sliceNumber,
                             extent[4], extent[5])
            imageClip.ReleaseDataFlagOn()

            texture = vtk.vtkTexture()
            texture.SetQualityTo32Bit()
            texture.SetInput(imageClip.GetOutput())
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOff()

            for i in range(3):
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInput(plane.GetOutput())
                mapper.SetClippingPlanes(self._ClippingPlanes[i])

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.SetTexture(texture)
                actor.PickableOff()
                actor.SetProperty(self._PropertyZX)

                self._PlanesZX.append(plane)
                self._ImageClipsZX.append(imageClip)
                self._ActorsZX.append(actor)

        numberOfPlanes = (extent[3] - extent[2] + 1) / reduce * 3
        return self._ActorsZX[-numberOfPlanes:]

    def _MakeAllActors(self):
        planesXY = self._MakeXYActors()
        planesYZ = self._MakeYZActors()
        planesZX = self._MakeZXActors()

        reslice = self._ImageReslice
        spacing = reslice.GetOutputSpacing()

        if (spacing[2] < 0):
            planesXY.reverse()
        if (spacing[0] < 0):
            planesYZ.reverse()
        if (spacing[1] < 0):
            planesZX.reverse()

        planesYX = list(planesXY)
        planesZY = list(planesYZ)
        planesXZ = list(planesZX)

        planesYX.reverse()
        planesZY.reverse()
        planesXZ.reverse()

        return (planesYZ, planesZX, planesXY,
                planesZY, planesXZ, planesYX)

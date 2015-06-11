"""
Copyright (c) 2000 Atamai, Inc.

Use, modification and redistribution of the software, in source or
binary forms, are permitted provided that the following terms and
conditions are met:

1) Redistribution of the source code, in verbatim or modified
   form, must retain the above copyright notice, this license,
   the following disclaimer, and any notices that refer to this
   license and/or the following disclaimer.

2) Redistribution in binary form must include the above copyright
   notice, a copy of this license and the following disclaimer
   in the documentation or with other materials provided with the
   distribution.

3) Modified copies of the source code must be clearly marked as such,
   and must not be misrepresented as verbatim copies of the source code.

EXCEPT WHEN OTHERWISE STATED IN WRITING BY THE COPYRIGHT HOLDERS AND/OR
OTHER PARTIES, THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
SOFTWARE "AS IS" WITHOUT EXPRESSED OR IMPLIED WARRANTY INCLUDING, BUT
NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE.  IN NO EVENT UNLESS AGREED TO IN WRITING WILL
ANY COPYRIGHT HOLDER OR OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
THE SOFTWARE UNDER THE TERMS OF THIS LICENSE BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, LOSS OF DATA OR DATA BECOMING INACCURATE OR LOSS OF PROFIT OR
BUSINESS INTERRUPTION) ARISING IN ANY WAY OUT OF THE USE OR INABILITY TO
USE THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
"""

#
# This file represents a derivative work by Parallax Innovations Inc.
#

# This is the old version of VolumePlanesFactory, which works better with
# the Topoplogy classification data than the later versions. So we rename
# the file name to OldVolumePlanesFactory.py to co-exist with the latest
# version. H.Q.

from ActorFactory import *
from ClippingCubeFactory import *

import math


class VolumePlanesFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        # create a clipping cube to go with the volume
        self._ClippingCube = ClippingCubeFactory()
        self._ClippingCube.SetOpacity(0.0002)
        self._ClippingPlanes = self._ClippingCube.GetClippingPlanes()
        self.AddChild(self._ClippingCube)

        self._Input = None

        # generate the pipeline
        self._ImagePrefilter = vtk.vtkImageGaussianSmooth()
        self._ImagePrefilter.SetDimensionality(3)

        self._ImageReslice = vtk.vtkImageReslice()
        # self._ImageReslice.SetInterpolationModeToNearestNeighbor()
        self._ImageReslice.SetInterpolationModeToCubic()

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

        # the alpha pick threshold for the volume
        self._PickThreshold = 0.25
        # the implicit volume for finding the gradient
        self._ImplicitVolume = vtk.vtkImplicitVolume()

        # the extent of the texture maps
        self._VolumeExtent = (128, 128, 128)

        self._XYOpacity = 1.0
        self._YZOpacity = 1.0
        self._ZXOpacity = 1.0

    # add the volume rendering mechanism to a renderer
    def AddToRenderer(self, renderer):
        ActorFactory.AddToRenderer(self, renderer)
        actorList = self._MakeAllActors()
        self._RendererActorList[renderer] = actorList
        self._RendererCurrentIndex[renderer] = 5

        for actors in actorList:
            for actor in actors:
                actor.RenderOpaqueGeometry(renderer)
                actor.RenderTranslucentGeometry(renderer)

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

        clips = (self._ImageClipsXY, self._ImageClipsYZ, self._ImageClipsZX)
        planes = (self._PlanesXY, self._PlanesYZ, self._PlanesZX)
        actorlist = (self._ActorsXY, self._ActorsYZ, self._ActorsZX)

        for actor in actorList[index]:
            renderer.RemoveActor(actor)

        for i in range(0, 3):
            for actor in actorList[i] + actorList[3 + i]:
                try:
                    j = actorlist[i].index(actor)
                    del actorlist[i][j]
                    del clips[i][j]
                    del planes[i][j]
                except:
                    pass

        ActorFactory.RemoveFromRenderer(self, renderer)

    # call when orientation changes
    def _OnRenderEvent(self, renderer, vtkevent):
        """because we have pre-empted the RenderPane's StartRender
        method, we have to find the pane that belongs to the
        renderer and call the method ourselves
        """
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

    def OnRenderEvent(self, renderer, vtkevent):
        normal = renderer.GetActiveCamera().GetViewPlaneNormal()
        absNormal = map(abs, normal)
        plane = absNormal.index(max(absNormal))
        oldPlane = self._RendererCurrentIndex[renderer]
        allPlanes = self._RendererActorList[renderer]
        if (normal[plane] < 0):
            plane = plane + 3
        if (plane != oldPlane):
            if (oldPlane >= 0 and oldPlane < 6):
                for actor in allPlanes[oldPlane]:
                    renderer.RemoveActor(actor)
            for actor in allPlanes[plane]:
                renderer.AddActor(actor)
        self._RendererCurrentIndex[renderer] = plane

    def Hide(self):
        self._XYOpacity = self._PropertyXY.GetOpacity()
        self._YZOpacity = self._PropertyYZ.GetOpacity()
        self._ZXOpacity = self._PropertyZX.GetOpacity()

        self._PropertyXY.SetOpacity(0)
        self._PropertyYZ.SetOpacity(0)
        self._PropertyZX.SetOpacity(0)

    def Unhide(self):
        self._PropertyXY.SetOpacity(self._XYOpacity)
        self._PropertyYZ.SetOpacity(self._YZOpacity)
        self._PropertyZX.SetOpacity(self._ZXOpacity)

    def SetInput(self, input):
        # the input is the image data to slice through
        extent = input.GetWholeExtent()
        origin = input.GetOrigin()
        spacing = input.GetSpacing()

        resliceExtent = self._VolumeExtent

        resliceSpacing = (spacing[0] * (extent[1] - extent[0] + 1) / resliceExtent[0],
                          spacing[
                              1] * (extent[3] - extent[2] + 1) / resliceExtent[1],
                          spacing[2] * (extent[5] - extent[4] + 1) / resliceExtent[2])

        resliceOrigin = (origin[0] - 0.5 * spacing[0] + 0.5 * resliceSpacing[0],
                         origin[1] - 0.5 * spacing[1] +
                         0.5 * resliceSpacing[1],
                         origin[2] - 0.5 * spacing[2] + 0.5 * resliceSpacing[2])

        # set up the imaging pipeline

        self._ImagePrefilter.SetInput(input)
        self._ImagePrefilter.SetStandardDeviations(
            resliceSpacing[0] / spacing[0],
            resliceSpacing[
                1] / spacing[1],
            resliceSpacing[2] / spacing[2])
        self._ImagePrefilter.SetRadiusFactors(resliceSpacing[0] / spacing[0] - 0.5,
                                              resliceSpacing[
                                                  1] / spacing[1] - 0.5,
                                              resliceSpacing[2] / spacing[2] - 0.5)

        self._ImageReslice.SetInput(self._ImagePrefilter.GetOutput())
        self._ImageReslice.SetInput(input)
        self._ImageReslice.SetOutputExtent(0, resliceExtent[0] - 1,
                                           0, resliceExtent[1] - 1,
                                           0, resliceExtent[2] - 1)
        self._ImageReslice.SetOutputOrigin(resliceOrigin)
        self._ImageReslice.SetOutputSpacing(resliceSpacing)
        self._ImageReslice.UpdateWholeExtent()

        # set opacity according to slice spacing
        self._PropertyXY.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[2])))
        self._PropertyYZ.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[0])))
        self._PropertyZX.SetOpacity(
            1.0 - math.exp(-1.0 * abs(resliceSpacing[1])))
        # self._PropertyXY.SetOpacity(1)
        # self._PropertyYZ.SetOpacity(1)
        # self._PropertyZX.SetOpacity(1)

        # set clipping cube bounds
        self._ClippingCube.SetBounds(input.GetBounds())

        # set up implicit volume
        self._ImplicitVolume.SetVolume(input)
        self._ImplicitVolume.GetVolume().Update()

        self._Input = input

    def GetInput(self):
        return self._Input

    def SetClippingPlanes(self, planes):
        self._ClippingPlanes = planes
        for actor in self._ActorsXY + self._ActorsYZ + self._ActorsZX:
            actor.GetMapper().SetClippingPlanes(planes)
        self.Modified()

    def SetLookupTable(self, table):
        # the lookup table associated with the data
        self._LookupTable = table
        for actor in self._ActorsXY + self._ActorsYZ + self._ActorsZX:
            actor.GetTexture().SetLookupTable(table)
        self.Modified()

    def GetLookupTable(self):
        return self._LookupTable

    def SetVolumeExtent(self, *theExtent):
        self._VolumeExtent = tuple(theExtent)

    def GetVolumeExtent(self):
        return self._VolumeExtent

    def HasChangedSince(self, sinceMTime):
        if (ActorFactory.HasChangedSince(self, sinceMTime)):
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

        # if we have entrance and exit points,
        if len(picklist) == 2:
            point1 = picklist[0].position
            point2 = picklist[1].position
            vec = (point2[0] - point1[0], point2[
                   1] - point1[1], point2[2] - point1[2])
            pathlength = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)

            # get mininum voxel spacing
            spacing = min(map(abs, self._Input.GetSpacing()))

            # get the number of steps required along the length
            N = int(math.ceil(abs(pathlength / spacing)))
            dx, dy, dz = (vec[0] / N, vec[1] / N, vec[2] / N)

            # set up an implicit function that we can query
            vol = self._ImplicitVolume
            vol.SetTransform(self._Transform.GetLinearInverse())
            vol.SetOutValue(self._LookupTable.GetTableRange()[0])

            table = self._LookupTable
            range = table.GetTableRange()
            maxidx = table.GetNumberOfColors() - 1
            hitVolume = 0

            # cast a ray into the volume from one side
            x0, y0, z0 = point1
            for i in range(N):
                x = x0 + i * dx
                y = y0 + i * dy
                z = z0 + i * dz
                value = vol.FunctionValue(x + dx / 2, y + dy / 2, z + dz / 2)
                idx = int(
                    round((value - range[0]) / (range[1] - range[0]) * maxidx))
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

            if hitVolume:
                # cast a ray into the volume from the other side
                x1, y1, z1 = point2
                for i in range(N):
                    x = x1 - i * dx
                    y = y1 - i * dy
                    z = z1 - i * dz
                    value = vol.FunctionValue(
                        x - dx / 2, y - dy / 2, z - dz / 2)
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
                picklist = []

        for child in self._Children:
            if child != self._ClippingCube:  # already done it
                picklist = picklist + child.GetPickList(event)

        return picklist

    def _MakeXYActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutput().GetWholeExtent()
        origin = self._ImageReslice.GetOutput().GetOrigin()
        spacing = self._ImageReslice.GetOutput().GetSpacing()

        # origin is the location of index (0,0,0) in the image
        sliceOriginX = origin[0] - 0.5 * spacing[0]
        sliceOriginY = origin[1] - 0.5 * spacing[1]

        # the edge of the image opposite the origin
        sliceEdgeX = origin[0] + spacing[0] * (extent[1] - extent[0] + 0.5)
        sliceEdgeY = origin[1] + spacing[1] * (extent[3] - extent[2] + 0.5)

        for sliceNumber in range(extent[4], (extent[5] + 1) / reduce):
            # the z position of the slice
            sliceOriginZ = origin[2] + reduce * sliceNumber * spacing[2]

            plane = vtk.vtkPlaneSource()
            plane.SetOrigin(sliceOriginX,
                            sliceOriginY,
                            sliceOriginZ)
            plane.SetPoint1(sliceEdgeX,
                            sliceOriginY,
                            sliceOriginZ)
            plane.SetPoint2(sliceOriginX,
                            sliceEdgeY,
                            sliceOriginZ)

            mapper = vtk.vtkPolyDataMapper()
            if (self._ClippingPlanes):
                mapper.SetClippingPlanes(self._ClippingPlanes)
            mapper.SetInput(plane.GetOutput())

            imageClip = vtk.vtkImageClip()
            imageClip.SetInput(self._ImageReslice.GetOutput())
            imageClip.SetOutputWholeExtent(extent[0], extent[1],
                                           extent[2], extent[3],
                                           reduce * sliceNumber, reduce * sliceNumber)

            texture = vtk.vtkTexture()
            try:
                texture.SetQualityTo32Bit()
            except:
                pass
            texture.SetInput(imageClip.GetOutput())
            texture.SetLookupTable(self._LookupTable)
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOn()

            actor = self._NewActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)
            actor.PickableOff()
            actor.SetProperty(self._PropertyXY)

            self._PlanesXY.append(plane)
            self._ImageClipsXY.append(imageClip)
            self._ActorsXY.append(actor)

        numberOfPlanes = (extent[5] - extent[4] + 1) / reduce
        return self._ActorsXY[-numberOfPlanes:]

    def _MakeYZActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutput().GetWholeExtent()
        origin = self._ImageReslice.GetOutput().GetOrigin()
        spacing = self._ImageReslice.GetOutput().GetSpacing()

        # origin is the location of index (0,0,0) in the image
        sliceOriginY = origin[1] - 0.5 * spacing[1]
        sliceOriginZ = origin[2] - 0.5 * spacing[2]

        # the edge of the image opposite the origin
        sliceEdgeY = origin[1] + spacing[1] * (extent[3] - extent[2] + 0.5)
        sliceEdgeZ = origin[2] + spacing[2] * (extent[5] - extent[4] + 0.5)

        for sliceNumber in range(extent[0], (extent[1] + 1) / reduce):
            # the z position of the slice
            sliceOriginX = origin[0] + reduce * sliceNumber * spacing[0]

            plane = vtk.vtkPlaneSource()
            plane.SetOrigin(sliceOriginX,
                            sliceOriginY,
                            sliceOriginZ)
            plane.SetPoint1(sliceOriginX,
                            sliceEdgeY,
                            sliceOriginZ)
            plane.SetPoint2(sliceOriginX,
                            sliceOriginY,
                            sliceEdgeZ)

            mapper = vtk.vtkPolyDataMapper()
            if (self._ClippingPlanes):
                mapper.SetClippingPlanes(self._ClippingPlanes)
            mapper.SetInput(plane.GetOutput())

            imageClip = vtk.vtkImageClip()
            imageClip.SetInput(self._ImageReslice.GetOutput())
            imageClip.SetOutputWholeExtent(
                reduce * sliceNumber, reduce * sliceNumber,
                extent[2], extent[3],
                extent[4], extent[5])

            texture = vtk.vtkTexture()
            try:
                texture.SetQualityTo32Bit()
            except:
                pass
            texture.SetInput(imageClip.GetOutput())
            texture.SetLookupTable(self._LookupTable)
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOn()

            actor = self._NewActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)
            actor.PickableOff()
            actor.SetProperty(self._PropertyYZ)

            self._PlanesYZ.append(plane)
            self._ImageClipsYZ.append(imageClip)
            self._ActorsYZ.append(actor)

        numberOfPlanes = (extent[1] - extent[0] + 1) / reduce
        return self._ActorsYZ[-numberOfPlanes:]

    def _MakeZXActors(self, reduce=1):
        # get a texture-mapped actor
        extent = self._ImageReslice.GetOutputExtent()
        origin = self._ImageReslice.GetOutputOrigin()
        spacing = self._ImageReslice.GetOutputSpacing()

        # origin is the location of index (0,0,0) in the image
        sliceOriginX = origin[0] - 0.5 * spacing[0]
        sliceOriginZ = origin[2] - 0.5 * spacing[2]

        # the edge of the image opposite the origin
        sliceEdgeX = origin[0] + spacing[0] * (extent[1] - extent[0] + 0.5)
        sliceEdgeZ = origin[2] + spacing[2] * (extent[5] - extent[4] + 0.5)

        for sliceNumber in range(extent[2], (extent[3] + 1) / reduce):
            # the z position of the slice
            sliceOriginY = origin[1] + reduce * sliceNumber * spacing[1]

            plane = vtk.vtkPlaneSource()
            plane.SetOrigin(sliceOriginX,
                            sliceOriginY,
                            sliceOriginZ)
            plane.SetPoint1(sliceEdgeX,
                            sliceOriginY,
                            sliceOriginZ)
            plane.SetPoint2(sliceOriginX,
                            sliceOriginY,
                            sliceEdgeZ)

            mapper = vtk.vtkPolyDataMapper()
            if (self._ClippingPlanes):
                mapper.SetClippingPlanes(self._ClippingPlanes)
            mapper.SetInput(plane.GetOutput())

            imageClip = vtk.vtkImageClip()
            imageClip.SetInput(self._ImageReslice.GetOutput())
            imageClip.SetOutputWholeExtent(extent[0], extent[1],
                                           reduce * sliceNumber, reduce *
                                           sliceNumber,
                                           extent[4], extent[5])

            texture = vtk.vtkTexture()
            try:
                texture.SetQualityTo32Bit()
            except:
                pass
            texture.SetInput(imageClip.GetOutput())
            texture.SetLookupTable(self._LookupTable)
            texture.RepeatOff()
            texture.InterpolateOn()
            texture.MapColorScalarsThroughLookupTableOn()

            actor = self._NewActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)
            actor.PickableOff()
            actor.SetProperty(self._PropertyZX)

            self._PlanesZX.append(plane)
            self._ImageClipsZX.append(imageClip)
            self._ActorsZX.append(actor)

        numberOfPlanes = (extent[3] - extent[2] + 1) / reduce
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

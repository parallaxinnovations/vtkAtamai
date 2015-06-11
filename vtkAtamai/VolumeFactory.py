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
    'module_name': '$RCSfile: VolumeFactory.py,v $',
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
VolumeFactory - volume rendering using color transfer function

  The VolumeFactory uses VTK's built-in volume rendering functionality.
  Texture-accelerated volume rendering is used while the user is interacting
  with the volume, and ray-cast volume rendering is used for high-quality
  volume rendering.

  Interaction with the planes (i.e. slicing into the planes) is done
  via the ClippingCubeFactory.


Derived From:

  ActorFactory

See Also:

  ClippingCubeFactory

Initialization:

  VolumeFactory()

Public Methods:

  SetInput()             -- set a vtkImageData as input

  GetInput()             -- get the input

  SetColorTransferFunction() -- set the color transfer function

  GetColorTransferFunction() -- get the color transfer function

  SetOpacityTransferFunction() -- set the opacity transfer function

  GetOpacityTransferFunction() -- get the opacity transfer function

  GetVolumeProperty()    -- get the vtkVolumeProperty so you can modify it

  SetVolumeProperty()    -- set a new vtkVolumeProperty for this volume

  GetVolumeBounds()      -- get the bounding box

  SetVolumeBounds(*xl*,*xh*,*yl*,*yh*,*zl*,*zh*) -- specify a bounding box,
                            only the portions of the vtkImageData that lie
                            inside the box will be volume renderered

  SetPickThreshold(*t*)  -- set the opacity value for the volume that will
                            be considered "solid" when picking is done.

  GetPickThreshold()     -- get the pick threshold

  GetClippingCube()      -- get the ClippingCubeFactory used to clip into
                            the volume

"""

#======================================
import ActorFactory
import ClippingCubeFactory
import PaneFrame
import math
import vtk

#======================================


class VolumeFactory(ActorFactory.ActorFactory):

    def __init__(self):
        ActorFactory.ActorFactory.__init__(self)

        self._LookupTable = None  # lookup table is currently not used
        self._ColorTransferFunction = None
        self._OpacityTransferFunction = None
        self._RendererObserverList = {}

        # create a clipping cube to go with the volume
        self._ClippingCube = ClippingCubeFactory.ClippingCubeFactory()
        self.AddChild(self._ClippingCube)
        self._CubeClippingPlanes = vtk.vtkPlaneCollection()
        for i in range(6):
            self._CubeClippingPlanes.AddItem(vtk.vtkPlane())

        # corner clipping planes, in pairs with opposite normals
        self._CornerClippingPlanes = vtk.vtkPlaneCollection()
        for i in range(6):
            self._CornerClippingPlanes.AddItem(vtk.vtkPlane())

        # clipping planes for the volume, sorted for the
        # three chunks that will make up the final volume
        # (these are currently unused)
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

        # generate the pipeline pieces
        self._Input = None

        # transform the full-resolution volume
        self._RayCastReslice = vtk.vtkImageReslice()
        self._RayCastReslice.SetInterpolationModeToLinear()

        # subsample the volume for low-res rendering
        self._ImagePrefilter1 = vtk.vtkImageShrink3D()

        self._ImagePrefilter2 = vtk.vtkImageShrink3D()

        # transform the subsampled volume
        self._ImageReslice1 = vtk.vtkImageReslice()
        self._ImageReslice1.SetInterpolationModeToLinear()

        self._ImageReslice2 = vtk.vtkImageReslice()
        self._ImageReslice2.SetInterpolationModeToLinear()

        # convert to RGBA for rendering (unused)
        self._ImageMapToColors = vtk.vtkImageMapToColors()
        self._ImageMapToColors.SetOutputFormatToRGBA()

        # strictly for VTK 3.2 compatibility
        self._ImageToStructuredPoints = vtk.vtkImageToStructuredPoints()

        # a transform to apply to the image
        self._ImageTransform = None
        self._TransformToGrid = vtk.vtkTransformToGrid()

        # the opacity pick threshold for the volume
        self._PickThreshold = 0.99
        # the implicit volume for finding the gradient
        self._ImplicitVolume = vtk.vtkImplicitVolume()

        # the texture dimensions (later this will be set automatically
        #    to provide the desired interactive rendering time)
        self._TextureSize = 128

        # the bounds of the volume
        self._VolumeBounds = None

        # vtkVolume specific stuff
        self._VolumeProperty = vtk.vtkVolumeProperty()
        self._VolumeProperty.SetInterpolationTypeToLinear()

        rayCastFunction = vtk.vtkVolumeRayCastCompositeFunction()
        self._VolumeRayCastMapper = vtk.vtkVolumeRayCastMapper()
        self._VolumeRayCastMapper.SetVolumeRayCastFunction(rayCastFunction)
        self._VolumeRayCastMapper.SetClippingPlanes(
            self._ClippingCube.GetClippingPlanes())
        try:  # vtk 3.2 does not contain this function call:
            self._VolumeRayCastMapper.AutoAdjustSampleDistancesOff()
        except:
            pass

        self._VolumeTextureMapper1 = vtk.vtkVolumeTextureMapper2D()
        self._VolumeTextureMapper1.SetTargetTextureSize(self._TextureSize / 4,
                                                        self._TextureSize / 4)
        self._VolumeTextureMapper1.SetMaximumNumberOfPlanes(
            self._TextureSize / 2)
        self._VolumeTextureMapper1.SetClippingPlanes(
            self._ClippingCube.GetClippingPlanes())
        try:  # vtk 3.2 does not contain this function call:
            # set to the amount of available texture memory (24MB is a good
            # start)
            self._VolumeTextureMapper1.SetMaximumStorageSize(24 * 1024 * 1024)
        except:
            pass

        self._VolumeTextureMapper2 = vtk.vtkVolumeTextureMapper2D()
        self._VolumeTextureMapper2.SetTargetTextureSize(self._TextureSize,
                                                        self._TextureSize)
        self._VolumeTextureMapper2.SetMaximumNumberOfPlanes(self._TextureSize)
        self._VolumeTextureMapper2.SetClippingPlanes(
            self._ClippingCube.GetClippingPlanes())

        try:  # vtk 3.2 does not contain this function call:
            # set to the amount of available texture memory (24MB is a good
            # start)
            self._VolumeTextureMapper2.SetMaximumStorageSize(24 * 1024 * 1024)
        except:
            pass

        # set two levels of detail: texture and ray-casting
        self._Volume = vtk.vtkLODProp3D()
        self._Volume.PickableOff()
        idT1 = self._Volume.AddLOD(self._VolumeTextureMapper1,
                                   self._VolumeProperty,
                                   0.02)
        idT2 = self._Volume.AddLOD(self._VolumeTextureMapper2,
                                   self._VolumeProperty,
                                   0.1)

        # remember these LOD id numbers
        self._lod = [idT1, idT2]

#        idRC = self._Volume.AddLOD(self._VolumeRayCastMapper,
#                                   self._VolumeProperty,
#                                   2.0)
        self._Volume.SetLODLevel(idT1, 2.0)
        self._Volume.SetLODLevel(idT2, 1.0)
#        self._Volume.SetLODLevel(idRC, 0.0)

    def GetLODIds(self):
        return self._lod

    def HandleEvent(self, event):
        return self._ClippingCube.HandleEvent(event)

    def SetVisibility(self, renderer, i):
        self._Volume.SetVisibility(i)
        self.Modified()

    # add the volume rendering mechanism to a renderer
    def AddToRenderer(self, renderer):
        ActorFactory.ActorFactory.AddToRenderer(self, renderer)
        # force update of these
        self._ImageReslice1.UpdateWholeExtent()
        self._ImageReslice2.UpdateWholeExtent()
        renderer.AddViewProp(self._Volume)
        # I'm not quite sure what this does...
        renderer.GetCullers().InitTraversal()
        renderer.GetCullers().GetNextItem().SetSortingStyleToBackToFront()

        try:  # new way of adding render callback
            self._RendererObserverList[renderer] = \
                renderer.AddObserver('StartEvent', self.OnRenderEvent)
        except:
            renderer.SetStartRenderMethod(lambda s=self, r=renderer:
                                          s._OnRenderEvent(r, 'StartEvent'))

    # remove volume from renderer and free resources
    def RemoveFromRenderer(self, renderer):
        renderer.RemoveViewProp(self._Volume)

        try:
            renderer.RemoveObserver(self._RendererObserverList[renderer])
            del self._RendererObserverList[renderer]
        except:
            done = 0
            for frame in PaneFrame.PaneFrame.AllPaneFrames:
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

        ActorFactory.ActorFactory.RemoveFromRenderer(self, renderer)

    # like OnRenderEvent, but for VTK 3.2 backwards compatibility
    def _OnRenderEvent(self, renderer, vtkevent):
        # because we have pre-empted the RenderPane's StartRender
        #    method, we have to find the pane that belongs to the
        #    renderer and call the method ourselves
        done = 0
        for frame in PaneFrame.PaneFrame.AllPaneFrames:
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
        self._RenderTime.Modified()

    def SetImageStencil(self, stencil):
        self._ImageReslice1.SetStencil(stencil)
        self._ImageReslice2.SetStencil(stencil)
        self._RayCastReslice.SetStencil(stencil)

    def SetImageTransform(self, transform):
        self._ImageTransform = transform
        if not transform:
            self._ImageReslice1.SetResliceTransform(None)
            self._ImageReslice2.SetResliceTransform(None)
            self._RayCastReslice.SetResliceTransform(None)
        elif transform.IsA('vtkLinearTransform'):
            self._ImageReslice1.SetResliceTransform(
                transform.GetLinearInverse())
            self._ImageReslice2.SetResliceTransform(
                transform.GetLinearInverse())
            self._RayCastReslice.SetResliceTransform(
                transform.GetLinearInverse())
        elif transform.IsA('vtkHomogeneousTransform'):
            self._ImageReslice1.SetResliceTransform(
                transform.GetHomogeneousInverse())
            self._ImageReslice2.SetResliceTransform(
                transform.GetHomogeneousInverse())
            self._RayCastReslice.SetResliceTransform(
                transform.GetHomogeneousInverse())
        else:
            tgrid = self._TransformToGrid
            tgrid.SetInput(transform.GetInverse())
            gridt = vtk.vtkGridTransform()
            gridt.SetInterpolationModeToCubic()
            gridt.SetDisplacementGrid(tgrid.GetOutput())
            self._ImageReslice1.SetResliceTransform(transform.GetInverse())
            self._ImageReslice2.SetResliceTransform(transform.GetInverse())
            self._RayCastReslice.SetResliceTransform(transform.GetInverse())

        self._ImplicitVolume.SetTransform(
            self._ImageReslice1.GetResliceTransform())

    def GetImageTransform(self, transform):
        return self._ImageTransform

    def SetInput(self, input):
        # the input is the image data to slice through
        input.UpdateInformation()
        extent = input.GetWholeExtent()
        origin = input.GetOrigin()
        spacing = input.GetSpacing()

        if self._VolumeBounds:
            bounds = list(self._VolumeBounds)
        else:
            bounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                      origin[0] + spacing[0] * (extent[1] + 0.5),
                      origin[1] + spacing[1] * (extent[2] - 0.5),
                      origin[1] + spacing[1] * (extent[3] + 0.5),
                      origin[2] + spacing[2] * (extent[4] - 0.5),
                      origin[2] + spacing[2] * (extent[5] + 0.5)]
        if bounds[0] > bounds[1]:
            bounds[0:2] = [bounds[1], bounds[0]]
        if bounds[2] > bounds[3]:
            bounds[2:4] = [bounds[3], bounds[2]]
        if bounds[4] > bounds[5]:
            bounds[4:6] = [bounds[5], bounds[4]]

        resliceExtent = [0, self._TextureSize / 2 - 1,
                         0, self._TextureSize / 2 - 1,
                         0, self._TextureSize / 2 - 1]

        resliceSpacing = ((bounds[1] - bounds[0]) / (self._TextureSize / 2),
                          (bounds[3] - bounds[2]) / (self._TextureSize / 2),
                          (bounds[5] - bounds[4]) / (self._TextureSize / 2))

        resliceOrigin = (bounds[0] + resliceSpacing[0] * 0.5,
                         bounds[2] + resliceSpacing[1] * 0.5,
                         bounds[4] + resliceSpacing[2] * 0.5)

        # first shrink the image & antialias
        shrink = [1, 1, 1]
        for i in range(3):
            s = int(abs(resliceSpacing[i] / spacing[i]))
            if s > 1:
                shrink[i] = s

        self._ImagePrefilter1.SetInput(input)
        self._ImagePrefilter1.SetShrinkFactors(map(int, shrink))
        self._ImagePrefilter1.MeanOn()
        self._ImagePrefilter1.ReleaseDataFlagOn()

        # we might need to convert from signed to unsigned here...
        t = input.GetScalarType()
        minval, maxval = input.GetScalarRange()
        if (t != vtk.VTK_UNSIGNED_SHORT) and (t != vtk.VTK_UNSIGNED_CHAR):
            f = vtk.vtkImageShiftScale()
            f.SetInput(self._ImagePrefilter1.GetOutput())
            f.SetShift(-minval)
            f.SetScale(1.0)
            f.SetOutputScalarType(t + 1)
            f.ReleaseDataFlagOn()
            obj = f.GetOutput()
        else:
            obj = self._ImagePrefilter1.GetOutput()

        # need to shift to correct the error in vtkImageShrink3D...
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy((1.0, 0.0, 0.0, 0.5 * (spacing[0] - resliceSpacing[0]),
                         0.0, 1.0, 0.0, 0.5 * (spacing[1] - resliceSpacing[1]),
                         0.0, 0.0, 1.0, 0.5 * (spacing[2] - resliceSpacing[2]),
                         0.0, 0.0, 0.0, 1.0))

        # apply the shift correction, resample to power of two
        # (if vtkImageReslice did antialiasing, there would be no need
        # for the vtkImageShrink3D)
        self._ImageReslice1.SetInput(obj)
        self._ImageReslice1.SetResliceAxes(matrix)
        self._ImageReslice1.SetOutputExtent(resliceExtent)
        self._ImageReslice1.SetOutputOrigin(resliceOrigin)
        self._ImageReslice1.SetOutputSpacing(resliceSpacing)
        self._ImageReslice1.ReleaseDataFlagOff()

        # do the higher-resolution textures

        resliceExtent = [0, self._TextureSize - 1,
                         0, self._TextureSize - 1,
                         0, self._TextureSize - 1]

        resliceSpacing = ((bounds[1] - bounds[0]) / (self._TextureSize),
                          (bounds[3] - bounds[2]) / (self._TextureSize),
                          (bounds[5] - bounds[4]) / (self._TextureSize))

        resliceOrigin = (bounds[0] + resliceSpacing[0] * 0.5,
                         bounds[2] + resliceSpacing[1] * 0.5,
                         bounds[4] + resliceSpacing[2] * 0.5)

        # first shrink the image & antialias
        shrink = [1, 1, 1]
        for i in range(3):
            s = int(abs(resliceSpacing[i] / spacing[i]))
            if s > 1:
                shrink[i] = s

        self._ImagePrefilter2.SetInput(input)
        self._ImagePrefilter2.SetShrinkFactors(map(int, shrink))
        self._ImagePrefilter2.MeanOn()
        self._ImagePrefilter2.ReleaseDataFlagOn()

        # we might need to convert from signed to unsigned here...
        t = input.GetScalarType()
        minval, maxval = input.GetScalarRange()
        if (t != vtk.VTK_UNSIGNED_SHORT) and (t != vtk.VTK_UNSIGNED_CHAR):
            f = vtk.vtkImageShiftScale()
            f.SetInput(self._ImagePrefilter2.GetOutput())
            f.SetShift(-minval)
            f.SetScale(1.0)
            f.SetOutputScalarType(t + 1)
            f.ReleaseDataFlagOn()
            obj = f.GetOutput()
        else:
            obj = self._ImagePrefilter2.GetOutput()

        # need to shift to correct the error in vtkImageShrink3D...
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy((1.0, 0.0, 0.0, 0.5 * (spacing[0] - resliceSpacing[0]),
                         0.0, 1.0, 0.0, 0.5 * (spacing[1] - resliceSpacing[1]),
                         0.0, 0.0, 1.0, 0.5 * (spacing[2] - resliceSpacing[2]),
                         0.0, 0.0, 0.0, 1.0))

        # apply the shift correction, resample to power of two
        # (if vtkImageReslice did antialiasing, there would be no need
        # for the vtkImageShrink3D)
        self._ImageReslice2.SetInput(obj)
        self._ImageReslice2.SetResliceAxes(matrix)
        self._ImageReslice2.SetOutputExtent(resliceExtent)
        self._ImageReslice2.SetOutputOrigin(resliceOrigin)
        self._ImageReslice2.SetOutputSpacing(resliceSpacing)
        self._ImageReslice2.ReleaseDataFlagOff()

        # apply the color table (this is currently not used)
        self._ImageMapToColors.SetInput(self._ImageReslice1.GetOutput())
        self._ImageMapToColors.ReleaseDataFlagOff()

        # convert to structured points before chopping up and sending to
        # the textures (this is currently not used)
        self._ImageToStructuredPoints.SetInput(
            self._ImageMapToColors.GetOutput())
        self._ImageToStructuredPoints.ReleaseDataFlagOff()

        # this is for if we want to warp the volume before renderering
        self._TransformToGrid.SetGridSpacing(
            map(lambda x: 4 * x, resliceSpacing))
        self._TransformToGrid.SetGridOrigin(
            resliceOrigin)
        self._TransformToGrid.SetGridExtent(
            map(lambda x: x / 4, resliceExtent))

        # set clipping cube bounds
        self._ClippingCube.SetROIBounds(bounds)

        # set up implicit volume
        self._ImplicitVolume.SetTransform(
            self._ImageReslice1.GetResliceTransform())
        self._ImplicitVolume.SetVolume(input)
        self._ImplicitVolume.GetVolume().Update()

        # texture-map LOD gets the subsampled volume
        self._ImageReslice1.UpdateWholeExtent()

        self._VolumeTextureMapper1.SetInput(self._ImageReslice1.GetOutput())

        self._ImageReslice2.UpdateWholeExtent()
        self._VolumeTextureMapper2.SetInput(self._ImageReslice2.GetOutput())

        # ray-cast LOD gets the full resolution volume
        self._RayCastReslice.SetInput(input)
        self._RayCastReslice.SetOutputSpacing(map(abs, spacing))
        self._RayCastReslice.ReleaseDataFlagOn()

        # we might need to convert from signed to unsigned here...
        t = input.GetScalarType()
        minval, maxval = input.GetScalarRange()
        if (t != vtk.VTK_UNSIGNED_SHORT) and (t != vtk.VTK_UNSIGNED_CHAR):
            f = vtk.vtkImageShiftScale()
            f.SetInput(self._RayCastReslice.GetOutput())
            f.SetShift(-minval)
            f.SetScale(1.0)
            f.SetOutputScalarType(t + 1)
            f.ReleaseDataFlagOn()
            obj = f.GetOutput()
        else:
            obj = self._RayCastReslice.GetOutput()

        self._VolumeRayCastMapper.SetInput(obj)
        self._Input = input
        self.Modified()

    def GetInput(self):
        return self._Input

    def SetClippingCube(self, cube):
        self._ClippingCube = cube

    def GetClippingCube(self):
        return self._ClippingCube

    # def SetLookupTable(self,table):
    #    # the lookup table associated with the data
    #    self._LookupTable = table
    #    self._ImageMapToColors.SetLookupTable(table)
    #    self.Modified()

    # def GetLookupTable(self):
    #    return self._LookupTable

    def SetColorTransferFunction(self, func):
        self._ColorTransferFunction = func
        self._VolumeProperty.SetColor(func)

    def GetColorTransferFunction(self):
        return self._ColorTransferFunction

    def SetOpacityTransferFunction(self, func):
        self._OpacityTransferFunction = func
        self._VolumeProperty.SetScalarOpacity(func)

    def GetOpacityTransferFunction(self):
        return self._OpacityTransferFunction

    def SetVolumeProperty(self, property):
        self._VolumeProperty = property
        if (property):
            self._ColorTransferFunction = property.GetColor()
            self._OpacityTransferFunction = property.GetScalarOpacity()
        else:
            self._ColorTransferFunction = None
            self._OpacityTransferFunction = None
        self._Volume.SetProperty(property)

    def GetVolumeProperty(self):
        return self._VolumeProperty

#    def SetVolumeBounds(self,*b):
#        if len(b) == 0:
#            b = b[0]
#        self._VolumeBounds = tuple(map(float,b))
#        for renderer in renderers:
#            self.RemoveFromRenderer(renderer)
#        if self._Input:
#            self.SetInput(self._Input)
#        for renderer in renderers:
#            self.AddToRenderer(renderer)

    def GetVolumeBounds(self):
        return self._VolumeBounds

    def HasChangedSince(self, sinceMTime):
        if (ActorFactory.ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        if (self._Input and self._Input.GetMTime() > sinceMTime):
            return 1
        if (self._LookupTable and self._LookupTable.GetMTime() > sinceMTime):
            return 1
        if (self._ColorTransferFunction and
                self._ColorTransferFunction.GetMTime() > sinceMTime):
            return 1
        if (self._OpacityTransferFunction and
                self._OpacityTransferFunction.GetMTime() > sinceMTime):
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

            point1 = picklist[0].position
            point2 = picklist[1].position
            vec = (point2[0] - point1[0],
                   point2[1] - point1[1],
                   point2[2] - point1[2])
            pathlength = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
            if pathlength < 1.0:
                hitVolume = 1
            else:
                hitVolume = 0

            # set up an implicit function that we can query
            vol = self._ImplicitVolume
            if self._OpacityTransferFunction:
                vol.SetOutValue(0.0)
            else:
                table = self._LookupTable
                if table:
                    vol.SetOutValue(self._LookupTable.GetTableRange()[0])
                    _range = table.GetTableRange()
                    maxidx = table.GetNumberOfColors() - 1
                else:
                    return []

            if self._PickThreshold > 0.0 and not hitVolume:
                # cast a ray into the volume from one side

                # get mininum voxel spacing
                spacing = min(map(abs, self._Input.GetSpacing()))

                # get the number of steps required along the length
                N = int(math.ceil(abs(pathlength / spacing)))
                dx, dy, dz = (vec[0] / N, vec[1] / N, vec[2] / N)
                dr = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

                transparency = 1.0
                x0, y0, z0 = point1

                for i in range(N):
                    x = x0 + i * dx
                    y = y0 + i * dy
                    z = z0 + i * dz
                    value = vol.FunctionValue(
                        x + dx / 2, y + dy / 2, z + dz / 2)
                    if self._OpacityTransferFunction:
                        alpha = self._OpacityTransferFunction.GetValue(value)
                    else:
                        idx = int(round((value - _range[0]) /
                                        (_range[1] - _range[0]) * maxidx))
                        if idx < 0:
                            idx = 0
                        elif idx > maxidx:
                            idx = maxidx
                        alpha = table.GetTableValue(idx)[3]
                    transparency = transparency * math.pow(1.0 - alpha, dr)
                    # check if opacity is greater than threshold
                    if (1.0 - transparency) > self._PickThreshold:
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
                    transparency = 1.0
                    for i in range(N):
                        x = x1 - i * dx
                        y = y1 - i * dy
                        z = z1 - i * dz
                        value = vol.FunctionValue(
                            x - dx / 2, y - dy / 2, z - dz / 2)
                        if self._OpacityTransferFunction:
                            alpha = \
                                self._OpacityTransferFunction.GetValue(value)
                        else:
                            idx = int(round((value - _range[0]) /
                                            (_range[1] - _range[0]) * maxidx))
                            if idx < 0:
                                idx = 0
                            elif idx > maxidx:
                                idx = maxidx
                            alpha = table.GetTableValue(idx)[3]
                        transparency = transparency * math.pow(1.0 - alpha, dr)
                        if (1.0 - transparency) > self._PickThreshold:
                            if i != 0:
                                picklist[1].position = (x, y, z)
                                gx, gy, gz = vol.FunctionGradient(x, y, z)
                                picklist[1].normal = (-gx, -gy, -gz)
                            break
                else:
                    picklist = []

        for child in self._Children:
            if child != self._ClippingCube:    # already done it
                picklist = picklist + child.GetPickList(event)

        return picklist

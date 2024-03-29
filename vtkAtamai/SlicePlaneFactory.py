from __future__ import division
from __future__ import print_function
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
    'module_name': '$RCSfile: SlicePlaneFactory.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
SlicePlaneFactory - provides a slice view through a 3D image

  The SlicePlaneFactory class provides a textured slice which cuts
  through an image data set.  This class supports most of the same
  methods as vtkPlaneSource.

  Multiple inputs can be set, each with its own lookup table.
  The opacity of the inputs can be modified in order to provide
  transparency overlay views.

  Also, the ImageTransform for each input specifies a transformation
  to apply to the image before it is texture mapped onto the planes.
  This transformation can be a linear or nonlinear transformation.

Derived From:

  ActorFactory

See Also:

  OrthoPlanesFactory

Initialization:

  SlicePlaneFactory()

Public Methods:

  Specify the image volume:

    SetInputConnection(*imagedata*,*i*=0)   -- set a vtkImageData to slice through

    GetInputConnection(*i*=0)               -- get input *i*

    AddInputConnection(*imagedata*)         -- add an input after the last input

    RemoveInputConnection(*i*=0)            -- remove an input

    GetNumberOfInputs()           -- current number of inputs

    SetVolumeBounds(*xl*,*xh*,*yl*,*yh*,*zl*,*zh*) -- specify the bounds
                      of the data set (if not specified, the bounds of
                      the first Input will be used)

    GetVolumeBounds()      -- get the bounding box

  Change the display of the image:

    SetLookupTable(*table*,*i*=0) -- change the lookup table for image *i*

    GetLookupTable(*i*=0)         -- get the lookup table

    SetOpacity(*alpha*,*i*=0)     -- set the opacity of image *i*

    GetOpacity(*i*=0)             -- get the opacity

    SetVisibility(*yesno*, *i*=0, *renderer*=None) -- change visibility of
                                     image *i* in a specific renderer

    GetVisibility(*i*=0, *renderer*=None) -- get the visibility

    SetImageTransform(*axes*,*i*=0) -- set a world coords -> image coords
                                     transformation to be used when displaying
                                     the image

    GetImageTransform(*i*=0)        -- get the image transformation

    SetClippingPlanes(*planes*,*i*=0) -- clip the image before displaying it

    GetClippingPlanes(*i*=0)        -- get the image clipping planes

  Get a copy of the image slice:

    GetOutput(*i*=0,*colormap*=0,*pad*=0) -- *colormap* specifies whether to
                                     get the raw data or colormapped data, and
                                     *pad* specifies whether to pad the data
                                     to a power of two e.g. for texture mapping

  Interpolation:

    SetSliceInterpolate(*boolean*) -- interpolate while resampling (default on)

    SetTextureInterpolate(*boolean*) -- interpolate when texture mapping
                                        (default on)

  Use a canonical slice orientation:

    SetPlaneOrientationToYZ() -- sagittal

    SetPlaneOrientationToZX() -- coronal

    SetPlaneOrientationToXY() -- axial

  Set an arbitrary slice orientation and extent:

    SetOrigin(*x,*y,*z*) -- as per vtkPlaneSource

    SetPoint1(*x*,*y,*z*) -- as per vtkPlaneSource

    SetPoint2(*x*,*y*,*z*) -- as per vtkPlaneSource

  Adjust the slice plane:

    Push(*distance*)        -- push by specified distance along normal

    SetSlicePosition(*pos*) -- set position along normal direction

    SetSliceIndex(*index*)  -- set slice index (i.e. slice number)

    SetCenter(*x*,*y*,*z*)  -- move the slice so that (*x*,*y*,*z*) is centered

    SetNormal(*nx*,*ny*,*nz*) -- rotate the plane by adjusting its normal
                            (the rotation is easier to do by using e.g.
                            GetTransform().Rotate()

  Utility functions:

    IntersectWithViewRay(x,y,render) -- return the x,y,z world-coords for
                             the x,y display-coords of the renderer

    IntersectWithLine(p1,p2) -- return the x,y,z world-coords where the
                             line defined by endpoints p1,p2 intersects
                             the plane

  Get the implicit function for the slice:

    GetPlaneEquation() -- a vtkPlane for e.g. slicing polydata

"""

#======================================
from . import ActorFactory
from . import OutlineFactory
import math
import vtk
import logging

logger = logging.getLogger(__name__)
#======================================


class SlicePlaneFactory(ActorFactory.ActorFactory):

    def __init__(self):

        ActorFactory.ActorFactory.__init__(self)

        # generate the pipeline components

        # the following are required for each input
        self._Inputs = {}
        self._ImageReslicers = {}
        self._ResliceTransforms = {}
        self._ImageTransforms = {}
        self._TransformGrids = {}
        self._TextureCoords = {}
        self._LookupTables = {}
        self._Properties = {}
        self._ImagePreClips = {}
        self._ImagePostClips = {}
        self._ImageMapToColors = {}
        self._ClippingPlanes = {}

        self._PushColor = [1.0, 1.0, 0.0]
        self._RotateColor = [1.0, 0.0, 1.0]
        self._SpinColor = [0.0, 1.0, 1.0]
        self._DefaultOutlineColor = [1.0, 0.0, 1.0]

        # thankfully, we don't need more than one of these
        self._Plane = vtk.vtkPlaneSource()
        self._Plane.SetXResolution(1)
        self._Plane.SetYResolution(1)

        self._ResliceAxes = vtk.vtkMatrix4x4()

        self._PlaneEquation = None

        self._PlaneOrientation = None  # internal storage of type of plane

        self._SliceInterpolate = 1
        self._TextureInterpolate = 1

        self._DisablePushAction = 0
        self._RestrictPlaneToVolume = 0
        self._VolumeBounds = None
        self.__UserAction = None

        self.__OutlineColor = (0.0, 1.0, 0.0)
        self._bOutlineIsVisible = False

        outline = OutlineFactory.OutlineFactory()
        outline.SetInputConnection(self._Plane.GetOutputPort())
        outline.SetColor(self.__OutlineColor)
        self.AddChild(outline)

        self.BindEvent("<ButtonPress>", self.DoStartAction)
        self.BindEvent("<Motion>", self.DoPush)

    def SetDefaultOutlineColor(self, color):
        self._DefaultOutlineColor = color
        self.SetOutlineColor(color)

    def SetUserAction(self, action):
        self.__UserAction = action

    def tearDown(self):

        ActorFactory.ActorFactory.tearDown(self)

        for i in list(self._Inputs.keys()):
            self.RemoveInputConnection(i)

        del(self._Plane)
        del(self._ResliceAxes)

    def GetOutlineVisibility(self):
        return self._bOutlineIsVisible

    def SetOutline(self, yesno):

        yesno = bool(yesno)

        # abort early if this is a NoOp
        if self._bOutlineIsVisible == yesno:
            return

        self._bOutlineIsVisible = yesno

        outline = self.GetOutline()

        if outline:
            outline.SetVisibility(yesno)

    def GetOutline(self):
        try:
            return self.GetChild("Outline")
        except:
            return None

    def OutlineOn(self):
        self.SetOutline(1)

    def OutlineOff(self):
        self.SetOutline(0)

    def SetOutlineColor(self, color):

        self.__OutlineColor = color

        try:
            outline = self.GetChild("Outline")
            outline.SetColor(color)
        except:
            pass

    def HasChangedSince(self, sinceMTime):

        if (ActorFactory.ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        for name in self._Inputs:
            input = self._Inputs[name]

            # VTK-6
            # if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            #    print 'SlicePlaneFactory:HasChangedSince - fix UpdateInformation()!'
            #    #input.UpdateInformation()  # TODO: VTK-6 figure out what to do here
            # else:
            # input.UpdateInformation()  # TODO: VTK-6 figure out what to do
            # here

            if (input.GetMTime() > sinceMTime):
                if (self._PlaneOrientation != None):
                    pass
                else:
                    self._UpdateNormal()
                    self._UpdateOrigin()
                return 1
        for name in self._LookupTables:
            table = self._LookupTables[name]
            if (table and table.GetMTime() > sinceMTime):
                return 1
        return 0

    def GetPlane(self):
        return self._Plane

    # Get the output image
    def GetOutputPort(self, name=0, color=0, pad=0):

        if self.GetInputConnection(name) is None:
            return None

        if color:
            output = self._ImageMapToColors[name].GetOutputPort()
        else:
            output = self._ImageReslicers[name].GetOutputPort()

        if pad:  # don't clip off the power-of-two padding
            return output

        if (color):
            if self._ImagePostClips[name] is None:
                self._ImagePostClips[name] = vtk.vtkImageClip()
            clip = self._ImagePostClips[name]
        else:
            if self._ImagePreClips[name] is None:
                self._ImagePreClips[name] = vtk.vtkImageClip()
            clip = self._ImagePreClips[name]

        # VTK-6
        clip.SetInputConnection(output)

        # need all this garbage to determine what part of ImageReslice's
        # output extent is being mapped onto the plane
        planeOrigin = self._Plane.GetOrigin()
        planePoint1 = self._Plane.GetPoint1()
        planePoint2 = self._Plane.GetPoint2()

        planeAxis1 = [planePoint1[0] - planeOrigin[0],
                      planePoint1[1] - planeOrigin[1],
                      planePoint1[2] - planeOrigin[2]]

        planeAxis2 = [planePoint2[0] - planeOrigin[0],
                      planePoint2[1] - planeOrigin[1],
                      planePoint2[2] - planeOrigin[2]]

        # the x,y dimensions of the plane
        planeSizeX = math.sqrt(planeAxis1[0] * planeAxis1[0] +
                               planeAxis1[1] * planeAxis1[1] +
                               planeAxis1[2] * planeAxis1[2])
        planeSizeY = math.sqrt(planeAxis2[0] * planeAxis2[0] +
                               planeAxis2[1] * planeAxis2[1] +
                               planeAxis2[2] * planeAxis2[2])

        # the x,y spacing of the pixels
        spacingX, spacingY, spacingZ = self._ImageReslicers[
            name].GetOutputSpacing()

        # calculate the extent
        extentX = int(math.floor(old_div(planeSizeX, spacingX) + 0.5))
        extentY = int(math.floor(old_div(planeSizeY, spacingY) + 0.5))

        clip.SetOutputWholeExtent(0, extentX - 1, 0, extentY - 1, 0, 0)

        return clip.GetOutputPort()

    def GetPlaneEquation(self):
        # return the vtkPlane which describes the plane
        if not self._PlaneEquation:
            self._PlaneEquation = vtk.vtkPlane()
            self._PlaneEquation.SetNormal(self._Plane.GetNormal())
            self._PlaneEquation.SetOrigin(self._Plane.GetOrigin())
        return self._PlaneEquation

    def GetNumberOfInputs(self):
        return len(self._Inputs)

    def OnExecuteInformation(self, colors, event="ExecuteInformationEvent"):

        image = colors.GetInput()

        # VTK-6
        # if vtk.vtkVersion().GetVTKMajorVersion() > 5:
        #    print 'SlicePlaneFactory:OnExecuteInformation - fix UpdateInformation()!'
        #    #image.UpdateInformation()  # TODO: VTK-6 figure out what to do here
        # else:
        # image.UpdateInformation()  # TODO: VTK-6 figure out what to do here

        # 2017-05-18: colors must be updated here otherwise we handle e.g. RGB pngs incorrectly
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            if colors.GetLookupTable() is None:
                colors.SetLookupTable(vtk.vtkLookupTable())  # provide a dummy table
            colors.Update()

        for name in self._ImageMapToColors:
            if colors == self._ImageMapToColors[name]:
                break

        if image.GetNumberOfScalarComponents() == 3:
            colors.SetOutputFormatToRGB()
            if self._LookupTables[name] and image.GetScalarType() != 3:
                colors.SetLookupTable(self._LookupTables[name])
            else:
                colors.SetLookupTable(None)
        elif image.GetNumberOfScalarComponents() == 4:
            colors.SetOutputFormatToRGBA()
            if self._LookupTables[name] and image.GetScalarType() != 3:
                colors.SetLookupTable(self._LookupTables[name])
            else:
                colors.SetLookupTable(None)
        else:
            colors.SetLookupTable(self._LookupTables[name])
            # first image is RGB (opaque), others are RGBA (translucent)
            if name == 0:
                colors.SetOutputFormatToRGB()
            else:
                colors.SetOutputFormatToRGBA()

    def AddInputData(self, image_data, name=None):

        alg = vtk.vtkTrivialProducer()
        alg.SetOutput(image_data)
        self.AddInputConnection(alg.GetOutputPort(), name=name)

    def AddInputConnection(self, alg, name=None, table=None):

        # this change permits sliceplanefactory to be named - fallback is to
        # use a numerical index
        if name is None:
            name = len(self._Inputs)

        while name in self._Inputs:
            name += 1

        resliceTransform = vtk.vtkTransform()
        resliceTransform.SetInput(self._Transform)
        axesTransform = vtk.vtkMatrixToLinearTransform()
        axesTransform.SetInput(self._ResliceAxes)
        resliceTransform.Concatenate(axesTransform)

        # JDG: changed reslice from a basic image reslice object
        # to one that has MIP capabilities
        reslice = vtk.vtkImageSlabReslice()
        reslice.SetSlabThickness(0.0)

        reslice.SetResliceTransform(resliceTransform)
        if self._SliceInterpolate:
            reslice.SetInterpolationModeToLinear()
        else:
            reslice.SetInterpolationModeToNearestNeighbor()
        reslice.SetOptimization(2)

        reslice.SetInputConnection(alg)

        colors = vtk.vtkImageMapToColors()
        colors.AddObserver('OnExecuteInformation', self.OnExecuteInformation)

        colors.SetInputConnection(reslice.GetOutputPort())
        try:
            colors.PassAlphaToOutputOn()
        except:
            pass

        coords = vtk.vtkTextureMapToPlane()
        coords.SetInputConnection(self._Plane.GetOutputPort())
        coords.AutomaticPlaneGenerationOff()

        property = vtk.vtkProperty()

        self._Inputs[name] = alg
        self._ImageReslicers[name] = reslice
        self._ResliceTransforms[name] = resliceTransform
        self._ImageMapToColors[name] = colors
        self._TextureCoords[name] = coords
        self._Properties[name] = property

        self.SetLookupTable(table, name=name)

        self._ImagePreClips[name] = None
        self._ImagePostClips[name] = None
        self._ImageTransforms[name] = None
        self._TransformGrids[name] = None
        self._ClippingPlanes[name] = None

        actors = self._ActorDict
        for renderer in self._Renderers:
            actor = self._NewActor(name)
            actor.SetPickable(name == 0)
            actors[renderer][name] = actor
            renderer.AddActor(actor)

        ## JDG self.OnExecuteInformation(colors)
        self._UpdateNormal()
        self._UpdateOrigin()
        self.Modified()

        return name

    def RemoveInputConnection(self, name=0):

        actors = self._ActorDict
        for renderer in self._Renderers:

            temp = actors[renderer]
            pickable = temp[name].GetPickable()
            renderer.RemoveActor(temp[name])
            del temp[name]

            if pickable:
                # find another suitable slice
                for n in temp:
                    if isinstance(n, int):
                        temp[n].SetPickable(1)
                        break

        del self._Inputs[name]
        del self._ImageReslicers[name]
        del self._ResliceTransforms[name]
        del self._ImageMapToColors[name]
        del self._TextureCoords[name]
        del self._Properties[name]
        del self._LookupTables[name]
        del self._ImagePreClips[name]
        del self._ImagePostClips[name]
        del self._ImageTransforms[name]
        del self._TransformGrids[name]
        del self._ClippingPlanes[name]

        self.Modified()

    def SetInputData(self, image_data, name=0, table=None):

        alg = vtk.vtkTrivialProducer()
        alg.SetOutput(image_data)
        self.SetInputConnection(alg.GetOutputPort(), name=name, table=table)

    def SetInputConnection(self, alg, name=0, table=None):

        if name not in self._Inputs:
            self.AddInputConnection(alg, name, table=table)
            return

        self._Inputs[name] = alg
        self._ImageReslicers[name].SetInputConnection(alg)
        self.SetLookupTable(name, table)

        # self.OnExecuteInformation(self._ImageMapToColors[name])

        self.UpdatePlaneExtent()

        self._UpdateNormal()
        self._UpdateOrigin()
        self.Modified()

    def GetInputConnection(self, name=0):
        """Returns the input port associated with this slice plane"""
        if name in self._Inputs:
            return self._Inputs[name]
        else:
            return None

    def SetClippingPlanes(self, clippingPlanes, name=0):

        self._ClippingPlanes[name] = clippingPlanes
        actors = self.GetActorDict()
        for renderer in self._Renderers:
            actor = actors[renderer][name]
            actor.GetMapper().SetClippingPlanes(clippingPlanes)
        self.Modified()

    def GetClippingPlanes(self, name=0):
        return self._ClippingPlanes[name]

    def SetRestrictPlaneToVolume(self, yesno):
        self._RestrictPlaneToVolume = yesno
        self.Modified()

    def GetRestrictPlaneToVolume(self):
        return self._RestrictPlaneToVolume

    def RestrictPlaneToVolumeOn(self):
        self._RestrictPlaneToVolume = 1

    def RestrictPlaneToVolumeOff(self):
        self._RestrictPlaneToVolume = 0

    def SetSliceInterpolate(self, val):
        self._SliceInterpolate = val
        if val:
            for name in self._ImageReslicers:
                reslice = self._ImageReslicers[name]
                reslice.SetInterpolationModeToLinear()
        else:
            for name in self._ImageReslicers:
                reslice = self._ImageReslicers[name]
                reslice.SetInterpolationModeToNearestNeighbor()
        self.Modified()

    def GetSliceInterpolate(self):
        return self._SliceInterpolate

    def SliceInterpolateOn(self):
        self.SetSliceInterpolate(1)

    def SliceInterpolateOff(self):
        self.SetSliceInterpolate(0)

    def SetTextureInterpolate(self, val):
        self._TextureInterpolate = val
        for renderer in self._Renderers:
            for name in self._ActorDict[renderer]:
                actor = self._ActorDict[renderer][name]
                texture = actor.GetTexture()
                if texture:
                    texture.SetInterpolate(val)
        self.Modified()

    def GetTextureInterpolate(self):
        return self._TextureInterpolate

    def TextureInterpolateOn(self):
        self.SetTextureInterpolate(1)

    def TextureInterpolateOff(self):
        self.SetTextureInterpolate(0)

    def GetImageReslice(self, name=0):

        # get the associated reslicer
        return self._ImageReslicers[name]

    def SetLookupTable(self, table, name=0):

        # the lookup table associated with the image data
        self._LookupTables[name] = table
        if name in self._ImageMapToColors:
            self.OnExecuteInformation(self._ImageMapToColors[name])
        for renderer in self._Renderers:
            actors = self._ActorDict[renderer]
            if name in actors:
                actor = actors[name]
                if actor.GetTexture():
                    actor.GetTexture().SetLookupTable(table)
        self.Modified()

    def GetLookupTable(self, name=0):
        return self._LookupTables[name]

    def SetOpacity(self, alpha, name=0):
        self._Properties[name].SetOpacity(alpha)
        self.Modified()

    def GetOpacity(self, name=0):
        return self._Properties[name].GetOpacity()

    def SetVisibility(self, yesno, name=0, renderer=None):
        # Set the visibility of input `name` on renderer.
        # see _MakeActors()

        if renderer is None:
            for ren in self._Renderers:
                if name in self._ActorDict[ren]:
                    self._ActorDict[ren][name].SetVisibility(yesno)
        else:
            if name in self._ActorDict[renderer]:
                self._ActorDict[renderer][name].SetVisibility(yesno)

        self.Modified()

    def GetVisibility(self, name=0, renderer=None):
        if renderer is None:
            return self._ActorDict[self._Renderers[0]][name].GetVisibility()
        else:
            return self._ActorDict[renderer][name].GetVisibility()

    def SetAmbient(self, ambient, name=0):
        self._Properties[name].SetAmbient(ambient)
        self.Modified()

    def GetAmbient(self, name=0):
        return self._Properties[name].GetAmbient()

    def SetImageTransform(self, trans, name=0):

        if (trans is self._ImageTransforms.get(name, None)):
            return

        # the TransformGrid is used to accelerate nonlinear transforms
        self._TransformGrids[name] = None

        # a linear transform is much more efficient than a nonlinear
        # transform, so we set our concatenated transform type according
        # to the image transform type
        if trans is None:
            transform = vtk.vtkTransform()
        elif (trans.IsA('vtkLinearTransform')):
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            transform.Concatenate(trans.GetLinearInverse())
            transform.PreMultiply()
        elif (trans.IsA('vtkHomogenousTransform')):
            transform = vtk.vtkPerspectiveTransform()
            transform.PostMultiply()
            transform.Concatenate(trans.GetHomogenousInverse())
            transform.PreMultiply()
        else:  # nonlinear warp transforms
            transform = vtk.vtkGeneralTransform()
            transform.PostMultiply()
            transform.Concatenate(trans.GetInverse())
            transform.PreMultiply()
            # accelerate by sampling a grid, then interpolating
            tgrid = vtk.vtkTransformToGrid()
            tgrid.SetInput(transform)
            gridt = vtk.vtkGridTransform()
            gridt.SetInterpolationModeToCubic()
            gridt.SetDisplacementGrid(tgrid.GetOutput())
            self._TransformGrids[name] = tgrid

        transform.SetInput(self._Transform)
        axesTransform = vtk.vtkMatrixToLinearTransform()
        axesTransform.SetInput(self._ResliceAxes)
        transform.Concatenate(axesTransform)
        self._ResliceTransforms[name] = transform
        if self._TransformGrids[name]:
            self._ImageReslicers[name].SetResliceTransform(gridt)
        else:
            self._ImageReslicers[name].SetResliceTransform(transform)
        self._ImageTransforms[name] = trans

        self._UpdateOrigin()

        self.Modified()

    def GetImageTransform(self, name=0):
        return self._ImageTransforms.get(name, None)

    def GeneratePlaneFromPolyData(self):
        # generate a plane which is aligned with the polydata --
        # you must call this method each time the polydata is changed.
        # -- this method is yet to be implemented
        pass

    def SetPlaneOrientationToXY(self):
        self.SetPlaneOrientation(0)

    def SetPlaneOrientationToYZ(self):
        self.SetPlaneOrientation(1)

    def SetPlaneOrientationToZX(self):
        self.SetPlaneOrientation(2)

    def SetPlaneOrientation(self, i):
        # generate a XY plane if i = 0
        # or a YZ plane if i = 1
        # or a ZX plane if i = 2

        # this method must be called _after_ SetInput

        self._PlaneOrientation = i
        self.UpdatePlaneExtent()

        self._UpdateNormal()
        self._UpdateOrigin()
        self._Plane.Update()

        self.Modified()

    def UpdatePlaneExtent(self):

        if self._PlaneOrientation is None:
            return

        i = self._PlaneOrientation

        image = self._ImageReslicers[0].GetInput()
        extent = image.GetExtent()
        origin = image.GetOrigin()
        spacing = image.GetSpacing()

        xbounds = [origin[0] + spacing[0] * (extent[0] - 0.5),
                   origin[0] + spacing[0] * (extent[1] + 0.5)]
        ybounds = [origin[1] + spacing[1] * (extent[2] - 0.5),
                   origin[1] + spacing[1] * (extent[3] + 0.5)]
        zbounds = [origin[2] + spacing[2] * (extent[4] - 0.5),
                   origin[2] + spacing[2] * (extent[5] + 0.5)]

        if spacing[0] < 0:
            xbounds.reverse()
        if spacing[1] < 0:
            ybounds.reverse()
        if spacing[2] < 0:
            zbounds.reverse()

        # limit volume bounds to voxel centers at the boundaries
        # to avoid blank images at the boundries
        bounds = [origin[0] + spacing[0] * extent[0],
                  origin[0] + spacing[0] * extent[1],
                  origin[1] + spacing[1] * extent[2],
                  origin[1] + spacing[1] * extent[3],
                  origin[2] + spacing[2] * extent[4],
                  origin[2] + spacing[2] * extent[5]]

        self._VolumeBounds = [min(bounds[0:2]), max(bounds[0:2]),
                              min(bounds[2:4]), max(bounds[2:4]),
                              min(bounds[4:6]), max(bounds[4:6])]

        self._Plane.SetXResolution(1)
        self._Plane.SetYResolution(1)

        if i == 0 or i == 'xy' or i == 'XY':
            self._Plane.SetOrigin(xbounds[0], ybounds[0], 0)
            self._Plane.SetPoint1(xbounds[1], ybounds[0], 0)
            self._Plane.SetPoint2(xbounds[0], ybounds[1], 0)
        elif i == 1 or i == 'yz' or i == 'YZ':
            self._Plane.SetOrigin(0, ybounds[0], zbounds[0])
            self._Plane.SetPoint1(0, ybounds[1], zbounds[0])
            self._Plane.SetPoint2(0, ybounds[0], zbounds[1])
        elif i == 2 or i == 'zx' or i == 'ZX':
            self._Plane.SetOrigin(xbounds[0], 0, zbounds[0])
            self._Plane.SetPoint1(xbounds[1], 0, zbounds[0])
            self._Plane.SetPoint2(xbounds[0], 0, zbounds[1])
        else:
            raise ValueError("unrecognized orientation")

    def SetSlicePosition(self, position):
        # set the position of the slice along its normal
        plane = self._Plane
        amount = 0  # in case we fall through the elif cascade
        planeOriginX, planeOriginY, planeOriginZ = plane.GetOrigin()
        planeNormalX, planeNormalY, planeNormalZ = plane.GetNormal()
        if (planeNormalX == 0 and planeNormalY == 0):
            amount = (position - planeOriginZ) * planeNormalZ
        elif (planeNormalY == 0 and planeNormalZ == 0):
            amount = (position - planeOriginX) * planeNormalX
        elif (planeNormalX == 0 and planeNormalZ == 0):
            amount = (position - planeOriginY) * planeNormalY
        else:
            logger.error(
                "SetSlicePosition() only works for xy, xz, or yz planes")
        self.Push(amount)

    def GetSlicePosition(self):
        plane = self._Plane
        planeOriginX, planeOriginY, planeOriginZ = plane.GetOrigin()
        planeNormalX, planeNormalY, planeNormalZ = plane.GetNormal()

        if planeNormalX == 0 and planeNormalY == 0:
            return planeOriginZ
        elif planeNormalY == 0 and planeNormalZ == 0:
            return planeOriginX
        elif planeNormalX == 0 and planeNormalZ == 0:
            return planeOriginY
        else:
            logger.error(
                "GetSlicePosition() only works for xy, xz, or yz planes")

    def SetSliceIndex(self, index):

        # set the slice index in terms of the data extent
        image = self._ImageReslicers[0].GetInput()

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            print('SlicePlaneFactory:SetSliceIndex - fix UpdateInformation()!')
            # image.UpdateInformation()  # TODO: VTK-6 figure out what to do
            # here
        else:
            image.UpdateInformation()  # TODO: VTK-6 figure out what to do here

        originX, originY, originZ = image.GetOrigin()
        spacingX, spacingY, spacingZ = image.GetSpacing()
        del image

        planeOriginX, planeOriginY, planeOriginZ = self._Plane.GetOrigin()
        planeNormalX, planeNormalY, planeNormalZ = self._Plane.GetNormal()

        amount = 0
        if (planeNormalX == 0 and planeNormalY == 0):
            amount = (originZ + index * spacingZ - planeOriginZ) * planeNormalZ
        elif (planeNormalY == 0 and planeNormalZ == 0):
            amount = (originX + index * spacingX - planeOriginX) * planeNormalX
        elif (planeNormalX == 0 and planeNormalZ == 0):
            amount = (originY + index * spacingY - planeOriginY) * planeNormalY
        else:
            logger.error(
                "SetSliceIndex() only works for xy, xz, or yz planes")

        self.Push(amount)

    def GetSliceIndex(self):
        plane = self._Plane

        if len(self._ImageReslicers) == 0:
            return -1

        image = self._ImageReslicers[0].GetInput()

        # VTK-6
        # if vtk.vtkVersion().GetVTKMajorVersion() > 5:
        #    print 'SlicePlaneFactory:GetSliceIndex - fix UpdateInformation()!'
        #    #image.UpdateInformation()  # TODO: VTK-6 figure out what to do here
        # else:
        # image.UpdateInformation()  # TODO: VTK-6 figure out what to do here

        planeOriginX, planeOriginY, planeOriginZ = plane.GetOrigin()
        planeNormalX, planeNormalY, planeNormalZ = plane.GetNormal()
        originX, originY, originZ = image.GetOrigin()
        spacingX, spacingY, spacingZ = image.GetSpacing()
        del image

        if planeNormalX == 0 and planeNormalY == 0:
            return old_div((planeOriginZ - originZ), spacingZ)
        elif planeNormalY == 0 and planeNormalZ == 0:
            return old_div((planeOriginX - originX), spacingX)
        elif planeNormalX == 0 and planeNormalZ == 0:
            return old_div((planeOriginY - originY), spacingY)
        else:
            logger.error(
                "GetSliceIndex() only works for xy, xz, or yz planes")

        plane.SetOrigin(planeOriginX, planeOriginY, planeOriginZ)
        self._UpdateOrigin()

    def Push(self, distance):

        # just like vtkPlane::Push()
        o1 = self.GetTransformedCenter()
        self._Plane.Push(distance)
        self._UpdateOrigin()
        o2 = self.GetTransformedCenter()
        n = self.GetTransformedNormal()
        self.Modified()

        # return the actual amount pushed, in case we hit bounds
        return (o2[0] - o1[0]) * n[0] + (o2[1] - o1[1]) * n[1] + (o2[2] - o1[2]) * n[2]

    def SetNormal(self, *a):
        # set the normal of the slice plane
        if len(a) == 1:
            a = tuple(a[0])
        self._Plane.SetNormal(a)
        self._UpdateNormal()
        # plane output doesn't seem to get updated automatically in VTK6
        self._Plane.Update()
        self.Modified()

    def GetNormal(self):
        return self._Plane.GetNormal()

    def GetTransformedNormal(self):
        return self._Transform.TransformNormal(self.GetNormal())

    def GetVector1(self):
        # get the 'view right' vector for the plane
        o = self._Plane.GetOrigin()
        p1 = self._Plane.GetPoint1()
        vec = (p1[0] - o[0], p1[1] - o[1], p1[2] - o[2])
        norm = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
        return (old_div(vec[0], norm), old_div(vec[1], norm), old_div(vec[2], norm))

    def GetTransformedVector1(self):
        return self._Transform.TransformVector(self.GetVector1())

    def GetVector2(self):
        # get the 'view up' vector for the plane
        o = self._Plane.GetOrigin()
        p2 = self._Plane.GetPoint2()
        vec = (p2[0] - o[0], p2[1] - o[1], p2[2] - o[2])
        norm = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
        return old_div(vec[0], norm), old_div(vec[1], norm), old_div(vec[2], norm)

    def GetTransformedVector2(self):
        return self._Transform.TransformVector(self.GetVector2())

    def GetVector(self):
        # for backward compatibility
        return self.GetVector2()

    def GetTransformedVector(self):
        # for backward compatibility
        return self.GetTransformedVector2()

    def GetSize1(self):
        # length of plane axis 1
        o = self._Plane.GetOrigin()
        p1 = self._Plane.GetPoint1()
        vec = (p1[0] - o[0], p1[1] - o[1], p1[2] - o[2])
        return math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)

    def GetSize2(self):
        # length of plane axis 2
        o = self._Plane.GetOrigin()
        p2 = self._Plane.GetPoint2()
        vec = (p2[0] - o[0], p2[1] - o[1], p2[2] - o[2])
        return math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)

    def SetOrigin(self, *a):
        # set the origin of the slice plane
        import pdb
        pdb.set_trace()
        if len(a) == 1:
            a = tuple(a[0])
        self._Plane.SetOrigin(a)
        self._UpdateOrigin()
        # plane output doesn't seem to get updated automatically in VTK6
        self._Plane.Update()
        self.Modified()

    def GetOrigin(self):
        return self._Plane.GetOrigin()

    def SetPoint1(self, *a):
        # set the normal of the slice plane
        import pdb
        pdb.set_trace()
        if len(a) == 1:
            a = tuple(a[0])
        self._Plane.SetPoint1(a)
        self._UpdateNormal()
        # plane output doesn't seem to get updated automatically in VTK6
        self._Plane.Update()
        self.Modified()

    def GetPoint1(self):
        return self._Plane.GetPoint1()

    def SetPoint2(self, *a):
        """set the normal of the slice plane"""
        import pdb
        pdb.set_trace()
        if len(a) == 1:
            a = tuple(a[0])
        self._Plane.SetPoint2(a)
        self._UpdateNormal()
        self._Plane.Update()
        self.Modified()

    def GetPoint2(self):
        return self._Plane.GetPoint2()

    def SetCenter(self, *a):
        # set the normal of the slice plane
        import pdb
        pdb.set_trace()
        if len(a) == 1:
            a = tuple(a[0])
        self._Plane.SetCenter(a)
        self._UpdateOrigin()
        # plane output doesn't seem to get updated automatically in VTK6
        self._Plane.Update()
        self.Modified()

    def GetCenter(self):
        return self._Plane.GetCenter()

    def GetTransformedCenter(self):
        return self._Transform.TransformPoint(self.GetCenter())

    def GetPickList(self, event):
        # get a list of PickInformation objects, one for each picked actor
        picklist = []

        for name in self._ActorDict[event.renderer]:
            actor = self._ActorDict[event.renderer][name]
            i = event.picker.GetProp3Ds().IsItemPresent(actor)

            if (i != 0):
                o = self._Plane.GetOrigin()
                p2 = self._Plane.GetPoint2()
                vec = (p2[0] - o[0], p2[1] - o[1], p2[2] - o[2])

                info = ActorFactory.PickInformation()
                info.actor = actor
                info.position = event.picker.GetPickedPositions().GetPoint(
                    i - 1)
                info.normal = \
                    self._Transform.TransformNormal(self._Plane.GetNormal())
                info.vector = self._Transform.TransformVector(vec)

                picklist.append(info)

        for child in self._Children:
            picklist = picklist + child.GetPickList(event)

        return picklist

    def IntersectWithViewRay(self, x, y, renderer):
        # return the intersection of the view ray from
        #  display coordinates x,y

        # get the mouse delta in world coordinates
        renderer.SetDisplayPoint(x, y, 0.25)
        renderer.DisplayToWorld()
        lx1, ly1, lz1, w1 = renderer.GetWorldPoint()

        renderer.SetDisplayPoint(x, y, 0.75)
        renderer.DisplayToWorld()
        lx2, ly2, lz2, w2 = renderer.GetWorldPoint()

        return self.IntersectWithLine((old_div(lx1, w1), old_div(ly1, w1), old_div(lz1, w1)),
                                      (old_div(lx2, w2), old_div(ly2, w2), old_div(lz2, w2)))

    def IntersectWithLine(self, p1, p2):
        # return the intersection of the line with endpoints p1,p2 with plane

        # get plane normal and center
        nx, ny, nz = self.GetTransformedNormal()
        cx, cy, cz = self.GetTransformedCenter()

        # find line vector
        lx = p2[0] - p1[0]
        ly = p2[1] - p1[1]
        lz = p2[2] - p1[2]

        # dot the normal with the vector
        dotprod = nx * lx + ny * ly + nz * lz

        # divide-by-zero exception will be thrown in there is no intersection

        t = old_div((nx * (cx - p1[0]) + ny * (cy - p1[1]) + nz * (cz - p1[2])),   \
            dotprod)

        return (p1[0] + t * lx, p1[1] + t * ly, p1[2] + t * lz)

    def _UpdateOrigin(self):
        # a protected method, called when the slice plane moves along
        # its normal

        # restrict plane to bounds of image
        if (self._RestrictPlaneToVolume):
            producer = self.GetInputConnection().GetProducer()
            producer.UpdateInformation()
            image = producer.GetOutputDataObject(0)
            spacing = image.GetSpacing()
            if self._VolumeBounds:
                bounds = self._VolumeBounds
            else:

                origin = image.GetOrigin()
                extent = image.GetExtent()
                # UpdateInformation don't give us updated bounds, so we
                # calculate it here
                bounds = [
                    origin[0] + spacing[0] * extent[
                        0], origin[0] + spacing[0] * extent[1],
                    origin[1] + spacing[1] * extent[
                        2], origin[1] + spacing[1] * extent[3],
                    origin[2] + spacing[2] * extent[4], origin[2] + spacing[2] * extent[5]]
                bounds = [min(bounds[0:2]), max(bounds[0:2]),
                          min(bounds[2:4]), max(bounds[2:4]),
                          min(bounds[4:6]), max(bounds[4:6])]

            # avoid blank images at the up limit boundaries
            for i in range(3):
                if bounds[2 * i] < bounds[2 * i + 1]:
                    bounds[2 * i] = bounds[2 * i] + spacing[i] * 0.000001
                    bounds[2 * i + 1] = bounds[2 * i + 1] - \
                        spacing[i] * 0.000001

            abs_normal = list(map(abs, self._Plane.GetNormal()))
            center = list(self._Plane.GetCenter())
            i = abs_normal.index(max(abs_normal))
            if center[i] > bounds[2 * i + 1]:
                center[i] = bounds[2 * i + 1]
                self._Plane.SetCenter(center[0], center[1], center[2])
                # plane output doesn't seem to get updated automatically in
                # VTK6
                self._Plane.Update()
            elif center[i] < bounds[2 * i]:
                center[i] = bounds[2 * i]
                self._Plane.SetCenter(center[0], center[1], center[2])
                # plane output doesn't seem to get updated automatically in
                # VTK6
                self._Plane.Update()

        if self._PlaneEquation:
            self._PlaneEquation.SetOrigin(self._Plane.GetOrigin())

        planeOrigin = self._Plane.GetOrigin()

        matrix = self._ResliceAxes
        matrix.SetElement(0, 3, 0)
        matrix.SetElement(1, 3, 0)
        matrix.SetElement(2, 3, 0)

        # transpose is an exact way to invert a pure rotation matrix
        matrix.Transpose()
        originX, originY, originZ, w = \
            matrix.MultiplyPoint(planeOrigin + (1.0,))

        matrix.Transpose()
        newOriginX, newOriginY, newOriginZ, w = \
            matrix.MultiplyPoint((0.0, 0.0, originZ, 1.0))

        matrix.SetElement(0, 3, newOriginX)
        matrix.SetElement(1, 3, newOriginY)
        matrix.SetElement(2, 3, newOriginZ)

        for name in self._ImageReslicers:
            reslice = self._ImageReslicers[name]
            spacingX, spacingY, spacingZ = reslice.GetOutputSpacing()
            reslice.SetOutputOrigin(0.5 * spacingX + originX,
                                    0.5 * spacingY + originY,
                                    0.0)

            # set up a transform grid for nonlinear transform acceleration
            if self._TransformGrids[name]:
                self._TransformGrids[name].SetGridOrigin(
                    reslice.GetOutputOrigin())
                self._TransformGrids[name].SetGridSpacing(
                    [4 * x for x in reslice.GetOutputSpacing()])
                self._TransformGrids[name].SetGridExtent(
                    [old_div(x, 4) for x in reslice.GetOutputExtent()])

        ## JDG self.Modified()

    def _UpdateNormal(self):

        # a private method, called when a property of the slice plane changes
        if self._PlaneEquation:
            self._PlaneEquation.SetNormal(self._Plane.GetNormal())
            self._PlaneEquation.SetOrigin(self._Plane.GetOrigin())

        planeOrigin = self._Plane.GetOrigin()
        planePoint1 = self._Plane.GetPoint1()
        planePoint2 = self._Plane.GetPoint2()
        planeAxis3 = self._Plane.GetNormal()

        planeAxis1 = [planePoint1[0] - planeOrigin[0],
                      planePoint1[1] - planeOrigin[1],
                      planePoint1[2] - planeOrigin[2]]

        planeAxis2 = [planePoint2[0] - planeOrigin[0],
                      planePoint2[1] - planeOrigin[1],
                      planePoint2[2] - planeOrigin[2]]

        # the x,y dimensions of the plane
        planeSizeX = math.sqrt(planeAxis1[0] * planeAxis1[0] +
                               planeAxis1[1] * planeAxis1[1] +
                               planeAxis1[2] * planeAxis1[2])
        planeSizeY = math.sqrt(planeAxis2[0] * planeAxis2[0] +
                               planeAxis2[1] * planeAxis2[1] +
                               planeAxis2[2] * planeAxis2[2])

        if planeSizeX == 0.0 or planeSizeY == 0.0:
            return

        # the x,y axes of the plane (the z-axis is the normal)
        planeAxis1[0] = old_div(planeAxis1[0], planeSizeX)
        planeAxis1[1] = old_div(planeAxis1[1], planeSizeX)
        planeAxis1[2] = old_div(planeAxis1[2], planeSizeX)

        planeAxis2[0] = old_div(planeAxis2[0], planeSizeY)
        planeAxis2[1] = old_div(planeAxis2[1], planeSizeY)
        planeAxis2[2] = old_div(planeAxis2[2], planeSizeY)

        # generate the slicing matrix
        matrix = self._ResliceAxes
        matrix.SetElement(0, 0, planeAxis1[0])
        matrix.SetElement(1, 0, planeAxis1[1])
        matrix.SetElement(2, 0, planeAxis1[2])
        matrix.SetElement(3, 0, 0.0)
        matrix.SetElement(0, 1, planeAxis2[0])
        matrix.SetElement(1, 1, planeAxis2[1])
        matrix.SetElement(2, 1, planeAxis2[2])
        matrix.SetElement(3, 1, 0.0)
        matrix.SetElement(0, 2, planeAxis3[0])
        matrix.SetElement(1, 2, planeAxis3[1])
        matrix.SetElement(2, 2, planeAxis3[2])
        matrix.SetElement(3, 2, 0.0)
        matrix.SetElement(0, 3, 0)
        matrix.SetElement(1, 3, 0)
        matrix.SetElement(2, 3, 0)
        matrix.SetElement(3, 3, 1.0)

        # transpose is an exact way to invert a pure rotation matrix
        matrix.Transpose()
        originX, originY, originZ, w = \
            matrix.MultiplyPoint(planeOrigin + (1.0,))

        matrix.Transpose()
        newOriginX, newOriginY, newOriginZ, w = \
            matrix.MultiplyPoint((0.0, 0.0, originZ, 1.0))

        matrix.SetElement(0, 3, newOriginX)
        matrix.SetElement(1, 3, newOriginY)
        matrix.SetElement(2, 3, newOriginZ)

        for name in self._Inputs:
            reslice = self._ImageReslicers[name]
            coords = self._TextureCoords[name]
            image = reslice.GetInput()

            # calculate appropriate pixel spacing for the reslicing

            # VTK-6
            # if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            #    print 'SlicePlaneFactory:_UpdateNormal - fix UpdateInformation()!'
            #    #image.UpdateInformation()  # TODO: VTK-6 figure out what to do here
            # else:
            # image.UpdateInformation()  # TODO: VTK-6 figure out what to do
            # here

            spacing = image.GetSpacing()

            spacingX = abs(planeAxis1[0] * spacing[0]) +\
                abs(planeAxis1[1] * spacing[1]) +\
                abs(planeAxis1[2] * spacing[2])

            spacingY = abs(planeAxis2[0] * spacing[0]) +\
                abs(planeAxis2[1] * spacing[1]) +\
                abs(planeAxis2[2] * spacing[2])

            # pad extent up to a power of two for efficient texture mapping

            extentX = 1
            while (extentX < old_div(planeSizeX, spacingX)):
                extentX = extentX << 1

            extentY = 1
            while (extentY < old_div(planeSizeY, spacingY)):
                extentY = extentY << 1

            reslice.SetOutputSpacing(spacingX, spacingY, 1)
            reslice.SetOutputOrigin(0.5 * spacingX + originX,
                                    0.5 * spacingY + originY,
                                    0.0)

            reslice.SetOutputExtent(0, extentX - 1, 0, extentY - 1, 0, 0)

            # set up a transform grid for nonlinear transform acceleration
            if self._TransformGrids[name]:
                self._TransformGrids[name].SetGridOrigin(
                    reslice.GetOutputOrigin())
                self._TransformGrids[name].SetGridSpacing(
                    [4 * x for x in reslice.GetOutputSpacing()])
                self._TransformGrids[name].SetGridExtent(
                    [old_div(x, 4) for x in reslice.GetOutputExtent()])

            # find expansion factor to account for increasing the extent
            # to a power of two
            expand1 = extentX * spacingX
            expand2 = extentY * spacingY

            # set the texture coordinates to map the image to the plane
            coords.SetOrigin(planeOrigin[0], planeOrigin[1], planeOrigin[2])
            coords.SetPoint1(planeOrigin[0] + planeAxis1[0] * expand1,
                             planeOrigin[1] + planeAxis1[1] * expand1,
                             planeOrigin[2] + planeAxis1[2] * expand1)
            coords.SetPoint2(planeOrigin[0] + planeAxis2[0] * expand2,
                             planeOrigin[1] + planeAxis2[1] * expand2,
                             planeOrigin[2] + planeAxis2[2] * expand2)

        self.Modified()

    def SetDisablePushAction(self, yesno):
        self._DisablePushAction = yesno

    def DisablePushActionOn(self):
        self.SetDisablePushAction(1)

    def DisablePushActionOff(self):
        self.SetDisablePushAction(0)

    def DoStartAction(self, event):
        self._LastX = event.x
        self._LastY = event.y

        self._oldOutlineVisibility = self.GetOutlineVisibility()
        self.OutlineOn()

        action = self.__UserAction or 'Push'

        if action == 'Push':
            self.SetOutlineColor(self._PushColor)
        elif action == 'Rotate':
            self.SetOutlineColor(self._RotateColor)
        elif action == 'Spin':
            self.SetOutlineColor(self._SpinColor)

        # Make Plane Outline Invisible
        self.SetOutlineColor(self._DefaultOutlineColor)
        self.SetOutline(int(self._oldOutlineVisibility))
        self.__UserAction = None

    def DoPush(self, event):

        if self._DisablePushAction:
            return

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        try:
            lx, ly, lz = self.IntersectWithViewRay(self._LastX,
                                                   self._LastY,
                                                   renderer)
        except ZeroDivisionError:
            lx, ly, lz = self.GetOrigin()

        # find depth-buffer value for intersection point
        renderer.SetWorldPoint(lx, ly, lz, 1.0)
        renderer.WorldToDisplay()
        z = renderer.GetDisplayPoint()[2]

        # and use it to find the world coords of the current x,y coord
        # (i.e. the mouse moves solely in x,y plane)
        renderer.SetDisplayPoint(event.x, event.y, z)
        renderer.DisplayToWorld()
        wx, wy, wz, w = renderer.GetWorldPoint()
        wx, wy, wz = (old_div(wx, w), old_div(wy, w), old_div(wz, w))

        # mouse motion vector, in world coords
        dx, dy, dz = (wx - lx, wy - ly, wz - lz)

        # check to make sure that plane is not facing camera
        nx, ny, nz = self.GetTransformedNormal()
        vx, vy, vz = camera.GetViewPlaneNormal()
        n_dot_v = nx * vx + ny * vy + nz * vz

        if (abs(n_dot_v) < 0.9):
            # drag plane to exactly match cursor motion
            dd = old_div((dx * (nx - vx * n_dot_v) + dy * (ny - vy * n_dot_v) + dz * (nz - vz * n_dot_v)), \
                 (1.0 - n_dot_v * n_dot_v))
        else:
            # plane is perpendicular to viewing ray, so just push by distance
            dd = math.sqrt(dx * dx + dy * dy + dz * dz)
            if (n_dot_v * (event.x + event.y - self._LastX - self._LastY) > 0):
                dd = -dd

        # find the fraction of the push that was done, in case we hit bounds
        if dd != 0:
            f = old_div(self.Push(dd), dd)
        else:
            f = 1.0

        if (f < 0.9999):
            # hit bounds: set LastX,LastY appropriately
            renderer.SetWorldPoint(lx + dx * f, ly + dy * f, lz + dz * f, 1.0)
            renderer.WorldToDisplay()
            x, y, z = renderer.GetDisplayPoint()
            self._LastX = int(x + 0.5)
            self._LastY = int(y + 0.5)
        else:
            self._LastX = event.x
            self._LastY = event.y

        self.Modified()

    def _MakeActors(self):

        # get list of texture-mapped actors
        actors = {}

        # first, create the red background
        actor = ActorFactory.ActorFactory._NewActor(self)
        actor.GetProperty().SetColor(1, 0, 0)
        actor.VisibilityOff()
        mapper = vtk.vtkDataSetMapper()
        self._Plane.Update()  # VTK-6 force a pipeline update
        mapper.SetInputConnection(self._Plane.GetOutputPort())
        actor.SetMapper(mapper)
        actors['red'] = actor

        for name in self._Inputs:
            actors[name] = self._NewActor(name)
        return actors

    def _NewActor(self, name=0):

        # construct the graphics pipeline for image `name`
        actor = ActorFactory.ActorFactory._NewActor(self)

        mapper = vtk.vtkDataSetMapper()
        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            mapper.SetInputConnection(
                self._TextureCoords[name].GetOutputPort())
        else:
            mapper.SetInput(self._TextureCoords[name].GetOutput())
        if self.GetClippingPlanes(name) is not None:
            mapper.SetClippingPlanes(self.GetClippingPlanes(name))

        self.texture = vtk.vtkTexture()
        self.texture.SetQualityTo32Bit()

        vtk_ver = vtk.vtkVersion()
        vtk_ver = vtk_ver.GetVTKMajorVersion() * 10 + \
                  vtk_ver.GetVTKMinorVersion()
        if vtk_ver >= 82:
            self.texture.SetColorModeToDirectScalars()
        else:
            self.texture.MapColorScalarsThroughLookupTableOff()
        self.texture.SetInputConnection(
            self._ImageMapToColors[name].GetOutputPort())
        self.texture.SetInterpolate(self._TextureInterpolate)
        self.texture.RepeatOff()  # only necessary if interpolation is on
        if (self._LookupTables[name]):
            self.texture.SetLookupTable(self._LookupTables[name])

        actor.SetProperty(self._Properties[name])
        self._Properties[name].SetAmbient(0.5)
        actor.SetMapper(mapper)
        actor.SetTexture(self.texture)

        return actor

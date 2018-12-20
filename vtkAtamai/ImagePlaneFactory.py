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
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: ImagePlaneFactory.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
    'author': '$Author: jeremy_gill $',
    'version': '$Revision: 1.4 $',
    'date': '$Date: 2007/11/15 15:20:35 $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
ImagePlaneFactory - draw a 2D image by texturing it onto a plane

  This class is very similar to SlicePlaneFactory except that
  the source image is a singly slice in the xy plane instead of
  a full image volume.

  The whole image is used as a texture map.  You can use the
  SetPlaneBounds method to clip out a portion of the texture for
  display, or use the GeneratePlane method to display the entire
  texture.

Derived From:

  ActorFactory

See Also:

  SlicePlaneFactory

Public Methods:

  Specify the image volume:

    SetInput(*imagedata*,*i*=0)   -- set a vtkImageData to slice through

    GetInput(*i*=0)               -- get input *i*

    AddInput(*imagedata*)         -- add an input after the last input

    RemoveInput(*i*=0)            -- remove an input

    GetNumberOfInputs()           -- current number of inputs

  Change the display of the image:

    SetLookupTable(*table*,*i*=0) -- change the lookup table for image *i*

    GetLookupTable(*i*=0)         -- get the lookup table

    SetOpacity(*alpha*,*i*=0)     -- set the opacity of image *i*

    GetOpacity(*i*=0)             -- get the opacity

  Set the bounds for the 2D plane:

    SetPlaneBounds(*xmin*,*xmax*,*ymin*,*ymax*) -- set the bounds for the
                                         plane, to limit the region of the
                                         image that will be drawn

    GetPlaneBounds()                            -- get the bounds

  Interpolation:

    SetSliceInterpolate(*boolean*) -- interpolate while resampling (default on)

    SetTextureInterpolate(*boolean*) -- interpolate when texture mapping
                                        (default on)

  Render onto an arbitrary polygonal shape:

    SetPolyData(*data*) -- the data must lie in the plane of the slice

    GetPolyData() -- get the polydata (will be a plane by default)

"""

import math
from .ActorFactory import *


class ImagePlaneFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        # generate the pipeline components

        # the following are required for each input
        self._Inputs = []
        self._Outputs = []
        self._TextureCoords = []
        self._LookupTables = []
        self._Properties = []
        self._Reslicers = []
        self._ClippingPlanes = []

        # thankfully, we don't need more than one of these
        self._Plane = vtk.vtkPlaneSource()
        self._Plane.SetXResolution(1)
        self._Plane.SetYResolution(1)

        # autogenerate the plane size from image size
        self._AutomaticPlaneGeneration = 1

        # user can set polydata to render onto
        self._PolyData = self._Plane.GetOutput()

        self._PlaneEquation = None

        self._TextureInterpolate = 1

    def GetNumberOfInputs(self):
        return len(self._Inputs)

    def AddInput(self, input):
        # the input is the image data to slice through
        i = len(self._Inputs)

        coords = vtk.vtkTextureMapToPlane()
        coords.SetInput(self._PolyData)
        coords.AutomaticPlaneGenerationOff()

        property = vtk.vtkProperty()

        self._Inputs.append(input)
        self._Outputs.append(input)
        self._TextureCoords.append(coords)
        self._Properties.append(property)
        self._LookupTables.append(None)
        self._Reslicers.append(None)
        self._ClippingPlanes.append(None)

        actors = self._ActorDict
        for renderer in self._Renderers:
            actor = self._NewActor(i)
            actor.SetPickable(i == 0)
            actors[renderer].append(actor)
            renderer.AddActor(actor)

        if (i == 0 and self._AutomaticPlaneGeneration):
            self.GeneratePlane()
        self._UpdateTextureCoords()

        return i + 1

    def RemoveInput(self, i=0):
        actors = self._ActorDict
        for renderer in self._Renderers:
            temp = list(actors[renderer])
            renderer.RemoveActor(temp[i])
            if (i == 0 and len(temp) > 1):
                temp[1].SetPickable(temp[0].GetPickable())
            del temp[i]
            actors[renderer] = tuple(temp)

        del self._Inputs[i]
        del self._Outputs[i]
        del self._TextureCoords[i]
        del self._Properties[i]
        del self._LookupTables[i]
        del self._Reslicers[i]
        del self._ClippingPlanes[i]

    def SetInput(self, input, i=0):
        if (i == len(self._Inputs)):
            self.AddInput(input)
            return

        self._Inputs[i] = input
        if (i == 0 and self._AutomaticPlaneGeneration):
            self.GeneratePlane()
        self._UpdateTextureCoords()

    def GetInput(self, i=0):
        try:
            return self._Inputs[i]
        except:
            return None

    def SetPolyData(self, data):
        if (data):
            self._PolyData = data
            for coords in self._TextureCoords:
                coords.SetInput(data)
        else:
            self._PolyData = self._Plane.GetOutput()
        self.Modified()

    def GetPolyData(self):
        return self._PolyData

    def SetTextureInterpolate(self, val):
        self._TextureInterpolate = val
        actors = self.GetActorDict()
        for renderer in self._Renderers:
            actor = self.actors[renderer][i]
            actor.GetTexture().SetInterpolate(val)
        self.Modified()

    def GetTextureInterpolate(self):
        return self._TextureInterpolate

    def TextureInterpolateOn(self):
        self.SetTextureInterpolate(1)

    def TextureInterpolateOff(self):
        self.SetTextureInterpolate(0)

    def SetLookupTable(self, table, i=0):
        # the lookup table associated with the image data
        self._LookupTables[i] = table
        actors = self._ActorDict
        for renderer in self._Renderers:
            actor = actors[renderer][i]
            actor.GetTexture().SetLookupTable(table)
            actor.GetTexture().MapColorScalarsThroughLookupTableOn()
        self.Modified()

    def GetLookupTable(self, i=0):
        return self._LookupTables[i]

    def SetOpacity(self, alpha, i=0):
        self._Properties[i].SetOpacity(alpha)
        self.Modified()

    def GetOpacity(self, i=0):
        return self._Properties[i].GetOpacity()

    def SetPlaneBounds(self, *args):
        if len(args) == 1:
            args = args[0]
        xmin, xmax, ymin, ymax = args
        self._Plane.SetOrigin(xmin, ymin, 0)
        self._Plane.SetPoint1(xmax, ymin, 0)
        self._Plane.SetPoint2(xmin, ymax, 0)
        self._AutomaticPlaneGeneration = 0
        self._UpdateTextureCoords()

    def GeneratePlane(self):
        # Automatically generate a plane for the data:
        # this must be called _after_ SetInput()
        input = self._Inputs[0]

        try:
            input.UpdateInformation()
        except:
            input.UpdateImageInformation()

        extent = input.GetExtent()  # VTK 6
        origin = input.GetOrigin()
        spacing = input.GetSpacing()

        self._Plane.SetOrigin(origin[0] + spacing[0] * (extent[0] - 0.5),
                              origin[1] + spacing[1] * (extent[2] - 0.5),
                              origin[2] + spacing[2] * extent[4])
        self._Plane.SetPoint1(origin[0] + spacing[0] * (extent[1] + 0.5),
                              origin[1] + spacing[1] * (extent[2] - 0.5),
                              origin[2] + spacing[2] * extent[4])
        self._Plane.SetPoint2(origin[0] + spacing[0] * (extent[0] - 0.5),
                              origin[1] + spacing[1] * (extent[3] + 0.5),
                              origin[2] + spacing[2] * extent[4])

        self._UpdateTextureCoords()

    def _MakeActors(self):
        # get a texture-mapped actor
        actors = []
        for i in range(0, self.GetNumberOfInputs()):
            actors.append(self._NewActor(i))
        return actors

    def _NewActor(self, i=0):
        # construct the graphics pipeline for input i
        actor = ActorFactory._NewActor(self)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(self._TextureCoords[i].GetOutput())

        texture = vtk.vtkTexture()
        texture.RepeatOff()
        try:
            texture.SetQualityTo32Bit()
        except:
            pass
        texture.SetInterpolate(self._TextureInterpolate)
        if (self._LookupTables[i]):
            texture.MapColorScalarsThroughLookupTableOn()
            texture.SetLookupTable(self._LookupTables[i])
        else:
            texture.MapColorScalarsThroughLookupTableOff()
        texture.SetInput(self._Outputs[i])

        actor.SetProperty(self._Properties[i])
        actor.SetMapper(mapper)
        actor.SetTexture(texture)
        return actor

    def HasChangedSince(self, sinceMTime):
        if (ActorFactory.HasChangedSince(self, sinceMTime)):
            return 1
        for input in self._Inputs:
            if (input.GetMTime() > sinceMTime):
                return 1
        for table in self._LookupTables:
            if (table and table.GetMTime() > sinceMTime):
                return 1
        return 0

    def _UpdateTextureCoords(self):
        # a protected method, called when a property of the slice plane changes
        if (self._PlaneEquation):
            self._PlaneEquation.SetNormal((0, 0, 1))
            self._PlaneEquation.SetOrigin(self._Plane.GetOrigin())

        for i in range(len(self._Inputs)):
            coords = self._TextureCoords[i]
            input = self._Inputs[i]

            # calculate appropriate pixel spacing for the reslicing
            input.UpdateInformation()

            spacing = input.GetSpacing()
            origin = input.GetOrigin()
            extent = input.GetExtent()  # VTK 6

            spacingX = spacing[0]
            spacingY = spacing[1]

            # pad extent up to a power of two for efficient texture mapping
            extentX = 1
            while (extentX < extent[1] - extent[0] + 1):
                extentX = extentX << 1

            extentY = 1
            while (extentY < extent[3] - extent[2] + 1):
                extentY = extentY << 1

            # apply the pad only if necessary (yes, I use vtkImageReslice
            # even for padding)
            if (extentX > extent[1] - extent[0] + 1 or
                    extentY > extent[3] - extent[2] + 1):
                if (not self._Reslicers[i]):
                    self._Reslicers[i] = vtk.vtkImageReslice()
                    self._Reslicers[i].SetInterpolationModeToNearestNeighbor()
                reslice = self._Reslicers[i]
                reslice.SetInput(input)
                reslice.SetOutputOrigin(origin)
                reslice.SetOutputSpacing(spacing)
                reslice.SetOutputExtent(extent[0], extent[0] + extentX - 1,
                                        extent[2], extent[2] + extentY - 1,
                                        extent[4], extent[4])
                self._Outputs[i] = reslice.GetOutput()
            else:
                self._Outputs[i] = input

            for renderer in self._Renderers:
                actor = self._ActorDict[renderer][i]
                actor.GetTexture().SetInput(self._Outputs[i])

            # set the texture coordinates to map the image to the plane
            coords.SetOrigin(origin[0] + spacing[0] * (extent[0] - 0.5),
                             origin[1] + spacing[1] * (extent[2] - 0.5),
                             origin[2] + spacing[2] * extent[4])
            coords.SetPoint1(origin[0] + spacing[0] * (extent[0] + extentX - 0.5),
                             origin[1] + spacing[1] * (extent[2] - 0.5),
                             origin[2] + spacing[2] * extent[4])
            coords.SetPoint2(origin[0] + spacing[0] * (extent[0] - 0.5),
                             origin[1] + spacing[1] *
                             (extent[2] + extentY - 0.5),
                             origin[2] + spacing[2] * extent[4])

        self.Modified()

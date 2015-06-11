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
    'module_name': '$RCSfile: ImagePane.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
    'author': '$Author: hqian $',
    'version': '$Revision: 1.5 $',
    'date': '$Date: 2006/09/26 18:58:24 $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
ImagePane - high-quality image viewer

  The ImagePane is a RenderPane for viewing images.  The images are
  rendered directly to the screen with cubic, linear or nearest-neighbour
  interpolation.  Any Widgets or ActorFactories are drawn on top of the
  image.

  The main difference between the ImagePane and the RenderPane (or the
  RenderPane2D) is that the coordinate system in the window is a 2D
  coordinate system where horizontal is X, vertical is Y, and Z is always
  zero.
"""

import vtk
import RenderPane
import EventHandler
import math
import time

# this helper class works around the fact that
# in VTK 5, vtkImageBlend has no GetNumberOfInputs()
# method


class newImageBlend(vtk.vtkImageBlend):

    def GetNumberOfInputs(self):
        try:
            return self.__class__.__bases__[0].GetNumberOfInputs(self)
        except AttributeError:
            for i in range(20):
                if self.GetInput(i) is None:
                    return i

vtkImageBlend = newImageBlend


class vtkImageActor2(vtk.vtkActor):

    """This class is a special ImageActor substitute that uses a
    vtkTexture instead, the only real reason is to add a SetOpacity
    method!"""

    def __init__(self):
        self._ImagePad = vtk.vtkImageReslice()
        self._Texture = vtk.vtkTexture()
        self._Texture.SetInput(self._ImagePad.GetOutput())
        self._Texture.SetQualityTo32Bit()
        self._Texture.MapColorScalarsThroughLookupTableOff()
        self._Texture.RepeatOff()
        self._PlaneSource = vtk.vtkPlaneSource()
        self._Mapper = vtk.vtkDataSetMapper()
        self._Mapper.SetInput(self._PlaneSource.GetOutput())

        self.SetTexture(self._Texture)
        self.SetMapper(self._Mapper)
        self.PickableOff()

    def SetOpacity(self, opacity):
        self.GetProperty().SetOpacity(opacity)

    def GetOpacity(self):
        return self.GetProperty().GetOpacity()

    def SetInput(self, input):
        self._ImagePad.SetInput(input)

    def GetInput(self):
        return self._ImagePad.GetInput()

    def SetInterpolate(self, interp):
        self._Texture.SetInterpolate(interp)

    def GetInterpolate(self):
        return self._Texture.GetInterpolate()

    def InterpolateOn(self):
        self.SetInterpolate(1)

    def InterpolateOff(self):
        self.SetInterpolate(0)

    def SetDisplayExtent(self, extent):
        input = self.GetInput()
        input.UpdateInformation()
        spacing = input.GetSpacing()
        origin = input.GetOrigin()

        xdim = extent[1] - extent[0] + 1
        ydim = extent[3] - extent[2] + 1

        xdim2 = 16
        ydim2 = 16
        while xdim2 < xdim:
            xdim2 = xdim2 * 2
        while ydim2 < ydim:
            ydim2 = ydim2 * 2

        xmin = origin[0] + spacing[0] * (extent[0] - 0.5)
        xmax = origin[0] + spacing[0] * (extent[0] + xdim2 - 0.5)
        ymin = origin[1] + spacing[1] * (extent[2] - 0.5)
        ymax = origin[1] + spacing[1] * (extent[2] + ydim2 - 0.5)
        z = origin[2] + spacing[2] * extent[4]

        self._PlaneSource.SetOrigin(xmin, ymin, z)
        self._PlaneSource.SetPoint1(xmax, ymin, z)
        self._PlaneSource.SetPoint2(xmin, ymax, z)

        self._ImagePad.SetOutputOrigin(origin)
        self._ImagePad.SetOutputSpacing(spacing)
        self._ImagePad.SetOutputExtent(extent[0], extent[0] + xdim2 - 1,
                                       extent[2], extent[2] + ydim2 - 1,
                                       extent[4], extent[4])


class ImagePane(RenderPane.RenderPane):

    """ImagePane -- a RenderPane for viewing 2D and 3D images

    Default mouse bindings:

       Pan           -- Left
       Slice         -- Middle  or  Shift-Left
       Zoom          -- Right   or  Control-Left
       Window/Level  -- Shift-Right  or  Control-Shift-Left
       Oblique       -- not bound

    Default key bindings:

       p             -- Print pixel value under cursor
       r             -- Reset to original scale
       Up/Down       -- Prev/next slice
       Left/Right    -- Shrink/magnify
       shift-arrows  -- Pan
       ctrl-arrows   -- Window/level adjust

       All actors that are added to the widget will be
       drawn in (x,y) 2D image coordinates (set z=0),
       and will automatically scale & pan with the image.
    """

    def __init__(self, *args, **kw):
        RenderPane.RenderPane.__init__(self, *args, **kw)

        self._Dynamic = 0
        self._Aborted = 0
        self._Executing = 0
        self._SyncScalePanes = []
        self._SyncPanes = []

        # whether slicing is limited to image bounds
        self._SliceLimits = 1

        self._RenderingModes = {'DrawPixels': 0,
                                'Texture': 1}
        self._RenderingMode = 0

        self._InterpolationModes = {'NearestNeighbor': 0,
                                    'Nearest': 0,
                                    'Linear': 1,
                                    'Cubic': 3}
        self._InterpolationMode = 3
        self._DynamicInterpolationMode = 1
        self._NoRender = 0
        self._InExpose = 0
        self._AccelerationKey = None
        self._AccelerationFactor = 1.0
        self._AccelerationTime = 0.0
        self._LastRenderTimeInSeconds = 0.0
        self._OriginalColorWindow = 1.0
        self._OriginalColorLevel = 0.5
        self._LastX = 0
        self._LastY = 0
        self._StartX = 0
        self._StartY = 0

        self._InitializeDrawPixels()
        self._InitializeTexture()
        self._InitializeTexture2()

        self._Camera = vtk.vtkCamera()
        self._Camera.ParallelProjectionOn()
        self._Camera.SetParallelScale(256)
        self._Camera.SetFocalPoint(127.5, 127.5, 0)
        self._Camera.SetPosition(127.5, 127.5, 1000)
        self._Camera.SetClippingRange(0.0, 2000.0)

        self._CursorTransform = vtk.vtkMatrixToLinearTransform()
        self._CursorTransform.SetInput(vtk.vtkMatrix4x4())

        self._InOblique = 0  # in DoOblique method

        renderer = self.GetRenderer()
        renderer.SetActiveCamera(self._Camera)

        if self._RenderingMode == 0:
            renderer.AddActor2D(self._Actor2D)
        elif self._RenderingMode == 1:
            renderer.AddActor(self._ImageActor)
            for actor2 in self._ImageActor2:
                if actor2:
                    renderer.AddActor(actor2)
                    if self._Dynamic == 0:
                        actor2.SetVisibility(0)

        self.BindEvent('<Configure>', self.DoConfigure)

    def _InitializeDrawPixels(self):
        """Perform the initializations for drawing without textures,
           i.e. where image is drawn directly to the screen."""

        # ImageReslice extracts slices from each image volume and also
        # interpolates to get the pixel values to map to the screen
        self._ImageReslice = []
        # ImageColor performs color mapping operations on each volume
        self._ImageColor = []

        reslice = vtk.vtkImageReslice()
        reslice.SetInput(0, self.MakeDefaultImage())
        reslice.SetInterpolationMode(self._InterpolationMode)
        reslice.SetResliceAxes(vtk.vtkMatrix4x4())
        reslice.SetOutputExtent(0, 255, 0, 255, 0, 0)
        reslice.SetOutputOrigin(0, 0, 0)
        reslice.SetOutputSpacing(1, 1, 1)
        reslice.SetBackgroundLevel(0)
        reslice.SetOptimization(1)

        table = vtk.vtkLookupTable()
        table.SetTableRange(0, 1)
        table.Build()
        for i in range(256):
            table.SetTableValue(i, i / 255.0, i / 255.0, i / 255.0, 1.0)

        color = vtk.vtkImageMapToColors()
        color.SetInput(reslice.GetOutput())
        color.SetOutputFormatToRGB()
        color.SetLookupTable(table)
        color.AddObserver('ExecuteInformationEvent', self.OnMapToColors)

        self._ImageReslice.append(reslice)
        self._ImageColor.append(color)

        self._ImageBlend = vtk.vtkImageBlend()
        self._ImageBlend.SetInput(0, self._ImageColor[0].GetOutput())

        # the ImageChangeInformation adjusts the image so that the
        # currently viewed slice lies at z=0
        self._ImageChangeInformation = vtk.vtkImageChangeInformation()
        self._ImageChangeInformation.SetInput(self._ImageBlend.GetOutput())

        self._ImageMapper = vtk.vtkImageMapper()
        self._ImageMapper.SetInput(self._ImageChangeInformation.GetOutput())
        self._ImageMapper.SetColorWindow(255.0)
        self._ImageMapper.SetColorLevel(127.5)

        self._Actor2D = vtk.vtkActor2D()
        self._Actor2D.GetProperty().SetDisplayLocationToBackground()
        self._Actor2D.SetMapper(self._ImageMapper)

    def _InitializeTexture(self):
        """Perform the initializations for drawing with textures.
        This builds upon actions performed in _InitializeDrawPixels.
        """
        self._ImageActor = vtk.vtkImageActor()
        self._ImageActor.InterpolateOff()
        self._ImageActor.SetInput(self._ImageChangeInformation.GetOutput())

    def _InitializeTexture2(self):
        """Perform the initialization for extracting a single slice from
        the image, for use as the SliceOutput and for use in a second
        texture rendering mode that performs interpolation with the
        textures.
        """

        self._ImageReslice2 = []
        self._ImageColor2 = []
        self._ImageChangeInformation2 = []
        self._ImageActor2 = []

        reslice2 = vtk.vtkImageReslice()
        reslice2.SetInput(self.MakeDefaultImage())
        reslice2.SetInterpolationModeToNearestNeighbor()
        reslice2.SetResliceAxes(self._ImageReslice[0].GetResliceAxes())
        reslice2.SetBackgroundLevel(0)
        reslice2.SetOptimization(2)

        self._ImageReslice2.append(reslice2)

        color2 = vtk.vtkImageMapToColors()
        color2.SetInput(reslice2.GetOutput())
        color2.SetOutputFormatToRGB()
        color2.SetLookupTable(self._ImageColor[0].GetLookupTable())
        color2.AddObserver('ExecuteInformationEvent', self.OnMapToColors)

        self._ImageColor2.append(color2)

        info2 = vtk.vtkImageChangeInformation()
        info2.SetInput(self._ImageColor2[0].GetOutput())
        origin = info2.GetOutputOrigin()
        info2.SetOutputOrigin(origin[0], origin[1], 0.0)

        self._ImageChangeInformation2.append(info2)

        actor2 = vtk.vtkImageActor()
        actor2.SetInterpolate(self._InterpolationMode)
        actor2.SetInput(self._ImageChangeInformation2[0].GetOutput())

        self._ImageActor2.append(actor2)

    def DynamicOff(self):
        if self._Dynamic != 0:
            for reslice in self._ImageReslice:
                if reslice:
                    reslice.SetInterpolationMode(self._InterpolationMode)
            if self._RenderingMode == 1:
                self._ImageActor.SetVisibility(1)
                for actor2 in self._ImageActor2:
                    if actor2:
                        actor2.SetVisibility(0)
            self._Dynamic = 0
            self.Modified()

    def DynamicOn(self):
        if self._Dynamic == 0:
            for reslice in self._ImageReslice:
                if reslice:
                    reslice.SetInterpolationMode(
                        self._DynamicInterpolationMode)
            if self._RenderingMode == 1 and not self.IsOblique():
                self._ImageActor.SetVisibility(0)
                for actor2 in self._ImageActor2:
                    if actor2:
                        actor2.SetVisibility(1)
            self._Dynamic = 1
            self.Modified()

    def IsOblique(self):
        matrix = self._ImageReslice[0].GetResliceAxes()
        for vec in [(1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0)]:
            if list(matrix.MultiplyPoint(vec)).count(0.0) != 3:
                return 1
        for reslice in self._ImageReslice:
            trans = reslice.GetResliceTransform()
            if trans:
                for vec in [(1.0, 0.0, 0.0),
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0)]:
                    if list(trans.TransformVector(vec)).count(0.0) != 2:
                        return 1
        return self._InOblique

    #--------------------------------------
    def OnMapToColors(self, color, event):
        """Called before ImageMapToColors is executed.  If there is
        no lookup table, it ensures that the output number of scalar
        components matches the input number of scalar components.
        """
        if color.GetLookupTable() is None:
            input = color.GetInput()
            n = input.GetNumberOfScalarComponents()
            if n == 3:
                color.SetOutputFormatToRGB()
            elif n == 4:
                color.SetOutputFormatToRGBA()
            elif n == 2:
                color.SetOutputFormatToLuminanceAlpha()
            elif n == 1:
                color.SetOutputFormatToLuminance()
        else:
            color.SetOutputFormatToRGBA()
            # check that ActiveComponent is not too high
            input = color.GetInput()
            n = input.GetNumberOfScalarComponents()
            i = color.GetActiveComponent()
            if i >= n:
                color.SetActiveComponent(i % n)

    #--------------------------------------
    def BindDefaultInteraction(self):
        """Bind the default handlers for mouse events.

        The following are the default mouse bindings:

          - left - rotate camera
          - shift-left - pan camera
          - right - zoom camera
          - middle - interact with the ActorFactory under the mouse.

        """
        self.BindPanToButton(1)
        self.BindPushToButton(1, 'Shift')
        self.BindPushToButton(2)
        self.BindZoomToButton(3)
        self.BindWindowLevelToButton(3, 'Shift')

    def BindPanToButton(self, button=1, modifier=None):
        """Use the specified button to pan the camera."""
        self.BindModeToButton((self.DoStartMotion,
                               self.DoEndMotion,
                               self.DoCameraPan),
                              button, modifier)

    def BindZoomToButton(self, button=1, modifier=None):
        """Use the specified button to zoom the camera."""
        self.BindModeToButton((self.DoStartMotion,
                               self.DoEndMotion,
                               self.DoCameraZoom),
                              button, modifier)

    def BindPushToButton(self, button=1, modifier=None):
        self.BindModeToButton((self.DoStartMotion,
                               self.DoEndMotion,
                               self.DoPush),
                              button, modifier)

    def BindWindowLevelToButton(self, button=1, modifier=None):
        self.BindModeToButton((self.DoStartMotion,
                               self.DoEndMotion,
                               self.DoWindowLevel),
                              button, modifier)

    def BindResetToButton(self, button=1, modifier=None):
        self.BindModeToButton((lambda e, s=self: s.ResetView(),
                               lambda e: None,
                               lambda e: None),
                              button, modifier)

    def BindKeyInteraction(self):
        """w.BindKeys()  -- set default key bindings
        """
        self.BindEvent('<KeyPress-r>', self.DoReset)
        self.BindEvent('<KeyPress-p>', self.DoPrintPixel)
        self.BindEvent('<KeyPress-t>', self.DoSwitchRenderingMode)

        self.BindEvent('<Shift-KeyPress-Left>', self.DoCameraPanLeft)
        self.BindEvent('<Shift-KeyPress-Right>', self.DoCameraPanRight)
        self.BindEvent('<Shift-KeyPress-Down>', self.DoCameraPanDown)
        self.BindEvent('<Shift-KeyPress-Up>', self.DoCameraPanUp)

        self.BindEvent('<KeyPress-Down>', self.DoNextSlice)
        self.BindEvent('<KeyPress-Up>', self.DoPrevSlice)

        self.BindEvent('<KeyPress-Left>', self.DoDecreaseScale)
        self.BindEvent('<KeyPress-Right>', self.DoIncreaseScale)

        self.BindEvent('<Control-KeyPress-Left>', self.DoDecreaseLevel)
        self.BindEvent('<Control-KeyPress-Right>', self.DoIncreaseLevel)
        self.BindEvent('<Control-KeyPress-Down>', self.DoDecreaseWindow)
        self.BindEvent('<Control-KeyPress-Up>', self.DoIncreaseWindow)

    def MakeDefaultImage(self):
        """w.MakeDefaultImage()  -- create the default image

        The default image is simply an 'X' that lies in the xy plane.
        """
        image = vtk.vtkImageCanvasSource2D()
        image.SetNumberOfScalarComponents(1)
        image.SetScalarType(10)
        image.SetExtent(0, 255, 0, 255, 0, 0)
        image.SetDrawColor(1.0)
        image.FillBox(0, 255, 0, 255)
        image.SetDrawColor(0.0)
        image.FillBox(2, 253, 2, 253)
        image.SetDrawColor(0.8)
        image.DrawSegment(2, 3, 252, 253)
        image.DrawSegment(3, 2, 253, 252)
        image.DrawSegment(3, 253, 253, 3)
        image.DrawSegment(2, 252, 252, 2)
        image.SetDrawColor(1.0)
        image.DrawSegment(2, 253, 253, 2)
        image.DrawSegment(2, 2, 253, 253)

        return image.GetOutput()

    def SetResliceAxes(self, *args):
        """w.SetResliceAxes(axes)  -- set the slice orientation

        Specify the slice orientation using either a vtkMatrix4x4
        or a list of 9 numbers.  The columns of the matrix (or the
        three 3-tuples in the list) are the x, y, and z slice axes
        vectors.
        """
        matrix = vtk.vtkMatrix4x4()
        if len(args) == 1:
            args = args[0]
        try:
            if len(args) == 9:
                for i in range(3):
                    for j in range(3):
                        matrix.SetElement(i, j, args[3 * j + i])
            elif len(args) == 3:
                for i in range(3):
                    for j in range(3):
                        matrix.SetElement(i, j, args[j][i])
        except:
            matrix.DeepCopy(args)

        o = self._ImageReslice[0].GetOutputOrigin()[2]
        transform = vtk.vtkTransform()
        transform.Concatenate(self.GetResliceAxes())
        transform.Translate(0, 0, o)
        self._CursorTransform.GetInput().DeepCopy(transform.GetMatrix())

        center = self.GetCenterCoords()
        for reslice in self._ImageReslice + self._ImageReslice2:
            if reslice:
                reslice.SetResliceAxes(matrix)
        self.SetCenterCoords(center)

    def GetResliceAxes(self):
        """w.GetResliceAxes()  -- get the slice orientation as a vtkMatrix4x4
        """
        return self._ImageReslice[0].GetResliceAxes()

    def SetResliceTransform(self, transform, i=None):
        """w.SetResliceTransform()  -- set a tranform to apply to the image

        The transform can be a linear or nonlinear tranform.  It provides
        the mapping from the output image coordinate system to the input
        coordinate system.
        """
        if i is None:
            for reslice in self._ImageReslice + self._ImageReslice2:
                if reslice:
                    reslice.SetResliceTransform(transform)
        else:
            self._ImageReslice[i].SetResliceTransform(transform)
            self._ImageReslice2[i].SetResliceTransform(transform)

    def GetResliceTransform(self, i=0):
        """w.GetResliceTransform()  -- get the image transformation
        """
        return self._ImageReslice[i].GetResliceTransform()

    def SetLookupTable(self, table, i=0):
        """w.SetLookupTable(table,i=0)  -- specify the lookup table to use
        """
        # don't use subclass' GetLookupTable method
        if ImagePane.GetLookupTable(self, i) == table:
            return
        self._ImageColor[i].SetLookupTable(table)
        self._ImageColor2[i].SetLookupTable(table)
        if table:
            range = table.GetTableRange()
            self._OriginalColorWindow = range[1] - range[0]
            self._OriginalColorLevel = 0.5 * (range[0] + range[1])

    def GetLookupTable(self, i=0):
        """w.GetLookupTable(i=0)  -- get the lookup table for the image
        """
        try:
            return self._ImageColor[i].GetLookupTable()
        except:
            raise ValueError("no image for input " + repr(i))

    def SetOpacity(self, opacity, i=0):
        """w.SetOpacity(opacity,i=0)  -- set opacity for image

        This has no effect for the base image, only for subsequent images
        """
        if i != 0:
            self._ImageBlend.SetOpacity(i, opacity)
            self._ImageActor2[i].SetOpacity(opacity)

    def GetOpacity(self, i=0):
        """w.GetOpacity(i=0)  -- get opacity for image
        """
        return self._ImageBlend.GetOpacity(i)

    def SetActiveComponent(self, j, i=None):
        """w.SetActiveComponent(j,i=None)  -- set component to display

        This has no effect for the base image, only for subsequent images
        """
        if i is None:
            for color in self._ImageColor + self._ImageColor2:
                if color:
                    color.SetActiveComponent(j)
        else:
            self._ImageColor[i].SetActiveComponent(j)
            self._ImageColor2[i].SetActiveComponent(j)

    def GetActiveComponent(self, i=0):
        """w.GetActiveComponent(i=0)  -- get the component that is displayed
        """
        return self._ImageColor[i].GetActiveComponent()

    def GetNumberOfInputs(self):
        """w.GetNumberOfInputs()  -- get current number of images
        """
        return self._ImageBlend.GetNumberOfInputs()

    def AddInput(self, input):
        """w.AddInput(input)  -- add a new input
        """
        self.SetInput(input, self.GetNumberOfInputs())

    def RemoveInput(self, input):
        """w.RemoveInput(input)  -- remove a particular input

        Note that removing an input does not change the numbering
        of the other inputs, it actually just sets this input to None.
        """
        for i in range(self.GetNumberOfInputs()):
            if self.GetInput(i) == input:
                self.SetInput(None, i)
                return
        raise ValueError("RemoveInput: the specified input does not exist")

    def _SetInput(self, input, i=0):
        # don't use subclass' GetInput method
        if input == ImagePane.GetInput(self, i):
            return

        if input is None:
            if i == 0:
                self._ImageReslice[i].SetInput(self.MakeDefaultImage())
                self._ImageReslice2[i].SetInput(self.MakeDefaultImage())
            else:
                self._ImageReslice[i] = None
                self._ImageReslice2[i] = None
                self._ImageColor[i] = None
                self._ImageColor2[i] = None
                self._ImageChangeInformation2[i] = None
                if self._RenderingMode == 1:
                    if self._ImageActor2[i]:
                        self._Renderer.RemoveActor(self._ImageActor2[i])
                self._ImageBlend.SetInput(i, None)
                if len(self._ImageReslice) == \
                        self._ImageBlend.GetNumberOfInputs() + 1:
                    del self._ImageReslice[i]
                    del self._ImageReslice2[i]
                    del self._ImageColor[i]
                    del self._ImageChangeInformation2[i]
                    del self._ImageActor2[i]
            return

        n = self.GetNumberOfInputs()
        if i >= n:
            self._ImageReslice = self._ImageReslice + [None] * (i - n + 1)
            self._ImageReslice2 = self._ImageReslice2 + [None] * (i - n + 1)
            self._ImageColor = self._ImageColor + [None] * (i - n + 1)
            self._ImageColor2 = self._ImageColor2 + [None] * (i - n + 1)
            self._ImageChangeInformation2 = (self._ImageChangeInformation2 +
                                             [None] * (i - n + 1))
            self._ImageActor2 = self._ImageActor2 + [None] * (i - n + 1)

        if self._ImageReslice[i] is None:
            reslice = vtk.vtkImageReslice()
            reslice.SetResliceAxes(self._ImageReslice[0].GetResliceAxes())
            reslice.SetResliceTransform(self._ImageReslice[0].
                                        GetResliceTransform())
            reslice.SetOutputExtent(self._ImageReslice[0].GetOutputExtent())
            reslice.SetOutputSpacing(self._ImageReslice[0].GetOutputSpacing())
            reslice.SetOutputOrigin(self._ImageReslice[0].GetOutputOrigin())
            reslice.SetInterpolationMode(self._ImageReslice[0].
                                         GetInterpolationMode())
            reslice.SetBackgroundLevel(0)
            reslice.SetOptimization(2)
            reslice2 = vtk.vtkImageReslice()
            reslice2.SetInterpolationModeToNearestNeighbor()
            reslice2.SetResliceAxes(self._ImageReslice[0].GetResliceAxes())
            reslice2.SetResliceTransform(self._ImageReslice[0].
                                         GetResliceTransform())
            reslice2.SetBackgroundLevel(0)
            reslice2.SetOptimization(2)

            color = vtk.vtkImageMapToColors()
            color.SetOutputFormatToRGBA()
            color.SetInput(reslice.GetOutput())
            color.AddObserver('ExecuteInformationEvent', self.OnMapToColors)

            color2 = vtk.vtkImageMapToColors()
            color2.SetOutputFormatToRGBA()
            color2.SetInput(reslice2.GetOutput())
            color2.AddObserver('ExecuteInformationEvent', self.OnMapToColors)

            info2 = vtk.vtkImageChangeInformation()
            info2.SetInput(color2.GetOutput())
            origin = info2.GetOutputOrigin()
            info2.SetOutputOrigin(origin[0], origin[1], 0.0)

            actor2 = vtk.vtkImageActor()
            actor2.SetInterpolate(self._InterpolationMode)
            actor2.SetInput(info2.GetOutput())
            if self._Dynamic == 0:
                actor2.SetVisibility(0)

            self._ImageReslice[i] = reslice
            self._ImageReslice2[i] = reslice2
            self._ImageColor[i] = color
            self._ImageColor2[i] = color2
            self._ImageBlend.SetInput(i, color.GetOutput())
            self._ImageChangeInformation2[i] = info2
            self._ImageActor2[i] = actor2

            # make sure actors are in correct order
            if self._RenderingMode == 1:
                for actor in self._ImageActor2:
                    if actor and actor != actor2:
                        self._Renderer.RemoveActor(actor)
                for actor in self._ImageActor2:
                    if actor:
                        self._Renderer.AddActor(actor)

        reslice = self._ImageReslice[i]
        reslice.SetInput(input)
        reslice2 = self._ImageReslice2[i]
        reslice2.SetInput(input)

        """
        # rearrange pipeline as a test
        reslice = self._ImageReslice[i]
        color = self._ImageColor[i]
        color.SetInput(input)
        reslice.SetInput(color.GetOutput())
        self._ImageBlend.SetInput(i,reslice.GetOutput())
        """

    def SetInput(self, input, i=0):
        """w.SetInput(input,i=0)  -- set the vtkImageData to display
        """
        if input == ImagePane.GetInput(self, i):
            return

        self._SetInput(input, i)

        # unless this is the base input, we are done
        if i != 0 or input is None:
            return

        # reset to match the new input if this is the base input
        input.UpdateInformation()
        nspacing = min(map(abs, input.GetSpacing()))
        width, height = self.GetRenderer().GetSize()

        bounds = self.GetTransformedBounds()
        spacing = self.GetTransformedSpacing()

        if width > 0 and height > 0:
            extent = (0, width - 1,
                      0, height - 1,
                      0, 0)
        else:
            extent = (0, int(math.floor((bounds[1] - bounds[0]) / nspacing + 0.5)) - 1,
                      0, int(
                          math.floor((bounds[3] - bounds[2]) / nspacing + 0.5)) - 1,
                      0, 0)

        reslice = self._ImageReslice[i]
        reslice.SetOutputExtent(extent)

        self.SetScale(1.0)
        if (extent[1] - extent[0]) % 2 == 1:
            cx = math.floor(0.5 * (bounds[1] - bounds[0]) / spacing[0]) + 0.5
        else:
            cx = math.floor(0.5 * (bounds[1] - bounds[0]) / spacing[0] + 0.5)
        if (extent[3] - extent[2]) % 2 == 1:
            cy = math.floor(0.5 * (bounds[3] - bounds[2]) / spacing[1]) + 0.5
        else:
            cy = math.floor(0.5 * (bounds[3] - bounds[2]) / spacing[1] + 0.5)
        self._SetCenterPixel((cx, cy))
        if (spacing[2] > 0):
            cz = math.floor(0.5 * (bounds[5] - bounds[4]) / spacing[2] + 0.5)
        else:
            cz = 1
        self._SetSlice(cz)

    def GetInput(self, i=0):
        """w.GetInput(i=0)  -- get image input
        """
        try:
            return self._ImageReslice[i].GetInput()
        except:
            return None

    def GetBlendedOutput(self):
        """w.GetBlendedOutput()  -- get the displayed 2D image
        """
        return self._ImageBlend.GetOutput()

    def GetImageOutput(self, i=0):
        """w.GetImageOutput(i=0)  -- get the output before color mapping
        """
        return self._ImageColor[i].GetInput()

    def GetSliceOutput(self, i=0):
        """w.GetSliceOutput(i=0)  -- get the image slice

        This method provides the image slice that is displayed in the pane.
        Unlike GetImageOutput() it does not provide the interpolated pixels
        as displayed in the pane, but rather provides the full slice at
        the same pixel spacing as in the original 3D image volume.
        """
        return self._ImageReslice2[i].GetOutput()

    def GetCursorTransform(self):
        """w.GetCursorTransform()  -- get the cursor transform

        This transform converts cursor coords to input image coords
        """
        return self._CursorTransform

    def SetRenderingMode(self, mode):
        """w.SetRenderingMode(mode)  -- set rendering mode

        The rendering mode is either 'DrawPixels' or 'Texture'
        """
        oldMode = self._RenderingMode
        self._RenderingMode = self._RenderingModes[mode]
        renderer = self._Renderer
        if oldMode != self._RenderingMode:
            if oldMode == 0:
                renderer.RemoveActor2D(self._Actor2D)
            elif oldMode == 1:
                renderer.RemoveActor(self._ImageActor)
                for actor in self._ImageActor2:
                    if actor:
                        renderer.RemoveActor(actor)
            if self._RenderingMode == 0:
                renderer.AddActor2D(self._Actor2D)
            elif self._RenderingMode == 1:
                renderer.AddActor(self._ImageActor)
                if self._Dynamic:
                    self._ImageActor.SetVisibility(0)
                    for actor in self._ImageActor2:
                        if actor:
                            renderer.AddActor(actor)
                            actor.SetVisibility(1)
                else:
                    self._ImageActor.SetVisibility(1)
                    for actor in self._ImageActor2:
                        if actor:
                            renderer.AddActor(actor)
                            actor.SetVisibility(0)

    def GetRenderingMode(self):
        """w.GetRenderingMode()  -- get the current rendering mode
        """
        for pair in self._RenderingModes.items():
            if pair[1] == self._RenderingMode:
                return pair[0]

    def SetInterpolationMode(self, mode):
        """w.SetInterpolationMode(mode)  -- set static interpolation

        Set the interpolation mode to use for displaying the images:
        'NearestNeighbor', 'Linear', or 'Cubic'
        """
        self._InterpolationMode = self._InterpolationModes[mode]
        for actor in self._ImageActor2:
            if actor:
                actor.SetInterpolate(self._InterpolationMode)
        for reslice in self._ImageReslice:
            if reslice:
                reslice.SetInterpolationMode(self._InterpolationMode)
        if self._InterpolationMode < self._DynamicInterpolationMode:
            self._DynamicInterpolationMode = self._InterpolationMode

    def GetInterpolationMode(self):
        """w.GetInterpolationMode()  -- get the current interpolation mode
        """
        for pair in self._InterpolationModes.items():
            if pair[1] == self._InterpolationMode:
                return pair[0]

    def SetDynamicInterpolationMode(self, mode):
        """w.SetDynamicInterpolationMode(self)  -- set dynamic interpolation

        Set the interpolation mode to use during pan, resize, and slice
        operations.
        """
        self._DynamicInterpolationMode = self._InterpolationModes[mode]

    def GetDynamicInterpolationMode(self):
        """w.GetDynamicInterpolationMode()  -- get the dynamic interpolation
        """
        for pair in self._InterpolationModes.items():
            if pair[1] == self._DynamicInterpolationMode:
                return pair[0]

    def GetImageCoords2D(self, *args):
        """w.GetImageCoords2D(x,y)  -- get 2D image coords for mouse (x,y)

        Get the (x,y) image coordinates that correspond to the specified
        mouse.  These 2D coordinates are related to the 3D image
        coordinates via the ResliceAxes matrix.
        """
        if len(args) == 1:
            dx, dy = args[0]
        else:
            dx, dy = args

        o = self._Renderer.GetOrigin()
        dx = dx - o[0]
        dy = dy - o[1]

        reslice = self._ImageReslice[0]
        spacing = reslice.GetOutputSpacing()
        extent = reslice.GetOutputExtent()
        origin = reslice.GetOutputOrigin()

        x = (dx + extent[0]) * spacing[0] + origin[0]
        y = (dy + extent[2]) * spacing[1] + origin[1]

        return (x, y)

    def GetImageCoords3D(self, *args):
        """w.GetImageCoords3D(x,y)  -- get 3D image coords for mouse (x,y)

        Get the (x,y,z) image coordinates that correspond to the
        specified mouse coordinates.
        """
        if len(args) == 1:
            dx, dy = args[0]
        else:
            dx, dy = args

        o = self._Renderer.GetOrigin()
        dx = dx - o[0]
        dy = dy - o[1]

        reslice = self._ImageReslice[0]
        spacing = reslice.GetOutputSpacing()
        extent = reslice.GetOutputExtent()
        origin = reslice.GetOutputOrigin()

        x = (dx + extent[0]) * spacing[0] + origin[0]
        y = (dy + extent[2]) * spacing[1] + origin[1]
        z = extent[4] * spacing[2] + origin[2]

        x, y, z, w = reslice.GetResliceAxes().MultiplyPoint((x, y, z, 1))

        return (x, y, z)

    def GetImageIndices(self, *args):
        """Get the image i,j,k indices at mouse position (x,y).
        """
        if len(args) == 1:
            dx, dy = args[0][0], args[0][1]
        else:
            dx, dy = args[0], args[1]

        input = self.GetInput()
        spacing = input.GetSpacing()
        origin = input.GetOrigin()

        position = self.GetImageCoords3D(dx, dy)

        indices = ((position[0] - origin[0]) / spacing[0],
                   (position[1] - origin[1]) / spacing[1],
                   (position[2] - origin[2]) / spacing[2])

        return indices

    def GetImageValue(self, *args):
        """w.GetImageValue(x,y)  -- get image value at mouse x,y

        Get the interpolated image data value at mouse position (x,y).
        The current display interpolation mode is used.
        If the image has multiple components, then a tuple is returned.
        """
        if len(args) == 1:
            dx, dy = args[0]
        else:
            dx, dy = args

        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        reslice.UpdateWholeExtent()
        data = reslice.GetOutput()

        n = data.GetNumberOfScalarComponents()
        val = []
        dataType = data.GetScalarType()
        is_float = (dataType == 10 or dataType == 11)
        for i in range(n):
            try:
                c = data.GetScalarComponentAsDouble(extent[0] + dx,
                                                    extent[2] + dy,
                                                    extent[4], i)
            except AttributeError:
                c = data.GetScalarComponentAsFloat(extent[0] + dx,
                                                   extent[2] + dy,
                                                   extent[4], i)

            if not is_float:
                c = int(c)
            val.append(c)
        if len(val) == 1:
            return val[0]
        else:
            return tuple(val)

    def GetTransformedBounds(self, i=0):
        """v.GetTransformedBounds()  -- get permuted bounding box

        Return the Bounds of the input after permuting them through
        the ResliceAxes.  If the reslice axes are oblique, then
        a weighted averaging is done using the direction cosines.
        """
        reslice = self._ImageReslice[i]

        input = reslice.GetInput()
        input.UpdateInformation()
        inSpacing = input.GetSpacing()
        inExtent = input.GetWholeExtent()
        inOrigin = input.GetOrigin()

        inCenter = [0.0, 0.0, 0.0]
        for i in range(3):
            inCenter[i] = inOrigin[i] + \
                0.5 * (inExtent[2 * i] +
                       inExtent[2 * i + 1]) * inSpacing[i]

        matrix = vtk.vtkMatrix4x4()
        rmatrix = reslice.GetResliceAxes()
        if rmatrix is not None:
            matrix.DeepCopy(rmatrix)

        transform = reslice.GetResliceTransform()
        if transform is not None:
            vtk.vtkMatrix4x4().Multiply4x4(
                transform.GetMatrix(), matrix, matrix)
        imatrix = vtk.vtkMatrix4x4()
        imatrix.DeepCopy(matrix)
        imatrix.Invert()

        bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        for i in range(3):
            r = 0.0
            c = 0.0
            d = 0.0
            for j in range(3):
                c = c + imatrix.GetElement(i, j) * (inCenter[j] -
                                                    matrix.GetElement(j, 3))
                tmp = abs(matrix.GetElement(j, i))
                d = d + tmp * abs(inSpacing[j]) * (inExtent[2 * j + 1] -
                                                   inExtent[2 * j])
                r = r + tmp * tmp
            d = d / r
            bounds[2 * i] = c - 0.5 * d
            bounds[2 * i + 1] = c + 0.5 * d

        return tuple(bounds)

    def GetTransformedSpacing(self, i=0):
        """v.GetTransformedSpacing()  -- get permuted voxel spacing

        Return the Spacing of the input after permuting it through
        the ResliceAxes.  If the reslice axes are oblique, then
        a weighted averaging is done using the direction cosines.
        """
        reslice = self._ImageReslice[i]

        input = reslice.GetInput()
        input.UpdateInformation()
        inSpacing = input.GetSpacing()

        matrix = vtk.vtkMatrix4x4()
        rmatrix = reslice.GetResliceAxes()
        if rmatrix is not None:
            matrix.DeepCopy(rmatrix)
        transform = reslice.GetResliceTransform()
        if transform is not None:
            vtk.vtkMatrix4x4().Multiply4x4(
                transform.GetMatrix(), matrix, matrix)

        spacing = [0.0, 0.0, 0.0]
        for i in range(3):
            r = 0.0
            for j in range(3):
                tmp = abs(matrix.GetElement(j, i))
                spacing[i] = spacing[i] + tmp * abs(inSpacing[j])
                r = r + tmp * tmp
            spacing[i] = spacing[i] / r

        return tuple(spacing)

    def Reset(self):
        """w.Reset()  -- reset to centered, 1-to-1 scaling
        """
        xl, xh, yl, yh = self.GetTransformedBounds()[0:4]
        xs, ys = self.GetTransformedSpacing()[0:2]
        self.SyncSetScale(1.0)
        extent = self._ImageReslice[0].GetOutputExtent()
        # if window dimension is odd, use pixel center,
        # else use pixel edge (ensures pixel-pixel match)
        if (extent[1] - extent[0]) % 2 == 1:
            cx = math.floor(0.5 * (xh - xl) / xs) + 0.5
        else:
            cx = math.floor(0.5 * (xh - xl) / xs + 0.5)
        if (extent[3] - extent[2]) % 2 == 1:
            cy = math.floor(0.5 * (yh - yl) / ys) + 0.5
        else:
            cy = math.floor(0.5 * (yh - yl) / ys + 0.5)
        self.SetCenterPixel(cx, cy)
        self.SetSlice(math.floor(self.GetSlice() + 0.5))

    def _ShowCursor(self):
        RenderPane.RenderPane._ShowCursor(self)
        for pane in self._SyncPanes:
            for cursor in pane._Cursors:
                cursor.SetSlaveStatus(pane.GetRenderer(), 1)

    def _HideCursor(self):
        for pane in self._SyncPanes:
            for cursor in pane._Cursors:
                cursor.SetSlaveStatus(pane.GetRenderer(), 0)

        RenderPane.RenderPane._HideCursor(self)

    # TODO: remove this sync stuff and update from latest [sic] Atamai code
    # ++++

    def SetSyncPanes(self, panes):
        """w.SetSyncPanes(panes)  -- set the panes to sync with

        Whenever the zoom/pan/slice of this pane is adjusted, the
        same will be done with all of the panes that this pane is
        synced to.
        """
        self._SyncPanes = panes

    def GetSyncPanes(self):
        """w.GetSyncPanes()  -- get the panes that this pane syncs with
        """
        return self._SyncPanes

    def SetSyncScalePanes(self, panes):
        """w.SetSyncScalePanes(panes)  -- set the panes to sync scale with

        Whenever the scale (i.e. zoom) of this pane is adjusted, the
        same will be done with all of the panes that this pane is
        synced to.
        """
        self._SyncScalePanes = panes

    def GetSyncScalePanes(self):
        """w.GetSyncScalePanes()  -- get the panes that this pane syncs with
        """
        return self._SyncScalePanes

    # TODO: remove this sync stuff ----

    def GetSlice(self):
        """w.GetSlice()  -- return the index of the current slice

        Note that slice numbering starts at 0.  The returned number
        will have a fractional component if the current view is
        an interpolation between two slices.
        """
        reslice = self._ImageReslice[0]

        o = reslice.GetOutputOrigin()[2]
        ol = self.GetTransformedBounds()[4]
        s = self.GetTransformedSpacing()[2]
        if s == 0:
            return 0
        return (o - ol) / s

    def SetSlice(self, i):
        """w.SetSlice(i)  -- set which slice to view

        Note that slice numbering starts at 0.
        """
        self._SetSlice(i)
        centerCoords = self.GetCenterCoords()
        for pane in self._SyncPanes:
            pane.SetCenterCoords(centerCoords)

    def _SetSlice(self, i):
        reslice = self._ImageReslice[0]

        ol, oh = self.GetTransformedBounds()[4:6]
        s = self.GetTransformedSpacing()[2]

        o = ol + s * i

        if self._SliceLimits:
            j = 1  # skip first input of this pane
            for pane in [self] + self._SyncPanes:
                for k in range(j, pane.GetNumberOfInputs()):
                    if pane.GetInput(k):
                        nl, nh = pane.GetTransformedBounds(k)[4:6]
                        if nl < ol:
                            ol = nl
                        if nh > oh:
                            oh = nh
                j = 0

            # restrict slice to within volume bounds
            if o < ol:
                o = ol
            if o > oh:
                o = oh

        # work around numeric precision issue with optimized reslice
        if o != 0.0 and (o == ol or o == oh):
            for reslice in self._ImageReslice:
                if reslice:
                    reslice.OptimizationOff()
        else:
            for reslice in self._ImageReslice:
                if reslice:
                    reslice.OptimizationOn()

        origin = list(reslice.GetOutputOrigin())
        origin[2] = o
        transform = vtk.vtkTransform()
        transform.Concatenate(self.GetResliceAxes())
        transform.Translate(0, 0, o)
        self._CursorTransform.GetInput().DeepCopy(transform.GetMatrix())
        origin = tuple(origin)

        for reslice in self._ImageReslice:
            if reslice:
                reslice.SetOutputOrigin(origin)

        for reslice2 in self._ImageReslice2:
            if reslice2:
                origin = list(reslice2.GetOutputOrigin())
                origin[2] = o
                reslice2.SetOutputOrigin(origin)

        self._UpdateCamera()
        self.Modified()

    def GetCenterPixel(self):
        """w.GetCenterPixel()  -- get the (x,y) indices for the window center

        The pixel indices start at zero.  The returned number
        will have a fractional component if the current view is
        not centered on one of the image pixels.
        """
        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        spacing = reslice.GetOutputSpacing()
        origin = reslice.GetOutputOrigin()
        xc = 0.5 * (extent[0] + extent[1]) * spacing[0] + origin[0]
        yc = 0.5 * (extent[2] + extent[3]) * spacing[1] + origin[1]
        xl, xh, yl, yh = self.GetTransformedBounds()[0:4]
        sx, sy = self.GetTransformedSpacing()[0:2]

        return ((xc - xl) / sx,
                (yc - yl) / sy)

    def SetCenterPixel(self, *args):
        """w.SetCenterPixel(x,y)  -- set (x,y) indices for the window center

        The pixel indices start at zero.
        """
        if len(args) == 1:
            args = args[0]

        self._SetCenterPixel(args)
        centerCoords = self.GetCenterCoords()
        for pane in self._SyncPanes:
            pane.SetCenterCoords(centerCoords)

    def _SetCenterPixel(self, args):
        i, j = args

        xl, xh, yl, yh = self.GetTransformedBounds()[0:4]
        sx, sy = self.GetTransformedSpacing()[0:2]
        xc = xl + sx * i
        yc = yl + sy * j

        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        spacing = reslice.GetOutputSpacing()
        origin = list(reslice.GetOutputOrigin())
        origin[0] = xc - 0.5 * (extent[0] + extent[1]) * spacing[0]
        origin[1] = yc - 0.5 * (extent[2] + extent[3]) * spacing[1]
        origin = tuple(origin)

        for reslice in self._ImageReslice:
            if reslice:
                reslice.SetOutputOrigin(origin)
        self._UpdateCamera()

    def GetScale(self):
        """w.GetScale()  -- get the image magnification factor
        """
        s0 = min(self.GetTransformedSpacing())
        s1 = min(self._ImageReslice[0].GetOutputSpacing())
        # JDG:
        #   This may need to be changed to the lines below
        # s0 = min(self.GetTransformedSpacing()[0:1])
        # s1 = min(self._ImageReslice[0].GetOutputSpacing()[0:1])
        return s0 / s1

    def SetScale(self, s):
        """w.SetScale(s)  -- set the image magnification factor

        This sets the ratio of the smallest of the three voxel
        dimensions to the size of a display pixel.
        """
        newspacing = min(self.GetTransformedSpacing()) / s

        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        spacing = reslice.GetOutputSpacing()
        origin = reslice.GetOutputOrigin()
        center = (0.5 * (extent[0] + extent[1]) * spacing[0] + origin[0],
                  0.5 * (extent[2] + extent[3]) * spacing[1] + origin[1],
                  0.5 * (extent[4] + extent[5]) * spacing[2] + origin[2])

        origin = list(origin)
        for i in range(2):
            origin[i] = center[i] - 0.5 * \
                (extent[2 * i] + extent[2 * i + 1]) * newspacing
        origin = tuple(origin)
        spacing = (newspacing, newspacing, newspacing)

        for reslice in self._ImageReslice:
            if reslice:
                reslice.SetOutputSpacing(spacing)
                reslice.SetOutputOrigin(origin)
        self._UpdateCamera()

    def SyncSetScale(self, s):
        """w.SyncSetScale(s)  -- set scale and synchronize other panes
        """
        self.SetScale(s)
        cs = self.GetCoordScale()
        height = self._Renderer.GetSize()[1]
        for pane in self._SyncScalePanes + self._SyncPanes:
            pheight = pane._Renderer.GetSize()[1]
            f1 = math.floor(1.0 * height / pheight + 0.5)
            f2 = math.floor(1.0 * pheight / height + 0.5)
            if f1 > f2:
                pane.SetCoordScale(cs * f1)
            else:
                pane.SetCoordScale(cs / f2)

    def GetCenterCoords(self):
        """w.GetCenterCoords()  -- return the window center in data coords
        """
        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        spacing = reslice.GetOutputSpacing()
        origin = reslice.GetOutputOrigin()
        x = 0.5 * (extent[0] + extent[1]) * spacing[0] + origin[0]
        y = 0.5 * (extent[2] + extent[3]) * spacing[1] + origin[1]
        z = 0.5 * (extent[4] + extent[5]) * spacing[2] + origin[2]
        x, y, z, w = reslice.GetResliceAxes().MultiplyPoint((x, y, z, 1))

        return (x, y, z)

    def SetCenterCoords(self, *args):
        """w.SetCenterCoords(x,y,z)  -- set the window center in data coords

        This method will reposition the slice view so that the point
        (x,y,z) lies at the center of the window.
        """
        if len(args) == 1:
            args = args[0]
        x, y, z = args

        reslice = self._ImageReslice[0]
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy(reslice.GetResliceAxes())
        matrix.Invert()
        x, y, z, w = matrix.MultiplyPoint((x, y, z, 1))

        bounds = self.GetTransformedBounds()
        spacing = self.GetTransformedSpacing()

        i = (x - bounds[0]) / spacing[0]
        j = (y - bounds[2]) / spacing[1]
        k = (z - bounds[4]) / spacing[2]

        self._SetCenterPixel((i, j))
        self._SetSlice(k)

    def GetCoordScale(self):
        """w.GetCoordScale()  -- return size of screen pixel in data units
        """
        return min(self._ImageReslice[0].GetOutputSpacing())

    def SetCoordScale(self, s):
        """w.SetCoordScale(s)  -- set size of screen pixel in data units

        The screen pixels are assumed to be square.
        """
        self.SetScale(min(self.GetTransformedSpacing()) / s)

    def _UpdateCamera(self):
        """v._UpdateCamera()  -- update camera position

        Update the camera to match the image, so that 3D actors
        will be rendered at the correct location wrt the image
        (this must be called whenever the _ImageReslice is modified)
        """
        camera = self._Camera
        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()
        origin = reslice.GetOutputOrigin()
        spacing = reslice.GetOutputSpacing()
        xc = origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0]
        yc = origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1]
        yd = (extent[3] - extent[2] + 1) * spacing[1]
        d = camera.GetDistance()
        camera.SetParallelScale(0.5 * yd)
        camera.SetFocalPoint(xc, yc, 0.0)
        camera.SetPosition(xc, yc, +d)

        width, height = extent[1] - extent[0], extent[3] - extent[2]
        self._ImageActor.SetDisplayExtent(0, width - 1, 0, height - 1, 0, 0)
        self._ImageChangeInformation.SetOutputOrigin(origin[0], origin[1], 0.0)

        zorigin = origin[2]
        """
        # old code, doesn't work for obliques
        for reslice2 in self._ImageReslice2:
            matrix = vtk.vtkMatrix4x4()
            rmatrix = reslice2.GetResliceAxes()
            if rmatrix is not None:
                matrix.DeepCopy(rmatrix)
            transform = reslice2.GetResliceTransform()
            if transform is not None:
                vtkMatrix4x4.Multiply4x4(transform.GetMatrix(),matrix,matrix)
            imatrix = vtk.vtkMatrix4x4()
            imatrix.DeepCopy(matrix)
            imatrix.Invert()

            input = reslice2.GetInput()
            input.UpdateInformation()
            origin = input.GetOrigin() + (1.0,)
            origin = imatrix.MultiplyDoublePoint(origin)
            spacing = input.GetSpacing() + (0.0,)
            spacing = imatrix.MultiplyDoublePoint(spacing)
            extent = input.GetWholeExtent()

            v = map(abs,matrix.MultiplyDoublePoint((1,0,0,0)))
            i = v.index(max(v))
            v = map(abs,matrix.MultiplyDoublePoint((0,1,0,0)))
            j = v.index(max(v))

            reslice2.SetOutputOrigin(origin[0],origin[1],zorigin)
            reslice2.SetOutputSpacing(spacing[0],spacing[1],spacing[2])
            reslice2.SetOutputExtent(extent[2*i],extent[2*i+1],
                                     extent[2*j],extent[2*j+1],
                                     0,0)
        """
        for i in range(len(self._ImageReslice2)):
            reslice2 = self._ImageReslice2[i]
            if not reslice2:
                continue

            spacing = list(self.GetTransformedSpacing(i))
            bounds = self.GetTransformedBounds(i)
            origin = [bounds[0], bounds[2], zorigin]
            extent = [0, int(math.floor((bounds[1] - bounds[0]) / spacing[0]
                                        + 0.5)),
                      0, int(math.floor((bounds[3] - bounds[2]) / spacing[1]
                                        + 0.5)),
                      0, 0]

            if extent[1] + 1 > 1024:
                size = int(math.ceil((extent[1] + 1) / 1024.0))
                extent[1] = (extent[1] + 1) / size - 1
                spacing[0] = spacing[0] * size

            if extent[3] + 1 > 1024:
                size = int(math.ceil((extent[3] + 1) / 1024.0))
                extent[3] = (extent[3] + 1) / size - 1
                spacing[1] = spacing[1] * size

            reslice2.SetOutputSpacing(spacing)
            reslice2.SetOutputOrigin(origin)
            reslice2.SetOutputExtent(extent)

            self._ImageActor2[i].SetDisplayExtent(extent)

        # adjust the cursor position
        # (this means that for mouse drag events, the DoCursorMotion
        #  method will be called twice, maybe _UpdateCamera should receive
        #  an event as an argument so it can check for Motion?)
        if self._Focus:
            event = EventHandler.Event()
            event.type = '6'
            event.x = self._MouseX
            event.y = self._MouseY
            event.state = 0
            event.renderer = self._Renderer
            self.DoCursorMotion(event)

    def RenderSyncPanes(self):
        windows = [self.GetRenderWindow()]
        for pane in self._SyncPanes:
            window = pane.GetRenderWindow()
            if not window in windows:
                windows.append(window)
        del windows[0]
        for window in windows:
            window.SwapBuffersOff()
        for window in windows:
            window.Render()
            window.SwapBuffersOn()
        for window in windows:
            window.Frame()

    def DoConfigure(self, event):
        width, height = event.width, event.height

        reslice = self._ImageReslice[0]
        extent = reslice.GetOutputExtent()

        old_width = extent[1] - extent[0] + 1
        old_height = extent[3] - extent[2] + 1

        if width == old_width and height == old_height:
            return

        extent = list(extent)
        extent[1] = extent[0] + width - 1
        extent[3] = extent[2] + height - 1
        extent = tuple(extent)

        center = self.GetCenterPixel()
        for reslice in self._ImageReslice:
            if reslice:
                reslice.SetOutputExtent(extent)
        self.SetScale(self.GetScale() / (old_width - 1) * (width - 1))
        self.SetCenterPixel(center)

    def DoStartMotion(self, event):
        self._LastX = event.x
        self._LastY = event.y
        self._StartX = event.x
        self._StartY = event.y

    def DoEndMotion(self, event):
        self._Executing = 1
        self._LastX = event.x
        self._LastY = event.y
        self._Executing = 0

        for pane in self._SyncScalePanes + self._SyncPanes:
            pane.DynamicOff()
        self.DynamicOff()

        cs = self.GetCoordScale()
        height = self._Renderer.GetSize()[1]
        for pane in self._SyncScalePanes + self._SyncPanes:
            pheight = pane._Renderer.GetSize()[1]
            f1 = math.floor(1.0 * height / pheight + 0.5)
            f2 = math.floor(1.0 * pheight / height + 0.5)
            if f1 > f2:
                pane.SetCoordScale(cs * f1)
            else:
                pane.SetCoordScale(cs / f2)

        RenderPane.RenderPane.DoEndMotion(self, event)

    def DoCameraPan(self, event):
        x, y = event.x, event.y

        for pane in self._SyncPanes:
            pane.DynamicOn()
        self.DynamicOn()

        reslice = self._ImageReslice[0]

        xps, yps = self.GetTransformedSpacing()[0:2]
        xds, yds = reslice.GetOutputSpacing()[0:2]
        deltax = (self._LastX - x) * xds / xps
        deltay = (self._LastY - y) * yds / yps

        xc, yc = self.GetCenterPixel()
        self.SetCenterPixel(xc + deltax, yc + deltay)

        self._LastX = x
        self._LastY = y

    def DoPush(self, event):
        x, y = event.x, event.y

        for pane in self._SyncPanes:
            pane.DynamicOn()
        self.DynamicOn()

        reslice = self._ImageReslice[0]

        delta = (y - self._LastY) * (reslice.GetOutputSpacing()[2] /
                                     self.GetTransformedSpacing()[2])

        if self._LastY == self._StartY:
            self._Slice = self.GetSlice()

        self._Slice = self._Slice + delta

        self.SetSlice(int(math.floor(self._Slice + 0.5)))

        self._LastX = x
        self._LastY = y

    def DoCameraZoom(self, event):
        x, y = event.x, event.y

        self.DynamicOn()

        zoomFactor = math.pow(1.02, (0.5 * (self._LastY - y)))
        self.SetScale(self.GetScale() / zoomFactor)

        self._LastX = x
        self._LastY = y

    def DoOblique(self, event):
        x, y = event.x, event.y
        dx = x - self._LastX
        dy = y - self._LastY
        r = math.sqrt(dx ** 2 + dy ** 2)
        if r == 0:
            return
        dx = dx / r
        dy = dy / r

        self._InOblique = 1
        self.DynamicOn()
        self._InOblique = 0

        matrix = self._ImageReslice[0].GetResliceAxes()
        transform = vtk.vtkTransform()
        transform.Concatenate(matrix)
        transform.RotateWXYZ(0.2 * r, dy, dx, 0)
        self.SetResliceAxes(transform.GetMatrix())

        self._LastX = x
        self._LastY = y

    def DoWindowLevel(self, event):
        x, y = event.x, event.y

        table = self.GetLookupTable()
        if not table:
            return
        range = table.GetTableRange()
        window = range[1] - range[0]
        level = 0.5 * (range[0] + range[1])

        owin = self._OriginalColorWindow

        level = level + (x - self._LastX) * owin / 500.0
        window = window + (y - self._LastY) * owin / 250.0

        if window == 0:
            window = 1e-3

        table.SetTableRange(level - window * 0.5,
                            level + window * 0.5)

        self._LastX = x
        self._LastY = y

    def _GetKeyAcceleration(self, event):
        """v._GetKeyAcceleration(event)  -- do keyboard acceleration

        This is an internal method for providing keyboard acceleration:
        the longer you hold a key down, the faster you go, up to a maximum
        of 10X the initial speed.  An acceleration factor of zero means
        that the rendering can't keep up with the KeyPress events,
        so we ignore the KeyPress events until we're ready to render again.
        """
        t = time.time()
        if event.keysym != self._AccelerationKey:
            self._AccelerationKey = event.keysym
            self._AccelerationTime = t
            self._AccelerationFactor = 1.0
            return 1.0

        if (t - self._AccelerationTime < 0.1 or
                t - self._AccelerationTime < self._LastRenderTimeInSeconds + 0.05):
            return 0

        if t - self._AccelerationTime > self._LastRenderTimeInSeconds + 0.2:
            self._AccelerationFactor = 1.0
        elif self._AccelerationFactor < 10:
            self._AccelerationFactor = self._AccelerationFactor * 1.5

        self._AccelerationTime = t
        return self._AccelerationFactor

    def DoCameraPanLeft(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        i, j = self.GetCenterPixel()
        extent = self._ImageReslice[0].GetOutputExtent()
        # is window center at the center or the edge of a pixel?
        if (extent[1] - extent[0]) % 2 == 1:
            i = math.floor(i - accel) + 0.5
        else:
            i = math.floor(i - accel + 0.5)
        self.SetCenterPixel(i, j)

    def DoCameraPanRight(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        i, j = self.GetCenterPixel()
        extent = self._ImageReslice[0].GetOutputExtent()
        # is window center at the center or the edge of a pixel?
        if (extent[1] - extent[0]) % 2 == 1:
            i = math.floor(i + accel) + 0.5
        else:
            i = math.floor(i + accel + 0.5)
        self.SetCenterPixel(i, j)

    def DoCameraPanDown(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        i, j = self.GetCenterPixel()
        extent = self._ImageReslice[0].GetOutputExtent()
        # is window center at the center or the edge of a pixel?
        if (extent[3] - extent[2]) % 2 == 1:
            j = math.floor(j - accel) + 0.5
        else:
            j = math.floor(j - accel + 0.5)
        self.SetCenterPixel(i, j)

    def DoCameraPanUp(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        i, j = self.GetCenterPixel()
        extent = self._ImageReslice[0].GetOutputExtent()
        # is window center at the center or the edge of a pixel?
        if (extent[3] - extent[2]) % 2 == 1:
            j = math.floor(j + accel) + 0.5
        else:
            j = math.floor(j + accel + 0.5)
        self.SetCenterPixel(i, j)

    def DoNextSlice(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        self.SetSlice(math.floor(self.GetSlice() + accel + 0.5))

    def DoPrevSlice(self, event):
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        self.SetSlice(math.floor(self.GetSlice() - accel + 0.5))

    def DoDecreaseLevel(self, event):
        table = self.GetLookupTable()
        if not table:
            return
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        range = table.GetTableRange()
        window = range[1] - range[0]
        level = 0.5 * (range[0] + range[1])
        level = level - accel * self._OriginalColorWindow / 500.0
        table.SetTableRange(level - window * 0.5, level + window * 0.5)
        self.Modified()

    def DoIncreaseLevel(self, event):
        table = self.GetLookupTable()
        if not table:
            return
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        range = table.GetTableRange()
        window = range[1] - range[0]
        level = 0.5 * (range[0] + range[1])
        level = level + accel * self._OriginalColorWindow / 500.0
        table.SetTableRange(level - window * 0.5, level + window * 0.5)
        self.Modified()

    def DoDecreaseWindow(self, event):
        table = self.GetLookupTable()
        if not table:
            return
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        range = table.GetTableRange()
        window = range[1] - range[0]
        level = 0.5 * (range[0] + range[1])
        window = window - accel * self._OriginalColorWindow / 250.0
        table.SetTableRange(level - window * 0.5, level + window * 0.5)
        self.Modified()

    def DoIncreaseWindow(self, event):
        table = self.GetLookupTable()
        if not table:
            return
        accel = self._GetKeyAcceleration(event)
        if accel == 0:
            return

        range = table.GetTableRange()
        window = range[1] - range[0]
        level = 0.5 * (range[0] + range[1])
        window = window + accel * self._OriginalColorWindow / 250.0
        table.SetTableRange(level - window * 0.5, level + window * 0.5)
        self.Modified()

    def DoIncreaseScale(self, event):
        if not self._GetKeyAcceleration(event):
            return

        scale = self.GetScale()
        if scale >= 1:
            scale = math.floor(scale + 0.5) + 1
        else:
            scale = math.floor(1 / scale + 0.5) - 1
            if scale < 1:
                scale = 2.0
            else:
                scale = 1.0 / scale

        self.SyncSetScale(scale)

    def DoDecreaseScale(self, event):
        if not self._GetKeyAcceleration(event):
            return

        scale = self.GetScale()
        if scale >= 1:
            scale = math.floor(scale + 0.5) - 1
            if scale < 1:
                scale = 0.5
        else:
            scale = math.floor(1 / scale + 0.5) + 1
            scale = 1.0 / scale

        self.SyncSetScale(scale)

    def DoReset(self, event):
        self.Reset()

    def DoPrintPixel(self, event):
        print self.GetImageCoords3D(event.x, event.y), \
            self.GetImageCoords2D(event.x, event.y), \
            self.GetImageValue(event.x, event.y)

    def DoSwitchRenderingMode(self, event):
        if self.GetRenderingMode() == 'Texture':
            self.SetRenderingMode('DrawPixels')
        elif self.GetRenderingMode() == 'DrawPixels':
            self.SetRenderingMode('Texture')

    def HasChangedSince(self, sinceMTime):
        if RenderPane.RenderPane.HasChangedSince(self, sinceMTime):
            return 1
        blend = self._ImageBlend
        if blend.GetMTime() > sinceMTime:
            return 1
        for i in range(self.GetNumberOfInputs()):
            reslice = self._ImageReslice[i]
            if reslice:
                if reslice.GetMTime() > sinceMTime:
                    return 1
                input = reslice.GetInput()
                if input and input.GetMTime() > sinceMTime:
                    return 1
            color = self._ImageColor[i]
            if color:
                if color.GetMTime() > sinceMTime:
                    return 1
        return 0

    def HandleEvent(self, event):
        RenderPane.RenderPane.HandleEvent(self, event)

    def HighlightBorder(self, onoff):
        if onoff == 1:
            # light it up
            pass
        elif onoff == 2:
            # turn it off
            pass

    def SetSliceLimits(self, onoff):
        self._SliceLimits = onoff

    def GetSliceLimits(self):
        return self._SliceLimits

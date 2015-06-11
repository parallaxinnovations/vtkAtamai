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
    'module_name': '$RCSfile: IntensityLabel.py,v $',
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
IntensityLabel - a widget that displays the image value under the cursor

  The IntensityLabel is a readout for the intensity of the image voxel
  under the cursor.  Every time that the cursor moves, the
  label will update.

  Before the value is displayed, a linear shift/scale will be applied:

  val = val * *scale* + *shift*

  where the default values are *shift*=0 and *scale*=1.

Public Methods:

  SetCursor(*cursor*)       -- set the cursor to read the position of

  SetTransform(*transform*) -- set a transform to apply before getting
                             the intensity

  SetInput(*image*)         -- set the vtkImageData to get the value of

  SetInterpolate(*i*)     -- set interpolation on/off (default: on)

  GetInterpolate()        -- is interpolation on

  SetShift(*shift*)       -- add this offset to the image values

  SetScale(*scale*)       -- use this scale factor with the image values

"""

from vtkAtamai.Label import *
import vtk

if "FreeType" in vtk.vtkTextMapper().GetClassName():
    _FS = 18
else:
    _FS = 14


class IntensityLabel(Label):

    def __init__(
        self, parent=None, x=0, y=0, width=100, height=27, fontsize=_FS,
            **kw):

        kw["height"] = height
        kw["width"] = width
        kw["x"] = x
        kw["y"] = y
        kw["fontsize"] = fontsize
        kw["font"] = "courier"
        kw["text"] = "0.000"

        apply(Label.__init__, (self, parent), kw)

        self._Cursor = None

        self._Transform = None

        self._Shift = 0.0

        self._Scale = 1.0

        self._Input = None

        self._Reslice = vtk.vtkImageReslice()
        self._Reslice.SetOutputExtent(0, 0, 0, 0, 0, 0)
        self._Reslice.SetInterpolationModeToLinear()

    def SetInterpolate(self, interpolation):
        self._Reslice.SetInterpolate(interpolation)

    def GetInterpolate(self):
        return self._Reslice.GetInterpolate()

    def GetInterpolation(self):
        return self._reslice.GetInterpolation()

    def SetInput(self, input):
        self._Input = input
        self._Reslice.SetInput(input)

    def GetInput(self):
        return self._Input

    def SetShift(self, shift):
        self._Shift = shift

    def GetShift(self):
        return self._Shift

    def SetScale(self, scale):
        self._Scale = scale

    def GetScale(self):
        return self._Scale

    def SetCursor(self, cursor):
        self._Cursor = cursor
        cursor.AddListenerMethod(self._Listen)

    def SetTransform(self, transform):
        self._Transform = transform

    def GetTransform(self):
        return self._Transform

    def _Listen(self, transform):
        # get the position of the cursor
        x, y, z = transform.TransformPoint(0, 0, 0)
        if self._Transform:
            x, y, z = self._Transform.TransformPoint(x, y, z)

        self._Reslice.SetOutputOrigin(x, y, z)
        self._Reslice.GetOutput().SetUpdateExtent(0, 0, 0, 0, 0, 0)
        self._Reslice.GetOutput().Update()

        try:
            val = self._Reslice.GetOutput().GetScalarComponentAsDouble(
                0, 0, 0, 0)
        except AttributeError:
            val = self._Reslice.GetOutput().GetScalarComponentAsFloat(
                0, 0, 0, 0)

        val = val * self._Scale + self._Shift

        # create a formatted string, and set the label
        text = "%#.4g" % (val)
        self.Configure(text=text)

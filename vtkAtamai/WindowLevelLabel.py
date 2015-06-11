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
    'module_name': '$RCSfile: WindowLevelLabel.py,v $',
    'creator': 'Ravi Gupta <rgupta@imaging.robarts.ca>',
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
WindowLevelLabel - a widget that displays the window level and height.


Public Methods:

  SetLookupTable(*table*) -- set the vtk lookup table used

  SetShift(*shift*)       -- add this offset to the image values

  SetScale(*scale*)       -- use this scale factor with the image values

"""

from vtkAtamai import Label
import vtk

if "FreeType" in vtk.vtkTextMapper().GetClassName():
    _FS = 18
else:
    _FS = 14


class WindowLevelLabel(Label.Label):

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

        Label.__init__(self, parent, **kw)

        self._Table = None
        self._Window = None
        self._Level = None
        self._Shift = 0.0
        self._Scale = 1.0

    def SetLookupTable(self, table):
        self._Table = table

    def GetLookupTable(self):
        return self._Table

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

    def _Listen(self, transform):
        min, max = self._Table.GetTableRange()

        self._Window = max - min
        self._Level = (max + min) / 2.0

        # create a formatted string, and set the label
        text = "W %#4g L %#4g" % (self._Window * self._Scale,
                                  self._Level * self._Scale + self._Shift)
        self.Configure(text=text)

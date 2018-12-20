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
    'module_name': '$RCSfile: CoordinateLabel.py,v $',
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
CoordinateLabel - a widget that displays cursor coordinates

  The CoordinateLabel is a readout for the positions of cursors
  and similar things.  Every time that the cursor moves, the
  label will update.

Derived From:

  Label

See Also:

  Widget

Public Methods:

  SetCursor(*cursor*)       -- set the cursor to read the position of

  SetTransform(*transform*) -- set a transform to apply before printing
                               the coordinates

"""
from vtkAtamai.Label import *
import vtk

if "FreeType" in vtk.vtkTextMapper().GetClassName():
    _FS = 18
else:
    _FS = 14


class CoordinateLabel(Label):

    def __init__(
        self, parent=None, x=0, y=0, width=280, height=27, fontsize=_FS,
            **kw):

        kw["height"] = height
        kw["width"] = width
        kw["x"] = x
        kw["y"] = y
        kw["fontsize"] = fontsize
        kw["font"] = "courier"
        kw["text"] = "  0.00R   0.00A   0.00S"

        Label.__init__(*(self, parent), **kw)

        self._Cursor = None

        self._Transform = None

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

        # convert the sign into PA, LR, IS
        xs = 'R'
        ys = 'A'
        zs = 'S'

        if x < 0:
            xs = 'L'
            x = -x
        if y < 0:
            ys = 'P'
            y = -y
        if z < 0:
            zs = 'I'
            z = -z

        # create a formatted string, and set the label
        text = "%6.2f%s %6.2f%s %6.2f%s" % (x, xs, y, ys, z, zs)
        self.Configure(text=text)

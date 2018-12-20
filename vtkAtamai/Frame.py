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

__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: Frame.py,v $',
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
Frame - a Widget for inside a RendePane that contains other Widgets

  The DisplaySize, DisplayOrigin of the Frame are the "inside" of the frame
  if the borderwidth != 0.

Derived From:

  Widget

See Also:

  Button, Label

Initialization:

  Frame(*parent*=None,*borderwidth*=0,*relief*="raised",***kw*)

  *parent*      -- the RenderPane or Frame to put the frame into

  *borderwidth* -- the width of the bevel around the frame

  *relief*      -- "raised" or "sunken"

  ***kw*        -- keywords passed on to Widget

"""

#======================================
from .Widget import *
import vtk

#======================================


class Frame(Widget):

    def __init__(self, parent=None, borderwidth=0, relief='raised', **kw):
        Widget.__init__(*(self, parent), **kw)

        self._Config['borderwidth'] = borderwidth
        self._Config['relief'] = relief

        self._CreateFrame()

        if parent:
            self.ConfigureGeometry(parent.GetDisplayOrigin(),
                                   parent.GetDisplaySize())

        self.BindEvent("<Configure>", self.DoConfigure)

    def DoConfigure(self, event):
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = event.x, event.y

        self._SetPoints()
        self._Actors[0].SetPosition(x - x0, y - y0)

    def _SetPoints(self):
        points = self._Points
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize

        points.SetNumberOfPoints(8)
        points.SetPoint(0, -borderwidth,       -borderwidth,        0)
        points.SetPoint(1, 0,                  0,                   0)
        points.SetPoint(2, width + borderwidth,  -borderwidth,        0)
        points.SetPoint(3, width,              0,                   0)
        points.SetPoint(4, width + borderwidth,  height + borderwidth,  0)
        points.SetPoint(5, width,              height,              0)
        points.SetPoint(6, -borderwidth,       height + borderwidth,  0)
        points.SetPoint(7, 0,                  height,              0)

    def _CreateFrame(self):
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = self._Renderer.GetOrigin()

        self._Points = vtk.vtkPoints()
        self._SetPoints()

        cells = vtk.vtkCellArray()
        if borderwidth > 0:
            cells.InsertNextCell(4)
            cells.InsertCellPoint(0)
            cells.InsertCellPoint(1)
            cells.InsertCellPoint(3)
            cells.InsertCellPoint(2)
            cells.InsertNextCell(4)
            cells.InsertCellPoint(2)
            cells.InsertCellPoint(3)
            cells.InsertCellPoint(5)
            cells.InsertCellPoint(4)
            cells.InsertNextCell(4)
            cells.InsertCellPoint(4)
            cells.InsertCellPoint(5)
            cells.InsertCellPoint(7)
            cells.InsertCellPoint(6)
            cells.InsertNextCell(4)
            cells.InsertCellPoint(6)
            cells.InsertCellPoint(7)
            cells.InsertCellPoint(1)
            cells.InsertCellPoint(0)

        try:  # for VTK 3.x
            scalars = vtk.vtkScalars()
            scalars.SetDataTypeToUnsignedChar()
            if self._Config['relief'] == 'raised':
                scalars.InsertScalar(0, 2)
                scalars.InsertScalar(1, 2)
                scalars.InsertScalar(2, 3)
                scalars.InsertScalar(3, 3)
            else:
                scalars.InsertScalar(0, 3)
                scalars.InsertScalar(1, 3)
                scalars.InsertScalar(2, 2)
                scalars.InsertScalar(3, 2)
        except:
            scalars = vtk.vtkUnsignedCharArray()
            if self._Config['relief'] == 'raised':
                scalars.InsertTuple1(0, 2)
                scalars.InsertTuple1(1, 2)
                scalars.InsertTuple1(2, 3)
                scalars.InsertTuple1(3, 3)
            else:
                scalars.InsertTuple1(0, 3)
                scalars.InsertTuple1(1, 3)
                scalars.InsertTuple1(2, 2)
                scalars.InsertTuple1(3, 2)

        data = vtk.vtkPolyData()
        data.SetPoints(self._Points)
        data.SetPolys(cells)
        data.GetCellData().SetScalars(scalars)

        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInput(data)
        mapper.SetLookupTable(self._LookupTable)
        mapper.SetColorModeToMapScalars()
        mapper.SetScalarRange(0, 3)

        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)
        actor.SetPosition(x - x0, y - y0)

        self._Scalars = scalars
        self._Actors.append(actor)
        if self._Renderer:
            self._Renderer.AddActor2D(actor)

    def IsInWidget(self, event):
        x0, y0 = self._DisplayOrigin
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize
        width = width + 2 * borderwidth
        height = height + 2 * borderwidth

        x = event.x - x0 + borderwidth
        y = event.y - y0 + borderwidth

        return (x >= 0 and y >= 0 and x < width and y < height)

    def ConfigureGeometry(self, position, size):
        # account for the size of the border when doing configuration

        try:
            b = self._Config['borderwidth']
        except KeyError:
            b = 0

        x, y = position
        w, h = size

        Widget.ConfigureGeometry(self, (x + b, y + b), (w - 2 * b, h - 2 * b))

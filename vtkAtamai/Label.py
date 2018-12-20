from __future__ import division
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

from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: Label.py,v $',
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
Label - a widget for displaying text

  The Label is a simple widget for displaying text inside a RenderPane.

Derived From:

  Widget

See Also:

  Frame, Button

Initialization:

  Label(*parent*=None,*x*=<x>,*y*=<y>,*width*=<auto>,*height*=<auto>,*text*="",
        *font*="arial",*fontsize*=15,*bitmap*=None,*borderwidth*=3)

  *parent*      -- the RenderPane or Frame to put the label into

  *x*,*y*       -- the position of the label (manditory)

  *width*,*height* -- the size of the label (will be computed if not supplied)

  *text*          -- the text to display

  *font*          -- one of "Courier", "Arial" or "Times"

  *fontsize*      -- the size of the font, in pixels

  *bitmap*        -- an RGB vtkImageData to display

  *borderwidth*   -- the width of the bevel around the label

-------------------------------------------------------------------------
"""


#======================================
from vtkAtamai.Widget import *
import vtk

#======================================


class Label(Widget):

    def __init__(self, parent=None, text="", fontsize=15, font='arial',
                 borderwidth=0, bitmap=None, **kw):
        if not 'width' in kw:
            kw['width'] = 30 + len(text) * 12
        if not 'height' in kw:
            kw['height'] = 30

        Widget.__init__(*(self, parent), **kw)

        # add to the configuration dictionary
        self._Config['bitmap'] = bitmap
        self._Config['text'] = text
        self._Config['font'] = font
        self._Config['fontsize'] = fontsize
        self._Config['borderwidth'] = borderwidth

        self._CreateLabel()

        self.BindEvent("<Configure>", self.DoConfigure)

    def Configure(self, **kw):
        try:
            self._TextMapper.SetInput(kw['text'])
            self._Config['text'] = kw['text']
            del kw['text']
            self.Modified()
        except:
            pass

    def DoConfigure(self, event):
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = event.x, event.y

        self._SetPoints()
        self._Actors[0].SetPosition(x - x0, y - y0)
        if self._Config['bitmap']:
            self._Actors[1].SetPosition(x - x0, y - y0)
            i = 2
        else:
            i = 1
        mapper = self._Actors[i].GetMapper()
        if "FreeType" in mapper.GetClassName():
            self._Actors[i].SetPosition(x + old_div(width, 2) - x0,
                                        y + old_div(height, 2) - y0)
        else:  # not a FreeType font, needs position correction
            self._Actors[i].SetPosition(x + old_div(width, 2) - x0 + 1,
                                        y + old_div(height, 2) - y0 + 1)
        self.Modified()

    def _SetPoints(self):
        points = self._Points
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize

        points.SetNumberOfPoints(8)
        points.SetPoint(0, 0,                  0,                   0)
        points.SetPoint(1, borderwidth,        borderwidth,         0)
        points.SetPoint(2, width,              0,                   0)
        points.SetPoint(3, width - borderwidth,  borderwidth,         0)
        points.SetPoint(4, width,              height,              0)
        points.SetPoint(5, width - borderwidth,  height - borderwidth,  0)
        points.SetPoint(6, 0,                  height,              0)
        points.SetPoint(7, borderwidth,        height - borderwidth,  0)

    def _CreateLabel(self):
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = self._Renderer.GetOrigin()

        image = self._Config['bitmap']

        # set up the border
        self._Points = vtk.vtkPoints()
        self._SetPoints()

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(4)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(3)
        cells.InsertCellPoint(5)
        cells.InsertCellPoint(7)

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
            scalars.InsertScalar(0, 0)
            scalars.InsertScalar(1, 2)
            scalars.InsertScalar(2, 2)
            scalars.InsertScalar(3, 3)
            scalars.InsertScalar(4, 3)
        except (NameError, AttributeError):
            scalars = vtk.vtkUnsignedCharArray()
            scalars.InsertTuple1(0, 0)
            scalars.InsertTuple1(1, 2)
            scalars.InsertTuple1(2, 2)
            scalars.InsertTuple1(3, 3)
            scalars.InsertTuple1(4, 3)

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

        # if there is a bitmap
        if image:
            image.UpdateInformation()
            extent = image.GetExtent()  # VTK 6
            spacing = image.GetSpacing()
            origin = image.GetOrigin()

            newextent = (0, width - 1 - borderwidth * 2,
                         0, height - 1 - borderwidth * 2,
                         extent[4], extent[5])
            newspacing = (spacing[0] * float(extent[1] - extent[0]) /
                          float(newextent[1] - newextent[0]),
                          spacing[1] * float(extent[3] - extent[2]) /
                          float(newextent[3] - newextent[2]),
                          spacing[2])
            neworigin = (origin[0] + extent[0] * spacing[0] -
                         newextent[0] * newspacing[0],
                         origin[1] + extent[2] * spacing[1] -
                         newextent[2] * newspacing[1],
                         origin[2])

            reslice = vtk.vtkImageReslice()
            reslice.SetInput(image)
            reslice.SetInterpolationModeToCubic()
            reslice.SetOutputExtent(newextent)
            reslice.SetOutputSpacing(newspacing)
            reslice.SetOutputOrigin(neworigin)
            self._BitmapReslice = reslice

            mapper = vtk.vtkImageMapper()
            mapper.SetInput(reslice.GetOutput())
            mapper.SetColorWindow(255.0)
            mapper.SetColorLevel(127.5)

            actor = vtk.vtkActor2D()
            actor.SetMapper(mapper)
            actor.SetPosition(x - x0, y - y0)

            self._Actors.append(actor)
            if self._Renderer:
                self._Renderer.AddActor2D(actor)

        mapper = vtk.vtkTextMapper()
        mapper.SetInput(self._Config['text'])
        try:
            property = mapper.GetTextProperty()
        except AttributeError:
            property = mapper
        property.SetFontSize(self._Config['fontsize'])
        if self._Config['font'] in ('courier', 'Courier'):
            property.SetFontFamilyToCourier()
        elif self._Config['font'] in ('arial', 'Arial'):
            property.SetFontFamilyToArial()
        elif self._Config['font'] in ('times', 'Times'):
            property.SetFontFamilyToTimes()
        property.SetJustificationToCentered()
        property.SetVerticalJustificationToCentered()
        property.BoldOn()
        self._TextMapper = mapper

        actor = vtk.vtkActor2D()
        actor.GetProperty().SetColor(*self._Config['foreground'])
        actor.SetMapper(mapper)
        if "FreeType" in mapper.GetClassName():
            actor.SetPosition(x + old_div(width, 2) - x0,
                              y + old_div(height, 2) - y0)
        else:  # not a FreeType font, needs position correction
            actor.SetPosition(x + old_div(width, 2) - x0 + 1,
                              y + old_div(height, 2) - y0 + 1)

        self._Actors.append(actor)
        if self._Renderer:
            self._Renderer.AddActor2D(actor)

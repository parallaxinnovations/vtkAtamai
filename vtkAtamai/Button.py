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
    'module_name': '$RCSfile: Button.py,v $',
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
Button - a button widget for inside a RenderPane

  Basically, you bind a callback method to the button.  When the button is
  pressed, that method is invoked.

Derived From:

  Widget

See Also:

  Frame, Label

Initialization:

  Button(*parent*=None,*text*="",*command*=None,*borderwidth*=3,***kw*)

  *parent*      -- the RenderPane or Frame to put the button into

  *text*        -- the text within the button

  *fontsize*    -- the size of the font, in pixels

  *command*     -- the callback method

  *borderwidth* -- the width of the bevel around the button

  ***kw*        -- keywords passed on to Widget

  *bitmap*	-- a vtkImage for displaying a bitmap on the button

  *highlight_bitmap* -- a vtkImage for displaying a bitmap on the button,
                        during mouse overs

  *pressed_bitmap*   -- a vtkImage for displaying a bitmap on the button,
                        while any mouse button is pressed on the button

"""


#======================================
from vtkAtamai.Widget import *
import vtk

#======================================


class Button(Widget):

    def __init__(self, parent=None, text="", fontsize=15, font='arial',
                 command=None, bitmap=None, highlight_bitmap=None,
                 pressed_bitmap=None, borderwidth=2, **kw):

        # automatically set up the width and height
        if not ('width' in kw or 'rwidth' in kw):
            kw['width'] = 30 + len(text) * 12
        if not ('height' in kw or 'rheight' in kw):
            kw['height'] = 30

        # call Widget initialization
        apply(Widget.__init__, (self, parent), kw)

        # add a new event type
        EventHandler.EventType["Command"] = '100'

        # add to the configuration dictionary
        self._Config['text'] = text
        self._Config['fontsize'] = fontsize
        self._Config['font'] = font
        self._Config['command'] = command
        self._Config['borderwidth'] = borderwidth
        if bitmap:
            self._Config['bitmap'] = bitmap
        if highlight_bitmap:
            self._Config['highlight_bitmap'] = highlight_bitmap
        if pressed_bitmap:
            self._Config['pressed_bitmap'] = pressed_bitmap

        self._CreateButton()

        self._Pressed = 0
        self._Modifiers = 0

        self.BindEvent("<ButtonPress>", self.DoPress)
        self.BindEvent("<ButtonRelease>", self.DoRelease)
        self.BindEvent("<Enter>", self.DoEnter)
        self.BindEvent("<Leave>", self.DoLeave)
        self.BindEvent("<Configure>", self.DoConfigure)

    def DoRelease(self, event):
        self._Scalars.SetTuple1(1, 2)
        self._Scalars.SetTuple1(2, 2)
        self._Scalars.SetTuple1(3, 3)
        self._Scalars.SetTuple1(4, 3)

        if self.IsInWidget(event) and self._Pressed and \
                self._Pressed == int(event.num):
            if self._Config['command']:
                self._Config['command']()
            e = Event()
            e.type = EventHandler.EventType["Command"]
            e.num = self._Pressed
            e.state = self._Modifiers
            e.keysym = repr(self._Pressed)
            e.x = event.x
            e.y = event.y
            self.HandleEvent(e)

        self._Pressed = 0
        self._Scalars.Modified()
        self.Modified()

    def DoPress(self, event):
        if self._Pressed or not self.IsInWidget(event):
            return
        self._Scalars.SetTuple1(1, 3)
        self._Scalars.SetTuple1(2, 3)
        self._Scalars.SetTuple1(3, 2)
        self._Scalars.SetTuple1(4, 2)
        self._Pressed = int(event.num)
        self._Modifiers = event.state
        self._Scalars.Modified()
        self.Modified()

    def DoEnter(self, event):
        try:  # VTK 3.x
            self._Scalars.SetScalar(0, 1)
        except AttributeError:
            self._Scalars.SetTuple1(0, 1)
        if self._Pressed and event.state & (128 << int(self._Pressed)):
            self._Scalars.SetTuple1(1, 3)
            self._Scalars.SetTuple1(2, 3)
            self._Scalars.SetTuple1(3, 2)
            self._Scalars.SetTuple1(4, 2)
        else:
            self._Pressed = 0
        self._Scalars.Modified()
        self.Modified()

    def DoLeave(self, event):
        self._Scalars.SetTuple1(0, 0)
        self._Scalars.SetTuple1(1, 2)
        self._Scalars.SetTuple1(2, 2)
        self._Scalars.SetTuple1(3, 3)
        self._Scalars.SetTuple1(4, 3)
        self._Scalars.Modified()
        self.Modified()

    def DoConfigure(self, event):
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = event.x, event.y

        self._SetPoints()
        self._Actors[0].SetPosition(x - x0, y - y0)
        mapper = self._Actors[1].GetMapper()
        if "FreeType" in mapper.GetClassName():
            self._Actors[1].SetPosition(x + width / 2 - x0,
                                        y + height / 2 - y0)
        else:  # not a FreeType font, needs position correction
            self._Actors[1].SetPosition(x + width / 2 - x0 + 1,
                                        y + height / 2 - y0 + 1)
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

    def _CreateButton(self):
        borderwidth = self._Config['borderwidth']
        width, height = self._DisplaySize
        x, y = self._DisplayOrigin
        x0, y0 = self._Renderer.GetOrigin()

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
        apply(actor.GetProperty().SetColor, self._Config['foreground'])

        actor.SetMapper(mapper)
        if "FreeType" in mapper.GetClassName():
            actor.SetPosition(x + width / 2 - x0,
                              y + height / 2 - y0)
        else:  # not a FreeType font, needs position correction
            actor.SetPosition(x + width / 2 - x0 + 1,
                              y + height / 2 - y0 + 1)

        self._Actors.append(actor)
        if self._Renderer:
            self._Renderer.AddActor2D(actor)

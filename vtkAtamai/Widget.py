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
    'module_name': '$RCSfile: Widget.py,v $',
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
Widget - base class for widgets that can be placed in a RenderPane

  The Widget class is the base class for buttons, frames, sliders, etc.
  that can be placed within a RenderPane.  Essentially, these are a
  set of widgets implemented completely in python/VTK that are independent
  of the overlying GUI toolkit.

  The difference between these widgets and the usual GUI widgets
  (e.g. Tk or wxWindows buttons) is that they are used inside the RenderPane,
  while other GUI widgets are used outside the RenderPane.  From a VTK
  perspective, a Widget is used for displaying a vtkActor2D just as an
  ActorFactory is used for displaying a vtkActor.

  The position and size of the widgets are specified in display coordinates.
  If x is negative, then the widget is placed relative to the right border of
  the RenderPane.  If width is negative or zero, the width of the widget is
  relative to the width of the RenderPane.  Similar for y and height.

Derived From:

  EventHandler

See Also:

  RenderPane, Frame, Button

Initialization:

  Widget(*parent*=None,*x*=0,*y*=0,*width*=0,*height*=0,
         *background*=(0.75,0.75,0.75),*foreground*=(0.0,0.0,0.0))

  *parent* --  the RenderPane or parent Widget to place this widget inside of

  *x*,*y*  -- (*x*,*y*) location of the Widget in display coords

  *width*,*height* -- width and height in display coords

  *background*   background color, i.e. base color for buttons, frames, etc

  *foreground*   foreground color, i.e. for text and whatnot

Public Methods:

  AddWidget(*widget*)        -- add a child widget to this widget

  RemoveWidget(*widget*)     -- remove a child widget

  GetDisplayOrigin()         -- get position in display coords

  GetDisplaySize()           -- get size in display coords

Used by RenderPane:

  AddToRenderer(*renderer*)      -- add 2D actors to specified renderer

  RemoveFromRenderer(*renderer*) -- remove from renderer

  IsInWidget(*event*)            -- is (*x*,*y*) of event inside this widget

  ConfigureGeometry(*position*,*size*) -- reconfigure the widget, given the
                                    position and size of its parent

Protected Members:

  _Widgets                     -- list of child widgets

  _CurrentWidget               -- the child widget under the mouse

  _FocusWidget                 -- the widget receiving events

  _Renderer                    -- renderer for this widget

  _Actors                      -- the 2D actors inside the renderer

  _Origin                      -- position of widget (can be -ve, see above)

  _Size                        -- size of widget (can be 0 or -ve, see above)

  _Config                      -- dictionary of configuration items

"""

#======================================
from EventHandler import *
import vtk


#======================================
class Widget(EventHandler):

    def __init__(self, parent=None, x=0, y=0, width=0, height=0,
                 rx=0.0, ry=0.0, rwidth=0.0, rheight=0.0,
                 background=(0.75, 0.75, 0.75), foreground=(0.0, 0.0, 0.0)):

        EventHandler.__init__(self)

        # Store the modified time
        self._MTime = vtk.vtkObject()

        # the basic allowed flags
        self._Config = {'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'rx': rx,
                        'ry': ry,
                        'rwidth': rwidth,
                        'rheight': rheight,
                        'background': background,
                        'foreground': foreground}

        # the child widgets of this widget
        self._Widgets = []
        self._CurrentWidget = None
        self._FocusWidget = None

        # the renderer that these widgets are located in
        self._Renderer = None
        self._Actors = []

        # lookup table for shading of bevels
        self._LookupTable = vtk.vtkLookupTable()
        self._LookupTable.SetNumberOfColors(4)
        self._LookupTable.SetTableRange(0, 3)
        self._BuildLookupTable(self._Config['background'])

        if parent:
            parent.AddWidget(self)
            self.ConfigureGeometry(parent.GetDisplayOrigin(),
                                   parent.GetDisplaySize())

    def _BuildLookupTable(self, color):
        # set up bevel shadings for the given color
        alpha = 1.0
        if len(color) > 3:
            alpha = color[3]

        color = list(color[0:3])
        select = map(lambda x: x * 1.10, color)
        shadow = map(lambda x: x * 0.59, color)
        light = map(lambda x: x * 1.15, color)

        colors = (color, select, shadow, light)

        for i in range(4):
            for j in range(3):
                if colors[i][j] > 1.0:
                    colors[i][j] = 1.0
            apply(self._LookupTable.SetTableValue, [i] + colors[i] + [alpha])

    #--------------------------------------
    def HasChangedSince(self, sinceMTime):
        # recursively check modified times
        if self._MTime.GetMTime() > sinceMTime:
            return 1
        for widget in self._Widgets:
            if widget.HasChangedSince(sinceMTime):
                return 1
        return 0

    def Modified(self):
        self._MTime.Modified()

    #--------------------------------------
    def AddWidget(self, widget):
        self._Widgets.append(widget)
        if self._Renderer:
            widget.AddToRenderer(self._Renderer)
        self.Modified()

    def RemoveWidget(self, widget):
        if self._Renderer:
            widget.RemoveFromRenderer(self._Render)
        self._Widgets.remove(widget)
        self.Modified()

    #--------------------------------------
    def HandleEvent(self, event):
        # for debug purposes
        # self.PrintEvent(event)

        # if there are no child widgets, no special
        # actions are required
        if not self._Widgets:
            return EventHandler.HandleEvent(self, event)

        # pass configure events to all widgets
        if event.type == '22':  # <Configure>
            for widget in self._Widgets:
                widget.ConfigureGeometry(self._DisplayOrigin,
                                         self._DisplaySize)
                widget.HandleEvent(event)
            return EventHandler.HandleEvent(self, event)

        # set current widget to the one under the mouse
        if event.type in ('4', '5', '6', '7', '8'):
            for widget in self._Widgets:
                if widget.IsInWidget(event):
                    newCurrentWidget = widget
                    break
            else:  # or None if not over any widget
                newCurrentWidget = None

            # check to see if the focus should be changed
            if (newCurrentWidget != self._FocusWidget and
                ((event.type == '6' and event.state & 0x1f00 == 0) or
                 (event.type == '5' and
                  event.state & 0x1f00 & ~(0x80 << event.num) == 0))):
                newFocusWidget = newCurrentWidget
            else:
                newFocusWidget = self._FocusWidget

            # check to see if we left the FocusWidget
            if ((self._CurrentWidget == self._FocusWidget and
                 self._CurrentWidget != newCurrentWidget) or
                    self._FocusWidget != newFocusWidget):
                if self._FocusWidget:
                    # make a copy of the current event
                    e = Event()
                    for attr in dir(event):
                        setattr(e, attr, getattr(event, attr))
                    # but change the type to 'Leave'
                    e.type = '8'  # 'Leave'
                    # and pass to the widget
                    self._FocusWidget.HandleEvent(e)

            # check to see if we entered the new FocusWidget
            if ((newCurrentWidget == self._FocusWidget and
                 self._CurrentWidget != newCurrentWidget) or
                    self._FocusWidget != newFocusWidget):
                if newFocusWidget:
                    # make a copy of the current event
                    e = Event()
                    for attr in dir(event):
                        setattr(e, attr, getattr(event, attr))
                    # but change the type to 'Enter'
                    e.type = '7'  # 'Enter'
                    # and pass to the widget
                    newFocusWidget.HandleEvent(e)

            self._FocusWidget = newFocusWidget
            self._CurrentWidget = newCurrentWidget

        # pass the event to the widget that has the focus
        if (self._FocusWidget and
                not event.type in ('7', '8')):  # 'Enter','Leave'
            return self._FocusWidget.HandleEvent(event)
        else:
            return EventHandler.HandleEvent(self, event)

    #--------------------------------------
    def IsInWidget(self, event):
        # is the event within the bounds of the widget?
        x0, y0 = self._DisplayOrigin
        width, height = self._DisplaySize

        x = event.x - x0
        y = event.y - y0

        return (x >= 0 and y >= 0 and x < width and y < height)

    #--------------------------------------
    def AddToRenderer(self, renderer):
        self._Renderer = renderer
        for actor in self._Actors:
            renderer.AddActor2D(actor)
        for widget in self._Widgets:
            widget.AddToRenderer(renderer)

    def RemoveFromRenderer(self, renderer):
        for widget in self._Widgets:
            widget.RemoveFromRenderer(renderer)
        for actor in self._Actors:
            renderer.RemoveActor2D(actor)
        self._Renderer = None

    #--------------------------------------
    def GetDisplayOrigin(self):
        return self._DisplayOrigin

    def GetDisplaySize(self):
        return self._DisplaySize

    #--------------------------------------
    def ConfigureGeometry(self, position, size):
        # the parent or renderer calls this when the dimensions/position
        # of the parent change
        x, y = (self._Config['x'], self._Config['y'])
        w, h = (self._Config['width'], self._Config['height'])
        rx, ry = (self._Config['rx'], self._Config['ry'])
        rw, rh = (self._Config['rwidth'], self._Config['rheight'])
        x0, y0 = position
        w0, h0 = size

        if x < 0 and rx == 0.0:
            rx = 1.0

        if y < 0 and ry == 0.0:
            ry = 1.0

        if w <= 0 and rw == 0.0:
            rw = 1.0

        if h <= 0 and rh == 0.0:
            rh = 1.0

        # the 'int' stuff is to keep the rounding consistent,
        #  otherwise there might be gaps left between relatively-placed
        #  widgets due to roundoff errors
        w = int(x + w0 * rx + w + w0 * rw) - int(x + w0 * rx)
        x = int(x + w0 * rx)
        h = int(y + h0 * ry + h + h0 * rh) - int(y + h0 * ry)
        y = int(y + h0 * ry)

        self._ParentOrigin = position
        self._ParentSize = size
        self._DisplayOrigin = (x + x0, y + y0)
        self._DisplaySize = (w, h)

    #--------------------------------------
    def Configure(self, **kw):
        keys = kw.keys()

        for key in keys:
            # throw an exception if key doesn't exist
            self._Config[key]
            # otherwise set the entry from arg list
            self._Config[key] = kw[key]

        if ('x' in keys or 'y' in keys or 'width' in keys or 'height' in keys
            or 'rx' in keys or 'ry' in keys or 'rwidth' in keys or 'rheight'
                in keys):
            self.ConfigureGeometry(self._ParentOrigin, self._ParentSize)

        self.Modified()

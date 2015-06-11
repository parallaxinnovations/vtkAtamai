# =========================================================================
#
# Copyright (c) 2000 Atamai, Inc.
# Copyright (c) 2011-2015 Parallax Innovations Inc.
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

"""
wxPaneFrame - a PaneFrame that is also a wxWindow

  This class allows RenderPane to be used with wxPython.  It
  requires the wxGLCanvas that comes with wxWindows.  Copies
  of wxPython are available from http://wxpython.org.

  You are recommended to use the latest stable release of
  wxWindows.  Development releases are unlikely to work
  properly, since this class taxes wxWindows very heavily.

Derived From:

  RenderPane, wxWindow

"""

#======================================
import wx
import vtk
import PaneFrame
from EventHandler import Event
baseClass = wx.Window

# a few configuration items, see what works best on your system

# under UNIX the wxWindow has erase/redraw problems, so use
# the wxGLCanvas instead
if wx.Platform != '__WXMSW__':
    import wx.glcanvas
    baseClass = wx.glcanvas.GLCanvas

# Keep capturing mouse after mouse is dragged out of window
# (in wxGTK 2.3.2 there is a bug that keeps this from working,
# but it is only relevant in wxGTK if there are multiple windows)
_useCapture = (wx.Platform == "__WXMSW__")


class EventTimer(wx.Timer):

    """Simple wx.Timer class.
    """

    def __init__(self, func):
        """Default class constructor.
        @param iren: current render window
        """
        wx.Timer.__init__(self)
        self.func = func

    def Notify(self):
        """ The timer has expired.
        """
        self.func()


#======================================
class wxPaneFrame(PaneFrame.PaneFrame, baseClass):

    # convert event types
    EvtType = {
        wx.EVT_CHAR.typeId: '2',
        wx.EVT_KEY_DOWN.typeId: '2',
        wx.EVT_KEY_UP.typeId: '3',
        wx.EVT_MOUSEWHEEL.typeId: '4',
        wx.EVT_LEFT_DCLICK.typeId: '4',
        wx.EVT_MIDDLE_DCLICK.typeId: '4',
        wx.EVT_RIGHT_DCLICK.typeId: '4',
        wx.EVT_LEFT_DOWN.typeId: '4',
        wx.EVT_MIDDLE_DOWN.typeId: '4',
        wx.EVT_RIGHT_DOWN.typeId: '4',
        wx.EVT_LEFT_UP.typeId: '5',
        wx.EVT_MIDDLE_UP.typeId: '5',
        wx.EVT_RIGHT_UP.typeId: '5',
        wx.EVT_MOTION.typeId: '6',
        wx.EVT_ENTER_WINDOW.typeId: '7',
        wx.EVT_LEAVE_WINDOW.typeId: '8',
        wx.EVT_SET_FOCUS.typeId: '9',
        wx.EVT_KILL_FOCUS.typeId: '10',
        wx.EVT_MOVE.typeId: '22',
        wx.EVT_SIZE.typeId: '22',
    }

    # convert ascii or wx.KeyCode<128 to X-Window style keysym
    KeySym = [
        "??", "??", "??", "??", "??", "??", "??", "??",
        "BackSpace", "Tab", "??", "??", "??", "Return", "??", "??",
        "??", "??", "??", "??", "??", "??", "??", "??",
        "??", "??", "??", "Escape", "??", "??", "??", "??",
        "space", "exclam", "quotedbl", "numbersign",
        "dollar", "percent", "ampersand", "quoteright",
        "parenleft", "parenright", "asterisk", "plus",
        "comma", "minus", "period", "slash",
        "0", "1", "2", "3", "4", "5", "6", "7",
        "8", "9", "colon", "semicolon",
        "less", "equal", "greater", "question",
        "at", "A", "B", "C", "D", "E", "F", "G",
        "H", "I", "J", "K", "L", "M", "N", "O",
        "P", "Q", "R", "S", "T", "U", "V", "W",
        "X", "Y", "Z", "bracketleft",
        "backslash", "bracketright", "asciicircum", "underscore",
        "quoteleft", "a", "b", "c", "d", "e", "f", "g",
        "h", "i", "j", "k", "l", "m", "n", "o",
        "p", "q", "r", "s", "t", "u", "v", "w",
        "x", "y", "z", "braceleft",
        "bar", "braceright", "asciitilde", "Delete"
    ]

    # virtual keycode to ascii for keycodes >= 300
    KeyCharFromCode = {
        wx.WXK_NUMPAD0: '0',
        wx.WXK_NUMPAD1: '1',
        wx.WXK_NUMPAD2: '2',
        wx.WXK_NUMPAD3: '3',
        wx.WXK_NUMPAD4: '4',
        wx.WXK_NUMPAD5: '5',
        wx.WXK_NUMPAD6: '6',
        wx.WXK_NUMPAD7: '7',
        wx.WXK_NUMPAD8: '8',
        wx.WXK_NUMPAD9: '9',
        wx.WXK_MULTIPLY: '*',
        wx.WXK_ADD: '+',
        wx.WXK_SEPARATOR: ',',
        wx.WXK_SUBTRACT: '-',
        wx.WXK_DECIMAL: '.',
        wx.WXK_DIVIDE: '/',
        # the following might only be true for Linux
        370: ' ',
        371: '\t',
        372: '\n',
        389: '\177',
        390: '=',
        391: '*',
        392: '+',
        393: ',',
        394: '-',
        395: '.',
        396: '/',
    }

    # virtual keycode to keysym for keycodes >= 300
    KeySymFromCode = {
        wx.WXK_START: "Begin",
        wx.WXK_LBUTTON: "??",
        wx.WXK_RBUTTON: "??",
        wx.WXK_CANCEL: "Cancel",
        wx.WXK_MBUTTON: "??",
        wx.WXK_CLEAR: "Clear",
        wx.WXK_SHIFT: "Shift_L",
        307: "Alt_L",
        wx.WXK_CONTROL: "Control_L",
        wx.WXK_MENU: "Menu",

        wx.WXK_PAUSE: "Pause",
        wx.WXK_CAPITAL: "Caps_Lock",
        wx.WXK_PRIOR: "Prior",
        wx.WXK_NEXT: "Next",
        wx.WXK_END: "End",
        wx.WXK_HOME: "Home",
        wx.WXK_LEFT: "Left",
        wx.WXK_UP: "Up",
        wx.WXK_RIGHT: "Right",
        wx.WXK_DOWN: "Down",

        wx.WXK_SELECT: "Select",
        wx.WXK_PRINT: "Print",
        wx.WXK_EXECUTE: "Execute",
        wx.WXK_SNAPSHOT: "Sys_Req",
        wx.WXK_INSERT: "Insert",
        wx.WXK_HELP: "Help",
        wx.WXK_NUMPAD0: "KP_0",
        wx.WXK_NUMPAD1: "KP_1",
        wx.WXK_NUMPAD2: "KP_2",
        wx.WXK_NUMPAD3: "KP_3",

        wx.WXK_NUMPAD4: "KP_4",
        wx.WXK_NUMPAD5: "KP_5",
        wx.WXK_NUMPAD6: "KP_6",
        wx.WXK_NUMPAD7: "KP_7",
        wx.WXK_NUMPAD8: "KP_8",
        wx.WXK_NUMPAD9: "KP_9",
        wx.WXK_MULTIPLY: "KP_Multiply",
        wx.WXK_ADD: "KP_Add",
        wx.WXK_SEPARATOR: "KP_Separator",
        wx.WXK_SUBTRACT: "KP_Subtract",

        wx.WXK_DECIMAL: "KP_Decimal",
        wx.WXK_DIVIDE: "KP_Divide",
        wx.WXK_F1: "F1",
        wx.WXK_F2: "F2",
        wx.WXK_F3: "F3",
        wx.WXK_F4: "F4",
        wx.WXK_F5: "F5",
        wx.WXK_F6: "F6",
        wx.WXK_F7: "F7",
        wx.WXK_F8: "F8",

        wx.WXK_F9: "F9",
        wx.WXK_F10: "F10",
        wx.WXK_F11: "F11",
        wx.WXK_F12: "F12",
        wx.WXK_F13: "F13",
        wx.WXK_F14: "F14",
        wx.WXK_F15: "F15",
        wx.WXK_F16: "F16",
        wx.WXK_F17: "F17",
        wx.WXK_F18: "F18",

        wx.WXK_F19: "F19",
        wx.WXK_F20: "F20",
        wx.WXK_F21: "F21",
        wx.WXK_F22: "F22",
        wx.WXK_F23: "F23",
        wx.WXK_F24: "F24",
        wx.WXK_NUMLOCK: "Num_Lock",
        wx.WXK_SCROLL: "Scroll_Lock",
        wx.WXK_PAGEUP: "Prior",
        wx.WXK_PAGEDOWN: "Next",

        # these might only be valid under Linux
        370: "KP_Space",
        371: "KP_Tab",
        372: "KP_Enter",
        373: "KP_F1",
        374: "KP_F2",
        375: "KP_F3",
        376: "KP_F4",
        377: "KP_Home",
        378: "KP_Left",
        379: "KP_Up",

        380: "KP_Right",
        381: "KP_Down",
        382: "KP_Prior",
        384: "KP_Next",
        386: "KP_End",
        387: "KP_Begin",
        388: "KP_Insert",
        389: "KP_Delete",

        390: "KP_Equal",
        391: "KP_Multiply",
        392: "KP_Add",
        393: "KP_Separator",
        394: "KP_Subtract",
        395: "KP_Decimal",
        396: "KP_Divide",

    }

    def tearDown(self):
        PaneFrame.PaneFrame.tearDown(self)
        self.Unbind(wx.EVT_PAINT)
        self.Unbind(wx.EVT_ERASE_BACKGROUND)
        self.Unbind(wx.EVT_RIGHT_DOWN)
        self.Unbind(wx.EVT_LEFT_DOWN)
        self.Unbind(wx.EVT_MIDDLE_DOWN)
        self.Unbind(wx.EVT_RIGHT_UP)
        self.Unbind(wx.EVT_LEFT_UP)
        self.Unbind(wx.EVT_MIDDLE_UP)
        self.Unbind(wx.EVT_RIGHT_DCLICK)
        self.Unbind(wx.EVT_LEFT_DCLICK)
        self.Unbind(wx.EVT_MIDDLE_DCLICK)
        self.Unbind(wx.EVT_MOUSEWHEEL)
        self.Unbind(wx.EVT_MOTION)
        self.Unbind(wx.EVT_ENTER_WINDOW)
        self.Unbind(wx.EVT_LEAVE_WINDOW)
        self.Unbind(wx.EVT_CHAR)
        self.Unbind(wx.EVT_KEY_UP)
        self.Unbind(wx.EVT_SIZE)
        if _useCapture and hasattr(wx, 'EVT_MOUSE_CAPTURE_LOST'):
            self.Unbind(wx.EVT_MOUSE_CAPTURE_LOST)
        self.cancelTimers()

    def Freeze2(self):
        self.__is_frozen = True

    def Thaw2(self):
        self.__is_frozen = False

    def isFrozen2(self):
        return self.__is_frozen

    def __init__(self, parent=None, ID=-1, *args, **kw):

        # First do special handling of some keywords:
        # stereo, position, size, width, height, style

        stereo = 0

        self._last_mouse_pos = None
        self.__is_frozen = False

        if 'stereo' in kw:
            if kw['stereo']:
                stereo = 1
            del kw['stereo']

        position = wx.DefaultPosition

        if 'position' in kw:
            position = kw['position']
            del kw['position']

        size = wx.DefaultSize

        if 'size' in kw:
            size = kw['size']
            if not isinstance(size, wx.Size):
                size = apply(wx.Size, size)
            del kw['size']

        if 'width' in kw and 'height' in kw:
            size = wx.Size(kw['width'], kw['height'])
            del kw['width']
            del kw['height']

        # wx.WANTS_CHARS says to give us e.g. TAB
        # wx.NO_FULL_REPAINT_ON_RESIZE cuts down resize flicker under GTK
        style = wx.WANTS_CHARS | wx.NO_FULL_REPAINT_ON_RESIZE

        if 'style' in kw:
            style = style | kw['style']
            del kw['style']

        # if there is no parent, make a frame window
        if parent is None:
            parent = wx.Frame(None, -1, "wxRenderWindow", position, size)
            parent.Show(1)
            self._wxFrame = parent

        # initialize the wxWindow -- take care here to ensure double-buffering is
        # enabled under Linux
        if wx.Platform != '__WXMSW__':
            attribList = [
                wx.glcanvas.WX_GL_RGBA,
                wx.glcanvas.WX_GL_DOUBLEBUFFER,
                wx.glcanvas.WX_GL_DEPTH_SIZE, 16
            ]
            baseClass.__init__(
                self, parent, id=ID, pos=position, size=size, style=style, attribList=attribList)
        else:
            baseClass.__init__(self, parent, ID, position, size, style)

        # create the RenderWindow and initialize it
        self._RenderWindow = vtk.vtkRenderWindow()

        self.__Created = 0

        # create the RenderWindow and initialize it
        self._RenderWindowInteractor = vtk.vtkGenericRenderWindowInteractor()
        self._RenderWindowInteractor.SetRenderWindow(self._RenderWindow)
        self._RenderWindowInteractor.GetRenderWindow(
        ).AddObserver('CursorChangedEvent',
                      self.CursorChangedEvent)

        try:
            self._RenderWindowInteractor.GetRenderWindow().SetSize(
                size.width, size.height)
        except AttributeError:
            self._RenderWindowInteractor.GetRenderWindow().SetSize(
                size[0], size[1])

        if stereo:
            self._RenderWindowInteractor.GetRenderWindow(
            ).StereoCapableWindowOn()
            self._RenderWindowInteractor.GetRenderWindow(
            ).SetStereoTypeToCrystalEyes()

        # The superclass can't be initialized until _RenderWindow
        # has been declared.
        PaneFrame.PaneFrame.__init__(self)

        self.__handle = None
        self.__has_painted = False
        self.__is_mapped = False
        self._own_mouse = False
        self._mouse_capture_button = 0
        self._cursor_map = {0: wx.CURSOR_ARROW,  # VTK_CURSOR_DEFAULT
                            1: wx.CURSOR_ARROW,  # VTK_CURSOR_ARROW
                            2: wx.CURSOR_SIZENESW,  # VTK_CURSOR_SIZENE
                            3: wx.CURSOR_SIZENWSE,  # VTK_CURSOR_SIZENWSE
                            4: wx.CURSOR_SIZENESW,  # VTK_CURSOR_SIZESW
                            5: wx.CURSOR_SIZENWSE,  # VTK_CURSOR_SIZESE
                            6: wx.CURSOR_SIZENS,  # VTK_CURSOR_SIZENS
                            7: wx.CURSOR_SIZEWE,  # VTK_CURSOR_SIZEWE
                            8: wx.CURSOR_SIZING,  # VTK_CURSOR_SIZEALL
                            9: wx.CURSOR_HAND,  # VTK_CURSOR_HAND
                            10: wx.CURSOR_CROSS,  # VTK_CURSOR_CROSSHAIR
                            }

        # private variable for better Enter/Leave handling
        self.__ActiveButton = 0
        self.__SaveState = 0
        self._Inside = 0

        # refresh window by doing a Render
        wx.EVT_PAINT(self, self.OnPaint)

        # turn off background erase to reduce flicker
        wx.EVT_ERASE_BACKGROUND(self, lambda e: None)

        # Bind the events to the event converters
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnButtonDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnButtonDown)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnButtonDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnButtonUp)
        self.Bind(wx.EVT_LEFT_UP, self.OnButtonUp)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnButtonUp)

        # double click events
        self.Bind(wx.EVT_RIGHT_DCLICK, self.OnButtonDClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnButtonDClick)
        self.Bind(wx.EVT_MIDDLE_DCLICK, self.OnButtonDClick)

        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.EVT_MOTION, self.OnMotion)

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

        # If we use EVT_KEY_DOWN instead of EVT_CHAR, capital versions
        # of all characters are always returned.  EVT_CHAR also performs
        # other necessary keyboard-dependent translations.
        self.Bind(wx.EVT_CHAR, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self.Bind(wx.EVT_SIZE, self.OnSize)

        # the wx 2.8.7.1 documentation states that you HAVE to handle
        # this event if you make use of CaptureMouse, which we do.
        if _useCapture and hasattr(wx, 'EVT_MOUSE_CAPTURE_LOST'):
            self.Bind(wx.EVT_MOUSE_CAPTURE_LOST,
                      self.OnMouseCaptureLost)

        # pretend that we're a base window - let atamai help us out
        self._BindInteractor()

        # debug debug debug
        return

        # Bind the events to the event converters
        wx.EVT_MOUSE_EVENTS(self, self.ConvertMouseEvent)
        wx.EVT_KEY_DOWN(self, self.ConvertKeyEvent)
        wx.EVT_KEY_UP(self, self.ConvertKeyEvent)
        wx.EVT_SIZE(self, self.ConvertSizeEvent)
        # wx.EVT_MOVE(self, self.ConvertMoveEvent)
        wx.EVT_SET_FOCUS(self, self.ConvertFocusEvent)
        wx.EVT_KILL_FOCUS(self, self.ConvertFocusEvent)

    def ScheduleEvery(self, millisecs, func):
        # schedule the specified function to be called each time the
        # specified number of milliseconds has elapsed

        timer = EventTimer(func)
        timer.Start(millisecs, False)
        return timer

    def _CursorChangedEvent(self, obj, evt):
        """Change the wx cursor if the renderwindow's cursor was
        changed.
        """
        cur = self._cursor_map[obj.GetCurrentCursor()]
        c = wx.StockCursor(cur)
        self.SetCursor(c)

    def CursorChangedEvent(self, obj, evt):
        """Called when the CursorChangedEvent fires on the render
        window."""
        # This indirection is needed since when the event fires, the
        # current cursor is not yet set so we defer this by which time
        # the current cursor should have been set.
        wx.CallAfter(self._CursorChangedEvent, obj, evt)

    def HideCursor(self):
        """Hides the cursor."""
        c = wx.StockCursor(wx.CURSOR_BLANK)
        self.SetCursor(c)

    def ShowCursor(self):
        """Shows the cursor."""
        rw = self._RenderWindowInteractor.GetRenderWindow()
        cur = self._cursor_map[rw.GetCurrentCursor()]
        c = wx.StockCursor(cur)
        self.SetCursor(c)

    def OnSize(self, event):
        """Handles the wx.EVT_SIZE event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue (we call this before the
        # Render(), in case it raises an exception)
        event.Skip()

        try:
            width, height = event.GetSize()
        except:
            width = event.GetSize().width
            height = event.GetSize().height
        self._RenderWindowInteractor.SetSize(width, height)
        self._RenderWindowInteractor.ConfigureEvent()

        # this will check for __handle
        self.Render()

    def cancelTimers(self):
        # make sure timers get cancelled
        if self._QualityRenderId != -1:
            self._QualityRenderId.Destroy()
            self._QualityRenderId = -1

    def OnButtonDClick(self, event):

        event.Skip()

        ctrl, shift = event.ControlDown(), event.ShiftDown()
        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            ctrl, shift, chr(0), 1, None)

        button = 0
        if event.RightDClick():
            self._RenderWindowInteractor.RightButtonPressEvent()
            button = 'Right'
        elif event.LeftDClick():
            self._RenderWindowInteractor.LeftButtonPressEvent()
            button = 'Left'
        elif event.MiddleDClick():
            self._RenderWindowInteractor.MiddleButtonPressEvent()
            button = 'Middle'

        # save the button and capture mouse until the button is released
        # we only capture the mouse if it hasn't already been captured
        if _useCapture and not self._own_mouse:
            self._own_mouse = True
            self._mouse_capture_button = button
            self.CaptureMouse()

    def OnButtonDown(self, event):
        """Handles the wx.EVT_LEFT/RIGHT/MIDDLE_DOWN events for
        wxVTKRenderWindowInteractor.
        """

        # allow wx event processing to continue
        # on wxPython 2.6.0.1, omitting this will cause problems with
        # the initial focus, resulting in the wxVTKRWI ignoring keypresses
        # until we focus elsewhere and then refocus the wxVTKRWI frame
        # we do it this early in case any of the following VTK code
        # raises an exception.

        # JDG
        self._RenderWindow.SetDesiredUpdateRate(5)
        event.Skip()

        ctrl, shift = event.ControlDown(), event.ShiftDown()
        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            ctrl, shift, chr(0), 0, None)

        button = 0
        if event.RightDown():
            self._RenderWindowInteractor.RightButtonPressEvent()
            button = 'Right'
        elif event.LeftDown():
            self._RenderWindowInteractor.LeftButtonPressEvent()
            button = 'Left'
        elif event.MiddleDown():
            self._RenderWindowInteractor.MiddleButtonPressEvent()
            button = 'Middle'

        # save the button and capture mouse until the button is released
        # we only capture the mouse if it hasn't already been captured
        if _useCapture and not self._own_mouse:
            self._own_mouse = True
            self._mouse_capture_button = button
            self.CaptureMouse()

    def OnButtonUp(self, event):
        """Handles the wx.EVT_LEFT/RIGHT/MIDDLE_UP events for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue
        event.Skip()

        button = 0
        if event.RightUp():
            button = 'Right'
        elif event.LeftUp():
            button = 'Left'
        elif event.MiddleUp():
            button = 'Middle'

        # if the same button is released that captured the mouse, and
        # we have the mouse, release it.
        # (we need to get rid of this as soon as possible; if we don't
        #  and one of the event handlers raises an exception, mouse
        #  is never released.)
        if _useCapture and self._own_mouse and \
                button == self._mouse_capture_button:
            self.ReleaseMouse()
            self._own_mouse = False

        ctrl, shift = event.ControlDown(), event.ShiftDown()
        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            ctrl, shift, chr(0), 0, None)

        if button == 'Right':
            self._RenderWindowInteractor.RightButtonReleaseEvent()
        elif button == 'Left':
            self._RenderWindowInteractor.LeftButtonReleaseEvent()
        elif button == 'Middle':
            self._RenderWindowInteractor.MiddleButtonReleaseEvent()

    def OnMouseWheel(self, event):
        """Handles the wx.EVT_MOUSEWHEEL event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue
        event.Skip()

        ctrl, shift = event.ControlDown(), event.ShiftDown()
        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            ctrl, shift, chr(0), 0, None)
        if event.GetWheelRotation() > 0:
            self._RenderWindowInteractor.MouseWheelForwardEvent()
        else:
            self._RenderWindowInteractor.MouseWheelBackwardEvent()

    def OnMotion(self, event):
        """Handles the wx.EVT_MOTION event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue
        # we call this early in case any of the VTK code raises an
        # exception.
        event.Skip()

        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            event.ControlDown(),
            event.ShiftDown(),
            chr(0), 0, None)
        self._RenderWindowInteractor.MouseMoveEvent()

    def OnEnter(self, event):
        """Handles the wx.EVT_ENTER_WINDOW event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue
        event.Skip()

        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            event.ControlDown(),
            event.ShiftDown(),
            chr(0), 0, None)
        self._RenderWindowInteractor.EnterEvent()

    def OnLeave(self, event):
        """Handles the wx.EVT_LEAVE_WINDOW event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue
        event.Skip()

        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            event.ControlDown(),
            event.ShiftDown(),
            chr(0), 0, None)
        self._RenderWindowInteractor.LeaveEvent()

    def OnKeyDown(self, event):
        """Handles the wx.EVT_KEY_DOWN event for
        wxVTKRenderWindowInteractor.
        """

        ctrl, alt, shift = event.ControlDown(
        ), event.AltDown(), event.ShiftDown()
        keycode, keysym = event.GetKeyCode(), None
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)

        # This code is brought in to try to get a proper keysym -- the
        # default code always sets keysym to None, which breaks atamai code
        if keycode < 128:
            if keycode >= 65 and keycode <= 90 and shift == 0:
                keycode = keycode + 32  # convert to lower case
            keysym = self.KeySym[keycode]
        else:
            try:
                keysym = self.KeySymFromCode[keycode]
            except KeyError:
                keysym = '??'

        # wxPython 2.6.0.1 does not return a valid event.Get{X,Y}()
        # for this event, so we use the cached position.
        (x, y) = self._RenderWindowInteractor.GetEventPosition()
        self._RenderWindowInteractor.SetEventInformation(x, y,
                                                         ctrl, shift, key, 0,
                                                         keysym)
        self._RenderWindowInteractor.SetAltKey(alt)

        self._RenderWindowInteractor.KeyPressEvent()

        # disallow underlying render interactor for acting on certain keys
        if key not in ('3', 'r',):
            self._RenderWindowInteractor.CharEvent()

        # make sure keyboard accelerators work
        if ctrl or alt:
            event.Skip()

    def OnKeyUp(self, event):
        """Handles the wx.EVT_KEY_UP event for
        wxVTKRenderWindowInteractor.
        """

        # event processing should continue, otherwise things like accelerators
        # will be broken
        event.Skip()

        ctrl, shift = event.ControlDown(), event.ShiftDown()
        keycode, keysym = event.GetKeyCode(), None
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)

        # This code is brought in to try to get a proper keysym -- the
        # default code always sets keysym to None, which breaks atamai code
        if keycode < 128:
            if keycode >= 65 and keycode <= 90 and shift == 0:
                keycode = keycode + 32  # convert to lower case
            keysym = self.KeySym[keycode]
        else:
            try:
                keysym = self.KeySymFromCode[keycode]
            except KeyError:
                keysym = '??'

        self._RenderWindowInteractor.SetEventInformationFlipY(
            event.GetX(), event.GetY(),
            ctrl, shift, key, 0,
            keysym)
        self._RenderWindowInteractor.KeyReleaseEvent()

    def OnMouseCaptureLost(self, event):
        """This is signalled when we lose mouse capture due to an
        external event, such as when a dialog box is shown.  See the
        wx documentation.
        """

        # the documentation seems to imply that by this time we've
        # already lost capture.  I have to assume that we don't need
        # to call ReleaseMouse ourselves.
        if _useCapture and self._own_mouse:
            self._own_mouse = False

    def GetDisplayId(self):
        """Function to get X11 Display ID from WX and return it in a format
        that can be used by VTK Python.

        We query the X11 Display with a new call that was added in wxPython
        2.6.0.1.  The call returns a SWIG object which we can query for the
        address and subsequently turn into an old-style SWIG-mangled string
        representation to pass to VTK.
        """
        d = None

        try:
            d = wx.GetXDisplay()

        except NameError:
            # wx.GetXDisplay was added by Robin Dunn in wxPython 2.6.0.1
            # if it's not available, we can't pass it.  In general,
            # things will still work; on some setups, it'll break.
            pass

        else:
            # wx returns None on platforms where wx.GetXDisplay is not relevant
            if d:
                d = hex(d)
                # On wxPython-2.6.3.2 and above there is no leading '0x'.
                if not d.startswith('0x'):
                    d = '0x' + d

                # we now have 0xdeadbeef
                # VTK wants it as: _deadbeef_void_p (pre-SWIG-1.3 style)
                d = '_%s_%s\0' % (d[2:], 'void_p')

        return d

    def ConvertFocusEvent(self, event):
        e = Event()
        e.type = self.EvtType[event.GetEventType()]
        e.state = 0
        e.num = 0
        # don't handle because wxGTK is a little broken
        if wx.Platform != '__WXGTK__':
            self.HandleEvent(e)

    def OnFirstWindowMapping(self):

        # Tell the RenderWindow to render inside the wx.Window.

        # on relevant platforms, set the X11 Display ID
        d = self.GetDisplayId()
        if d:
            self._RenderWindowInteractor.GetRenderWindow().SetDisplayId(d)

        # store the handle
        self.__handle = self.GetHandle()
        # and give it to VTK
        self._RenderWindowInteractor.GetRenderWindow().SetWindowInfo(
            str(self.__handle))

        # now that we've painted once, the Render() reparenting logic
        # is safe
        self.__has_painted = True
        self.__is_mapped = True

    def OnPaint(self, event):
        """Handles the wx.EVT_PAINT event for
        wxVTKRenderWindowInteractor.
        """

        # wx should continue event processing after this handler.
        # We call this BEFORE Render(), so that if Render() raises
        # an exception, wx doesn't re-call OnPaint repeatedly.
        event.Skip()

        # ignore events if we're frozen
        if self.__is_frozen:
            return

        if self.__is_mapped is False:
            self.OnFirstWindowMapping()

        if self._RenderWindowInteractor is None:
            return

        # make sure the RenderWindow is sized correctly
        self._RenderWindowInteractor.GetRenderWindow().SetSize(
            self.GetSizeTuple())

        # JDG: make sure all windows are modified
        for pane in self._RenderPanes:
            pane.Modified()

        self.Render()

    #--------------------------------------
    def Render(self, force_redraw=False):

        if self.__Created:

            # JDG: make sure all windows are modified
            if force_redraw:
                for pane in self._RenderPanes:
                    pane.Modified()

            return PaneFrame.PaneFrame.Render(self)

        elif self.__is_mapped:

            self._RenderWindow.SetWindowInfo(str(self.GetHandle()))
            self.__Created = 1
            return PaneFrame.PaneFrame.Render(self)

    #--------------------------------------
    def SetTitle(self, title):
        try:
            self._wxFrame.SetTitle(title)
        except AttributeError:
            pass

    def GetTitle(self):
        try:
            return self._wxFrame.GetTitle()
        except AttributeError:
            return ""

    #--------------------------------------
    def Start(self):
        wx.PySimpleApp().MainLoop()

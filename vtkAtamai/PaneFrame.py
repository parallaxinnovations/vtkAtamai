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

"""
PaneFrame - the base type for 3D rendering context

  The PaneFrame is a window that is designated for 3D rendering.
  A PaneFrame can be divided into multiple rectangular RenderPanes,
  but usually there is one RenderPane per PaneFrame.

  There is exactly one vtkRenderWindow associated with each PaneFrame.
  The PaneFrame is a stand-alone window for this base class, but in the
  subclasses (tkPaneFrame, wxPaneFrame) the PaneFrame is a widget or
  sub-window.

  The PaneFrame is responsible for capturing all keyboard and mouse
  events from the operating system and routing them to the appropriate
  PaneFrame.  The routing is done in the HandleEvent() method.

  Each PaneFrame subclass captures the events from a particular GUI
  toolkit by setting the appropriate callback functions, and translates
  them into an "event object" that can be passed to HandleEvent().
  The event object is described in the EventHandler documentation.

Derived From:

  EventHandler

See Also:

  RenderPane, tkPaneFrame, wxPaneFrame

Initialization:

  PaneFrame(*width*=400,*height*=400)

  *width*  - window width in pixels

  *height* - window height in pixels

Public Methods:

  ConnectRenderPane(*pane*)    -- add a render pane

  DisconnectRenderPane(*pane*) -- remove a render pane

  GetRenderPanes()             -- get a list of all panes

  GetRenderWindow()            -- get the VTK render window

  SetTitle(*title*)            -- set the title for the window

  Render()                     -- call Render() on the RenderWindow if
                                  any panes need to be rendered

  RenderAll()                  -- call Render() on all PaneFrames in this
                                  application

  ScheduleOnce(*ms*,*func*)    -- schedule a function to be called after
                                  the specified number of milliseconds
                                  (returns an id you can use to unschedule)

  ScheduleEvery(*ms*,*func*)   -- schedule a function to be called every
                                  time the specified number of millisecs
                                  have elapsed
                                  (returns an id you can use to unschedule)

  UnSchedule(*id*)             -- remove the specified item from the schedule

  SetDesiredFPS(*rate*)        -- set the desired frames-per-second for
                                  interaction with the window

  Start()                      -- begin the interaction loop
                                  (this method will never return)

Protected Attributes:

  _RenderWindow  -- the vtkRenderWindow

  _RenderFTime   -- the time of the last render, in the same format
                    as the python time.time() function

Notes:

  You will rarely want to bind any events to the PaneFrame.
  All interactions should be handled by binding
  methods to the RenderPane.

"""

#======================================
import vtk

from zope import interface
from vtkAtamai.interfaces import IPaneFrame
from vtkAtamai import EventHandler

import time
import logging
import copy


class PaneFrame(EventHandler.EventHandler):
    # a list of all the PaneFrames in this application
    AllPaneFrames = []
    _ScheduledCallbacks = []
    _ScheduleId = 0

    interface.implements(IPaneFrame)

    def __del__(self):
        # remove ourselves from the list of paneframes
        if self in self.AllPaneFrames:
            self.AllPaneFrames.remove(self)
        # cancel any timers
        if self._QualityRenderId != -1:
            self.cancelTimers()

    def cancelTimers(self):
        pass

    def tearDown(self):

        self._FocusPane = self._RenderWindow = self._RenderWindowInteractor = None

    def __init__(self, width=400, height=400, **kw):
        EventHandler.EventHandler.__init__(self)

        PaneFrame.AllPaneFrames.append(self)

        # other names that this object is known by
        self._Aliases = []

        # list of all panes in this frame
        self._RenderPanes = []

        # the pane that the mouse is currently positioned over
        self._CurrentPane = None

        # the pane that has the focus (i.e. the one that was clicked in last)
        self._FocusPane = None

        # the ID of the timer that checks whether to do high-quality renders
        self._QualityRenderId = -1

        # the time when the last render occurred
        self._RenderFTime = 0.0

        # the desired interactive update rate, in frames per second
        self._DesiredFPS = 5

        self._State = 0

        # if the renderwindow is already created, we are done
        if hasattr(self, '_RenderWindow'):
            return

        self._RenderWindow = vtk.vtkRenderWindow()

        if 'stereo' in kw:
            if kw['stereo']:
                self._RenderWindow.StereoCapableWindowOn()
                self._RenderWindow.SetStereoTypeToCrystalEyes()
            del kw['stereo']

        if 'fullscreen' in kw:
            if kw['fullscreen']:
                self._RenderWindow.FullScreenOn()
            del kw['fullscreen']

        self._RenderWindow.SetSize(width, height)
        self._RenderWindowInteractor = vtk.vtkRenderWindowInteractor()
        self._RenderWindowInteractor.SetRenderWindow(self._RenderWindow)

        self._BindInteractor()

    def _BindInteractor(self):

        self.interactor_style = vtk.vtkInteractorStyleUser()

        self._RenderWindowInteractor.SetInteractorStyle(self.interactor_style)

        #obj = self.interactor_style
        obj = self._RenderWindowInteractor

        obj.AddObserver("LeftButtonPressEvent",
                        self._OnButtonPress)
        obj.AddObserver("LeftButtonReleaseEvent",
                        self._OnButtonRelease)

        obj.AddObserver("MiddleButtonPressEvent",
                        self._OnButtonPress)
        obj.AddObserver("MiddleButtonReleaseEvent",
                        self._OnButtonRelease)

        obj.AddObserver("RightButtonPressEvent",
                        self._OnButtonPress)
        obj.AddObserver("RightButtonReleaseEvent",
                        self._OnButtonRelease)

        obj.AddObserver("MouseMoveEvent",
                        self._OnMotion)

        obj.AddObserver("KeyPressEvent",
                        self._OnKeyPress)
        obj.AddObserver("KeyReleaseEvent",
                        self._OnKeyRelease)
        obj.AddObserver("CharEvent", self._OnChar)

        obj.AddObserver("ConfigureEvent",
                        self._OnConfigure)
        obj.AddObserver("EnterEvent",
                        self._OnEnter)
        obj.AddObserver("LeaveEvent",
                        self._OnLeave)

        obj.AddObserver("TimerEvent",
                        self._OnTimer)

    #--------------------------------------
    def SetTitle(self, title):
        self._RenderWindow.SetWindowName(title)

    def GetTitle(self):
        self._RenderWindow.GetWindowName()

    #--------------------------------------
    def SetDesiredFPS(self, fps):
        """Set the desired frames-per-second for interaction."""
        self._DesiredFPS = fps

    def GetDesiredFPS(self):
        """Get the desired frames-per-second for interaction."""
        return self._DesiredFPS

    #--------------------------------------
    def _OnTimer(self, obj=None, event=""):
        epochmillisecs = time.time() * 1000  # ms since epoch
        for item in list(PaneFrame._ScheduledCallbacks):
            if epochmillisecs > item[2]:
                if item[3] <= 0:
                    PaneFrame._ScheduledCallbacks.remove(item)
                else:  # reschedule
                    item[2] = epochmillisecs + item[3]
                item[1]()
        obj.CreateTimer(1)

    def _OnButtonPress(self, obj=None, event=""):

        # JDG retire this after we eliminate Atamai event handling
        if self._RenderWindowInteractor.GetInteractorStyle() != self.interactor_style:
            return

        e = EventHandler.Event()
        e.type = '4'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            8192 * obj.GetRepeatCount() | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = {"LeftButtonPressEvent": 1,
                 "MiddleButtonPressEvent": 2,
                 "RightButtonPressEvent": 3}[event]
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetEventPosition()
        self._State = self._State | (0x80 << e.num)  # set bit for button
        self.HandleEvent(e)

    def _OnButtonRelease(self, obj=None, event=""):

        # JDG retire this after we eliminate Atamai event handling
        if self._RenderWindowInteractor.GetInteractorStyle() != self.interactor_style:
            return

        e = EventHandler.Event()
        e.type = '5'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = {"LeftButtonReleaseEvent": 1,
                 "MiddleButtonReleaseEvent": 2,
                 "RightButtonReleaseEvent": 3}[event]
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetEventPosition()
        self._State = self._State & ~(0x80 << e.num)  # clear bit for button
        self.HandleEvent(e)

    def _OnMotion(self, obj=None, event=""):

        # JDG retire this after we eliminate Atamai event handling
        if self._RenderWindowInteractor.GetInteractorStyle() != self.interactor_style:
            return

        (x, y) = obj.GetEventPosition()
        (oldx, oldy) = obj.GetLastEventPosition()
        if x == oldx and y == oldy:
            return
        e = EventHandler.Event()
        e.type = '6'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = (x, y)
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _OnChar(self, obj=None, event=""):
        pass

    def _OnKeyPress(self, obj=None, event=""):

        # JDG retire this after we eliminate Atamai event handling
        if self._RenderWindowInteractor.GetInteractorStyle() != self.interactor_style:
            return

        e = EventHandler.Event()
        e.type = '2'

        e.alt_key = obj.GetAltKey()
        e.ctrl_key = obj.GetControlKey()
        e.shift_key = obj.GetShiftKey()

        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = obj.GetKeySym()
        e.char = obj.GetKeyCode()
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetLastEventPosition()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _OnKeyRelease(self, obj=None, event=""):

        # JDG retire this after we eliminate Atamai event handling
        if self._RenderWindowInteractor.GetInteractorStyle() != self.interactor_style:
            return

        e = EventHandler.Event()
        e.type = '3'

        e.alt_key = obj.GetAltKey()
        e.ctrl_key = obj.GetControlKey()
        e.shift_key = obj.GetShiftKey()

        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = obj.GetKeySym()
        e.char = obj.GetKeyCode()
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetLastEventPosition()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _OnConfigure(self, obj=None, event=""):
        e = EventHandler.Event()
        e.type = '22'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetLastEventPosition()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _OnEnter(self, obj=None, event=""):
        e = EventHandler.Event()
        e.type = '7'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetEventPosition()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _OnLeave(self, obj=None, event=""):
        e = EventHandler.Event()
        e.type = '8'
        e.state = 1 * (obj.GetShiftKey() > 0) | \
            4 * (obj.GetControlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = obj.GetSize()
        (e.x, e.y) = obj.GetEventPosition()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    #--------------------------------------
    def _TrapTimer(self):
        epochmillisecs = time.time() * 1000  # ms since epoch
        for item in list(PaneFrame._ScheduledCallbacks):
            if epochmillisecs > item[2]:
                if item[3] <= 0:
                    PaneFrame._ScheduledCallbacks.remove(item)
                else:  # reschedule
                    item[2] = epochmillisecs + item[3]
                item[1]()

    def _TrapButtonPress(self, num):
        e = EventHandler.Event()
        e.type = '4'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = num
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._RenderWindowInteractor.GetEventPosition()
        # should be changed to the below eventually:
        #(e.x, e.y) = self._InteractorStyle.GetLastPos()
        self._State = self._State | (0x80 << num)  # set bit for button
        self.HandleEvent(e)

    def _TrapButtonRelease(self, num):
        e = EventHandler.Event()
        e.type = '5'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = num
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._RenderWindowInteractor.GetEventPosition()
        self._State = self._State & ~(0x80 << num)  # clear bit for button
        self.HandleEvent(e)

    def _TrapMotion(self):
        (x, y) = self._InteractorStyle.GetLastPos()
        (oldx, oldy) = self._InteractorStyle.GetOldPos()
        if x == oldx and y == oldy:
            return
        e = EventHandler.Event()
        e.type = '6'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = (x, y)
        # self.PrintEvent(e)
        self.HandleEvent(e)
        self._TrapTimer()

    def _TrapKeyPress(self):
        e = EventHandler.Event()
        e.type = '2'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = self._InteractorStyle.GetKeySym()
        e.char = chr(self._InteractorStyle.GetChar())
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._InteractorStyle.GetLastPos()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _TrapKeyRelease(self):
        e = EventHandler.Event()
        e.type = '3'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = self._InteractorStyle.GetKeySym()
        e.char = chr(self._InteractorStyle.GetChar())
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._InteractorStyle.GetLastPos()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _TrapConfigure(self):
        e = EventHandler.Event()
        e.type = '22'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._InteractorStyle.GetLastPos()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _TrapEnter(self):
        e = EventHandler.Event()
        e.type = '7'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._InteractorStyle.GetLastPos()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    def _TrapLeave(self):
        e = EventHandler.Event()
        e.type = '8'
        e.state = 1 * (self._InteractorStyle.GetShiftKey() > 0) | \
            4 * (self._InteractorStyle.GetCtrlKey() > 0) | \
            self._State
        e.keysym = '??'
        e.char = '\0'
        e.num = 0
        (e.width, e.height) = self._RenderWindowInteractor.GetSize()
        (e.x, e.y) = self._InteractorStyle.GetLastPos()
        # self.PrintEvent(e)
        self.HandleEvent(e)

    #--------------------------------------
    def _SetCurrentPane(self, pane, event):
        # change the current pane, send an
        # Enter event to the new pane and a
        # Leave event to the old pane
        if pane == self._CurrentPane:
            return

        if self._CurrentPane is not None:
            # make a deep copy of the current event
            e = copy.deepcopy(event)
            # but change the type to 'Leave'
            e.type = '8'  # 'Leave'
            # and pass to the pane
            self._CurrentPane.HandleEvent(e)

        if pane is not None:
            # make a deep copy of the current event
            e = copy.deepcopy(event)
            # but change the type to 'Enter'
            e.type = '7'  # 'Enter'
            # and pass to the pane
            pane.HandleEvent(e)

        self._CurrentPane = pane

    #--------------------------------------
    def _SetFocusPane(self, pane, event):
        # change the current pane, send an
        # Enter event to the new pane and a
        # Leave event to the old pane
        if pane == self._FocusPane:
            return

        if self._FocusPane is not None:
            # make a copy of the current event
            e = copy.deepcopy(event)
            # but change the type to 'FocusOut'
            e.type = EventHandler.EventHandler.EventType['FocusOut']
            # and pass to the pane
            self._FocusPane.HandleEvent(e)

        if pane is not None:
            # make a copy of the current event
            e = copy.deepcopy(event)
            # but change the type to 'FocusIn'
            e.type = EventHandler.EventHandler.EventType['FocusIn']
            # and pass to the pane
            pane.HandleEvent(e)

        self._FocusPane = pane

    #--------------------------------------
    def _HandleConfigure(self, event):
        # pass off the configure event to the Panes
        width = event.width
        height = event.height
        if not (width and height):
            return

        if len(self._RenderPanes) == 0:
            raise Exception("No attached render panes!!")

        for pane in self._RenderPanes:
            # set up the new viewport for the pane
            xmin, ymin, xmax, ymax = pane.GetViewport()
            left, bottom, right, top = pane.GetViewportOffsets()

            xmin = (xmin * width + left) / width
            xmax = (xmax * width + right) / width
            ymin = (ymin * height + bottom) / height
            ymax = (ymax * height + top) / height

            pane.GetRenderer().SetViewport(xmin, ymin, xmax, ymax)

            # pass the event along to the renderer
            xmin = int(xmin * width + 0.5)
            xmax = int(xmax * width + 0.5)
            ymin = int(ymin * height + 0.5)
            ymax = int(ymax * height + 0.5)

            e = EventHandler.Event()
            e.type = '22'
            e.x = xmin
            e.y = ymin
            e.width = xmax - xmin
            e.height = ymax - ymin
            e.state = 0
            e.num = 0

            pane.HandleEvent(e)

    #--------------------------------------
    def _QualityRender(self):
        # this method is called every 0.5 seconds and checks to see
        # if interaction has stopped, and if so then it does a
        # high-quality render

        if (time.time() - self._RenderFTime) < 0.5:
            return

        # check mouse button state - if a button is pressed, no HQ rendering
        # will occur
        if self._State != 0:
            return

        if self._RenderWindow.GetDesiredUpdateRate() < 0.1:
            return

        self._RenderWindow.SetDesiredUpdateRate(0.05)
        self.RenderAll(force_redraw=True)

    #--------------------------------------
    def HandleEvent(self, event):
        # note: both key and mouse events are sent to the pane under
        #       the mouse, there is no "focus" for keypresses

        # for debug purposes
        # self.PrintEvent(event)

        # initialize return value to '1' (nothing done)
        returnval = 1

        # set QualityRender to be called every so often for LOD stuff
        if self._QualityRenderId < 0:
            self._QualityRenderId = \
                self.ScheduleEvery(500, self._QualityRender)

        # set an interactive update rate for next render
        n = 0   # count the total number of actors
        renderers = self._RenderWindow.GetRenderers()
        renderers.InitTraversal()
        while 1:
            ren = renderers.GetNextItem()
            if not ren:
                break
            n = n + ren.GetViewProps().GetNumberOfItems()
        # divide the FPS by the number of props, to reverse the
        #  calculation done in vtkRenderWindow (we assume that one
        #  of the props is rendering much slower than all others,
        #  the vtkRenderWindow assumes each prop takes the same time
        #  to render which is almost never the case)
#        if n != 0:  # avoid division by zero
#            self._RenderWindow.SetDesiredUpdateRate(self._DesiredFPS*1.0/n)

        # pass configure events to all panes
        if event.type == '22':
            self._HandleConfigure(event)
            returnval = EventHandler.EventHandler.HandleEvent(self, event)
            return returnval

        # if buttons are being held down, don't change focus
        # (unless this is a button release event)
        if event.type in ('4', '5', '6'):
            # pass event to the render panes under the cursor
            newCurrentPane = None
            if len(self._RenderPanes) == 0:
                raise Exception("No attached render panes!!")

            for pane in self._RenderPanes:
                if pane.GetRenderer().IsInViewport(event.x, event.y):
                    newCurrentPane = pane
                    break
            # set the focus if a button is not being held down or was
            # just pressed, or if the mouse button has just been released
            if event.state & 0x1f00 == 0 or \
                (event.type == '5' and
                 event.state & 0x1f00 == 128 << event.num):
                self._SetFocusPane(newCurrentPane, event)

            if newCurrentPane != self._CurrentPane:
                if newCurrentPane == self._FocusPane:
                    self._SetCurrentPane(newCurrentPane, event)
                else:
                    self._SetCurrentPane(None, event)

        # set current pane if Enter
        if event.type == '7':
            if self._FocusPane:
                self._SetCurrentPane(self._FocusPane, event)
            else:
                if len(self._RenderPanes) == 0:
                    raise Exception("No attached render panes!!")
                for pane in self._RenderPanes:
                    if pane.GetRenderer().IsInViewport(event.x, event.y):
                        self._SetCurrentPane(pane, event)
                        break

        # set current pane to None if Leave
        elif event.type == '8':
            self._SetCurrentPane(None, event)

        # pass the event to the pane that has the focus
        elif self._FocusPane:
            if not self._FocusPane.HandleEvent(event):
                returnval = None  # flag that event was handled

        # also let the PaneFrame handle it, i.e pass to superclass
        if not EventHandler.EventHandler.HandleEvent(self, event):
            returnval = None

        self.RenderAll()

        return returnval

    #--------------------------------------
    def ConnectRenderPane(self, pane):
        if pane in self._RenderPanes:
            return
        self._RenderPanes.append(pane)
        self._RenderWindow.AddRenderer(pane.GetRenderer())

    def DisconnectRenderPane(self, pane):
        if self._CurrentPane == pane:
            self._CurrentPane = None
        if self._FocusPane == pane:
            self._FocusPane = None
        self._RenderPanes.remove(pane)
        self._RenderWindow.RemoveRenderer(pane.GetRenderer())

    def GetRenderPanes(self):
        return self._RenderPanes

    #--------------------------------------
    def RenderAll(self, force_redraw=False):
        rendereredframes = []
        for frame in PaneFrame.AllPaneFrames:
            try:
                frame._RenderWindow.SwapBuffersOff()
                if (frame.Render(force_redraw=force_redraw)):
                    rendereredframes.append(frame)
                frame._RenderWindow.SwapBuffersOn()
            except:
                logging.exception("PaneFrame")
        for frame in rendereredframes:
            frame._RenderWindow.Frame()

    def Render(self, force_redraw=False):
        renderneeded = 0
        if len(self._RenderPanes) == 0:
            raise Exception("No attached render panes!!")
        for pane in self._RenderPanes:
            if pane.HasChangedSince(pane.GetRenderTime()):
                renderneeded = 1
        if renderneeded:
            self._RenderWindow.Render()
            self._RenderFTime = time.time()

        return renderneeded

    #--------------------------------------
    def GetRenderWindow(self):
        return self._RenderWindow

    #--------------------------------------
    def ScheduleOnce(self, millisecs, func):
        # schedule the specified function to be called after the
        # specified number of milliseconds
        PaneFrame._ScheduleId = PaneFrame._ScheduleId + 1
        PaneFrame._ScheduledCallbacks.append(
            [PaneFrame._ScheduleId, func, time.time() * 1000 + millisecs, 0.0])
        return PaneFrame._ScheduleId

    def ScheduleEvery(self, millisecs, func):
        # schedule the specified function to be called each time the
        # specified number of milliseconds has elapsed
        PaneFrame._ScheduleId = PaneFrame._ScheduleId + 1
        PaneFrame._ScheduledCallbacks.append(
            [PaneFrame._ScheduleId, func, time.time() * 1000 + millisecs, millisecs])
        return PaneFrame._ScheduleId

    def UnSchedule(self, id):
        for item in list(PaneFrame._ScheduledCallbacks):
            if item[0] == id:
                PaneFrame._ScheduledCallbacks.remove(item)

    #--------------------------------------
    def Start(self):

        self.Render()
        self._RenderWindowInteractor.Initialize()
        self._RenderWindowInteractor.CreateTimer(0)
        self._RenderWindowInteractor.Start()


# a 'friend' method
def RenderAll():

    rendereredframes = []
    for frame in PaneFrame.AllPaneFrames:
        frame._RenderWindow.SwapBuffersOff()
        if (frame.Render()):
            rendereredframes.append(frame)
        frame._RenderWindow.SwapBuffersOn()
    for frame in rendereredframes:
        frame._RenderWindow.Frame()

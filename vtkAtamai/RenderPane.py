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
    'module_name': '$RCSfile: RenderPane.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
    'author': '$Author: jeremy_gill $',
    'version': '$Revision: 1.3 $',
    'date': '$Date: 2007/10/09 21:31:35 $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
RenderPane - the base type for a virtual scene

  The RenderPane can contain widgets (e.g. buttons), one or more
  3D cursors, and can be connected to the ActorFactories which
  represent virtual 3D objects.

  There is exactly one vtkRenderer associated with each RenderPane.
  There can be more than one RenderPane inside a PaneFrame, just
  as a vtkRenderWindow can support multiple vtkRenderers.  Usually,
  however, the is one PaneFrame per RenderPane.

  The default interaction bindings are as follows:

  - Button 1 -   rotate the camera

  - Shift-B1 -   pan the camera

  - Button 2 -   manipulate the actor under the cursor

  - Button 3 -   dolly/zoom the camera

Derived From:

  EventHandler

See Also:

  PaneFrame, ActorFactory, CursorFactory, Widget, RenderPane2D

Initialization:

  RenderPane(*master*)

  *master*  - the PaneFrame that will hold this RenderPane

Public Methods:

  ConnectActorFactory(*factory*) -- connect a factory: the factory will add
                              a set of actors to the renderer

  DisconnectActorFactory(*factory*) -- disconnect the factory and remove
                              the factory's actors from the pane

  GetActorFactories()      -- get the list of connected actor factories


  ConnectCursor(*cursor*)    -- connect a cursor (see CursorFactory.py)

  DisconnectCursor(*cursor*) -- disconnect a cursor

  GetCursors()             -- get a list of all cursors


  AddWidget(*widget*)      -- add a widget to the renderer

  RemoveWidget(*widget*)   -- remove a widget to the renderer

  GetWidgets()             -- get a list of all widgets


  GetRenderer()            -- get the VTK renderer for this pane

  GetRenderWindow()        -- get the VTK render window for this pane


  SetBackground(*r*,*g*,*b*) -- set the background color

  GetBackground()          -- get the background color


  SetViewport(*xmin*,*ymin*,*xmax*,*ymax*) -- set the viewport within the
                              frame to use for the renderer, similar
                              to vtkRenderer.SetViewport()

  GetViewport()            -- get the current viewport

  SetViewportOffsets(*left*,*bottom*,*right*,*top*) -- set offsets
                              (in pixels) for
                              the viewport borders, e.g. you can set the
                              pane to fill the entire window except for
                              20 pixels at the top of the top of the window.

  SetPointOfInterest(*x*,*y*,*z*) -- rotate the camera to place the specified
                              point in the center of the scene


  Render()                 -- render this pane (and all other panes that
                              share the same PaneFrame)


  ScheduleOnce(*ms*, *func*)    -- schedule a function to be called after
                              the specified number of milliseconds
                              (returns an id you can use to unschedule)

  ScheduleEvery(*ms*, *func*) -- schedule a function to be called every
                              time the specified number of millisecs
                              have elapsed
                              (returns an id you can use to unschedule)

  UnSchedule(*id*)         -- remove the specified item from the schedule


Interaction Bindings:

  The modifier ("Shift", "Control", etc.) is optional.

  BindPanToButton(*button*,*modifier*=None)  -- bind "pan" to specified button

  BindZoomToButton(*button*,*modifier*=None)  -- bind "zoom" to button

  BindRotateToButton(*button*,*modifier*=None) -- bind "rotate" to button

  BindActorToButton(*button*,*modifier*=None) -- pass button's events to actor

  BindNoneToButton(*button*,*modifier*=None)  -- unbind the button

  BindModeToButton(*mode*,*button*,*modifier*=None) -- the *mode* parameter can
                                               either be an InteractionMode
                                               object or can be a 3-tuple
                                               containting ButtonPress,
                                               ButtonRelease, and Motion
                                               methods to bind to the button

  BindDefaultInteraction() -- bind default interaction modes
                              (buttons 1/2/3 are rotate/actor/zoom,
                               Shift-1 is pan)


Handler Methods:

  DoStartMotion(*event*)     -- for rotate/pan/zoom (bind to ButtonPress)

  DoEndMotion(*event*)       -- for rotate/pan/zoom (bind to ButtonRelease)

  DoCameraRotate(*event*)    -- rotate the camera (bind to Motion)

  DoCameraPan(*event*)       -- pan the camera    (bind to Motion)

  DoCameraZoom(*event*)      -- zoom the camera   (bind to Motion)

  DoPickActor(*event*)       -- pick an actor     (bind to ButtonPress)

  DoReleaseActor(*event*)    -- release an actor  (bind to ButtonRelease)

  DoActorInteraction(*event*) -- pass event to actor (bind to Motion)


Other Important Methods:

  StartRender()            -- this method is called immediately before
                              each render

Protected Attributes:

  _Renderer                -- the vtkRenderer

  _Picker                  -- the vtkCellPicker

To Do:

  - If a cursor is added while the mouse is in the pane, it will not render
    properly until the mouse moves.  This is because it has to know where
    the mouse is in order to render properly.  Still looking for a painless
    solution for this.

  - Implement "Enter" and "Leave" events for actor factories, so that
    they can change color when the mouse passes over them.

"""

from zope import interface
from interfaces import IRenderPane
import logging

#======================================
import EventHandler
import PaneFrame

import math
import types
import sys
import vtk

#======================================


class RenderPane(EventHandler.EventHandler):

    """A rectangular window area that depicts a virtual scene.

    A RenderPane object represents a rectangular area within
    a 3D rendering context, or more specifically it represents
    a vtkRenderer.

    The RenderPane receives mouse, keyboard, configuration, and
    other events.  It generally uses these events to reposition
    the camera that is viewing the scene, or it passes the events
    on to ActorFactories in the pane.

    """

    interface.implements(IRenderPane)

    def __del__(self):
        print 'RenderPane deleted!'

    def __init__(self, master=None, *args, **kw):
        EventHandler.EventHandler.__init__(self)

        # the renderer associated with the pane
        self._Renderer = vtk.vtkRenderer()

        # the initial viewport
        self._Viewport = (0.0, 0.0, 1.0, 1.0)
        self._ViewportOffsets = (0.0, 0.0, 0.0, 0.0)

        # set the picker accuracy greater than the default
        self._Picker = vtk.vtkCellPicker()
        self._Picker.SetTolerance(0.0001)

        # pick information list, this is filled in by DoSmartPick
        self._PickInformationList = []

        # the actors in the pane
        self._ActorFactories = []
        self._CurrentActor = None
        self._CurrentActorFactory = None

        # the widgets (buttons, etc) in the pane
        self._Widgets = []
        self._CurrentWidget = None
        self._FocusWidget = None

        # cursor transform, for 3D cursor
        self._Cursors = []
        self._CursorOnFlag = 1
        self._CursorShownFlag = 0

        # the time of the last modification/render
        self._MTime = vtk.vtkObject()
        #self._RenderTime = vtk.vtkObject()
        try:  # user AddObserver in recent versions of VTK
            startMethod = lambda o, e, s=self: s.StartRender()
            self._Renderer.AddObserver("StartEvent", startMethod)
        except AttributeError:
            self._Renderer.SetStartRenderMethod(self.StartRender)
            self._Renderer.SetEndRenderMethod(self._RenderTime.Modified)

        # for the border around the pane
        self._BorderWidth = 0
        self._BorderColor = None

        # the PointOfInterest is the focus of attention
        self._PointOfInterest = (0, 0, 0)

        # are we the focus pane?
        self._Focus = 0

        # mouse position from last (or current) event
        self._MouseX = 0
        self._MouseY = 0

        # create default mouse bindings
        self.BindDefaultInteraction()

        # default master is a PaneFrame window
        if master is None:
            master = PaneFrame.PaneFrame(*args, **kw)

        # keep track of master
        self._master = master

        # master can be a PaneFrame
        if isinstance(master, PaneFrame.PaneFrame):
            master.ConnectRenderPane(self)
        # or a Tk Widget
        elif 'Tkinter' in sys.modules and hasattr(master, "tk"):
            import tkPaneFrame
            frame = tkPaneFrame.tkPaneFrame(master, *args, **kw)
            frame.ConnectRenderPane(self)
            # bind a minimal set of methods to make this look like
            # a Tk widget (dynamic method declaration!)
            self.pack = frame.pack
            self.grid = frame.grid
            self.configure = frame.configure
            self.tk = frame.tk
        # or a wxWindow
        elif 'wx' in sys.modules:
            import wxPaneFrame
            frame = wxPaneFrame.wxPaneFrame(master, *args, **kw)
            frame.ConnectRenderPane(self)
            self.wx = frame
            # bind important methods
            self.Show = lambda i, f=frame: f.Show(i)
        # or a QWindow
        elif 'qt' in sys.modules:
            import qtPaneFrame
            frame = qtPaneFrame.qtPaneFrame(master, *args, **kw)
            frame.show()
            frame.ConnectRenderPane(self)
            self.qt = frame

    def tearDown(self):

        for actor in self.GetActorFactories():
            actor.RemoveFromRenderer(self._Renderer)
        self._ActorFactories = []

        self.RemoveAllEventHandlers()

        del(self._BorderPoints)
        del(self._BorderActor)
        del(self._BorderScalars)
        del(self._BorderData)
        del(self._Picker)

    #--------------------------------------
    def SetPointOfInterest(self, position):
        """Move camera to ensure that the specified 3D coordinate is in view.

        This method moves the camera if the specified coodinate is currently
        not visible to the user.  If the coordinate is already in view, then
        the camera is not moved.

        """

        if len(position) == 1:
            position = position[0]

        x, y, z = position
        self._PointOfInterest = (x, y, z)

        self._Renderer.SetWorldPoint(x, y, z, 1.0)
        self._Renderer.WorldToDisplay()
        dx, dy, dz = self._Renderer.GetDisplayPoint()

        w, h = self._Renderer.GetSize()[:2]
        ox, oy = self._Renderer.GetOrigin()

        camera = self._Renderer.GetActiveCamera()

        cx, cy, cz = camera.GetFocalPoint()
        px, py, pz = camera.GetPosition()

        vx, vy, vz = (x - cx, y - cy, z - cz)
        d = math.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        vx, vy, vz = (vx / d, vy / d, vz / d)

        ovx, ovy, ovz = (px - cx, py - cy, pz - cz)
        d = math.sqrt(ovx ** 2 + ovy ** 2 + ovz ** 2)
        ovx, ovy, ovz = (ovx / d, ovy / d, ovz / d)

        theta = math.acos(vx * ovx + vy * ovy + vz * ovz) * 180 / math.pi

        # only shift the camera if the point of interest is 45 degrees
        # or more off center, or if the point is off-screen
        if theta > 45.0 or (w > 0 and h > 0 and
                            ((dx - ox - 0.5) / w < 0.0 or (dx - ox - 0.5) / w > 1.0 or
                             ((dy - oy - 0.5) / h < 0.0 or (dy - oy - 0.5) / h > 1.0))):
            camera.SetPosition(cx + d * vx, cy + d * vy, cz + d * vz)

        self.Modified()

    #--------------------------------------
    def BindDefaultInteraction(self):
        """Bind the default handlers for mouse events.

        The following are the default mouse bindings:

          - left - rotate camera
          - shift-left - pan camera
          - right - zoom camera
          - middle - interact with the ActorFactory under the mouse.

        """

        self.BindRotateToButton(1)
        self.BindPanToButton(1, modifier="Shift")
        self.BindActorToButton(2)
        self.BindZoomToButton(3)

    #--------------------------------------
    def BindModeToButton(self, methods, button=1, modifier=None):
        """Bind a set of handlers to a mouse button.

        Parameters:

        *methods* - either a 3-tuple containing the callbacks for
                    ButtonPress, ButtonRelease, and Motion or a
                    special "InteractionMode" object

        *button* - one of 1, 2 or 3

        *modifier* - "Shift", "Control", etc.

        """
        if modifier:
            # the modifier can be a string, or an int that actually
            # has the modifier bits set
            if isinstance(modifier, types.IntType):
                state = modifier
                modifier = ""
                vals = EventHandler.EventHandler.EventModifier.values()
                keys = EventHandler.EventHandler.EventModifier.keys()
                i = 0
                while state > 0:
                    if state & 1:
                        modifier = modifier + \
                            keys[vals.index(1 << i)] + "-"
                    i = i + 1
                    state = state / 2
            else:
                modifier = modifier + "-"
        else:
            modifier = ""

        # see if this is a InteractionMode object
        if hasattr(methods, 'DoButtonPress'):
            interaction = methods
            methods = (interaction.DoButtonPress,
                       interaction.DoButtonRelease,
                       interaction.DoMotion)

            interaction.AddRenderer(self._Renderer)

        # here we have some fun with lambdas
        method2 = methods[2]

        method1 = lambda e, s=self, m1=methods[1], b=button: \
            (s.BindEvent("<B%i-Motion>" % b, None),
             s.BindEvent("<ButtonRelease-%i>" % b, None),
             s.BindEvent("<FocusOut>", None),
             (m1 and m1(e)))

        method0 = lambda e, s=self, m0=methods[0], m1=method1, m2=method2, \
            b=button: \
            ((m0 and m0(e)),
             s.BindEvent("<FocusOut>", m1),
             s.BindEvent("<ButtonRelease-%i>" % b, m1),
             s.BindEvent("<B%i-Motion>" % b, m2))

        if methods[0] or methods[1] or methods[2]:
            self.BindEvent("<%sButtonPress-%i>" % (modifier, button), method0)
        else:
            self.BindEvent("<%sButtonPress-%i>" % (modifier, button), None)

    #--------------------------------------
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

    def BindRotateToButton(self, button=1, modifier=None):
        """Use the specified button to rotate the camera."""
        self.BindModeToButton((self.DoStartMotion,
                               self.DoEndMotion,
                               self.DoCameraRotate),
                              button, modifier)

    def BindActorToButton(self, button=1, modifier=None):
        """Pass the button events to the actor that was clicked."""
        self.BindModeToButton((self.DoPickActor,
                               self.DoReleaseActor,
                               self.DoActorInteraction),
                              button, modifier)

    def BindNoneToButton(self, button=1, modifier=None):
        """Do nothing with the specified button."""
        self.BindModeToButton((None,
                               None,
                               None),
                              button, modifier)

    #--------------------------------------
    def HandleEvent(self, event):
        """Do special event processing required for the RenderPane.

        The events are usually generated by a window (i.e. a PaneFrame
        object) which passes events to whichever pane that has the focus.
        The events are usually used either to reposition the camera or
        are passed on to one of the actors in the scene.

        If the pane has widgets then events will be sent to whichever
        widget has the focus, unless no widget has the focus.

        """
        # the HandleEvent method is long & complicated because it has
        # to keep track of which widget is current and which has the focus,
        # and it has to fork motion events to the cursor

        # for debug purposes
        # self.PrintEvent(event)

        # add 'renderer' to the event
        event.renderer = self._Renderer
        event.pane = self

        # pass configure events to all widgets
        if event.type == '22':  # 'Configure'
            self._SetBorderPoints(event.width, event.height)
            for widget in self._Widgets:
                widget.ConfigureGeometry((event.x, event.y),
                                         (event.width, event.height))
                widget.HandleEvent(event)
            self.Modified()
            return EventHandler.EventHandler.HandleEvent(self, event)

        if event.type == '7':  # 'Enter'
            self._Focus = 1
            self.DoEnter(event)
            self.DoCursorMotion(event)
        elif event.type == '8':  # 'Leave'
            self.DoLeave(event)
            self._Focus = 0

        if event.type in ('4', '5', '6', '7', '8'):  # if this is a mouse event
            # save the mouse position
            self._MouseX = event.x
            self._MouseY = event.y

            # set current widget to the one under the mouse
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
                    e = EventHandler.Event()
                    for attr in dir(event):
                        setattr(e, attr, getattr(event, attr))
                    # but change the type to 'Leave'
                    e.type = '8'  # 'Leave'
                    # and pass to the widget
                    self._FocusWidget.HandleEvent(e)
                elif event.type not in ('7', '8'):  # 'Enter','Leave'
                    self.DoLeave(event)

            # check to see if we entered the new FocusWidget
            if ((newCurrentWidget == self._FocusWidget and
                 self._CurrentWidget != newCurrentWidget) or
                    self._FocusWidget != newFocusWidget):
                if newFocusWidget:
                    # make a copy of the current event
                    e = EventHandler.Event()
                    for attr in dir(event):
                        setattr(e, attr, getattr(event, attr))
                    # but change the type to 'Enter'
                    e.type = '7'  # 'Enter'
                    # and pass to the widget
                    newFocusWidget.HandleEvent(e)
                elif event.type not in ('7', '8'):  # 'Enter','Leave'
                    self.DoEnter(event)

            if not self._CurrentWidget and event.type == '8':  # 'Leave'
                self.DoLeave(event)
            elif not newCurrentWidget and event.type == '7':  # 'Enter'
                self.DoEnter(event)

            self._FocusWidget = newFocusWidget
            self._CurrentWidget = newCurrentWidget

        # pass the event to the widget that has the focus
        # 'Enter','Leave'
        if self._FocusWidget and event.type not in ('7', '8'):
            return self._FocusWidget.HandleEvent(event)

        # finally, pass the event to the underlying handler
        # (this could be modified so that it will send events
        # to the currently selected ActorFactory instead)
        rval = EventHandler.EventHandler.HandleEvent(self, event)

        # deal with cursor motion
        if event.type == '6':  # 'Motion'
            self.DoCursorMotion(event)

        return rval

    #--------------------------------------
    def GetRenderer(self):
        """Get the vtkRenderer associated with this RenderPane."""
        return self._Renderer

    def GetRenderWindow(self):
        """Get the vtkRenderWindow associated with this RenderPane."""
        return self._Renderer.GetRenderWindow()

    #--------------------------------------
    def SetViewport(self, *args):
        """Set the viewport for the vtkRenderer.

        Parameters:

        *xmin*,*xmax*,*ymin*,*ymax* -- rectangle for the viewport, all values
                                      must be in the range 0,1

        Use this method specify that only a portion of the vtkRenderWindow
        will be drawn into by this RenderPane.

        """
        if len(args) == 1:
            args = args[0]
        xmin, ymin, xmax, ymax = args
        self._Viewport = (xmin, ymin, xmax, ymax)

        width, height = self._Renderer.GetRenderWindow().GetSize()[:2]
        self._SetRendererViewport(width, height)

    def GetViewport(self):
        """Get the (*xmin*,*ymin*,*xmax*,*ymax*) viewport parameters."""
        return self._Viewport

    def SetViewportOffsets(self, *args):
        """Add offsets to the viewport boundaries.

        Parameters:

        *left*,*top*,*right*,*bottom* -- pixel offsets for each boundary

        The viewport boundaries are calculated as follows:

        *left* *boundary* = *width* * *xmin* + *left*

        where *left* *boundary* is the pixel position of the leftmost
        boundary of the RenderPane, *width* is the width of the PaneFrame,
        *xmin* is set via SetViewport, and *left* is the viewport offset.
        The calculation done similarly for the other three boundaries.

        """
        if len(args) == 1:
            args = args[0]
        left, bottom, right, top = args
        self._ViewportOffsets = (left, bottom, right, top)

        width, height = self._Renderer.GetRenderWindow().GetSize()[:2]
        self._SetRendererViewport(width, height)

    def GetViewportOffsets(self, *args):
        """Get the (*left*,*top*,*right*,*bottom*) viewport offsets."""
        return self._ViewportOffsets

    def _SetRendererViewport(self, width, height):
        """Internal method to set vtkRenderer viewport.

        This method combines the Viewport and ViewportOffsets for the pane
        into viewport settings for the vtkRenderer.

        """

        if not (width and height):
            return

        xmin, ymin, xmax, ymax = self._Viewport
        left, bottom, right, top = self._ViewportOffsets

        xmin = (xmin * width + left) / width
        xmax = (xmax * width + right) / width
        ymin = (ymin * height + bottom) / height
        ymax = (ymax * height + top) / height

        self._Renderer.SetViewport(xmin, ymin, xmax, ymax)

        # generate configure event
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

        self.HandleEvent(e)

    #--------------------------------------
    def SetBackground(self, *args):
        """Set the (*r*,*g*,*b*) background color for the PaneFrame."""
        if len(args) == 1:
            args = args[0]
        self._Renderer.SetBackground(args[0], args[1], args[2])

    def GetBackground(self):
        """Get the (*r*,*g*,*b*) background color for the PaneFrame."""
        return self._Renderer.GetBackground()

    #--------------------------------------
    def GetDisplayOrigin(self):
        """Get the coordinates of lower left corner in display coordinates.

        This method is shorthand for GetRenderer().GetOrigin().

        """
        return self._Renderer.GetOrigin()

    def GetDisplaySize(self):
        """Get the (*width*,*height*) of the RenderPane in pixels."""
        return self._Renderer.GetSize()

    #--------------------------------------
    def DoEnter(self, event):
        """This method is called when the mouse enters the RenderPane.

        If a 3D cursor is set for this RenderPane, then this method causes
        the mouse pointer to disappear while the mouse is in the
        RenderPane.

        """

        # self._LastX = event.x
        # self._LastY = event.y
        if self._CursorOnFlag and self._Focus:
            self._ShowCursor()

    def DoLeave(self, event):
        """This method is called when the mouse leaves the RenderPane."""

        # JDG
        return

        # self._LastX = event.x
        # self._LastY = event.y
        if self._CursorOnFlag and self._Focus:
            self._HideCursor()
            self.Modified()

    #--------------------------------------
    def DoPickActor(self, event):
        """Find out what actor or actors are under the mouse cursor.

        This method can be called during a ButtonPress event to perform
        a pick to determine what actor is under the cursor.

        The following attributes are added to the event:

        *event*.actor   -- the actor that was picked

        *event*.picker  -- the picker used to do the picking

        If the actor belongs to an ActorFactory that is connected
        to this RenderPane, the event is then passed to that
        ActorFactory.

        As well, the following protected attributes are set for
        the RenderPane for use in later mouse Motion events:

        _CurrentActor -- the actor that was picked
        _CurrentActorFactory -- the factory that owns the actor

        """

        self.DoSmartPick(event)

        if self._PickInformationList:
            self._CurrentActor = self._PickInformationList[0].actor
            self._CurrentActorFactory = self._PickInformationList[0].factory

            event.actor = self._CurrentActor
            event.picker = self._Picker
            self._CurrentActorFactory.HandleEvent(event)
        else:
            self._CurrentActor = None
            self._CurrentActorFactory = None

    def DoReleaseActor(self, event):
        """Release the actor that is currently held by the mouse.

        This method can be called during a ButtonRelease event.  It
        should only be called if the DoPickActor() method was called
        previously.

        The following attributes are added to the event:

        *event*.actor   -- the actor that was picked

        *event*.picker  -- the picker used to do the picking

        If the actor belongs to an ActorFactory that is connected
        to this RenderPane, the event is then passed to that
        ActorFactory.

        """
        if (self._CurrentActorFactory == None):
            return

        event.actor = self._CurrentActor
        event.picker = self._Picker

        self._CurrentActorFactory.HandleEvent(event)
        self._CurrentActorFactory = None
        self._CurrentActor = None

    def DoActorInteraction(self, event):
        """Forward mouse events to the current ActorFactory.

        This method can be called during Motion events to pass
        the mouse events to the current ActorFactory as set by
        the DoPickActor method.

        The following attributes are added to the event before
        it is passed to the ActorFactory:

        *event*.actor   -- the actor that was picked

        *event*.picker  -- the picker used to do the picking

        """
        if (self._CurrentActorFactory == None):
            return

        event.actor = self._CurrentActor
        event.picker = self._Picker

        self._CurrentActorFactory.HandleEvent(event)

    #--------------------------------------
    def DoShowCursor(self, event):
        """Internal method for hiding/showing the mouse pointer."""
        # show the cursor after hiding it
        if self._CursorOnFlag:
            return

        self._CursorOnFlag = 1

        if event.type in ('4', '5', '6', '7', '8'):  # mouse event
            if not self._Renderer.IsInViewport(event.x, event.y):
                return
            for widget in self._Widgets:
                if widget.IsInWidget(event):
                    return

        self._ShowCursor()
        self.DoCursorMotion(event)

    def DoHideCursor(self, event):
        """Internal method for hiding/showing the mouse pointer."""
        # temporarily hide the cursor
        if not self._CursorOnFlag:
            return

        self._CursorOnFlag = 0

        self._HideCursor()
        self.Modified()

    def DoCursorMotion(self, event):
        """Internal method for moving the 3D cursor when the mouse moves."""
        # handle cursor motion, internal use only
        # do the pick
        return
        self.DoSmartPick(event)

        if self._PickInformationList:
            pickInfo = self._PickInformationList[0]
            position = pickInfo.position
            normal = pickInfo.normal
            vector = pickInfo.vector
        else:
            # no actor: place cursor in focal plane of camera
            camera = self._Renderer.GetActiveCamera()

            # get the z-buffer depth of focal point
            fx, fy, fz = camera.GetFocalPoint()
            self._Renderer.SetWorldPoint(fx, fy, fz, 1.0)
            self._Renderer.WorldToDisplay()
            z = self._Renderer.GetDisplayPoint()[2]

            # find world-coord from mouse position
            self._Renderer.SetDisplayPoint(event.x, event.y, z)
            self._Renderer.DisplayToWorld()
            x0, y0, z0, w = self._Renderer.GetWorldPoint()

            position = (x0 / w, y0 / w, z0 / w)
            normal = camera.GetViewPlaneNormal()
            vector = camera.GetViewUp()

        self._UpdateCursorTransform(position, normal, vector)

    #--------------------------------------
    def _ShowCursor(self):
        if self._CursorShownFlag:
            return

        self._CursorShownFlag = 1

        if self._Cursors:
            try:
                self._Renderer.GetRenderWindow().HideCursor()
            except:
                try:
                    self._Renderer.GetRenderWindow()\
                        .GetInteractor().HideCursor()
                except:
                    pass

        for cursor in self._Cursors:
            cursor.SetVisibility(self._Renderer, 1)

    def _HideCursor(self):
        if not self._CursorShownFlag:
            return

        self._CursorShownFlag = 0

        try:
            self._Renderer.GetRenderWindow().ShowCursor()
        except:
            try:
                self._Renderer.GetRenderWindow()\
                    .GetInteractor().ShowCursor()
            except:
                pass

        for cursor in self._Cursors:
            cursor.SetVisibility(self._Renderer, 0)

    #--------------------------------------
    def DoSmartPick(self, event):
        """Internal method to do a pick at the event x,y coordinates.

        Perform a pick in order to convert the x,y display coords
        of the event into x,y,z world coordinates according to where
        the view ray intersects each ActorFactory under the mouse.

        The pick results are stored in the _PickInformationList
        variable.

        """

        event.picker = self._Picker

        self._Picker.Pick(event.x, event.y, 0, self._Renderer)
        cameraPosition = event.renderer.GetActiveCamera().GetPosition()
        pickInfoList = []

        # query all factories for positions and normals
        for factory in self._ActorFactories:
            for pickInfo in factory.GetPickList(event):
                position = pickInfo.position
                pickInfo.distance = \
                    math.sqrt(((position[0] - cameraPosition[0]) ** 2) +
                              ((position[1] - cameraPosition[1]) ** 2) +
                              ((position[2] - cameraPosition[2]) ** 2))
                pickInfo.factory = factory
                pickInfoList.append(pickInfo)

        # sort the list
        pickInfoList.sort(
            lambda pn1, pn2: 2 * (pn1.distance > pn2.distance) - 1)
        self._PickInformationList = pickInfoList

        return pickInfoList

    #--------------------------------------
    def DoStartMotion(self, event):
        """Generic handler for ButtonPress events.

        This handler just saves the initial mouse position in
        the _StartX,_StartY variables and also initializes
        the _LastX,_LastY variables.

        """
        self._LastX = event.x
        self._LastY = event.y
        self._StartX = event.x
        self._StartY = event.y

    def DoEndMotion(self, event):
        """Generic handler for ButtonRelease events.

        This handler does nothing.

        """
        pass

    def DoCameraRotate(self, event):
        """Mouse Motion handler for rotating the scene."""
        x = event.x
        y = event.y

        width, height = self._Renderer.GetSize()[:2]
        x0, y0 = self._Renderer.GetOrigin()

        camera = self._Renderer.GetActiveCamera()
        if self._StartY - y0 < height / 8:
            camera.Roll(x - self._LastX)
        else:
            camera.Azimuth(self._LastX - x)
            camera.Elevation(self._LastY - y)
        camera.OrthogonalizeViewUp()

        self._LastX = x
        self._LastY = y

        self._Renderer.ResetCameraClippingRange()
        self.Modified()  # JDG

    def DoCameraPan(self, event):
        """Mouse Motion handler for panning the scene."""
        x = event.x
        y = event.y

        renderer = self._Renderer
        camera = self._Renderer.GetActiveCamera()
        pPoint0, pPoint1, pPoint2 = camera.GetPosition()
        fPoint0, fPoint1, fPoint2 = camera.GetFocalPoint()

        if (camera.GetParallelProjection()):
            renderer.SetWorldPoint(fPoint0, fPoint1, fPoint2, 1.0)
            renderer.WorldToDisplay()
            fx, fy, fz = renderer.GetDisplayPoint()
            renderer.SetDisplayPoint(fx - x + self._LastX,
                                     fy - y + self._LastY,
                                     fz)
            renderer.DisplayToWorld()
            fx, fy, fz, fw = renderer.GetWorldPoint()
            camera.SetFocalPoint(fx, fy, fz)

            renderer.SetWorldPoint(pPoint0, pPoint1, pPoint2, 1.0)
            renderer.WorldToDisplay()
            fx, fy, fz = renderer.GetDisplayPoint()
            renderer.SetDisplayPoint(fx - x + self._LastX,
                                     fy - y + self._LastY,
                                     fz)
            renderer.DisplayToWorld()
            fx, fy, fz, fw = renderer.GetWorldPoint()
            camera.SetPosition(fx, fy, fz)

        else:
            (fPoint0, fPoint1, fPoint2) = camera.GetFocalPoint()
            # Specify a point location in world coordinates
            renderer.SetWorldPoint(fPoint0, fPoint1, fPoint2, 1.0)
            renderer.WorldToDisplay()
            # Convert world point coordinates to display coordinates
            dPoint = renderer.GetDisplayPoint()
            focalDepth = dPoint[2]

            width, height = self._Renderer.GetRenderWindow().GetSize()[:2]
            xmin, ymin, xmax, ymax = self._Renderer.GetViewport()

            aPoint0 = width * 0.5 * (xmax + xmin) + (x - self._LastX)
            aPoint1 = height * 0.5 * (ymax + ymin) + (y - self._LastY)

            renderer.SetDisplayPoint(aPoint0, aPoint1, focalDepth)
            renderer.DisplayToWorld()

            (rPoint0, rPoint1, rPoint2, rPoint3) = renderer.GetWorldPoint()
            if (rPoint3 != 0.0):
                rPoint0 = rPoint0 / rPoint3
                rPoint1 = rPoint1 / rPoint3
                rPoint2 = rPoint2 / rPoint3

            camera.SetFocalPoint((fPoint0 - rPoint0) + fPoint0,
                                 (fPoint1 - rPoint1) + fPoint1,
                                 (fPoint2 - rPoint2) + fPoint2)

            camera.SetPosition((fPoint0 - rPoint0) + pPoint0,
                               (fPoint1 - rPoint1) + pPoint1,
                               (fPoint2 - rPoint2) + pPoint2)

        self._LastX = x
        self._LastY = y
        self.Modified()  # JDG

    def DoCameraZoom(self, event):
        """Mouse motion handler for zooming the scene."""
        x = event.x
        y = event.y

        renderer = self._Renderer
        camera = self._Renderer.GetActiveCamera()

        zoomFactor = math.pow(
            1.02, (0.5 * (y - self._LastY + x - self._LastX)))

        if camera.GetParallelProjection():
            parallelScale = camera.GetParallelScale() / zoomFactor
            camera.SetParallelScale(parallelScale)
        else:
            camera.Dolly(zoomFactor)
            renderer.ResetCameraClippingRange()

        self._LastX = x
        self._LastY = y
        self.Modified()  # JDG

    #--------------------------------------
    def ConnectCursor(self, cursor):
        """Connect a cursor to this RenderPane.

        The cursor is an ActorFactory that follows the mouse.

        """
        self._Cursors.append(cursor)
        cursor.AddToRenderer(self._Renderer)
        if self._CursorShownFlag:
            if len(self._Cursors) == 1:
                try:
                    self._Renderer.GetRenderWindow()\
                        .GetInteractor().HideCursor()
                except:
                    pass
        else:
            cursor.SetVisibility(self._Renderer, 0)

        self.Modified()

    def DisconnectCursor(self, cursor):
        """Disconnect a cursor from this RenderPane."""
        cursor.RemoveFromRenderer(self._Renderer)
        if self._CursorShownFlag:
            if len(self._Cursors) == 0:
                try:
                    self._Renderer.GetRenderWindow()\
                        .GetInteractor().ShowCursor()
                except:
                    pass

        self._Cursors.remove(cursor)
        self.Modified()

    def GetCursors(self):
        return self._Cursors

    #--------------------------------------
    def AddWidget(self, widget):
        """Add a widget to the RenderPane."""
        self._Widgets.append(widget)
        widget.ConfigureGeometry(self._Renderer.GetOrigin(),
                                 self._Renderer.GetSize())
        widget.AddToRenderer(self._Renderer)
        self.Modified()

    def RemoveWidget(self, widget):
        """Remove a widget from the RenderPane."""
        self._Widgets.remove(widget)
        widget.RemoveFromRenderer(self._Renderer)
        self.Modified()

    def GetWidgets(self):
        """Get a list of all widgets."""
        return self._Widgets

    #--------------------------------------
    def ConnectActorFactory(self, actorFactory):
        """Connect an ActorFactory to this RenderPane.

        This causes the ActorFactory to generate a set of actors for
        this RenderPane.  An ActorFactory can be connected to more
        than one RenderPane, but maintains a separate set of actors
        for each.

        """
        self._ActorFactories.append(actorFactory)
        actorFactory.AddToRenderer(self._Renderer)
        self.Modified()

    def DisconnectActorFactory(self, actorFactory):
        """Disconnect an ActorFactory from this RenderPane."""
        if actorFactory is None:
            logging.error("actorFactory is None - ignoring")
            return
        actorFactory.RemoveFromRenderer(self._Renderer)
        if actorFactory in self._ActorFactories:
            self._ActorFactories.remove(actorFactory)
            self.Modified()

    def GetActorFactories(self):
        """Get a list of all connected ActorFactories."""
        return self._ActorFactories

    #--------------------------------------
    def GetCurrentActor(self):
        """Get the current vtkActor."""
        return self._CurrentActor

    def GetCurrentActorFactory(self):
        """Get the current ActorFactory."""
        return self._CurrentActorFactory

    #--------------------------------------
    def Modified(self):
        """Update the timestamp."""
        self._MTime.Modified()

    def HasChangedSince(self, sinceMTime):
        """Determine whether this object has changed since *sinceMTime* .

        Given an MTime returned by VTK, this method check whether this
        object or a child component has a timestamp that is more recent.

        """
        if self._MTime.GetMTime() > sinceMTime:
            return 1
        if self._Renderer.GetMTime() > sinceMTime:
            return 1
        for factory in self._ActorFactories:
            if factory.HasChangedSince(sinceMTime):
                return 1
        for widget in self._Widgets:
            if widget.HasChangedSince(sinceMTime):
                return 1
        return 0

    def GetRenderTime(self):
        """Get the MTime for the last render."""
        return self._Renderer.GetMTime()  # JDG
        # return self._RenderTime.GetMTime()

    #--------------------------------------
    def StartRender(self):
        """This method is called immediately before a render is performed."""

        for cursor in self._Cursors:
            if cursor.GetVisibility(self._Renderer):
                cursor.Update(self._Renderer)

        # light follows camera
        camera = self._Renderer.GetActiveCamera()
        self._Renderer.GetLights().InitTraversal()
        light = self._Renderer.GetLights().GetNextItem()
        if light is None:
            light = vtk.vtkLight()
            self._Renderer.AddLight(light)
        light.SetPosition(camera.GetPosition())
        light.SetFocalPoint(camera.GetFocalPoint())

    #--------------------------------------
    def ResetView(self):
        """Reset the camera to point at the center of the scene."""
        # we have to remove the cursors because they aren't part of the
        #  real scene
        if self._CursorShownFlag:
            for cursor in self._Cursors:
                cursor.SetVisibility(self._Renderer, 0)
        self._Renderer.ResetCamera()
        if self._CursorShownFlag:
            for cursor in self._Cursors:
                cursor.SetVisibility(self._Renderer, 1)
        self.Modified()

    #--------------------------------------
    def Render(self, renderer=None):
        """Render the PaneFrame that holds this RenderPane.

        This method is not the equivalent of vtkRenderer.Render(),
        rather it is more the equivalent of
        vtkRenderer.GetRenderWindow().Render().

        """
        # the 'renderer=None' is just for backwards compatibility
        mywindow = self._Renderer.GetRenderWindow()
        # have to render the PaneFrame, to ensure that
        # all RenderPanes in that frame are updated properly
        for frame in PaneFrame.PaneFrame.AllPaneFrames:
            if frame.GetRenderWindow() == mywindow:
                frame.Render()
                break

    #--------------------------------------
    def Start(self):
        """For programs with only one RenderPane, start interaction.

        If your program has more than one RenderPane but only one PaneFrame,
        the use PaneFrame.Start().  If you are using a particular GUI
        toolkit, then you should start the interaction loop for the GUI
        toolkit rather than use Start().

        """
        PaneFrame.PaneFrame.AllPaneFrames[0].Start()

    #--------------------------------------
    def ScheduleOnce(self, millisecs, func):
        """Schedule a function to be called after *n* milliseconds.

        The function should not take any parameters.

        Result:

        An ID that can be used to UnSchedule() this fuction.

        """
        return PaneFrame.PaneFrame.AllPaneFrames[0].ScheduleOnce(millisecs, func)

    def ScheduleEvery(self, millisecs, func):
        """Schedule a function to be called every *n* milliseconds.

        The function should not take any parameters.

        Result:

        An ID that can be used to UnSchedule() this fuction.

        """
        return PaneFrame.PaneFrame.AllPaneFrames[0].ScheduleEvery(millisecs, func)

    def UnSchedule(self, id):
        """Unschedule a previously scheduled function."""
        PaneFrame.PaneFrame.AllPaneFrames[0].UnSchedule(id)

    #--------------------------------------
    def _UpdateCursorTransform(self, position, normal, vector):
        # helper function to set cursor transform from
        #  position and normal

        if not normal:
            normal = (1.0, 0.0, 0.0)
        if not vector:
            vector = (0.0, 1.0, 0.0)

        n_x, n_y, n_z = normal
        o_x, o_y, o_z = vector

        # normalize the normal
        norm = math.sqrt(n_x * n_x + n_y * n_y + n_z * n_z)

        if (norm != 0):
            n_x = n_x / norm
            n_y = n_y / norm
            n_z = n_z / norm
        else:
            n_x = 1.0
            n_y = 0.0
            n_z = 0.0

        # force the vector to be perpendicular to the normal
        dotprod = n_x * o_x + n_y * o_y + n_z * o_z

        o_x = o_x - n_x * dotprod
        o_y = o_y - n_y * dotprod
        o_z = o_z - n_z * dotprod

        norm = math.sqrt(o_x * o_x + o_y * o_y + o_z * o_z)

        # calculate the third vector from the first two
        if (norm != 0):
            o_x = o_x / norm
            o_y = o_y / norm
            o_z = o_z / norm

        # if we don't have a valid vector
        elif (n_x * n_x > n_y * n_y and n_x * n_x > n_z * n_z):
            o_x = n_z / math.sqrt(n_x * n_x + n_z * n_z)
            o_y = 0
            o_z = -n_x / math.sqrt(n_x * n_x + n_z * n_z)
        elif (n_y * n_y > n_z * n_z):
            o_y = n_x / math.sqrt(n_y * n_y + n_x * n_x)
            o_z = 0
            o_x = -n_y / math.sqrt(n_y * n_y + n_x * n_x)
        else:
            o_z = n_y / math.sqrt(n_z * n_z + n_y * n_y)
            o_x = 0
            o_y = -n_z / math.sqrt(n_z * n_z + n_y * n_y)

        # use cross product
        p_x = n_y * o_z - n_z * o_y
        p_y = n_z * o_x - n_x * o_z
        p_z = n_x * o_y - n_y * o_x

        # set up rotation matrix
        matrix = (n_x, o_x, p_x, position[0],
                  n_y, o_y, p_y, position[1],
                  n_z, o_z, p_z, position[2],
                  0.0, 0.0, 0.0, 1.0)

        for cursor in self._Cursors:
            cursor.GetTransform().SetMatrix(matrix)

    #--------------------------------------
    def SetBorderWidth(self, borderwidth):
        """Set the width of the border around the RenderPane."""

        if self._BorderWidth == borderwidth:
            return

        if borderwidth == 0:
            self._BorderWidth = borderwidth
            self._Renderer.RemoveActor2D(self._BorderActor)
            self._BorderActor = None

        if self._BorderWidth == 0:
            self._BorderWidth = borderwidth
            width, height = self._Renderer.GetSize()
            self._CreateBorder(width, height)

    def GetBorderWidth(self):
        """Get the width of the border around the RenderPane."""
        return self._BorderWidth

    #--------------------------------------
    def SetBorderColor(self, *args):
        """Set the (*r*,*g*,*b*) color of the border around the RenderPane."""
        if len(args) == 1:
            args = args[0]

        self._BorderColor = args
        try:
            if self._BorderColor:
                self._BorderActor.GetProperty().SetColor(self._BorderColor)
                self._BorderData.GetCellData().SetScalars(None)
                # print "Setting scalars to none"
            else:
                self._BorderData.GetCellData().SetScalars(self._BorderScalars)
        except:
            pass

    def GetBorderColor(self):
        """Get the (*r*,*g*,*b*) color of the border around the RenderPane."""
        return self._BorderColor

    #--------------------------------------
    def _SetBorderPoints(self, width=None, height=None):
        # set the border to the size of the Renderer
        if self._BorderWidth == 0:
            return

        if width == None or height is None:
            width, height = self._Renderer.GetSize()

        points = self._BorderPoints
        borderwidth = self._BorderWidth

        points.SetNumberOfPoints(8)
        points.SetPoint(0, 0,                  0,                   0)
        points.SetPoint(1, borderwidth,        borderwidth,         0)
        points.SetPoint(2, width,              0,                   0)
        points.SetPoint(3, width - borderwidth,  borderwidth,         0)
        points.SetPoint(4, width,              height,              0)
        points.SetPoint(5, width - borderwidth,  height - borderwidth,  0)
        points.SetPoint(6, 0,                  height,              0)
        points.SetPoint(7, borderwidth,        height - borderwidth,  0)

    #--------------------------------------
    def _CreateBorder(self, width, height):
        # one-shot border creation

        borderwidth = self._BorderWidth

        self._BorderPoints = vtk.vtkPoints()
        self._SetBorderPoints(width, height)

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

        scalars = vtk.vtkUnsignedCharArray()
        scalars.SetNumberOfTuples(4)
        scalars.SetTuple1(0, 190)
        scalars.SetTuple1(1, 190)
        scalars.SetTuple1(2, 64)
        scalars.SetTuple1(3, 64)

        data = vtk.vtkPolyData()
        data.SetPoints(self._BorderPoints)
        data.SetPolys(cells)
        if not self._BorderColor:
            data.GetCellData().SetScalars(scalars)

        mapper = vtk.vtkPolyDataMapper2D()

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            mapper.SetInputData(data)
        else:
            mapper.SetInput(data)

        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)
        actor.SetPosition(0, 0)
        if self._BorderColor:
            actor.GetProperty().SetColor(self._BorderColor)

        self._BorderScalars = scalars
        self._BorderData = data
        self._BorderActor = actor
        self._Renderer.AddActor2D(actor)

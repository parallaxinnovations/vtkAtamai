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
    'module_name': '$RCSfile: ActorFactory.py,v $',
    'creator': 'David Gobbi <dgobbi@atamai.com>',
    'project': 'Atamai Surgical Planning',
    #
    #  Current Information
    #
    'author': '$Author: jeremy_gill $',
    'version': '$Revision: 1.3 $',
    'date': '$Date: 2008/05/29 01:17:55 $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

"""
ActorFactory - the base type for 3D virtual objects

  An ActorFactory is a virtual object that can be displayed in
  one or more RenderPanes simultaneously.

  There can be many vtkActors associated with an ActorFactory.
  Each time the ActorFactory is connected to a RenderPane, the
  ActorFactory will generate a new set of actors for that pane.

  ActorFactories can be built hierarchically, i.e. several
  ActorFactories can be gathered together as Children of a
  single Parent and be manipulated as a single unit.

  Finally, an ActorFactory can receive events (usually mouse button
  and motion events passed down from the RenderPane).  These are used
  to drive user interaction of the actors.

  To derive your own class from the ActorFactory base class, you must
  override the '_MakeActors()' method, which generates a fresh tuple of
  actors as well as any other entities that cannot be shared between
  rendering contexts.  The '_MakeActors()' method should call the
  '_NewActor()' method to create fresh actors, instead of simply
  invoking 'vtkActor()'.


Derived From:

  EventHandler

See Also:

  RenderPane, OutlineFactory, OrthoPlanesFactory

Initialization:

  ActorFactory()

Public Methods:

  The following methods are general use:

    GetTransform()      -- get the transform for the actors, to change the
                           transform use
                           factory.GetTransform().SetInput(*transform*)

    HasChangedSince(*time*) -- true if the factory has been modified since the
                           specified time, you must override this if your
                           factory has any inputs or other externally
                           modifyable VTK objects that need to be checked

    GetClassName(*name*) -- get the class name

    IsA(*classname*)     -- determine whether this factory belongs to
                           either the specified class or a subclass

    GetRenderers()      -- return a list of all renderers

    GetRenderWindows()  -- return a list of all RenderWindows

    GetActors(*renderer*) -- get a list of the actors owned by the factory
                           that are currently in the specified renderer,
                           including those of any child factories

    Render()            -- render all PaneFrames that contain this
                           ActorFactory

  The following methods are used primarily by RenderPane:

    AddToRenderer(*renderer*)  -- add the actors to the renderer

    RemoveFromRenderer(*renderer*) -- remove the actors from a renderer

    GetPickList(*event*)  -- for use after a pick, returns a list of
                           PickInformation objects, one per each picked
                           actor that belongs to the factory or its children
                           (see the PickInformation class below for more info)

    HandleEvent(*event*)  -- pass an event to the ActorFactory

  The following methods are used primarily inside derived classes:

    AddChild(*factory*)    -- add a child ActorFactory

    RemoveChild(*factory*) -- remove a child ActorFactory

    GetChildren()       -- return a list of all children

    GetChild(*name*)    -- get the child with the specified name

    Modified()          -- update the Modification time - the factory should
                         call this whenever an attribute is modified

    ScheduleOnce(*ms*,*func*) -- schedule a function to be called after
                           the specified number of milliseconds
                           (returns an id you can use to unschedule)

    ScheduleEvery(*ms*,*func*) -- schedule a function to be called every
                           time the specified number of millisecs
                           have elapsed
                           (returns an id you can use to unschedule)

    UnSchedule(*id*)    -- remove the specified item from the schedule

Protected Methods:

    _MakeActors()       -- generate a list of actors to be displayed in a
                           renderer (this method should overridden in
                           all ActorFactory sub-classes)

    _NewActor()         -- return a new actor for use in the factory

    _FreeActor()        -- free an actor created by NewActor()


Protected Attributes:

    _Name          -- the name of this factory

    _MTime         -- vtkTimeStamp a la vtkObject, use Modified() to change

    _Renderers     -- a list of renderers that this factory is attached to

    _ActorDict     -- a dictionary which, given a renderer,
                      provides a list of the factory's actors which are in
                      that renderer (this does _not_ include the childrens'
                      actors)

    _Children      -- a list of actor factories that are children of this one

    _Transform     -- the default transform applied to all the actors



Important information about actors:

  An ActorFactory must maintain a separate list of actors for each
  vtkRenderer.  This is due to a limitation in VTK which sometimes
  makes it impossible for a vtkActor to be shared between more than
  one renderer.  This means that if an ActorFactory is not connected
  to any Renderer or RenderPane, it should contain no actors.  You
  should never create actors within the '__init__' method.  Generally
  you should create actors within the _MakeActors() method and
  nowhere else.

  This makes things complicated if you want to add more actors to
  the factory while it is connected to a renderer.  The easiest thing
  to do is to make a child ActorFactory class for each "piece" you
  want to add, and use the AddChild() method and RemoveChild() method
  to add and remove pieces as needed.  Otherwise, see the
  ThinPlateSplineFactory class as an example for adding and removing
  actors from a factory on-the-fly: it is always necessary to create
  a new actor for each renderer that is connected to the factory.


A little extra info about events:

  See EventHandler for general info about binding/handling events.

  All mouse-related events that are sent to an ActorFactory must have
  the following attributes:

   - event.x, event.y  - mouse position (from lower-left of window)

   - event.actor       - frontmost actor under cursor

   - event.renderer    - renderer that mouse is in

  In addition, if the event was a ButtonPress event then the following
  attribute must be present:

   - event.picker      - picker from the last ButtonPress pick


A little extra info about transformations:

  All the actors produced by an ActorFactory share the same vtkTransform
  as their UserTransform.  The UserTransform must not be used for other
  purposes.

  You can change the position/orientation of an actor factory by directly
  modifying the transformation, e.g.

    - actorFactory.GetTransform().Identity()

    - actorFactory.GetTransform().Translate(*x*,*y*,*z*)

  There is no SetTransform() method.  Instead, you should
  use

    - actorFactory.GetTransform().SetInput(*newTransform*)

  which has the same effect as the vtkActor SetUserTransform()
  or SetUserMatrix() methods.


A little extra info about child components:

  The best way to access a component of an ActorFactory is by name,
  i.e. actorFactory.GetChild(*name*) where *name* is the same string
  returned by child.GetName().  The default name of an ActorFactory is the
  class name without "Factory."

  The transformation of a component ActorFactory is, by default, relative to
  the position/orientation of its parent.  If you don't want this behaviour,
  then you must call child.GetTransform().SetInput(None) after
  actorFactory.AddChild(*child*) has been called.

"""

#======================================
from zope import interface
from vtkAtamai.interfaces import IActorFactory
import EventHandler
import PaneFrame
import vtk
import logging

#======================================


class PickInformation(object):

    """A helper class that contains information from about a pick."""

    def __init__(self):
        self.actor = None
        self.position = None  # pick position (x,y,z)
        self.normal = None   # normal to actor at pick position
        self.vector = None   # orientation about normal
        #    (i.e. a vector perpendicular to the normal)


class ActorFactory(EventHandler.EventHandler):

    """The base type for virtual objects that are displayed on the screen.

    An ActorFactory object represents a 3D object of arbitrary complexity
    that is displayed in one or more vtkRenderers.  Each time the
    ActorFactory is added to a new renderer, it generates a new set of
    actors and places them in the renderer.

    Mouse and keyboard events can be handled by an actor factory, via
    the inherited EventHandler class.

    """

    interface.implements(IActorFactory)

    def __init__(self):
        EventHandler.EventHandler.__init__(self)

        # default name is the class name, minus the "Factory"
        self._Name = self.__class__.__name__
        if self._Name[-7:] == 'Factory':
            self._Name = self._Name[0:-7]

        # Store the modified time
        self._MTime = vtk.vtkObject()
        self._RenderTime = vtk.vtkObject()

        # list of renderers the actors are displayed in
        self._Renderers = []
        # dictionary of actors for each renderer
        self._ActorDict = {}

        # ActorFactories which are children of this one
        self._Children = []

        # the transform for all of the actors
        self._Transform = vtk.vtkTransform()

        # this transform is used as a spare
        self._DummyTransform = vtk.vtkTransform()

    def tearDown(self):

        # tear down any children
        for child in self._Children[:]:
            child.tearDown()
            self._Children.remove(child)

        self.RemoveAllObservers()
        self.RemoveAllEventHandlers()

        # remove additional actors
        for renderer in self._ActorDict.keys():
            self.RemoveFromRenderer(renderer)
            del(self._ActorDict[renderer])

        del(self._DummyTransform)
        del(self._Transform)
        del(self._RenderTime)

    #--------------------------------------
    # Removed because it blocks proper GC, the ActorFactory is
    # never going to be deallocated until it has been disconnected
    # from the RenderPanes anyway.

    def __del__(self):
        print 'deleting {0}'.format(self.__class__)

        for renderer in self._Renderers:
            self.RemoveFromRenderer(renderer)

    #--------------------------------------
    def AddToRenderer(self, renderer):
        """Create a set of actors and add them to the renderer."""
        actors = self._MakeActors()

        # handle dictionaries
        if isinstance(actors, dict):
            actors_list = actors.values()
        else:
            actors_list = actors

        for actor in actors_list:
            if actor.IsA("vtkFollower"):
                actor.SetCamera(renderer.GetActiveCamera())
            renderer.AddActor(actor)

        self._Renderers.append(renderer)
        self._ActorDict[renderer] = actors
        for child in self._Children:
            child.AddToRenderer(renderer)

    def RemoveFromRenderer(self, renderer):
        """Remove all our actors from the render and delete them."""
        for child in self._Children[:]:
            child.RemoveFromRenderer(renderer)

        if renderer in self._ActorDict:
            actors = self._ActorDict[renderer]
            if self._Renderers.count(renderer) > 0:
                self._Renderers.remove(renderer)
            if isinstance(actors, list):
                # classic (list)
                for actor in actors:
                    renderer.RemoveActor(actor)
                    self._FreeActor(actor)
            else:
                # new (dictionary)
                for name in actors:
                    actor = actors[name]
                    renderer.RemoveActor(actor)
                    self._FreeActor(actor)

    #--------------------------------------
    def AddChild(self, child):
        """Add another ActorFactory as part of this ActorFactory.

        Parameters:

        *child* - an ActorFactory

        This allows an actor factor to be built as an assembly of
        smaller factories.  The base transform for all children
        is set to the transform of the parent by default, so that
        when the parent's transform is modified the childrens' transforms
        are also modified.  If this behaviour is not desired, then
        call child.GetTransform().SetInput(None) to disconnect the
        child's transform from the parent's transform.

        """
        for renderer in self._Renderers:
            child.AddToRenderer(renderer)
        # chain the transformations together
        if child.GetTransform() != self._Transform:
            child.GetTransform().SetInput(self._Transform)
        self._Children.append(child)
        self.Modified()

    def RemoveChild(self, child):
        """Remove a child component from from this ActorFactory."""
        if child in self._Children:
            self._Children.remove(child)
        for renderer in self._Renderers:
            child.RemoveFromRenderer(renderer)
        self.Modified()

    def GetChildren(self):
        """Get a list of all the children."""
        return self._Children

    def GetChild(self, name):
        """Get a child by name.

        The name of an ActorFactory is set using the SetName() method.

        """
        for child in self._Children:
            if child._Name == name:
                return child
        raise KeyError("no component named " + name)

    #--------------------------------------
    def GetRenderWindows(self, renfound=None, winfound=None):
        """Get all vtkRenderWindows in which this ActorFactory is rendered.

        This method is used internally to handle some tricky details
        related to double-buffering.  When an ActorFactory must be rendered,
        a list of vtkRenderWindows must be created with each vtkRenderWindow
        appearing only once in the list.  The Render method will render
        each window in turn, and then swap the back buffer to the front.
        This must be done properly or the animation will look very choppy.

        """
        if not renfound:
            renfound = []
        if not winfound:
            winfound = []

        windows = []
        for ren in self._Renderers:
            if not (ren in renfound):
                renfound.append(ren)
                win = ren.GetRenderWindow()
                if not (win in winfound):
                    winfound.append(win)
                    windows.append(win)

        for child in self._Children:
            windows = windows + child.GetRenderWindows(renfound, winfound)

        return windows

    #--------------------------------------
    def GetRenderers(self):
        """Get all vtkRenderers that our actors have been added to."""
        return self._Renderers

    def GetActors(self, renderer):
        """Get a list of actors that we have inside the specified renderer.

        The list of actors includes all of the actors from the children
        of this ActorFactory.

        """
        actors = []
        if renderer in self._ActorDict:
            actors = self._ActorDict[renderer]
            if isinstance(actors, dict):
                # new (dictionary)
                actors = actors.values()
            else:
                # class (list?)
                actors = list(actors)
        for child in self._Children:
            actors = actors + child.GetActors(renderer)
        return actors

    #--------------------------------------
    def GetPickList(self, event):
        """Get a list of PickInformation objects for an event.

        The purpose of this method is to determine which actors were under
        the mouse when a pick occurred.

        This method can only be called after a pick has been performed,
        and the event must have an "event.picker" attribute that is the
        vtkPicker that was used to perform the pick.  It returns an
        unsorted list of PickInformation objects, which have the following
        attributes:

         - actor     - the vtkActor that was picked

         - position  - (x,y,z) pick position in VTK world coordinates

         - normal    - the normal to a surface at the pick position

         - vector    - a vector to specify an orientation about the normal

        The normal and vector may be set to 'None' of no suitable values
        exist.

        """
        picklist = []

        actors = self._ActorDict[event.renderer]

        # handle new-style actor dictionary
        if isinstance(actors, dict):
            actors = actors.values()

        if actors:
            pickedActors = event.picker.GetProp3Ds()
            pickedPositions = event.picker.GetPickedPositions()
            transform = self._DummyTransform

            for actor in actors:

                i = pickedActors.IsItemPresent(actor)

                if i != 0:
                    try:
                        dataSet = actor.GetMapper().GetInputAsDataSet()
                    except:
                        dataSet = actor.GetMapper().GetInput()
                    position = pickedPositions.GetPoint(i - 1)

                    # transform the position into data coordinates
                    transform.SetMatrix(actor.GetMatrix())
                    dataPos = transform.GetInverse().TransformPoint(position)
                    pointId = dataSet.FindPoint(dataPos[0],
                                                dataPos[1],
                                                dataPos[2])
                    normals = dataSet.GetPointData().GetNormals()

                    if (normals):
                        # transform the normal back into world coordinates
                        try:  # VTK 3.x
                            normal = transform.TransformNormal(
                                normals.GetNormal(pointId))
                        except:
                            normal = transform.TransformNormal(
                                normals.GetTuple3(pointId))
                        normal = (normal[0], normal[1], normal[2])
                    else:
                        normal = None

                    info = PickInformation()
                    info.actor = actor
                    info.position = position
                    info.normal = normal

                    picklist.append(info)

        for child in self._Children:
            picklist = picklist + child.GetPickList(event)

        return picklist

    #--------------------------------------
    def HasChangedSince(self, sinceMTime):
        """Determine whether this object has changed since *sinceMTime* .

        Given an MTime returned by VTK, this method check whether this
        object or a child component has a timestamp that is more recent.

        """
        if self._MTime.GetMTime() > sinceMTime:
            return 1
        if self._Transform and self._Transform.GetMTime() > sinceMTime:
            return 1
        for child in self._Children:
            if child.HasChangedSince(sinceMTime):
                return 1
        return 0

    def Modified(self):
        """Update the timestamp for this object."""
        if self._MTime:
            self._MTime.Modified()

    def AddObserver(self, eventname, callback):
        return self._MTime.AddObserver(eventname, callback)

    def RemoveObserver(self, observer_index):
        return self._MTime.RemoveObserver(observer_index)

    def RemoveAllObservers(self):
        if self._MTime:
            self._MTime.RemoveAllObservers()

    def InvokeEvent(self, eventname):
        self._MTime.InvokeEvent(eventname)

    #--------------------------------------
    def GetClassName(self):
        """Get the name of this object's class.

        This method is just syntactic sugar for VTK folks.  Do not
        override this method in derived classes.

        """
        return self.__class__.__name__

    def IsA(self, classname):
        """Determine whether this object was derived from the specified class.

        Note that you must pass a string to this method, not a "class"
        object as for the python isinstance() function.  This method
        is meant for people who are familiar with VTK but less familiar
        with python.

        """
        global IsA_Helper  # see Learning Python page 120

        def IsA_Helper(cls, classname):
            if cls.__name__ == classname:
                return 1
            for base in cls.__bases__:
                if IsA_Helper(base, classname):
                    return 1
            return 0

        return IsA_Helper(self.__class__, classname)

   #--------------------------------------
    def GetTransform(self):
        """Get the transform for this object.

        You can link another transform to this one using the
        vtkTransform.SetInput() method.

        """
        return self._Transform

    #--------------------------------------
    def Render(self, renderer=None):
        """Update all the vtkRenderWindows associated with this object.

        Note that this behaviour is not analogous to vtkActor.Render().
        The render is not performed if this object has not been modified
        since the last render.  The internals of this method are a little
        bit complicated to ensure that all the rendering takes place in
        the back buffer and that only a single buffer swap is done.

        """
        # 'renderer=None' is for backwards compatibility
        if not self.HasChangedSince(self._RenderTime.GetMTime()):
            return

        windows = self.GetRenderWindows()
        # render all frames that contain this factory
        rendereredframes = []
        for frame in PaneFrame.PaneFrame.AllPaneFrames:
            if frame._RenderWindow in windows:
                frame._RenderWindow.SwapBuffersOff()
                if frame.Render():
                    rendereredframes.append(frame)
                frame._RenderWindow.SwapBuffersOn()

        for frame in rendereredframes:
            frame._RenderWindow.Frame()

        self._RenderTime.Modified()

    #--------------------------------------
    def ScheduleOnce(self, millisecs, func):
        """Schedule a function to be called after *n* milliseconds.

        The function should not take any parameters.

        Result:

        An ID that can be used to UnSchedule() this function.

        """
        return PaneFrame.PaneFrame.AllPaneFrames[0].ScheduleOnce(millisecs, func)

    def ScheduleEvery(self, millisecs, func):
        """Schedule a function to be called every *n* milliseconds.

        The function should not take any parameters.

        Result:

        An ID that can be used to UnSchedule() this function.

        """
        return PaneFrame.PaneFrame.AllPaneFrames[0].ScheduleEvery(millisecs, func)

    def UnSchedule(self, id):
        """Unschedule a previously scheduled function."""

        PaneFrame.PaneFrame.AllPaneFrames[0].UnSchedule(id)

    #--------------------------------------
    def _MakeActors(self):
        """Generate a set of actors.  Override in derived classes.

        Generate a list of all the vtkActors necessary to display this
        object in a vtkRenderer (not including actors for child components).
        Because the sharing of actors between renderers is not supported
        in VTK (it sometimes works and sometimes doesn't) the _MakeActors()
        method must create a fresh set of actors.

        Each actor should be create by a call to _NewActor(), rather than
        by a call to the vtkActor() constructor.

        """
        return []

    def _NewActor(self):
        """Create a new actor and link its transform to the factory.

        This method returns a new actor where the UserTransform of
        the actor is set to the Transform for this ActorFactory.

        """
        actor = vtk.vtkActor()
        actor.SetUserTransform(self._Transform)
        return actor

    def _FreeActor(self, actor):
        """This method is called whenever the factory deletes an actor.

        This method should be overridden in derived classes if there
        is any special cleanup that must be done when the actors are
        removed from a renderer and disposed of.

        """
        pass

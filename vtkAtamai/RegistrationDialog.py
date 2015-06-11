from Tkinter import *
import vtk

import math
import string

from PointerFactory import *


class CalibrationPointer(PointerFactory):

    def __init__(self, register):
        PointerFactory.__init__(self)
        self._Register = register
        self._Register.SetTrackedPointer(self)

    def __del__(self):
        self._Register.SetTrackedPointer(None)


def toanatomic(*coord):
    """toanatomic((x,y,z)) -> string

    convert a 3D coordinate into a string
    """
    if len(coord) == 1:
        x, y, z = coord[0]
    else:
        x, y, z = coord

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
    return "%6.2f%s %6.2f%s %6.2f%s" % (x, xs, y, ys, z, zs)


class RegistrationDialog(Frame):

    def __init__(self, master=None):
        if master is None:
            master = Toplevel()
            master.wm_title("Registration")
            Frame.__init__(self, master)
            self.pack(fill='both', expand='true')
        else:
            Frame.__init__(self, master)

        # the lists of landmarks
        self._SourceLandmarks = []
        self._TargetLandmarks = []

        # the index of the current landmark
        self._CurrentLandmark = 0

        # the transformation that matches the landmarks
        self._SourcePoints = vtk.vtkPoints()
        self._TargetPoints = vtk.vtkPoints()
        self._Transform = vtk.vtkLandmarkTransform()
        # self._Transform.SetModeToRigidBody()
        self._Transform.SetSourceLandmarks(self._SourcePoints)
        self._Transform.SetTargetLandmarks(self._TargetPoints)

        # the FiducialMarkerFactory draws the annotations on the image
        self._FiducialMarkerFactory = None

        # the OrthoPlanesFactory acts as the cursor for Source points
        self._OrthoPlanesFactory = None

        # the TrackedPointer acts as the cursor for Target points
        self._TrackedPointer = None

        # a list of 2D panes: whenever a point is chosen, these will
        # be adjusted to ensure that the point is visible
        self._Panes = []

        # build the user interface
        mframe = Frame(self)

        lframe = Frame(mframe)

        self._Scrollbar = Scrollbar(lframe,
                                    relief='sunken',
                                    bd=2)
        self._Listbox = Listbox(lframe,
                                yscrollcommand=self._Scrollbar.set,
                                # selectmode='multiple',
                                exportselection='false',
                                font='courier',
                                width=len(toanatomic(0, 0, 0)) + 6)
        self._Listbox.bind("<ButtonRelease-1>", self._Select)
        self._Listbox.bind("<KeyRelease>", self._SelectKey)
        # self._Listbox.bind("<KeyRelease-KP_Delete>",
        #                   lambda e,f=self._Delete: f())
        self._Listbox.bind("<KeyRelease-Delete>",
                           lambda e, f=self._Delete: f())
        # self._Listbox.bind("<KeyRelease-KP_Enter>",
        #                   lambda e,f=self._Add: f())
        self._Listbox.bind("<KeyRelease-Return>",
                           lambda e, f=self._Add: f())
        self._Scrollbar.config(command=self._Listbox.yview)

        self._Listbox.pack(side='left', fill='both', expand='true')
        self._Scrollbar.pack(side='left', fill='y')
        lframe.pack(side='left', fill='both', expand='true')

        bframe1 = Frame(mframe, bd=1)
        bframe = Frame(bframe1, relief='sunken', bd=1)

        self._AddB = Button(bframe, text='Add', command=self._Add)
        self._NextB = Button(bframe, text='Next', command=self._Next)
        self._SetB = Button(bframe, text='Set', command=self._Set)
        self._PrevB = Button(bframe, text='Prev', command=self._Prev)
        self._DeleteB = Button(bframe, text='Delete', command=self._Delete)

        self._AddB.pack(side='top', fill='both', expand='true')
        self._NextB.pack(side='top', fill='both', expand='true')
        self._SetB.pack(side='top', fill='both', expand='true')
        self._PrevB.pack(side='top', fill='both', expand='true')
        self._DeleteB.pack(side='top', fill='both', expand='true')
        bframe.pack(side='left', fill='both', expand='true')
        bframe1.pack(side='left', fill='both', expand='true')

        mframe.pack(side='top', fill='both', expand='true')

        self._StdDevLabel = Label(self,
                                  text='Standard Deviation:   --- mm  (0 Points)')
        self._StdDevLabel.pack(side='top', fill='y', expand='true')

        # self.bind('<Enter>',lambda e,s=self._Listbox: s.focus())

    def SetInstrumentTracker(self, tracker):
        self._InstrumentTracker = tracker
        tracker.RegisterInstrumentClass(
            lambda c=CalibrationPointer, s=self: c(s), 'UNKNOWN', '2000000')

    def SetTrackedPointer(self, pointer):
        if pointer == self._TrackedPointer:
            return
        if self._TrackedPointer:
            self._TrackedPointer.BindTrackerEvent("<ButtonPress-1>", None)
            self._TrackedPointer.BindTrackerEvent("<ButtonPress-2>", None)
            self._TrackedPointer.BindTrackerEvent("<ButtonPress-3>", None)
        if pointer:
            pointer.BindTrackerEvent("<ButtonPress-1>", self._PointerNext)
            pointer.BindTrackerEvent("<ButtonPress-2>", self._PointerSet)
            pointer.BindTrackerEvent("<ButtonPress-3>", self._PointerPrev)
        self._TrackedPointer = pointer

    def _PointerSet(self, event):
        self._Set()

    def _PointerNext(self, event):
        self._Next()

    def _PointerPrev(self, event):
        self._Prev()

    def SetFiducialMarkerFactory(self, factory):
        self._FiducialMarkerFactory = factory

    def GetFiducialMarkerFactory(self):
        return self._FiducialMarkerFactory

    def SetOrthoPlanesFactory(self, planes):
        self._OrthoPlanesFactory = planes

    def GetOrthoPlanesFactory(self):
        return self._OrthoPlanesFactory

    def AddPane(self, pane):
        self._Panes.append(pane)

    def RemovePane(self, pane):
        self._Panes.remove(pane)

    def GetPanes(self):
        return self._Panes

    def GetTransform(self):
        return self._Transform

    def _Select(self, event):
        i = self._Listbox.index('anchor')
        self.SetCurrentLandmark(i)

    def _SelectKey(self, event):
        i = self._Listbox.index('active')
        self.SetCurrentLandmark(i)

    def _Add(self):
        self.AddSourceLandmark(self._OrthoPlanesFactory.GetTransform().
                               TransformPoint(self._OrthoPlanesFactory.
                                              GetOrthoCenter()))

    def _Next(self):
        self.SetCurrentLandmark(self._CurrentLandmark + 1)

    def _Set(self):
        tool = self._TrackedPointer.GetTrackerTool()
        if tool.IsMissing() or tool.IsOutOfView():
            return

        tracker = tool.GetTracker()
        transform = vtk.vtkTransform()
        transform.SetMatrix(tracker.GetWorldCalibrationMatrix())
        self.SetTargetLandmark(self._CurrentLandmark,
                               transform.GetInverse().TransformPoint(
                                   tool.GetTransform().TransformPoint(0, 0, 0)))

    def _Prev(self):
        self.SetCurrentLandmark(self._CurrentLandmark - 1)

    def _Delete(self):
        self.RemoveSourceLandmark(self._CurrentLandmark)

    def _Update(self):
        self._SourcePoints.SetNumberOfPoints(0)
        self._TargetPoints.SetNumberOfPoints(0)
        for i in range(len(self._SourceLandmarks)):
            if self._TargetLandmarks[i] and self._SourceLandmarks[i]:
                apply(
                    self._SourcePoints.InsertNextPoint, self._SourceLandmarks[i])
                apply(
                    self._TargetPoints.InsertNextPoint, self._TargetLandmarks[i])

        self._TargetPoints.Modified()
        self._SourcePoints.Modified()
        leastsq = 0.0
        leastsqn = 0

        self._Listbox.delete(0, 'end')
        for i in range(len(self._SourceLandmarks)):
            landmark = self._SourceLandmarks[i]
            c = ' '
            if self._TargetLandmarks[i]:
                x1, y1, z1 = self._Transform.TransformPoint(
                    self._SourceLandmarks[i])
                x2, y2, z2 = self._TargetLandmarks[i]
                error = math.sqrt(
                    (x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
                leastsq = leastsq + error ** 2
                leastsqn = leastsqn + 1
                if error < 2.0:
                    c = '*'
                elif error < 4.0:
                    c = '+'
                else:
                    c = '-'
            self._Listbox.insert('end', "%c%3i %s" %
                                 (c, i + 1, toanatomic(landmark)))

        i = self._CurrentLandmark
        self._Listbox.selection_clear(0, 'end')
        self._Listbox.selection_set(i)
        self._Listbox.activate(i)

        if leastsqn == 1:
            ptext = 'Point'
        else:
            ptext = 'Points'

        if leastsqn > 2:
            self._StdDevLabel.configure(
                text=('Standard Deviation: %5.1f mm (%d %s)' %
                      (math.sqrt(leastsq / (leastsqn - 2)), leastsqn, ptext)))
            self._InstrumentTracker.GetTracker().SetWorldCalibrationMatrix(
                self._Transform.GetInverse().GetMatrix())
        else:
            self._StdDevLabel.configure(
                text=('Standard Deviation: %5.5s mm  (%d %s)' %
                      ('---', leastsqn, ptext)))

    def AddSourceLandmark(self, *coord):
        if len(coord) == 1:
            coord = coord[0]
        self._SourceLandmarks.append(tuple(coord))
        self._TargetLandmarks.append(None)
        self._FiducialMarkerFactory.AddLandmark(coord)
        self.SetCurrentLandmark(len(self._SourceLandmarks) - 1)

    def RemoveSourceLandmark(self, i):
        if i < 0 or i >= len(self._SourceLandmarks):
            return
        del self._SourceLandmarks[i]
        del self._TargetLandmarks[i]
        self._FiducialMarkerFactory.RemoveLandmark(i)
        if i > 0:
            self._CurrentLandmark = i - 1
        else:
            self._CurrentLandmark = 0
        self._Update()
        self._FiducialMarkerFactory.Render()

    def SetTargetLandmark(self, i, *coord):
        if len(coord) == 1:
            coord = coord[0]
        if coord:
            self._TargetLandmarks[i] = tuple(coord)
        else:
            self._TargetLandmarks[i] = None
        self._Update()

    def SetCurrentLandmark(self, i):
        if i < 0 or i >= len(self._SourceLandmarks):
            return
        self._CurrentLandmark = i
        self._FiducialMarkerFactory.SetCurrentLandmark(i)
        self._Listbox.activate(i)
        self._Listbox.selection_clear(0, 'end')
        self._Listbox.selection_set(i)
        pos = self._SourceLandmarks[i]
        for pane in self._Panes:
            pane.SetPointOfInterest(pos)
        self._OrthoPlanesFactory.SetOrthoCenter(
            self._OrthoPlanesFactory.GetTransform().GetInverse().
            TransformPoint(pos))
        self._Update()
        self._FiducialMarkerFactory.Render()

if __name__ == '__main__':
    dialog = RegistrationDialog()
    dialog.pack(fill='both', expand='true')

    dialog.mainloop()

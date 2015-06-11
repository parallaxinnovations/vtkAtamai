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
    'module_name': '$RCSfile: TrackedInstrumentFactory.py,v $',
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
TrackedInstrumentFactory - a superclass for tracked instruments

  The TrackedInstrumentFactory is the superclass for all tracked
  surgical instruments (or other tracked instruments).

  This class is derived from ActorFactory.  However, you should not
  connect a TrackedInstrumentFactory to the RenderPane yourself:  Rather,
  you should add the InstrumentTracker to the RenderPane and connect
  the TrackedInstrumentFactory to the InstrumenTracker.

  Each TrackedInstrumentFactory has a calibration matrix.  This matrix
  describes the orientation of the instrument itself relative to the
  orientation of the mobile, tracked portion of the tracker (i.e. of
  the LEDs in an optical tracking system).

  A TrackedInstrumentFactory will receive events from the InstrumentTracker,
  via the HandleTrackerEvent(event) method.  The 'event' objects have the
  following attributes:

  type  - the type of the event:

  -  <ButtonPress>   :'4'   - button on instrument was pressed

  -  <ButtonRelease> :'5'   - "" released

  -  <Motion>        :'6'   - the instrument moved

  -  <LeaveBounds>   :'7'   - instrument moved out-of-bounds

  -  <EnterBounds>   :'8'   - instrument moved into bounds

  -  <LeaveView>     :'9'   - instrument lost from view

  -  <EnterView>     :'10'  - instrument back into view

  num   - the button number if an instrument button was pressed

  state - an int with modifier bits defined as follows:

  - B1 :256         - button/switch 1

  - B2 :512         - button/switch 2

  - B3 :1024        - button/switch 3

  - OOB :8192       - out-of-bounds, i.e. calibration might be off

  - OOV :16384      - out-of-view, i.e. line-of-sight problems

  timestamp - the timestamp for the transform, in seconds since 1970

  transform - a vtkTransform that provides the position and orientation
              of the tool at the last Update()


  You bind events to callback methods using the BindTrackerEvent() method,
  e.g. here a simple callback that will print the position of the instrument
  when the first button on the instrument is pressed::

    def callback(event):
      print "instrument is at", event.transform.TransformPoint(0.0, 0.0, 0.0)

    instrument.BindTrackerEvent("<ButtonPress-1>",callback)

Derived From:

    ActorFactory

See Also:

    InstrumentTracker, PointerFactory, EventHandler

Initialization:

  TrackedInstrumentFactory()

Public Methods:

  SetCalibrationMatrix(*matrix*)       -- set the calibration matrix for
                                          the instrument.  The matrix can
                                          either be a python matrix or
                                          a vtkMatrix4x4.

  BindTrackerEvent(*descriptor*,*method*)  -- bind an event type to a method

  Note: The TrackedInstrument should not call Render after it receives an
  event, the InstrumentTracker will take care of the rendering

"""

#======================================
from ActorFactory import *

#======================================


class TrackedInstrumentFactory(ActorFactory):

    TrackerEventModifier = {"Button1": 256,
                            "Button2": 512,
                            "Button3": 1024,
                            "B1": 256,
                            "B2": 512,
                            "B3": 1024,
                            "OOB": 8192,
                            "OOV": 16384}

    TrackerEventType = {"ButtonPress": '4',
                        "Button": '4',
                        "ButtonRelease": '5',
                        "Motion": '6',
                        "LeaveBounds": '7',
                        "EnterBounds": '8',
                        "LeaveView": '9',
                        "EnterView": '10'}

    def __init__(self):
        ActorFactory.__init__(self)

        # the vtkTrackerTool associated with this instrument
        self._TrackerTool = None
        self._CalibrationMatrix = vtk.vtkMatrix4x4()

        # set up the property that will change to notify the user
        # of out-of-view events
        self._OriginalColor = None
        self._OOBColor = (0.7, 0.7, 0.0)    # out-of-bounds -- yellow
        self._OOVColor = (1.0, 0.0, 0.0)    # out-of-view   -- red
        self._WarningProperty = vtk.vtkProperty()

        # dictionary which binds events to methods
        # the key is a tuple of three items: (modifier,type,keysym/button)
        self.__TrackerEventDict = {}

        self.BindTrackerEvent("<LeaveBounds>", self.DoLeaveBounds)
        self.BindTrackerEvent("<EnterBounds>", self.DoEnterBounds)
        self.BindTrackerEvent("<LeaveView>", self.DoLeaveView)
        self.BindTrackerEvent("<EnterView>", self.DoEnterView)

    #--------------------------------------
    def DoLeaveBounds(self, event):
        self._TrackerTool.LED2Flash()
        if (self._OriginalColor == None):
            self._OriginalColor = self._WarningProperty.GetColor()
        apply(self._WarningProperty.SetColor, self._OOBColor)
        self.Modified()

    def DoEnterBounds(self, event):
        self._TrackerTool.LED2Off()
        apply(self._WarningProperty.SetColor, self._OriginalColor)
        self.Modified()

    def DoLeaveView(self, event):
        self._TrackerTool.LED1Flash()
        if (self._OriginalColor == None):
            self._OriginalColor = self._WarningProperty.GetColor()
        apply(self._WarningProperty.SetColor, self._OOVColor)
        self.Modified()

    def DoEnterView(self, event):
        self._TrackerTool.LED1On()
        if (event.state & 8192):  # tool is out-of-bounds
            apply(self._WarningProperty.SetColor, self._OOBColor)
        else:
            apply(self._WarningProperty.SetColor, self._OriginalColor)
        self.Modified()

    #--------------------------------------
    def SetTrackerTool(self, tool):
        self._TrackerTool = tool
        if (tool):
            self._TrackerTool.SetCalibrationMatrix(self._CalibrationMatrix)
            self._Transform.SetInput(tool.GetTransform())
        else:
            self._Transform.SetInput(None)
        self.Modified()

    def GetTrackerTool(self):
        return self._TrackerTool

    #--------------------------------------
    def SetCalibrationMatrix(self, matrix):
        # the calibration matrix can either be a vtkMatrix4x4 or
        # any suitable python matrix representation
        try:
            self._CalibrationMatrix.DeepCopy(matrix)
        except:
            for i in range(4):
                for j in range(4):
                    self._CalibrationMatrix.SetElement(i, j, matrix[i][j])
        if (self._TrackerTool):
            self._TrackerTool.SetCalibrationMatrix(self._CalibrationMatrix)
        self.Modified()

    def GetCalibrationMatrix(self):
        return self._CalibrationMatrix

    #--------------------------------------
    def BindTrackerEvent(self, eventDescriptor, func):
        if (eventDescriptor[0] != '<' or eventDescriptor[-1] != '>'):
            raise ValueError("malformed event discriptor " + eventDescriptor)

        # parse the event descriptor
        field = eventDescriptor[1:-1].split('-')

        # find all modifiers
        modifier = 0
        while 1:
            try:
                modifier = modifier | self.TrackerEventModifier[field[0]]
                del field[0]
            except:
                break

        # find the event type
        type = self.TrackerEventType[field[0]]
        del field[0]

        # find the button
        try:
            button = field[0]
            del field[0]
        except:
            button = None

        if (len(field) != 0):
            raise ValueError("malformed event discriptor " + eventDescriptor)

        # check to see if event is already bound, and make an
        # entry if it isn't
        try:
            eventList = self.__TrackerEventDict[type]
        except KeyError:
            eventList = self.__TrackerEventDict[type] = [0, {}, {}]

        # if there is a button, go to sub-dict
        # (make the sub-dict if it doesn't exist)
        if button:
            try:
                buttonList = eventList[2][button]
            except KeyError:
                buttonList = eventList[2][button] = [0, {}]
            # specify which modifiers have specific handlers,
            # and bind the function to the modifier
            buttonList[0] = buttonList[0] | modifier
            buttonList[1][modifier] = func
        else:
            # specify which modifiers have specific handlers,
            # and bind the function to the modifier
            eventList[0] = eventList[0] | modifier
            eventList[1][modifier] = func

    #--------------------------------------
    def HandleTrackerEvent(self, event):
        # dispatch events to the handlers
        type = event.type
        modifier = event.state

        # search for the event (this is pretty quick)
        try:
            eventList = self.__TrackerEventDict[type]
            try:  # see if there is a button specific binding
                buttonList = eventList[2][repr(event.num)]
                func = buttonList[1][buttonList[0] & modifier]
            except KeyError:
                func = eventList[1][eventList[0] & modifier]

        except KeyError:  # event not bound
            return

        # call the handler function!
        func(event)

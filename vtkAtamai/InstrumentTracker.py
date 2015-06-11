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
    'module_name': '$RCSfile: InstrumentTracker.py,v $',
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
InstrumentTracker - track real instruments in 3D space

  The InstrumentTracker represents the "virtual" component of
  a real 3D tracking system such as the POLARIS or the Flock of Birds.
  Each InstrumentTracker is represented by a vtkTracker object.

  This class is actually an ActorFactory.  The tools which are
  connected to the InstrumentTracker become its children, and
  hence appear in the Renderers that are associated with
  the InstrumentTracker.

  There are two methods for connecting a TrackedInstrumentFactory to
  the InstrumentTracker.  The easiest method is to use

  ConnectInstrumentToPort(*factory*,*port*)

  which informs the system that the instrument is connected to a
  particular instrument port.  A more sophisticated method is

  RegisterInstrumentClass(*class*,*mfg*,*id*)

  where "class" is a TrackedInstrumentFactory class object, and *mfg*,*id*
  are the manufacturer and identification number for the tool.

  For example, if you do this:

  tracker.RegisterInstrumentClass(AesculapPointerFactory,"Aesculap","2330001")

  then if a tool is plugged into the POLARIS which returns "Aesculap" and
  "2330001" when it is probed, then new AesculapPointerFactory actors
  will be added to all the Renders associated with the InstrumentTracker.
  That means that whenever you plug a tool into the POLARIS, you
  will see it pop up in 3D on your computer screen, and when you unplug
  the tool the "virtual" tool will disappear.

  Before this class tries to use a particular tracker, it always probes
  it to see if it is there.  The Probe() method can be used to determine
  if the tracking system is attached to the computer and functioning
  properly.

Derived From:

  ActorFactory

See Also:

  TrackedInstrumentFactory

PublicMethods:

  SetTracker(*tracker*)                   -- specify what vtkTracker to use

  GetTracker()                            -- get the vtkTracker object

  Probe()                                 -- probe to see if the tracker is
                                             attached to the computer and
                                             working

  RegisterInstrumentClass(*class*,*mfg*,*id*)  -- specify a class
                                             that will be used to generate
                                             a new tracked instrument each
                                             time a tool with the specified
                                             (*mfg*,*id*) tag is plugged in

  UnregisterInstrumentClass(*class*,*mfg*,*id*) -- clear a class registration

  ConnectInstrumentToPort(*instrument*,*port*) -- connect a TrackedInstrument
                                             to specified tool port (you should
                                             use RegisterInstrumentClass
                                             instead if possible)

  DisconnectInstrument(*instrument*)       -- disconnect an instrument

  RegisterDPT(*mfg*,*id*)                  -- set the ID of a known DPT
                                             (a DPT is tool that all other
                                             tools are tracked relative to)

  UnregisterDPT(*mfg*,*id*)                -- unregister a DPT ID

  SetReferencePort(*port*)                 -- set the reference port (use
                                             RegisterDPT instead if possible)

  StartTracking()                          -- start tracking

  StopTracking()                           -- stop tracking

  Update()                                 -- when tracking, call this
                                             periodically to update the
                                             intrument positions

  SetCalibrationMatrix(*matrix*)           -- set the calibration matrix for
                                             the tracker.  The matrix can
                                             either be a python matrix or
                                             a vtkMatrix4x4.

Protected Attributes:

  _Tracker         -- the vtkTracker object

  _Instruments     -- list which gives an instrument list for each port

------------------------------------------------------------
"""

import os
import sys
if os.name == 'posix':
    import commands

#======================================
from vtkAtamai.ActorFactory import *
import vtk

#======================================


class TrackerEvent(object):
    # the TrackerEvent class holds tracker event attributes
    pass

#======================================


class InstrumentTracker(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self._Tracker = None

        # actor factories are sorted by port, right now a max
        # of 14 ports are supported (sorry, lazy me)
        self._Instruments = [
            [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        self._Modifiers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self._MTimes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self._Missing = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self._ReferencePort = None

        # dictionary of TrackedInstrumentFactory generation functions
        # (actually list of functions, there can be more than one)
        # keyed on (manufacturer,ID) tags.
        self._RegisteredClasses = {}
        # list of which instruments have been automatically created
        self._AutoInstruments = []

        # list of IDs of DPTs to autodetect
        self._RegisteredDPTs = [('ELEKTA', '1000001'),
                                ('NDI', '1010001')]

        # this is true if the tracked has been successfully probed
        self._Probed = 0

    def __del__(self):
        self.StopTracking()

    #--------------------------------------
    def RegisterDPT(self, mfg, id):
        self._RegisteredDPTs.append((mfg, id))

    def UnregisterDPT(self, mfg, id):
        self._RegisteredDPTs.remove((mfg, id))

    #--------------------------------------
    def RegisterInstrumentClass(self, iclass, mfg, id):
        try:  # append to existing list
            self._RegisteredClasses[(mfg, id)].append(iclass)
        except KeyError:  # create a fresh list
            self._RegisteredClasses[(mfg, id)] = [iclass]

    def UnregisterInstrumentClass(self, iclass, mfg, id):
        self._RegisteredClasses[(mfg, id)].remove(iclass)
        # if list length is zero, remove entry from dictionary
        if len(self._RegisteredClasses[(mfg, id)]) == 0:
            del self._RegisteredClasses[(mfg, id)]

    #--------------------------------------
    def ConnectInstrumentToPort(self, instrument, i):
        # connect an instrument to a specific port
        self._Instruments[i].append(instrument)
        self.AddChild(instrument)
        instrument.SetTrackerTool(self._Tracker.GetTool(i))

    def DisconnectInstrumentFromPort(self, instrument):
        # remove from renderer
        self.RemoveChild(instrument)
        # remove from instrument list
        for instruments in self._Instruments:
            if instrument in instruments:
                instruments.remove(instrument)
                instrument.SetTrackerTool(None)

    #--------------------------------------
    def SetTracker(self, tracker):
        if (tracker != self._Tracker):
            self._Tracker = tracker
            self._Probed = 0

    def GetTracker(self):
        return self._Tracker

    #--------------------------------------
    def Probe(self):
        """success = A.Probe() -- probe for tracking system

        This method will return 1 if the tracking system is
        connected to the computer.  Both serial ports will be
        checked.  This method is called automatically by
        the StartTracking method.
        """
        if self._Probed == 0:
            # probe for tracker on default serial port
            firstport = self._Tracker.GetSerialPort()
            nports = 2
            for i in range(nports):
                # rotate through all ports, starting at firstport
                port = ((i + firstport - 1) % nports) + 1
                # check whether serial port is in use, because UNIX
                #  doesn't lock the device
                if os.name == 'posix':
                    # get the device name
                    if sys.platform[0:4] == 'irix':
                        device = "/dev/ttyd%d" % port
                    elif sys.platform[0:5] == 'linux':
                        device = "/dev/ttyS%d" % (port - 1)
                    else:
                        device = ("/dev/ttya", "/dev/ttyb")[port - 1]
                    # /sbin/fuser checks to see if another process
                    # is using the port
                    result = commands.getoutput("/sbin/fuser " + device)
                    result = result.strip()
                    # check for device name in command output
                    if device == result[0:len(device)]:
                        # check for processes on the output line
                        if result[len(device) + 1:] != '':
                            continue  # in use, go on to next port

                self._Tracker.SetSerialPort(port)
                self._Probed = self._Tracker.Probe()
                if self._Probed:
                    break  # found!

        return self._Probed

    #--------------------------------------
    def StartTracking(self):
        # only start tracking if successful probed
        if self.Probe():
            self._Tracker.StartTracking()
            if not hasattr(self, 'TrackingScheduleId'):
                self.TrackingScheduleId = \
                    self.ScheduleEvery(20, lambda s=self:
                                       (s.Update(), s.Render()))

    def StopTracking(self):
        if self._Probed == 0:
            return

        self._Tracker.StopTracking()
        if hasattr(self, 'TrackingScheduleId'):
            self.UnSchedule(self.TrackingScheduleId)
            del self.TrackingScheduleId

    #--------------------------------------
    def SetCalibrationMatrix(self, matrix):
        try:
            self._Tracker.SetWorldCalibrationMatrix(matrix)
        except:
            mat = vtk.vtkMatrix()
            for i in range(4):
                for j in range(4):
                    mat.SetElement(i, j, matrix[i][j])
            self._Tracker.SetWorldCalibrationMatrix(matrix)
        self.Modified()

    def GetCalibrationMatrix(self):
        return self._Tracker.GetWorldCalibrationMatrix()

    #--------------------------------------
    def SetReferencePort(self, port):
        self._Tracker.SetReferenceTool(port)
        self.Modified()

    def GetReferencePort(self):
        return self._Tracker.GetReferenceTool()

    #--------------------------------------
    def Update(self):
        # make sure we're up and running first, eh?
        if (not self._Probed):
            return

        # print self._Tracker.GetInternalUpdateRate()

        # will be set to 1 if we need to re-render
        needsRender = 0

        # create an event
        event = TrackerEvent()

        # update the tracker and get a timestamp
        self._Tracker.Update()
        event.timestamp = self._Tracker.GetUpdateTimeStamp()

        # for each tool, set up appropriate events and pass
        # them along to the instruments
        for i in range(self._Tracker.GetNumberOfTools()):
            tool = self._Tracker.GetTool(i)
            event.transform = tool.GetTransform()

            # if tool was absent and is absent, do nothing
            if (self._Missing[i] and tool.IsMissing()):
                continue

            # check if tool was just plugged in
            if (self._Missing[i] and not tool.IsMissing()):
                # get autodetect information
                mfg = tool.GetToolManufacturer()
                id = tool.GetToolType()
                print "New Tool: ", (mfg, id)    # debug line
                try:
                    # try to autodetect the tool
                    classlist = self._RegisteredClasses[(mfg, id)]
                    for iclass in classlist:
                        # use class to generate a TrackedInstrumentFactory
                        instrument = iclass()
                        self.ConnectInstrumentToPort(instrument, i)
                        self._AutoInstruments.append(instrument)
                        needsRender = 1
                except KeyError:
                    # next try to autodetect the DPTs
                    if (mfg, id) in self._RegisteredDPTs:
                        self.SetReferencePort(i)
                        self.ReferencePort = i
                        needsRender = 1

                # clear modifiers
                self._Modifiers[i] = 0

            # check if tool was just unplugged
            if (tool.IsMissing()):
                # clear flags before deleting tool
                newModifier = 0

            else:
                # set up modifier bits
                newModifier = ((tool.IsOutOfView() * 16384) |
                               (tool.IsOutOfVolume() * 8192) |
                               (tool.IsSwitch1On() * 256) |
                               (tool.IsSwitch2On() * 512) |
                               (tool.IsSwitch3On() * 1024))

            # check to see if any modifiers have changed
            modifier = self._Modifiers[i]
            changes = modifier ^ newModifier
            self._Modifiers[i] = newModifier

            if changes:
                # check for out-of-bounds change
                if changes & 8192:
                    if modifier & 8192:
                        event.type = '8'     # moved into bounds
                    else:
                        event.type = '7'     # moved out of bounds
                    event.num = 0            # no button associated with event
                    event.state = modifier
                    for instrument in self._Instruments[i]:
                        instrument.HandleTrackerEvent(event)
                        needsRender = 1
                    # add the change to the modifier
                    modifier = modifier ^ 8192

                # check for out-of-view change
                if changes & 16384:
                    if modifier & 16384:
                        event.type = '10'    # moved in to view
                    else:
                        event.type = '9'     # moved out of view
                    event.num = 0            # no button associated with event
                    event.state = modifier
                    for instrument in self._Instruments[i]:
                        instrument.HandleTrackerEvent(event)
                        needsRender = 1
                    # add the change to the modifier
                    modifier = modifier ^ 16384

                # check for button press/release
                for button in (1, 2, 3):
                    bit = (1 << (button + 7))
                    if changes & bit:
                        event.num = button  # button number
                        event.state = modifier
                        if modifier & bit:
                            event.type = '5'  # button release
                        else:
                            event.type = '4'  # button press
                        for instrument in self._Instruments[i]:
                            instrument.HandleTrackerEvent(event)
                            needsRender = 1
                        # add the change to the modifier
                        modifier = modifier ^ bit

            if (not tool.IsMissing()):
                # now that any state changes have been taken care of,
                # send along the motion event if the transform has changed
                if (self._MTimes[i] != event.transform.GetMTime()):
                    self._MTimes[i] = event.transform.GetMTime()
                    event.state = modifier
                    event.num = 0
                    event.type = '6'    # motion
                    for instrument in self._Instruments[i]:
                        instrument.HandleTrackerEvent(event)
                        needsRender = 1

            else:
                # tool was unplugged, so remove it
                for instrument in self._Instruments[i]:
                    if instrument in self._AutoInstruments:
                        # disconnect & forget about the instrument
                        self.DisconnectInstrumentFromPort(instrument)
                        self._AutoInstruments.remove(instrument)
                        needsRender = 1
                if (i == self._ReferencePort):
                    # ouch! someone unplugged the DPT!
                    self.SetReferencePort(-1)
                    needsRender = 1

            self._Missing[i] = tool.IsMissing()

        # finally, if any event was sent to any instrument, or if any
        # instruments were added or removed, then we have to render
        if (needsRender):
            self.Modified()

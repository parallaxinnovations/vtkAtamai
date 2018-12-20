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

from future import standard_library
standard_library.install_aliases()
from builtins import str
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: tkPaneFrame.py,v $',
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
tkPaneFrame - a PaneFrame that is also a Tk Widget

  This class allows you to use a RenderPane inside a Tkinter application.
  The tkPaneFrame uses the vtkTkRenderWidget that comes with VTK
  to provide a vtkRenderWindow inside a Tk widget.

  Except for the fact that it can be packed in with other widgets,
  its behaviour should be identical to that of the PaneFrame
  superclass.  This class uses Tk to do the event handling.

Derived From:

  RenderPane, Tkinter.Widget

"""

import tkinter
from vtkAtamai.PaneFrame import *
import vtk
import os

# new-style widget loading for VTK 4.x


def vtkLoadPythonTkWidgets(interp):
    """vtkLoadPythonTkWidgets(interp) -- load vtk-tk widget extensions

    This is a mess of mixed python and tcl code that searches for the
    shared object file that contains the python-vtk-tk widgets.  Both
    the python path and the tcl path are searched.
    """
    name = 'vtkRenderingPythonTkWidgets'
    pkgname = name.lower().capitalize()

    # find out if the file is already loaded
    loaded = interp.call('info', 'loaded')
    if pkgname in loaded:
        return

    # create the platform-dependent file name
    prefix = ''
    if os.name == 'posix':
        prefix = 'lib'
    extension = interp.call('info', 'sharedlibextension')
    filename = prefix + name + extension

    # create an extensive list of paths to search
    pathlist = sys.path
    # add tcl paths, ensure that {} is handled properly
    try:
        auto_path = interp.getvar('auto_path')
        if not type(auto_path) == tuple:
            auto_path = auto_path.split()
        for path in auto_path:
            prev = pathlist[-1]
            try:
                # try block needed when one uses Gordon McMillan's Python
                # Installer.
                if len(prev) > 0 and prev[0] == '{' and prev[-1] != '}':
                    pathlist[-1] = prev + ' ' + path
                else:
                    pathlist.append(path)
            except AttributeError:
                pass
    except:
        for path in interp.getvar('auto_path'):
            prev = pathlist[-1]
            try:
                # try block needed when one uses Gordon McMillan's Python
                # Installer.
                prev = str(prev)
                if len(prev) > 0 and prev[0] == '{' and prev[-1] != '}':
                    pathlist[-1] = prev + ' ' + path
                else:
                    pathlist.append(path)
            except AttributeError:
                pass

    # a common place for these sorts of things
    if os.name == 'posix':
        pathlist.append('/usr/local/lib')

    # attempt to load
    for path in pathlist:
        try:
            # try block needed when one uses Gordon McMillan's Python
            # Installer.
            path = str(path)
            if len(path) > 0 and path[0] == '{' and path[-1] == '}':
                path = path[1:-1]
            fullpath = os.path.join(path, filename)
        except AttributeError:
            pass
        if ' ' in fullpath:
            fullpath = '{' + fullpath + '}'
        if interp.eval('catch {load ' + fullpath + ' ' + pkgname + '}') == '0':
            return

    # re-generate the error
    interp.call('load', filename)


class tkPaneFrame(PaneFrame, tkinter.Widget):

    _ScheduleIdDict = {}

    def __init__(self, master=None, *args, **kw):
        used_default_root = 0
        if not master:
            if not tkinter._default_root:
                tkinter._default_root = tkinter.Tk()
            master = tkinter._default_root
            used_default_root = 1
        if vtk.vtkVersion().GetVTKMajorVersion() >= 4:
            vtkLoadPythonTkWidgets(master.tk)
        else:
            try:  # check for VTK_TK_WIDGET_PATH environment variable
                tkWidgetPath = os.environ['VTK_TK_WIDGET_PATH']
            except KeyError:
                tkWidgetPath = '.'

            try:  # try specified path or current directory
                master.tk.call('load', os.path.join(tkWidgetPath,
                                                    'vtkTkRenderWidget'))
            except:  # try tcl/tk load path
                master.tk.call('load', 'vtkTkRenderWidget')

        self._RenderWindow = vtk.vtkRenderWindow()

        if 'stereo' in kw:
            if kw['stereo']:
                self._RenderWindow.StereoCapableWindowOn()
                self._RenderWindow.SetStereoTypeToCrystalEyes()
            del kw['stereo']

        # first initialize the Tkinter widget
        kw['rw'] = self._RenderWindow.GetAddressAsString("vtkRenderWindow")

        tkinter.Widget.__init__(self, master, 'vtkTkRenderWidget', {}, kw)

        # then initialize the PaneFrame
        PaneFrame.__init__(self)

        # a silly special-purpose thingy
        self.__InExpose = 0

        # is the system cursor hidden?
        self.__SystemCursorHidden = 0

        if used_default_root:
            self.pack(expand='true', fill='both')

        # do the Tk bindings
        self.bind("<ButtonPress>", self.OnButtonPress)
        self.bind("<ButtonRelease>", self.OnButtonRelease)
        self.bind("<Motion>", self.ConvertTkEvent)
        self.bind("<KeyPress>", self.ConvertTkEvent)
        self.bind("<KeyRelease>", self.ConvertTkEvent)

        # self.bind("<Enter>",self.DoEnter)
# JG: the follow line is commented out to prevent automatic redraws whenever mouse
# leaves the tkPaneframe
# self.bind("<Leave>",self.DoLeave)
        self.bind("<Expose>", self.DoExpose)
        self.bind("<Configure>", self.DoConfigure)
# HQ: the following line is commented out to fix crash-on-exit problem in some apps.
# self.bind("<Destroy>",self.DoDestroy)

    def __getattr__(self, attr):
        # because the tk part of vtkTkRenderWidget must have
        # the only remaining reference to the RenderWindow when
        # it is destroyed, we can't actually store the RenderWindow
        # as an attribute but instead have to get it from the tk-side
        if attr == '_RenderWindow':
            return vtkRenderWindow('_%s_vtkRenderWindow_p' %
                                   self.tk.call(self._w, 'GetRenderWindow')[5:])
        raise AttributeError(attr)

    def OnButtonPress(self, event):
        self._RenderWindow.SetDesiredUpdateRate(5.0)
        self.ConvertTkEvent(event)

    def OnButtonRelease(self, event):
        self._RenderWindow.SetDesiredUpdateRate(0.0001)
        self.ConvertTkEvent(event)

    def ConvertTkEvent(self, event):
        # convert Tk events to our event style
        try:
            event.y = self._RenderWindow.GetSize()[1] - event.y - 1
        except:
            pass
        self.HandleEvent(event)

    def DoDestroy(self, event):
        pass

    def DoConfigure(self, event):
        self.HandleEvent(event)

    def DoExpose(self, event):
        # make sure we render when we should
        if not self.__InExpose:
            self.__InExpose = 1
            self.update()
            for pane in self._RenderPanes:
                if pane.HasChangedSince(pane.GetRenderTime()):
                    pane.StartRender()
            self._RenderWindow.Render()
            self.__InExpose = 0

    def DoEnter(self, event):
        # set the focus when mouse enters window
        # self._OldFocus = self.focus_get()
        self.focus()
        # and pass the event down the line
        self.ConvertTkEvent(event)

    def DoLeave(self, event):
        # Set the focus to the previous focus
        # if (self._OldFocus != None):
        #    self._OldFocus.focus()
        # pass the event down the line
        self.ConvertTkEvent(event)

    def _ScheduleHelper(self, id, func):
        item = tkPaneFrame._ScheduleIdDict[id]
        del tkPaneFrame._ScheduleIdDict[id]

        try:
            func()
        finally:
            # self.update()

            if item[1]:  # if this is from ScheduleEvery
                tkPaneFrame._ScheduleIdDict[id] = item
                item[0] = self.after(item[1],
                                     lambda s=self, i=id, f=func:
                                     s._ScheduleHelper(i, f))

    def ScheduleOnce(self, millisecs, func):
        id = PaneFrame._ScheduleId = PaneFrame._ScheduleId + 1
        item = [None, 0]
        tkPaneFrame._ScheduleIdDict[id] = item
        item[0] = self.after(millisecs,
                             lambda s=self, i=id, f=func:
                             s._ScheduleHelper(i, f))
        return PaneFrame._ScheduleId

    def ScheduleEvery(self, millisecs, func):
        id = PaneFrame._ScheduleId = PaneFrame._ScheduleId + 1
        item = [None, millisecs]
        tkPaneFrame._ScheduleIdDict[PaneFrame._ScheduleId] = item
        item[0] = self.after(millisecs,
                             lambda s=self, i=id, f=func:
                             s._ScheduleHelper(i, f))
        return PaneFrame._ScheduleId

    def UnSchedule(self, id):
        try:
            tk_id = tkPaneFrame._ScheduleIdDict[id][0]
            del tkPaneFrame._ScheduleIdDict[id]
            self.after_cancel(tk_id)
        except KeyError:
            pass

    def Start(self):
        self.mainloop()

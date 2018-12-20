from __future__ import division
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

from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: ModePalette.py,v $',
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
ModePalette - a control panel changing the mouse interaction mode

  The ModePalette is a row of button that specify different interaction
  modes.

Derived From:

  Frame

See Also:

  InteractionMode, WindowLevelInteractionMode, Widget

Initialization:

  ModePalette(*parent*)

  *parent* - the RenderPane or Widget to place the palette into

Public Methods:

  AddPane(*pane*) -- specify a pane to control with the palette

  RemovePane(*pane*) -- remove a pane

"""

from vtkAtamai.WindowLevelInteractionMode import *
from vtkAtamai.RenderPane import *
from vtkAtamai.RenderPane2D import *
import vtkAtamai.Widgets
import vtk

if "FreeType" in vtk.vtkTextMapper().GetClassName():
    _FS = 16
else:
    _FS = 14


class ModePalette(vtkAtamai.Widgets.Frame):

    def __init__(self, parent=None, x=0, y=0, fontsize=_FS, width=70 * 5, height=27):
        n = 5  # number of buttons

        vtkAtamai.Widgets.Frame.__init__(
            self, parent, x=x, y=y, width=width, height=height)

        self.rotate = vtkAtamai.Widgets.Button(self, x=0, y=0,
                                               width=old_div(width, n), height=height,
                                               fontsize=fontsize, text="Rotate")
        self.rotate.BindEvent("<Command>", self.BindRotate)

        self.zoom = vtkAtamai.Widgets.Button(self, x=old_div(width, n), y=0,
                                             width=old_div(width, n), height=height,
                                             fontsize=fontsize, text="Zoom")
        self.zoom.BindEvent("<Command>", self.BindZoom)

        self.pan = vtkAtamai.Widgets.Button(self, x=width / n * 2, y=0,
                                            width=old_div(width, n), height=height,
                                            fontsize=fontsize, text="Pan")
        self.pan.BindEvent("<Command>", self.BindPan)

        self.slice = vtkAtamai.Widgets.Button(self, x=width / n * 3, y=0,
                                              width=old_div(width, n), height=height,
                                              fontsize=fontsize, text="Slice")
        self.slice.BindEvent("<Command>", self.BindSlice)

        self.winlev = vtkAtamai.Widgets.Button(self, x=width / n * (n - 1), y=0,
                                               width=width - width / n * (n - 1), height=height,
                                               fontsize=fontsize, text="Win/Lev")
        self.winlev.BindEvent("<Command>", self.BindWinLev)

        # need WindowLevel mode
        self._WindowLevelMode = WindowLevelInteractionMode()

        self._Panes = []

    def SetWindowLevelMode(self, mode):
        self._WindowLevelMode = mode

    def SetLookupTable(self, table):
        self._WindowLevelMode.SetLookupTable(table)

    def AddPane(self, pane):
        self._Panes.append(pane)

    def RemovePane(self, pane):
        self._Panes.remove(pane)

    def BindRotate(self, event):
        for pane in self._Panes:
            if isinstance(pane, RenderPane2D):
                pane.BindPanToButton(event.num, event.state)
            else:
                pane.BindRotateToButton(event.num, event.state)

    def BindZoom(self, event):
        for pane in self._Panes:
            pane.BindZoomToButton(event.num, event.state)

    def BindPan(self, event):
        for pane in self._Panes:
            pane.BindPanToButton(event.num, event.state)

    def BindSlice(self, event):
        for pane in self._Panes:
            if isinstance(pane, RenderPane2D):
                pane.BindPushToButton(event.num, event.state)
            else:
                pane.BindActorToButton(event.num, event.state)

    def BindWinLev(self, event):
        for pane in self._Panes:
            pane.BindModeToButton(
                self._WindowLevelMode, event.num, event.state)

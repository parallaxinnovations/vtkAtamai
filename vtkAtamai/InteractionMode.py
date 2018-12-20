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

from builtins import object
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: InteractionMode.py,v $',
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
InteractionMode - define a new interaction mode for a RenderPane

  An InteractionMode specifies what is to be done when the mouse is
  dragged across a RenderPane.  The InteractionMode is connected
  to the RenderPane through the pane's BindModeToButton method.

  When this class is subclassed, usually the DoMotion() method is
  the only one that has to be overridden.

Derived From:

  none

See Also:

  RenderPane, WindowLevelInteractionMode

Initialization:

  InteractionMode()

Handler Methods:

  DoButtonPress(*event*)     -- called when button is pressed

  DoButtonRelease(*event*)   -- called when button is released

  DoMotion(*event*)          -- called when mouse moved while button down

Used by RenderPane:

  AddRenderer(*renderer*)    -- add a renderer

  RemoveRenderer(*renderer*) -- remove a renderer

Protected Members:

  _LastX, _LastY   -- the previous mouse position

  _StartX, _StartY -- the position of the mouse when the button was pressed

"""


class InteractionMode(object):

    def __init__(self):
        self._Renderers = []
        self._RenderMethod = {}

        self._LastX = 0
        self._LastY = 0

        self._StartX = 0
        self._StartY = 0

    #--------------------------------------
    def DoButtonPress(self, event):
        self._LastX = event.x
        self._LastY = event.y
        self._StartX = event.x
        self._StartY = event.y

    def DoMotion(self, event):
        self._LastX = event.x
        self._LastY = event.y

    def DoButtonRelease(self, event):
        pass

    #--------------------------------------
    def AddRenderer(self, renderer):
        self._Renderers.append(renderer)

    def RemoveRenderer(self, renderer):
        self._Renderers.remove(renderer)

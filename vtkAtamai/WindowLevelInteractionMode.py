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
    'module_name': '$RCSfile: WindowLevelInteractionMode.py,v $',
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
WindowLevelInteractionMode - change image window/level with the mouse

  This interaction mode allows you to use the mouse to modify the
  window and level of a vtkLookupTable.

  moving mouse horizontally -> level

  moving mouse vertically -> window


Derived From:

  InteractionMode

See Also:

  InteractionMode

Initialization:

  WindowLevelInteractionMode()

Public Methods:

  SetLookupTable(*table*)    -- set the vtkLookupTable to modify

  SetDataRange((*low*,*high*)) -- set the (*low*,*high*) range of the scalars
                              that are going to be passed through the table


Note:  When you call SetLookupTable(), the DataRange is automatically
       set to the current TableRange of the table.

"""

#======================================
import InteractionMode

#======================================


class WindowLevelInteractionMode(InteractionMode.InteractionMode):

    def __init__(self):
        InteractionMode.InteractionMode.__init__(self)

        self._LookupTable = None
        self._DataRange = (0, 1024)

    #--------------------------------------
    def SetLookupTable(self, table):
        self._LookupTable = table
        self._DataRange = table.GetTableRange()

    def GetLookupTable(self):
        return self._LookupTable

    #--------------------------------------
    def SetDataRange(self, range):
        self._DataRange = range

    def GetDataRange(self):
        return self._DataRange

    #--------------------------------------
    def DoMotion(self, event):
        if not self._LookupTable:
            return

        table = self._LookupTable

        mlo, mhi = self._DataRange
        lo, hi = table.GetTableRange()

        level = (lo + hi) / 2.0
        window = hi - lo

        level = level + (event.x - self._LastX) * (mhi - mlo) / 500.0
        window = window + (event.y - self._LastY) * (mhi - mlo) / 250.0

        if window <= 0:
            window = 1e-3

        lo = level - window / 2.0
        hi = level + window / 2.0

        table.SetTableRange(lo, hi)
        table.Modified()

        self._LastX = event.x
        self._LastY = event.y

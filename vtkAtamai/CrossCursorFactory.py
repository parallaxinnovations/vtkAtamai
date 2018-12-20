from __future__ import absolute_import
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
    'module_name': '$RCSfile: CrossCursorFactory.py,v $',
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
CrossCursorFactory - a 3D cursor that is a cross

  This is the most useful cursor for use with images.

Derived From:

  CursorFactory

See Also:

  ConeCursorFactory

"""

#======================================
from .CursorFactory import *

#======================================


class CrossCursorFactory(CursorFactory):

    def __init__(self):
        CursorFactory.__init__(self)
        # no shading
        self._TopProperty.SetAmbient(1.0)
        self._BotProperty.SetAmbient(1.0)
        self.SetInput(self._CreateCrossData())

    def _CreateCrossData(self):
        # create the data for the two cones
        a = self._CursorSize * 0.3
        b = self._CursorSize
        c = self._CursorSize * 0.1

        self.__CubeSource1 = vtk.vtkCubeSource()
        self.__CubeSource1.SetROIBounds(-c, c, a, b, -c, c)

        self.__CubeSource2 = vtk.vtkCubeSource()
        self.__CubeSource2.SetROIBounds(-c, c, -b, -a, -c, c)

        self.__CubeSource3 = vtk.vtkCubeSource()
        self.__CubeSource3.SetROIBounds(-c, c, -c, c, a, b)

        self.__CubeSource4 = vtk.vtkCubeSource()
        self.__CubeSource4.SetROIBounds(-c, c, -c, c, -b, -a)

        self.__CrossSource = vtk.vtkAppendPolyData()
        self.__CrossSource.AddInput(self.__CubeSource1.GetOutput())
        self.__CrossSource.AddInput(self.__CubeSource2.GetOutput())
        self.__CrossSource.AddInput(self.__CubeSource3.GetOutput())
        self.__CrossSource.AddInput(self.__CubeSource4.GetOutput())

        return self.__CrossSource.GetOutput()

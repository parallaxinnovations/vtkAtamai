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
    'module_name': '$RCSfile: ConeCursorFactory.py,v $',
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
ConeCursorFactory - a 3D cursor made of two cones

  This class serves as an example of how easy it is to create
  cursors of a specific shape.  All you have to do is call SetInput()
  in the '__init__' method.

Derived From:

  CursorFactory

See Also:

  CrossCursorFactory

"""

#======================================
from .CursorFactory import *

#======================================


class ConeCursorFactory(CursorFactory):

    def __init__(self):
        CursorFactory.__init__(self)
        self.SetInput(self._CreateCursorData())

    def _CreateCursorData(self):
        # create the data for the two cones
        self.__ConeSource = vtk.vtkConeSource()
        self.__ConeSource.SetResolution(10)
        self.__ConeSource.SetHeight(self._CursorSize)
        self.__ConeSource.SetAngle(30.0)

        redTransform = vtk.vtkTransform()
        redTransform.Translate(-self.__ConeSource.GetHeight() * 0.5, 0.0, 0.0)

        self.__RedConeTransform = vtk.vtkTransformPolyDataFilter()
        self.__RedConeTransform.SetInput(self.__ConeSource.GetOutput())
        self.__RedConeTransform.SetTransform(redTransform)

        greenTransform = vtk.vtkTransform()
        greenTransform.GetMatrix().SetElement(0, 0, -1.0)
        greenTransform.GetMatrix().SetElement(1, 1, -1.0)
        greenTransform.Modified()

        self.__GreenConeTransform = vtk.vtkTransformPolyDataFilter()
        self.__GreenConeTransform.SetInput(self.__RedConeTransform.GetOutput())
        self.__GreenConeTransform.SetTransform(greenTransform)

        self.__DoubleConeSource = vtk.vtkAppendPolyData()
        self.__DoubleConeSource.AddInput(self.__RedConeTransform.GetOutput())
        self.__DoubleConeSource.AddInput(self.__GreenConeTransform.GetOutput())

        return self.__DoubleConeSource.GetOutput()

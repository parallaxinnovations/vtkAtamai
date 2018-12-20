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
    'module_name': '$RCSfile: PointerFactory.py,v $',
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
PointerFactory - a simple tracked pointer

  This class is a TrackedInstrumentFactory that represents a simple
  pointer.

Derived From:

  TrackedInstrumentFactory

See Also:

  InstrumentTracker

Initialization:

  PointerFactory()

"""

#======================================
from .TrackedInstrumentFactory import *

#======================================


class PointerFactory(TrackedInstrumentFactory):

    def __init__(self):
        TrackedInstrumentFactory.__init__(self)

        self._CreatePointerData()

    #--------------------------------------
    def _CreatePointerData(self):
        # Create the VTK pipeline for the probe data.  The data
        # produced are self.__TipData and self.__HandleData

        # data shared between pointers
        tipPoints = vtk.vtkPoints()
        tipPoints.InsertNextPoint(0.01, 0.0,  0.75)
        tipPoints.InsertNextPoint(0.23, 0.0,  0.71)
        tipPoints.InsertNextPoint(0.44, 0.0,  0.61)
        tipPoints.InsertNextPoint(0.61, 0.0,  0.44)
        tipPoints.InsertNextPoint(0.71, 0.0,  0.23)
        tipPoints.InsertNextPoint(0.75, 0.0,  0.0)
        tipPoints.InsertNextPoint(0.75, 0.0, -10.0)
        tipPoints.InsertNextPoint(2.0, 0.0, -12.5)
        tipPoints.InsertNextPoint(2.0, 0.0, -77.5)

        handlePoints = vtk.vtkPoints()
        handlePoints.InsertNextPoint(2.0, 0.0, -77.5)
        handlePoints.InsertNextPoint(8.5, 0.0, -99.5)
        handlePoints.InsertNextPoint(8.5, 0.0, -169.5)
        handlePoints.InsertNextPoint(0.1, 0.0, -168.5)

        tipLine = vtk.vtkCellArray()
        tipLine.InsertNextCell(9)
        tipLine.InsertCellPoint(0)
        tipLine.InsertCellPoint(1)
        tipLine.InsertCellPoint(2)
        tipLine.InsertCellPoint(3)
        tipLine.InsertCellPoint(4)
        tipLine.InsertCellPoint(5)
        tipLine.InsertCellPoint(6)
        tipLine.InsertCellPoint(7)
        tipLine.InsertCellPoint(8)

        handleLine = vtk.vtkCellArray()
        handleLine.InsertNextCell(4)
        handleLine.InsertCellPoint(0)
        handleLine.InsertCellPoint(1)
        handleLine.InsertCellPoint(2)
        handleLine.InsertCellPoint(3)

        tipProfile = vtk.vtkPolyData()
        tipProfile.SetPoints(tipPoints)
        tipProfile.SetLines(tipLine)

        handleProfile = vtk.vtkPolyData()
        handleProfile.SetPoints(handlePoints)
        handleProfile.SetLines(handleLine)

        self.__TipExtrude = vtk.vtkRotationalExtrusionFilter()
        self.__TipExtrude.SetInput(tipProfile)
        self.__TipExtrude.SetResolution(24)
        self.__TipExtrude.Update()

        self.__HandleExtrude = vtk.vtkRotationalExtrusionFilter()
        self.__HandleExtrude.SetInput(handleProfile)
        self.__HandleExtrude.CappingOn()
        self.__HandleExtrude.SetResolution(24)
        self.__HandleExtrude.Update()

        # set up a permutation matrix to describe the
        # orientation of the pointer
        matrix = vtk.vtkMatrix4x4()
        # matrix.SetElement(0,0,0)
        # matrix.SetElement(1,1,0)
        # matrix.SetElement(2,2,0)
        # matrix.SetElement(0,2,1)
        # matrix.SetElement(1,1,1)
        # matrix.SetElement(2,0,-1)

        transform = vtk.vtkTransform()
        transform.SetMatrix(matrix)

        self.__TipRotate = vtk.vtkTransformPolyDataFilter()
        self.__TipRotate.SetInput(self.__TipExtrude.GetOutput())
        self.__TipRotate.SetTransform(transform)

        self.__HandleRotate = vtk.vtkTransformPolyDataFilter()
        self.__HandleRotate.SetInput(self.__HandleExtrude.GetOutput())
        self.__HandleRotate.SetTransform(transform)

        # polydata for the tip
        self.__TipData = self.__TipRotate.GetOutput()

        # polydata for the handle
        self.__HandleData = self.__HandleRotate.GetOutput()

    #--------------------------------------
    def _MakeActors(self):
        # the non-shareable portion of the pipeline
        tipMapper = vtk.vtkPolyDataMapper()
        tipMapper.SetInput(self.__TipData)

        handleMapper = vtk.vtkPolyDataMapper()
        handleMapper.SetInput(self.__HandleData)

        tip = self._NewActor()
        tip.SetMapper(tipMapper)
        tip.SetProperty(vtkProperty())
        tip.SetUserTransform(self._Transform)
        tip.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
        tip.GetProperty().SetSpecular(0.9)
        tip.GetProperty().SetSpecularPower(200.0)
        tip.GetProperty().SetColor(0.9, 0.9, 0.9)

        handle = self._NewActor()
        handle.SetMapper(handleMapper)
        handle.SetUserTransform(self._Transform)
        handle.SetProperty(self._WarningProperty)
        handle.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
        handle.GetProperty().SetSpecular(100.0)
        handle.GetProperty().SetSpecularPower(30.0)
        handle.GetProperty().SetAmbientColor(1.0, 1.0, 1.0)
        handle.GetProperty().SetAmbient(2.0)
        handle.GetProperty().SetColor(0.2, 0.2, 0.2)

        return (tip, handle)

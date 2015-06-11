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
    'module_name': '$RCSfile: AesculapPointerFactory.py,v $',
    'creator': 'Kirk Finnis <kfinnis@atamai.com>',
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
AesculapPointerFactory - represents an Aesculap actively tracked pointer

  The geometry of this ActorFactory matches the geometry of the Aesculap
  actively tracked pointer for the POLARIS tracking system.

Derived From:

  TrackedInstrumentFactory

See Also:

  PointerFactory, InstrumentTracker

Initialization:

  AesculapPointerFactory()

"""

#======================================
from vtkAtamai.TrackedInstrumentFactory import *
import vtk

#======================================


class AesculapPointerFactory(TrackedInstrumentFactory):

    def __init__(self):
        TrackedInstrumentFactory.__init__(self)
        self._Depth = 300
        self._CreatePointerData()

        # default calibration matrix for Aesculap probe
        self.SetCalibrationMatrix((0.0,     0.0,     1.0,    0.59,
                                   -1.0,     0.0,     0.0,   -0.14,
                                   0.0,    -1.0,     0.0,  -248.2,
                                   0.0,     0.0,     0.0,     1.0))

    #--------------------------------------
    def HandleTrackerEvent(self, event):
        # override this so that the buttons move up and down when pressed
        if event.type == '4':
            if event.num == 1:
                center = self.__Button1.GetCenter()
                self.__Button1.SetCenter(9, center[1], center[2])
            elif event.num == 2:
                center = self.__Button2.GetCenter()
                self.__Button2.SetCenter(9, center[1], center[2])
            elif event.num == 3:
                center = self.__Button3.GetCenter()
                self.__Button3.SetCenter(9, center[1], center[2])
        elif event.type == '5':
            if event.num == 1:
                center = self.__Button1.GetCenter()
                self.__Button1.SetCenter(10, center[1], center[2])
            elif event.num == 2:
                center = self.__Button2.GetCenter()
                self.__Button2.SetCenter(10, center[1], center[2])
            elif event.num == 3:
                center = self.__Button3.GetCenter()
                self.__Button3.SetCenter(10, center[1], center[2])

        TrackedInstrumentFactory.HandleTrackerEvent(self, event)

    #--------------------------------------
    def _CreatePointerData(self):
        # Create the VTK pipeline for the probe data.

        # we want the button properties to be shared between
        # actors that are produced for separate panes.

        self._HandleProperty = vtk.vtkProperty()
        self._HandleProperty.SetSpecularColor(1.0, 1.0, 1.0)
        self._HandleProperty.SetSpecular(20.0)
        self._HandleProperty.SetSpecularPower(20.0)
        self._HandleProperty.SetColor(0.2, 0.2, 0.2)

        self._Button1Property = vtk.vtkProperty()
        self._Button1Property.SetColor(0.3922, 0.5843, 0.9294)

        self._Button2Property = vtk.vtkProperty()
        self._Button2Property.SetColor(1.0, 1.0, 0.0)

        self._Button3Property = vtk.vtkProperty()
        self._Button3Property.SetColor(0.3922, 0.5843, 0.9294)

        # the shaft has the warning property, i.e. it goes red
        # when the probe is out-of-view
        self._WarningProperty.SetSpecularColor(1.0, 1.0, 1.0)
        self._WarningProperty.SetSpecular(0.9)
        self._WarningProperty.SetSpecularPower(200.0)
        self._WarningProperty.SetColor(0.9, 0.9, 0.9)

        self._TrajProperty = vtk.vtkProperty()
        self._TrajProperty.SetColor(1, 0, 0)

        # get on with the data

        # for handle:
        handlePoints = vtk.vtkPoints()
        handlePoints.InsertNextPoint(2.0, 0.0, -149.0)  # handle x 'tube'
        handlePoints.InsertNextPoint(10.0, 0.0, -157.0)  # start of handle
        handlePoints.InsertNextPoint(10.0, 0.0, -282.0)  # butt diameter = 20
        handlePoints.InsertNextPoint(3.0, 0.0, -287.0)  # handle shaft
        handlePoints.InsertNextPoint(3.0, 0.0, -290.0)  # cord plug
        handlePoints.InsertNextPoint(0.1, 0.0, -290.0)  # tit at end of probe

        # for probe bend:
        bendPoints = vtk.vtkPoints()
        bendPoints.InsertNextPoint(0, 0.0, -149.0)  # origin at handle

        bendPoints.InsertNextPoint(0, 0.0, -146.0)  # first bend
        bendPoints.InsertNextPoint(0.0, -1.0, -145.0)
        bendPoints.InsertNextPoint(0.0, -2.0, -144.0)

        bendPoints.InsertNextPoint(0.0, -8.0, -144.0)  # second bend
        bendPoints.InsertNextPoint(0.0, -9.0, -143.0)
        bendPoints.InsertNextPoint(0.0, -10.0, -142.0)
        bendPoints.InsertNextPoint(0.0, -9.0, -141.0)  # just under bend

        # for probe shaft:
        shaftPoints = vtk.vtkPoints()
        shaftPoints.InsertNextPoint(1.96, 0.0, -142.0)  # from bend
        shaftPoints.InsertNextPoint(0.8, 0.0, -2.0)
        shaftPoints.InsertNextPoint(0.1, 0.0, 0.0)  # to tip

        # the handle###########
        handleLine = vtk.vtkCellArray()
        handleLine.InsertNextCell(6)  # number.of.points
        handleLine.InsertCellPoint(0)
        handleLine.InsertCellPoint(1)
        handleLine.InsertCellPoint(2)
        handleLine.InsertCellPoint(3)
        handleLine.InsertCellPoint(4)
        handleLine.InsertCellPoint(5)

        handleProfile = vtk.vtkPolyData()
        handleProfile.SetPoints(handlePoints)
        handleProfile.SetLines(handleLine)

        self.__HandleExtrude = vtk.vtkRotationalExtrusionFilter()
        self.__HandleExtrude.SetInputData(handleProfile)
        self.__HandleExtrude.SetResolution(24)
        self.__HandleExtrude.Update()

        # the bend in the probe############
        probeBend = vtk.vtkCellArray()
        probeBend.InsertNextCell(8)
        probeBend.InsertCellPoint(0)
        probeBend.InsertCellPoint(1)
        probeBend.InsertCellPoint(2)
        probeBend.InsertCellPoint(3)
        probeBend.InsertCellPoint(4)
        probeBend.InsertCellPoint(5)
        probeBend.InsertCellPoint(6)
        probeBend.InsertCellPoint(7)

        probeBendProfile = vtk.vtkPolyData()
        probeBendProfile.SetPoints(bendPoints)
        probeBendProfile.SetLines(probeBend)

        self.__ProbeBend = vtk.vtkTubeFilter()
        self.__ProbeBend.SetInput(probeBendProfile)
        self.__ProbeBend.SetNumberOfSides(24)
        self.__ProbeBend.SetRadius(2)
        self.__ProbeBend.Update()

        # the shaft of the probe************
        probeShaft = vtk.vtkCellArray()
        probeShaft.InsertNextCell(3)
        probeShaft.InsertCellPoint(0)
        probeShaft.InsertCellPoint(1)
        probeShaft.InsertCellPoint(2)

        probeShaftProfile = vtk.vtkPolyData()
        probeShaftProfile.SetPoints(shaftPoints)
        probeShaftProfile.SetLines(probeShaft)

        self.__ProbeShaftExtrude = vtk.vtkRotationalExtrusionFilter()
        self.__ProbeShaftExtrude.SetInput(probeShaftProfile)
        self.__ProbeShaftExtrude.SetResolution(24)
        self.__ProbeShaftExtrude.Update()

        ### The Handle Logo ###
        self.logo = vtk.vtkVectorText()
        self.logo.SetText("Finnis Virtual Design")
        logotransform = vtk.vtkTransform()
        logotransform.PostMultiply()
        logotransform.Translate(-7, -0.5, 0.0)
        logotransform.RotateY(90)
        logotransform.RotateX(180)
        logotransform.Scale(2, 2, 2)
        logotransform.Translate(10.0, 0.0, -250)

        self.__Logo = vtk.vtkTransformPolyDataFilter()
        self.__Logo.SetInput(self.logo.GetOutput())
        self.__Logo.SetTransform(logotransform)

        ### The Trajectory Line ###
        self.__TrajLine = vtk.vtkLineSource()
        self.__TrajLine.SetPoint1(0, 0, 0)
        self.__TrajLine.SetPoint2(0, self._Depth * 0.071, self._Depth)

        ### The Buttons ###
        self.__Button1 = vtk.vtkCubeSource()
        self.__Button1.SetXLength(2)
        self.__Button1.SetYLength(7)
        self.__Button1.SetZLength(10)
        self.__Button1.SetCenter(10, 0, -189.5)

        self.__Button2 = vtk.vtkCubeSource()
        self.__Button2.SetXLength(2)
        self.__Button2.SetYLength(7)
        self.__Button2.SetZLength(10)
        self.__Button2.SetCenter(10, 0, -204.5)

        self.__Button3 = vtk.vtkCubeSource()
        self.__Button3.SetXLength(2)
        self.__Button3.SetYLength(7)
        self.__Button3.SetZLength(10)
        self.__Button3.SetCenter(10, 0, -219.5)

        # correct for the orientation of the pointer
        transform = vtk.vtkTransform()
        transform.RotateX(270)
        transform.RotateZ(180)

        self.__HandleExtrudeRotate = vtk.vtkTransformPolyDataFilter()
        self.__HandleExtrudeRotate.SetInput(self.__HandleExtrude.GetOutput())
        self.__HandleExtrudeRotate.SetTransform(transform)

        self.__ProbeBendRotate = vtk.vtkTransformPolyDataFilter()
        self.__ProbeBendRotate.SetInput(self.__ProbeBend.GetOutput())
        self.__ProbeBendRotate.SetTransform(transform)

        self.__ProbeShaftExtrudeRotate = vtk.vtkTransformPolyDataFilter()
        self.__ProbeShaftExtrudeRotate.SetInput(
            self.__ProbeShaftExtrude.GetOutput())
        self.__ProbeShaftExtrudeRotate.SetTransform(transform)

        self.__LogoRotate = vtk.vtkTransformPolyDataFilter()
        self.__LogoRotate.SetInput(self.__Logo.GetOutput())
        self.__LogoRotate.SetTransform(transform)

        self.__Button1Rotate = vtk.vtkTransformPolyDataFilter()
        self.__Button1Rotate.SetInput(self.__Button1.GetOutput())
        self.__Button1Rotate.SetTransform(transform)

        self.__Button2Rotate = vtk.vtkTransformPolyDataFilter()
        self.__Button2Rotate.SetInput(self.__Button2.GetOutput())
        self.__Button2Rotate.SetTransform(transform)

        self.__Button3Rotate = vtk.vtkTransformPolyDataFilter()
        self.__Button3Rotate.SetInput(self.__Button3.GetOutput())
        self.__Button3Rotate.SetTransform(transform)

        self.__TrajLineRotate = vtk.vtkTransformPolyDataFilter()
        self.__TrajLineRotate.SetInput(self.__TrajLine.GetOutput())
        self.__TrajLineRotate.SetTransform(transform)

        self.__HandleData = self.__HandleExtrudeRotate.GetOutput()
        self.__ProbeBendData = self.__ProbeBendRotate.GetOutput()
        self.__ProbeShaftData = self.__ProbeShaftExtrudeRotate.GetOutput()
        self.__LogoData = self.__LogoRotate.GetOutput()
        self.__Button1Data = self.__Button1Rotate.GetOutput()
        self.__Button2Data = self.__Button2Rotate.GetOutput()
        self.__Button3Data = self.__Button3Rotate.GetOutput()
        self.__TrajLineData = self.__TrajLineRotate.GetOutput()

    #--------------------------------------
    def _MakeActors(self):
        # the non-shareable portion of the pipeline
        handleMapper = vtk.vtkPolyDataMapper()
        handleMapper.SetInput(self.__HandleData)

        probeBendMapper = vtk.vtkPolyDataMapper()
        probeBendMapper.SetInput(self.__ProbeBendData)

        probeShaftMapper = vtk.vtkPolyDataMapper()
        probeShaftMapper.SetInput(self.__ProbeShaftData)

        trajLineMapper = vtk.vtkPolyDataMapper()
        trajLineMapper.SetInput(self.__TrajLine.GetOutput())

        logoMapper = vtk.vtkPolyDataMapper()
        logoMapper.SetInput(self.__LogoData)

        button1Mapper = vtk.vtkPolyDataMapper()
        button1Mapper.SetInput(self.__Button1Data)
        button2Mapper = vtk.vtkPolyDataMapper()
        button2Mapper.SetInput(self.__Button2Data)
        button3Mapper = vtk.vtkPolyDataMapper()
        button3Mapper.SetInput(self.__Button3Data)
        trajLineMapper = vtk.vtkPolyDataMapper()
        trajLineMapper.SetInput(self.__TrajLineData)

        handle = self._NewActor()
        handle.SetMapper(handleMapper)
        handle.SetProperty(self._HandleProperty)

        probeBend = self._NewActor()
        probeBend.SetMapper(probeBendMapper)
        probeBend.SetProperty(self._WarningProperty)

        probeShaft = self._NewActor()
        probeShaft.SetMapper(probeShaftMapper)
        # hack to let the extruded pointer match with the handle!
        probeShaft.RotateX(4.0)
        # probeShaft.SetPosition(0.0, -9.9, 0.0)
        probeShaft.SetProperty(self._WarningProperty)

        logo = self._NewActor()
        logo.SetMapper(logoMapper)
        logo.SetProperty(vtk.vtkProperty())
        logo.GetProperty().SetColor(1, 1, 1)

        button1 = self._NewActor()
        button1.SetMapper(button1Mapper)
        button1.SetProperty(self._Button1Property)

        button2 = self._NewActor()
        button2.SetMapper(button2Mapper)
        button2.SetProperty(self._Button2Property)

        button3 = self._NewActor()
        button3.SetMapper(button3Mapper)
        button3.SetProperty(self._Button3Property)

        trajLine = self._NewActor()
        trajLine.SetMapper(trajLineMapper)
        trajLine.SetProperty(self._TrajProperty)

        return (handle, probeBend, probeShaft, button1, button2, button3, trajLine, logo)

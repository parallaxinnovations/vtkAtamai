"""
UltrasoundProbeFactory - a tracked ultrasound probe

  This class is highly experimental.

"""
from __future__ import division
from __future__ import absolute_import

from builtins import range
from past.utils import old_div
from .TrackedInstrumentFactory import *
from .SlicePlaneFactory import *
from .ImagePlaneFactory import *
import math
try:
    import atexit
except:
    import sys
import atexit


class UltrasoundProbeFactory(TrackedInstrumentFactory):

    def __init__(self):
        TrackedInstrumentFactory.__init__(self)

        # create the chunk of pipeline that
        # can be shared between all renderers
        self.CreateProbeData()
        # self.CreateFanData(100,100)
        self.CreateFanData(5, 100, -45, 45)

        try:
            self.__Video = vtkMILVideoSource()
        except:
            self.__Video = vtk.vtkVideoSource()
        try:
            atexit.register(self.__Video.ReleaseSystemResources)
        except:
            atexit.register(self.__Video.ReleaseSystemResources)

        self.__Video.SetFrameSize(320, 240, 1)
        self.__Video.SetOutputFormatToLuminance()
        self.__Video.SetClipRegion(0, 255, 0, 240, 0, 0)
        self.__Video.SetOutputWholeExtent(0, 255, 0, 255, 0, 0)
        self.__Video.SetDataSpacing(old_div(2, 4.79), old_div(-2, 4.9), 0.5)
        self.__Video.SetDataOrigin(-58.48, 87.76, 0.0)
        self.__Video.SetFrameRate(10)

        self.__SlicePlane = SlicePlaneFactory()
        self.__SlicePlane.SetOrigin(-80, -0, 0)
        self.__SlicePlane.SetPoint1(+80, -0, 0)
        self.__SlicePlane.SetPoint2(-80, 100, 0)
        self.__SlicePlane.SetPolyData(self.__FanData)
        self.__SlicePlane.GetTransform().SetInput(self._Transform)
        self.AddChild(self.__SlicePlane)

        self.__VideoPlane = ImagePlaneFactory()
        self.__VideoPlane.SetInput(self.__Video.GetOutput())
        self.__VideoPlane.GeneratePlane()
        self.__VideoPlane.SetPolyData(self.__FanData)
        self.__VideoPlane.GetTransform().SetInput(self._Transform)
        self.AddChild(self.__VideoPlane)

        self.BindTrackerEvent("<LeaveView>", self.DoLeaveView)
        self.BindTrackerEvent("<EnterView>", self.DoEnterView)

    def DoLeaveView(self, event):
        TrackedInstrumentFactory.DoLeaveView(self, event)
        # self.__Video.Stop()

    def DoEnterView(self, event):
        TrackedInstrumentFactory.DoEnterView(self, event)
        # self.__Video.Play()

    def GetSlicePlane(self):
        return self.__SlicePlane

    def GetVideoPlane(self):
        return self.__VideoPlane

    def GetVideoSource(self):
        return self.__Video

    def SetInput(self, input):
        # set a volume to examine with the probe
        self.__SlicePlane.SetInput(input)

    def GetInput(self):
        return self.__SlicePlane.GetInput()

    def SetLookupTable(self, table):
        self.__SlicePlane.SetLookupTable(table)

    def GetLookupTable(self):
        return self.__SlicePlane.GetLookupTable()

    def CreateFanData(self, w, h, phi1=0, phi2=0):
        if (phi1 == 0 and phi2 == 0):
            # rectangle i.e. linear array
            points = vtk.vtkPoints()
            cells = vtk.vtkCellArray()
            polyline = vtk.vtkCellArray()
            vertices = [(old_div(-w, 2.0), 0, 0),
                        (old_div(-w, 2.0), h, 0),
                        (old_div(w, 2.0), h, 0),
                        (old_div(w, 2.0), 0, 0)]
            cells.InsertNextCell(4)
            polyline.InsertNextCell(5)
            for i in range(4):
                vertex = vertices[i]
                points.InsertPoint(i, vertex[0], vertex[1], vertex[2])
                cells.InsertCellPoint(i)
                polyline.InsertCellPoint(i)
            polyline.InsertCellPoint(0)
        else:
            # create a fan polygon with 20 segments
            points = vtk.vtkPoints()
            cells = vtk.vtkCellArray()
            polyline = vtk.vtkCellArray()
            polyline.InsertNextCell(13)
            phi1 = phi1 * math.pi / 180
            phi2 = phi2 * math.pi / 180
            points.InsertPoint(
                0, w * math.sin(phi1), w * math.cos(phi1) - w, 0)
            points.InsertPoint(1, (h + w) * math.sin(
                phi1), (h + w) * math.cos(phi1) - w, 0)
            polyline.InsertCellPoint(0)
            polyline.InsertCellPoint(1)
            for i in range(1, 11):
                phi = phi1 * (10 - i) / 10.0 + phi2 * i / 10.0
                points.InsertPoint(i + 1, (h + w) * math.sin(
                    phi), (h + w) * math.cos(phi) - w, 0)
                cells.InsertNextCell(3)
                cells.InsertCellPoint(0)
                cells.InsertCellPoint(i)
                cells.InsertCellPoint(i + 1)
                polyline.InsertCellPoint(i + 1)
            if (w != 0):
                points.InsertPoint(
                    12, w * math.sin(phi2), w * math.cos(phi2) - w, 0)
                cells.InsertNextCell(3)
                cells.InsertCellPoint(0)
                cells.InsertCellPoint(11)
                cells.InsertCellPoint(12)
                polyline.InsertCellPoint(12)
            polyline.InsertCellPoint(0)

        fan = vtk.vtkPolyData()
        fan.SetPoints(points)
        fan.SetPolys(cells)

        outline = vtk.vtkPolyData()
        outline.SetPoints(points)
        outline.SetLines(polyline)

        self.__FanData = fan
        self.__FanOutlineData = outline

    def CreateProbeData(self):
        # use a cylinder for the burrhole tip
        tip = vtk.vtkCylinderSource()
        tip.SetHeight(26.0)
        tip.SetRadius(6.0)
        tip.SetCenter(0.0, 13.0, 0.0)
        tip.SetResolution(24)
        tip.CappingOn()
        self.__TipSource = tip

        # set up points for the handle
        points = vtk.vtkPoints()
        points.InsertPoint(0, 9.594, 41.0, 7.5)
        points.InsertPoint(1, -6.0, 38.0, 7.5)
        points.InsertPoint(2, -6.0, 26.0, 7.5)
        points.InsertPoint(3, 22.0, 26.0, 7.5)
        points.InsertPoint(4, 40.0, 106.0, 7.5)
        points.InsertPoint(5, 25.383, 109.375, 7.5)
        points.InsertPoint(6, 9.594, 41.0, -7.5)
        points.InsertPoint(7, -6.0, 38.0, -7.5)
        points.InsertPoint(8, -6.0, 26.0, -7.5)
        points.InsertPoint(9, 22.0, 26.0, -7.5)
        points.InsertPoint(10, 40.0, 106.0, -7.5)
        points.InsertPoint(11, 25.383, 109.375, -7.5)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(4)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(3)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(3)
        cells.InsertCellPoint(4)
        cells.InsertCellPoint(5)
        cells.InsertCellPoint(0)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(6)
        cells.InsertCellPoint(7)
        cells.InsertCellPoint(8)
        cells.InsertCellPoint(9)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(9)
        cells.InsertCellPoint(10)
        cells.InsertCellPoint(11)
        cells.InsertCellPoint(6)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(7)
        cells.InsertCellPoint(6)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(1)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(8)
        cells.InsertCellPoint(7)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(2)
        cells.InsertCellPoint(3)
        cells.InsertCellPoint(9)
        cells.InsertCellPoint(8)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(3)
        cells.InsertCellPoint(4)
        cells.InsertCellPoint(10)
        cells.InsertCellPoint(9)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(4)
        cells.InsertCellPoint(5)
        cells.InsertCellPoint(11)
        cells.InsertCellPoint(10)
        cells.InsertNextCell(4)
        cells.InsertCellPoint(5)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(6)
        cells.InsertCellPoint(11)

        handle = vtk.vtkPolyData()
        handle.SetPoints(points)
        handle.SetPolys(cells)

        # set up a permutation matrix to describe the
        # orientation of the probe
        matrix = vtk.vtkMatrix4x4()
        matrix.SetElement(0, 0, 0)
        matrix.SetElement(1, 1, 0)
        matrix.SetElement(2, 2, 0)
        matrix.SetElement(0, 0, 1)
        matrix.SetElement(1, 1, -1)
        matrix.SetElement(2, 2, -1)

        transform = vtk.vtkTransform()
        transform.SetMatrix(matrix)

        self.__TipRotate = vtk.vtkTransformPolyDataFilter()
        self.__TipRotate.SetInput(self.__TipSource.GetOutput())
        self.__TipRotate.SetTransform(transform)

        self.__HandleRotate = vtk.vtkTransformPolyDataFilter()
        self.__HandleRotate.SetInput(handle)
        self.__HandleRotate.SetTransform(transform)

        # polydata for the tip
        self.__TipData = self.__TipRotate.GetOutput()

        # polydata for the handle
        self.__HandleData = self.__HandleRotate.GetOutput()

    def _MakeActors(self):
        # the non-shareable portion of the pipeline
        tipMapper = vtk.vtkDataSetMapper()
        tipMapper.SetInput(self.__TipData)

        handleMapper = vtk.vtkDataSetMapper()
        handleMapper.SetInput(self.__HandleData)

        outlineMapper = vtk.vtkDataSetMapper()
        outlineMapper.SetInput(self.__FanOutlineData)

        tipActor = self._NewActor()
        tipActor.SetMapper(tipMapper)
        tipActor.SetProperty(self._WarningProperty)
        tipActor.GetProperty().SetColor(1.0, 1.0, 1.0)

        handleActor = self._NewActor()
        handleActor.SetMapper(handleMapper)
        handleActor.SetProperty(tipActor.GetProperty())

        outlineActor = self._NewActor()
        outlineActor.SetMapper(outlineMapper)
        outlineActor.SetProperty(vtkProperty())
        # outlineActor.GetProperty().SetLineWidth(2.0)
        outlineActor.GetProperty().SetColor(1.0, 0.0, 0.0)

        return [tipActor, handleActor, outlineActor]

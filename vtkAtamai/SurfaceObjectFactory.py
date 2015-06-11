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
    'module_name': '$RCSfile: SurfaceObjectFactory.py,v $',
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
SurfaceObjectFactory - display vtkPolyData as a surface or a mesh

  The SurfaceObjectFactory will display vtkPolyData.  It can be
  combined with a ClippingCubeFactory to allow you to view inside
  the data.  To connect a ClippingCubeFactory with a SurfaceObjectFactory,
  use  surface.SetClippingPlanes(cube.GetClippingPlanes()).

Derived From:

  ActorFactory

See Also:

  ClippingCubeFactory

Initialization:

  SurfaceObjectFactory()

Public Methods:

  SetInput(*input*)         -- set vtkPolyData as input

  GetInput()                -- get the input

  GetProperty()             -- get vtkProperty for front faces

  SetProperty(*property*)   -- set the property

  GetBackfaceProperty()     -- get vtkProperty for back faces

  SetBackfaceProperty(*property*) -- set the backface property

  SetClippingPlanes(*planes*) -- set a vtkPlaneCollection to clip the data with

  GetClippingPlanes()       -- get the clipping planes

  StrippingOn()             -- use triangle strips to increase rendering speed

  StrippingOff()            -- turn off triangle stripping

  SetStripping(*bool*)      -- set stripping on/off

  GetStripping()            -- is stripping on

  SmoothingOn()             -- smooth the data before rendering

  SmoothingOff()            -- do not smooth data

  SetSmoothing(*bool*)      -- turn smoothing on/off

  GetSmoothing()            -- is smoothing applied

  NormalGenerationOn()      -- generate a normal for each vertex

  NormalGenerationOff()     -- leave data as is

  SetNormalGeneration(*bool*) -- set whether to generate normals

  GetNormalGeneration()     -- are normals generated

  SetFeatureAngle(*angle*)  -- set feature angle (in degrees) for data,
                               for use in normal generation and smoothing

  GetFeatureAngle()         -- get the feature angle

"""

#======================================
from ActorFactory import *
import logging

#======================================


class SurfaceObjectFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)
        self._input_data = None
        self._algorithm = None
        self._ClippingPlanes = None
        self._Cutters = {}
        self._Property = vtk.vtkProperty()
        self._BackfaceProperty = vtk.vtkProperty()

        self._FeatureAngle = 360

        self._TriangleFilter = None
        self._SmoothPolyDataFilter = None
        self._PolyDataNormals = None
        self._Stripper = None

    def SetStripping(self, val):
        if val and not self._Stripper:
            self._TriangleFilter = vtk.vtkTriangleFilter()
            self._Stripper = vtk.vtkStripper()
            self._BuildPipeline()
            self.Modified()
        elif self._Stripper and not val:
            self._TriangleStripper = None
            self._Stripper = None
            self._BuildPipeline()
            self.Modified()

    def GetStripping(self):
        return (self._Stripper != None)

    def StrippingOn(self):
        self.SetStripping(1)

    def StrippingOff(self):
        self.SetStripping(0)

    def SetNormalGeneration(self, val):
        if val and not self._PolyDataNormals:
            self._PolyDataNormals = vtk.vtkPolyDataNormals()
            self._PolyDataNormals.SetFeatureAngle(self._FeatureAngle)
            self._BuildPipeline()
            self.Modified()
        elif self._PolyDataNormals and not val:
            self._PolyDataNormals = None
            self._BuildPipeline()
            self.Modified()

    def GetNormalGeneration(self):
        return (self._PolyDataNormals != None)

    def NormalGenerationOn(self):
        self.SetNormalGeneration(1)

    def NormalGenerationOff(self):
        self.SetNormalGeneration(0)

    def SetSmoothing(self, val):
        if val and not self._SmoothPolyDataFilter:
            self._SmoothPolyDataFilter = vtk.vtkSmoothPolyDataFilter()
            self._SmoothPolyDataFilter.SetFeatureAngle(self._FeatureAngle)
            self._BuildPipeline()
            self.Modified()
        elif self._SmoothPolyDataFilter and not val:
            self._SmoothPolyDataFilter = None
            self._BuildPipeline()
            self.Modified()

    def GetSmoothing(self):
        return (self._SmoothPolyDataFilter != None)

    def SmoothingOn(self):
        self.SetSmoothing(1)

    def SmoothingOff(self):
        self.SetSmoothing(0)

    def SetFeatureAngle(self, angle):
        if self._FeatureAngle != angle:
            self._FeatureAngle = angle
            if self._PolyDataNormals:
                self._PolyDataNormals.SetFeatureAngle(angle)
            if self._SmoothPolyDataFilter:
                self._SmoothPolyDataFilter.SetFeatureAngle(angle)
            self.Modified()

    def GetFeatureAngle(self):
        return self._FeatureAngle

    def HasChangedSince(self, sinceMTime):
        if ActorFactory.HasChangedSince(self, sinceMTime):
            return 1
        if self._Property and self._Property.GetMTime() > sinceMTime:
            return 1
        return 0

    def SetProperty(self, property):
        self._Property = property
        for ren in self._Renderers:
            actor = self._ActorDict[ren][0]
            actor.SetProperty(property)
        self.Modified()

    def PickableOff(self):
        for ren in self._Renderers:
            actor = self._ActorDict[ren][0]
            actor.PickableOff()

    def PickableOn(self):
        for ren in self._Renderers:
            actor = self._ActorDict[ren][0]
            actor.PickableOn()

    def GetProperty(self):
        return self._Property

    def GetBackfaceProperty(self):
        return self._BackfaceProperty

    def SetBackfaceProperty(self, property):
        self._BackfaceProperty = property
        for ren in self._Renderers:
            actor = self._ActorDict[ren][0]
            actor.SetBackfaceProperty(property)
        self.Modified()

    def SetInputConnection(self, algorithm):
        if self._algorithm != algorithm:
            self._algorithm = algorithm
            self._input_data = None
            self._BuildPipeline()
            self.Modified()

    def SetInputData(self, input):
        if self._input_data != input:
            self._input_data = input
            self._algorithm = None
            self._BuildPipeline()
            self.Modified()

    def GetInputConnection(self):
        return self._algorithm

    # deprecated
    def GetInput(self):
        return self._input_data

    def SetClippingPlanes(self, clippingPlanes):
        self._ClippingPlanes = clippingPlanes
        actors = self._ActorDict
        for renderer in self._Renderers:
            for actor in actors[renderer]:
                actor.GetMapper().SetClippingPlanes(clippingPlanes)
        self.Modified()

    def GetClippingPlanes(self):
        return self._ClippingPlanes

    def _BuildPipeline(self):

        alg = self._algorithm
        surface = self._input_data

        # accommodate for surface data without a producer
        if alg is None and surface is not None:
            logging.warning(
                "SurfaceObjectFactory SetInput() method has been called!")
            tp = vtk.vtkTrivialProducer()
            tp.SetOutput(surface)
            alg = tp.GetOutputPort()

        for f2 in [self._TriangleFilter,
                   self._SmoothPolyDataFilter,
                   self._PolyDataNormals,
                   self._Stripper]:
            if f2:
                f2.SetInputConnection(alg)
                alg = f2.GetOutputPort()

        actors = self._ActorDict
        for renderer in self._Renderers:
            for actor in actors[renderer]:
                actor.GetMapper().SetInputConnection(alg)

        return alg

    def _MakeActors(self):
        actors = []
        alg = self._BuildPipeline()
        actor = self._NewActor()
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(alg)
        actor.SetMapper(mapper)
        actor.SetProperty(self._Property)
        actor.SetBackfaceProperty(self._BackfaceProperty)
        actors.append(actor)

        if self._ClippingPlanes:
            mapper.SetClippingPlanes(self._ClippingPlanes)
            self._ClippingPlanes.InitTraversal()
            clippingPlanes = []
            while 1:
                plane = self._ClippingPlanes.GetNextItem()
                if plane is None:
                    break
                else:
                    clippingPlanes.append(plane)

            for plane in clippingPlanes:
                cutter = vtk.vtkCutter()
                cutter.SetInputConnection(alg)
                cutter.SetCutFunction(plane)
                newPlanes = vtk.vtkPlaneCollection()
                for newPlane in clippingPlanes:
                    if newPlane != plane:
                        newPlanes.AddItem(newPlane)
                mapper = vtk.vtkDataSetMapper()
                mapper.SetClippingPlanes(newPlanes)
                mapper.SetInputConnection(cutter.GetOutputPort())
                actor = self._NewActor()
                actor.SetMapper(mapper)
                # actor.GetProperty().SetColor(1,0,0)
                self._Cutters[actor] = cutter
                actors.append(actor)

        return actors

    def _NewActor(self):
        actor = ActorFactory._NewActor(self)
        actor.SetProperty(self._Property)
        # Temporary fix to allow picking of Surface Objects...
        # if (self._ClippingPlanes):
        #    actor.PickableOff()
        return actor

    def _FreeActor(self, actor):
        if actor in self._Cutters:
            del self._Cutters[actor]
        ActorFactory._FreeActor(self, actor)

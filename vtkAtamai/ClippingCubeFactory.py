from __future__ import division
from __future__ import print_function
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

from builtins import range
from builtins import object
from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: ClippingCubeFactory.py,v $',
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
ClippingCubeFactory - six clipping planes that are dragged by the mouse

  The clipping cube is a set of six semi-transparent clipping planes that
  can be manipulated (pushed back and forth) with the mouse.  These clipping
  planes can be used to clip vtkPolyData.

Derived From:

  ActorFactory

See Also:

  VolumePlanesFactory

Initialization:

  ClippingCubeFactory()

Public Methods:

  SetFaceProperty(*p*)  -- set the vtkProperty for the faces

  GetFaceProperty()     -- get the current face property

  SetEdgeProperty(*p*)  -- set the vtkProperty for the edges

  GetEdgeProperty()     -- get the current edge property

  GetClippingPlanes()   -- get a vtkPlaneCollection of the clipping planes

  GetClippingPlane(*index*) -- get a single vtkPlane (index is 0 through 5)

  SetBounds(*bounds*)     -- set the maximum bounds (size) of the cube,
                             as a 6-tuple consisting of
                             (*xmin*,*xmax*,*ymin*,*ymax*,*zmin*,*zmax*)

  GetBounds()             -- get the maximum bounds

"""

#======================================
from .ActorFactory import *
import math
import vtk

#======================================
# helper class - not to be used outside this file


class ClippingCubeFacePlane(object):

    def __init__(self, clippingCubeFactory, vertices, planeIndex):
        self.__ClippingCubeFactory = clippingCubeFactory
        self.__Vertices = vertices
        self.__PlaneIndex = planeIndex
        axis = old_div(planeIndex, 2)
        self.__Axis = axis
        self.__Direction = 1 - 2 * (planeIndex - 2 * axis)
        self.__Permutation = {0: (0, 1, 2), 1: (1, 2, 0), 2: (2, 0, 1)}[axis]

        # axis is 0, 1, or 2  (i.e. x,y,z)
        faceVertices = []
        opposingVertices = []

        skip = 2 ** axis

        for i in range(2 ** (2 - axis)):
            for j in range(skip):
                faceVertices.append(vertices[2 * i * skip + j])
                opposingVertices.append(vertices[(2 * i + 1) * skip + j])

        if (2 * axis != planeIndex):
            faceVertices.reverse()
            opposingVertices.reverse()
            tmp = faceVertices
            faceVertices = opposingVertices
            opposingVertices = tmp

        self.__FaceVertices = faceVertices
        self.__OpposingVertices = opposingVertices

    def Push(self, distance):
        axis = self.__Axis
        planeIndex = self.__PlaneIndex
        faceVertices = self.__FaceVertices
        cubeFactory = self.__ClippingCubeFactory
        direction = self.__Direction

        o1 = self.GetTransformedCenter()

        if (distance > 0):  # i.e. pushing towards center
            opposingVertices = self.__OpposingVertices
            bounds = cubeFactory.GetBounds()[2 * axis:2 * (axis + 1)]
            # minimum plane separation
            minsep = (bounds[1] - bounds[0]) * 0.005
            for i in range(4):
                d = abs(faceVertices[i][axis] - opposingVertices[i][axis])
                if (d - minsep < distance):
                    distance = d - minsep
        else:  # i.e. pushing away from center
            distance = -distance
            bounds = cubeFactory.GetBounds()[2 * axis:2 * (axis + 1)]
            if ((bounds[1] - bounds[0]) * direction > 0):
                bound = bounds[0]
            else:
                bound = bounds[1]
            for i in range(4):
                d = abs(faceVertices[i][axis] - bound)
                if (d < distance):
                    distance = d
            distance = -distance

        distance = distance * direction

        for vertex in faceVertices:
            vertex[axis] = vertex[axis] + distance

        cubeFactory._ResetPlanes(planeIndex)

        o2 = self.GetTransformedCenter()
        n = self.GetTransformedNormal()
        # return the actual distance pushed
        return (o2[0] - o1[0]) * n[0] + (o2[1] - o1[1]) * n[1] + (o2[2] - o1[2]) * n[2]

    def SetCenter(self, *center):
        if len(center) == 1:
            center = center[0]

        axis = self.__Axis
        oldCenter = 0
        for vertex in self.__FaceVertices:
            oldCenter = oldCenter + vertex[axis]
        oldCenter = old_div(oldCenter, 4.0)

        direction = 1 - 2 * (self.__PlaneIndex - 2 * axis)
        self.Push(direction * (center[axis] - oldCenter))

    def GetCenter(self):
        face = self.__FaceVertices
        center = [0.0, 0.0, 0.0]
        for i in range(4):
            center[0] = center[0] + 0.25 * face[i][0]
            center[1] = center[1] + 0.25 * face[i][1]
            center[2] = center[2] + 0.25 * face[i][2]
        return tuple(center)

    def GetTransformedCenter(self):
        transform = self.__ClippingCubeFactory.GetTransform()
        if (transform):
            return transform.TransformFloatPoint(self.GetCenter())
        else:
            return self.GetCenter()

    def SetNormal(self, *normal):
        if len(normal) == 1:
            normal = normal[0]

        # do axis permutation
        x = self.__Axis
        y = x + 1
        z = y + 1
        if (y > 2):
            y = y - 3
        if (z > 2):
            z = z - 3

        center = self.GetCenter()

        print("SetNormal is still incomplete")

    def GetNormal(self):
        return self.__ClippingCubeFactory.GetClippingPlane(self.__PlaneIndex)\
            .GetNormal()

    def GetTransformedNormal(self):
        transform = self.__ClippingCubeFactory.GetTransform()
        if (transform):
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            transform.SetMatrix(self.__ClippingCubeFactory.GetTransform().
                                GetMatrix())
            return transform.TransformNormal(self.GetNormal())
        else:
            return self.GetNormal()

    def IntersectWithViewRay(self, x, y, renderer):
        # return the intersection of the view ray from
        #  display coordinates x,y

        # get the mouse delta in world coordinates
        renderer.SetDisplayPoint(x, y, 0.25)
        renderer.DisplayToWorld()
        lx1, ly1, lz1, w1 = renderer.GetWorldPoint()

        renderer.SetDisplayPoint(x, y, 0.75)
        renderer.DisplayToWorld()
        lx2, ly2, lz2, w2 = renderer.GetWorldPoint()

        return self.IntersectWithLine((old_div(lx1, w1), old_div(ly1, w1), old_div(lz1, w1)),
                                      (old_div(lx2, w2), old_div(ly2, w2), old_div(lz2, w2)))

    def IntersectWithLine(self, p1, p2):
        # return the intersection of the line with endpoints p1,p2 with plane

        # get plane normal and center
        nx, ny, nz = self.GetTransformedNormal()
        cx, cy, cz = self.GetTransformedCenter()

        # find line vector
        lx = p2[0] - p1[0]
        ly = p2[1] - p1[1]
        lz = p2[2] - p1[2]

        # dot the normal with the vector
        dotprod = nx * lx + ny * ly + nz * lz

        # divide-by-zero exception will be thrown in there is no intersection

        t = old_div((nx * (cx - p1[0]) + ny * (cy - p1[1]) + nz * (cz - p1[2])),   \
            dotprod)

        return (p1[0] + t * lx, p1[1] + t * ly, p1[2] + t * lz)

#======================================


class ClippingCubeFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self.cubeactors = []

        self._FaceProperty = vtk.vtkProperty()
        self._FaceProperty.SetOpacity(0.0002)
        self._FaceProperty.SetRepresentationToWireframe()
        self._EdgeProperty = vtk.vtkProperty()
        self._EdgeProperty.SetColor(1, 0, 0)
        self._EdgeProperty.SetOpacity(0.0)
        self._ClippingPlanes = []

        for i in range(6):
            self._ClippingPlanes.append(vtk.vtkPlane())

        self._ClippingPlanesCollection = None

        self._LineSources = []
        self._PlaneSources = []
        self._Planes = []
        self._Plane = None

        self._Bounds = (-0.5, +0.5, -0.5, +0.5, -0.5, +0.5)

        bounds = self._Bounds
        self._Vertices = [[bounds[0], bounds[2], bounds[4]],
                          [bounds[1], bounds[2], bounds[4]],
                          [bounds[0], bounds[3], bounds[4]],
                          [bounds[1], bounds[3], bounds[4]],
                          [bounds[0], bounds[2], bounds[5]],
                          [bounds[1], bounds[2], bounds[5]],
                          [bounds[0], bounds[3], bounds[5]],
                          [bounds[1], bounds[3], bounds[5]]]

        self._PlaneVertexIndices = ((0, 2, 4),
                                    (7, 3, 5),
                                    (0, 4, 1),
                                    (7, 6, 3),
                                    (0, 1, 2),
                                    (7, 5, 6))

        self._LineVertexIndices = ((0, 1),
                                   (2, 3),
                                   (4, 5),
                                   (6, 7),
                                   (0, 2),
                                   (1, 3),
                                   (4, 6),
                                   (5, 7),
                                   (0, 4),
                                   (1, 5),
                                   (2, 6),
                                   (3, 7))

        for i in range(12):
            self._LineSources.append(vtk.vtkLineSource())

        for i in range(6):
            self._PlaneSources.append(vtk.vtkPlaneSource())
            plane = ClippingCubeFacePlane(self, self._Vertices, i)
            self._Planes.append(plane)

        self._ResetPlanes()

        self.BindEvent("<ButtonPress>", self.DoStartAction)
        self.BindEvent("<ButtonRelease>", self.DoEndAction)
        self.BindEvent("<Motion>", self.DoPush)
        self.ShowCubeWhenPicked = 0

    def DoStartAction(self, event):
        try:
            index = list(self._ActorDict[event.renderer]).index(event.actor)
            self._Plane = self._Planes[index]
        except ValueError:
            self._Plane = None
        self._LastX = event.x
        self._LastY = event.y
        if (self.ShowCubeWhenPicked):
            self._EdgeProperty.SetOpacity(1.0)
            self.Modified()

    def DoEndAction(self, event):
        self._Plane = None
        if (self.ShowCubeWhenPicked):
            self._EdgeProperty.SetOpacity(0.0)
            self.Modified()

    def ShowClippingCubeWhenPickedOn(self):
        self._EdgeProperty.SetOpacity(0.0)
        self.ShowCubeWhenPicked = 1
        self.Modified()

    def ShowClippingCubeWhenPickedOff(self):
        self._EdgeProperty.SetOpacity(0.0)
        self.ShowCubeWhenPicked = 0
        self.Modified()

    def DoPush(self, event):
        if self._Plane is None:
            return

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX,
                                                      self._LastY,
                                                      renderer)

        # find depth-buffer value for point
        renderer.SetWorldPoint(lx, ly, lz, 1.0)
        renderer.WorldToDisplay()
        z = renderer.GetDisplayPoint()[2]

        # and use it to find the world coords of current x,y coord
        # (i.e. the mouse moves solely in x,y plane)
        renderer.SetDisplayPoint(event.x, event.y, z)
        renderer.DisplayToWorld()
        wx, wy, wz, w = renderer.GetWorldPoint()
        wx, wy, wz = (old_div(wx, w), old_div(wy, w), old_div(wz, w))

        # mouse motion vector, in world coords
        dx, dy, dz = (wx - lx, wy - ly, wz - lz)

        # check to make sure that plane is not facing camera
        nx, ny, nz = self._Plane.GetTransformedNormal()
        vx, vy, vz = camera.GetViewPlaneNormal()
        n_dot_v = nx * vx + ny * vy + nz * vz

        if (abs(n_dot_v) < 0.9):
            # drag plane to exactly match cursor motion
            dd = old_div((dx * (nx - vx * n_dot_v) + dy * (ny - vy * n_dot_v) + dz * (nz - vz * n_dot_v)), \
                 (1.0 - n_dot_v * n_dot_v))
        else:
            # plane is perpendicular to viewing ray, so just push by distance
            dd = math.sqrt(dx * dx + dy * dy + dz * dz)
            if (event.x + event.y - self._LastX - self._LastY < 0):
                dd = -dd

        # find the fraction of the push that was done, in case we hit bounds
        if (dd != 0):
            f = old_div(self._Plane.Push(dd), dd)
        else:
            f = 1.0

        if (f < 0.9999):
            # hit bounds: set LastX,LastY appropriately
            renderer.SetWorldPoint(lx + dx * f, ly + dy * f, lz + dz * f, 1.0)
            renderer.WorldToDisplay()
            x, y, z = renderer.GetDisplayPoint()
            self._LastX = int(x + 0.5)
            self._LastY = int(y + 0.5)
        else:
            self._LastX = event.x
            self._LastY = event.y

        self.Modified()

    def GetFaceProperty(self):
        return self._FaceProperty

    def SetFaceProperty(self, property):
        self._FaceProperty = property
        for ren in self._Renderers:
            for i in range(0, 6):
                self._ActorDict[ren][i].SetProperty(property)

    def GetEdgeProperty(self):
        return self._EdgeProperty

    def SetEdgeProperty(self, property):
        self._EdgeProperty = property
        for ren in self._Renderers:
            for i in range(6, 18):
                self._ActorDict[ren][i].SetProperty(property)

    def SetOpacity(self, opacity):
        self._FaceProperty.SetOpacity(opacity)
        self.Modified()

    def GetOpacity(self):
        return self._FaceProperty.GetOpacity()

    def SetBounds(self, *bounds):
        if len(bounds) == 1:
            bounds = bounds[0]
        x0, x1, y0, y1, z0, z1 = bounds
        bounds = (min(x0, x1), max(x0, x1),
                  min(y0, y1), max(y0, y1),
                  min(z0, z1), max(z0, z1))
        self._Bounds = tuple(bounds)
        self._SetVerticesFromBounds()
        self._ResetPlanes()

    def GetBounds(self):
        return self._Bounds

    def GetClippingPlanes(self):
        if self._ClippingPlanesCollection is None:
            collection = vtk.vtkPlaneCollection()
            for plane in self._ClippingPlanes:
                collection.AddItem(plane)
            self._ClippingPlanesCollection = collection
        return self._ClippingPlanesCollection

    def GetClippingPlane(self, index):
        collection = self.GetClippingPlanes()
        collection.InitTraversal()
        for i in range(index):
            collection.GetNextItem()
        return collection.GetNextItem()

    def GetPlanes(self):
        return self._Planes

    def GetPlane(self, actor, renderer=None):
        if (renderer != None):
            renderers = (renderer,)
        else:
            renderers = self.GetRenderers()
        for renderer in renderers:
            actors = list(self.GetActors(renderer))
            if actor in actors:
                return self._Planes[actors.index(actor)]

    def SetPickable(self, i):

        for actor in self.cubeactors:
            if i == 0:
                actor.PickableOff()
            elif i == 1:
                actor.PickableOn()

    def _MakeActors(self):
        actors = []
        for i in range(6):
            # the face actors
            actor = self._NewActor()
            actor.SetProperty(self._FaceProperty)
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputConnection(self._PlaneSources[i].GetOutputPort())
            actor.SetMapper(mapper)
            actors.append(actor)
        for i in range(12):
            # the edge actors
            actor = self._NewActor()
            actor.SetProperty(self._EdgeProperty)
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputConnection(self._LineSources[i].GetOutputPort())
            actor.SetMapper(mapper)
            actors.append(actor)
        self.cubeactors = actors
        return actors

    def _SetVerticesFromBounds(self):
        bounds = self._Bounds
        vertices = self._Vertices
        for i in range(8):
            for j in range(3):
                if (i % (2 ** (j + 1)) < 2 ** j):
                    inc = 0
                else:
                    inc = 1
                vertices[i][j] = bounds[2 * j + inc]

    def GetVertices(self):
        return self._Vertices

    def _ResetPlanes(self, planeIndex=-1):
        vertices = self._Vertices
        for i in range(6):
            indexTuple = self._PlaneVertexIndices[i]
            plane = self._PlaneSources[i]
            plane.SetOrigin(*vertices[indexTuple[0]])
            plane.SetPoint1(*vertices[indexTuple[1]])
            plane.SetPoint2(*vertices[indexTuple[2]])
        for i in range(12):
            indexTuple = self._LineVertexIndices[i]
            line = self._LineSources[i]
            line.SetPoint1(*vertices[indexTuple[0]])
            line.SetPoint2(*vertices[indexTuple[1]])

        # adjust plane equations appropriately
        if (planeIndex == -1):
            indexList = list(range(6))
        else:
            indexList = [planeIndex]

        for i in indexList:
            planeEquation = self._ClippingPlanes[i]
            plane = self._PlaneSources[i]
            planeEquation.SetNormal(plane.GetNormal())
            planeEquation.SetOrigin(plane.GetOrigin())

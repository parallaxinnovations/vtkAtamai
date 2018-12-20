from __future__ import division
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
from past.utils import old_div
__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name': '$RCSfile: CubePlanesFactory.py,v $',
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
CubePlanesFactory - a set of six planes that slice through a volume

  The CubePlanesFactory draws texture-mapped slices on the surfaces
  of a cube that cut through a 3D image data set.  It also provides
  interaction modes to allow you to manipulate the three planes.

Derived From:

  ActorFactory

See Also:

  SlicePlaneFactory, OrthoPlanesFactory

Initialization:

  CubePlanesFactory()

"""

#======================================
from .ActorFactory import *
from .SlicePlaneFactory import *
import math

#======================================


class CubePlanesFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self._Inputs = []
        self._LookupTables = []
        self._Planes = []

        self._FrameColor = [1.0000, 0.8431, 0.0000]
        self._PushColor = [0, 1, 0]
        self._RotateColor = [1, 0, 0]
        self._SpinColor = [0, 1, 1]

        for i in range(6):
            plane = SlicePlaneFactory()
            plane.RestrictPlaneToVolumeOn()
            # plane.OutlineOn()
            # plane.SetOutlineColor(self._FrameColor)
            self._Planes.append(plane)
            self.AddChild(plane)
            plane._Transform = self._Transform

        # 3 pairs of parallel planes
        self._PlanePairs = {}
        for i in range(3):
            self._PlanePairs[self._Planes[i]] = self._Planes[i + 3]
            self._PlanePairs[self._Planes[i + 3]] = self._Planes[i]

        # Eight points of the cube
        self._CubePoints = vtk.vtkPoints()
        self._CubePoints.SetNumberOfPoints(8)

        # Cube source
        self._CubeSource = vtk.vtkCubeSource()

        # Bounds of the volume input
        self._Bounds = None

        self.BindEvent("<ButtonPress>", self.DoStartAction)
        self.BindEvent("<ButtonRelease>", self.DoEndAction)
        self.BindEvent("<Motion>", self.DoAction)
        self.BindEvent("<B1-ButtonPress>", self.DoResetPlanes)
        self.BindEvent("<B2-ButtonPress>", self.DoResetPlanes)
        self.BindEvent("<B3-ButtonPress>", self.DoResetPlanes)

    def DoResetPlanes(self, event):
        self._Transform.Identity()
        self.Modified()

    def DoStartAction(self, event):
        for plane in self._Planes:
            if event.actor in plane.GetActors(event.renderer):
                self._LastX = event.x
                self._LastY = event.y
                self._Plane = plane
                break

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        # in world coordinates
        wx, wy, wz = self._Plane.IntersectWithViewRay(self._LastX,
                                                      self._LastY,
                                                      renderer)

        # transform back to local coords of SlicePlaneFactory
        trans = self._Transform.GetInverse()
        lx, ly, lz = trans.TransformPoint(wx, wy, wz)

        v1 = self._Plane.GetVector1()
        v2 = self._Plane.GetVector2()
        planeSize1 = self._Plane.GetSize1()
        planeSize2 = self._Plane.GetSize2()
        planeOrigin = self._Plane.GetOrigin()
        planePoint1 = self._Plane.GetPoint1()
        planePoint2 = self._Plane.GetPoint2()

        if self._Plane is self._Planes[0] or \
                self._Plane is self._Planes[3]:  # X-Y
            # plane boundary
            bound = (planeOrigin[0],
                     planeOrigin[1],
                     planePoint1[0],
                     planePoint2[1])
            # coords in 2D
            x2D = lx
            y2D = ly

        elif self._Plane is self._Planes[1] or \
                self._Plane is self._Planes[4]:  # Y-Z
            bound = (planeOrigin[1],
                     planeOrigin[2],
                     planePoint1[1],
                     planePoint2[2])
            x2D = ly
            y2D = lz

        elif self._Plane is self._Planes[2] or \
                self._Plane is self._Planes[5]:  # Z-X
            bound = (planeOrigin[2],
                     planeOrigin[0],
                     planePoint1[2],
                     planePoint2[0])
            x2D = lz
            y2D = lx

        else:
            pass

        # divide plane into three zones for different user interactions:
        # four corns  -- spin around plane normal at ortho center
        # four edges  -- rotate around one of the plane axes at ortho center
        # center area -- push
        x0 = bound[0]
        y0 = bound[1]
        x1 = bound[2]
        y1 = bound[3]

        # swap if necessary
        if x0 > x1:
            x0, x1 = x1, x0
            v1 = [-v1[0], -v1[1], -v1[2]]
        if y0 > y1:
            y0, y1 = y1, y0
            v2 = [-v2[0], -v2[1], -v2[2]]

        marginX = planeSize1 * 0.05
        marginY = planeSize2 * 0.05

        if (x2D < x0 + marginX):  # left margin
            if (y2D < y0 + marginY) or (y2D > y1 - marginY):  # corners
                self.__UserAction = 'Spin'
            else:                                             # left edge
                self.__UserAction = 'Rotate'
                self.__RotateAxis = v2
                self.__RadiusVector = (-v1[0], -v1[1], -v1[2])

        elif (x2D > x1 - marginX):  # right margin
            if (y2D < y0 + marginY) or (y2D > y1 - marginY):  # corners
                self.__UserAction = 'Spin'
            else:                                             # right edge
                self.__UserAction = 'Rotate'
                self.__RotateAxis = v2
                self.__RadiusVector = v1

        else:  # middle
            if (y2D < y0 + marginY):                          # bottom edge
                self.__UserAction = 'Rotate'
                self.__RotateAxis = v1
                self.__RadiusVector = (-v2[0], -v2[1], -v2[2])
            elif (y2D > y1 - marginY):                         # top edge
                self.__UserAction = 'Rotate'
                self.__RotateAxis = v1
                self.__RadiusVector = v2
            else:                                             # cetral area
                self.__UserAction = 'Push'

        # Make Plane Outline visible
        self._Plane.OutlineOn()
        if self.__UserAction == 'Push':
            self._Plane.SetOutlineColor(self._PushColor)
        elif self.__UserAction == 'Rotate':
            self._Plane.SetOutlineColor(self._RotateColor)
        elif self.__UserAction == 'Spin':
            self._Plane.SetOutlineColor(self._SpinColor)
        else:
            pass

        self.Modified()

    def DoEndAction(self, event):
        if self._Plane:
            self._Plane.DoEndAction(event)
            # Make Plane Outline Invisible
            self._Plane.OutlineOff()
            self._Plane = None

        self.__UserAction = None
        self.__RotateAxis = None
        self.__RadiusVector = None

        self.Modified()

    def DoAction(self, event):
        if (self._Plane == None):
            return

        if self.__UserAction == 'Push':
            self.DoPush(event)
        elif self.__UserAction == 'Spin':
            self.DoSpin(event)
        elif self.__UserAction == 'Rotate':
            self.DoRotation(event)
        else:
            pass

    def DoSpin(self, event):
        if (self._Plane == None):
            return

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX,
                                                      self._LastY,
                                                      renderer)

        # new intersection
        nx, ny, nz = self._Plane.IntersectWithViewRay(event.x,
                                                      event.y,
                                                      renderer)

        # mouse motion vector, in world coords
        dx, dy, dz = (nx - lx, ny - ly, nz - lz)

        # plane Center and plane normal before transform
        # p0 = self._Plane.GetOrigin()
        p1 = self._Plane.GetPoint1()
        p2 = self._Plane.GetPoint2()
        center = [old_div((p1[0] + p2[0]), 2.0),
                  old_div((p1[1] + p2[1]), 2.0),
                  old_div((p1[2] + p2[2]), 2.0)]

        # center = self._Plane.GetCenter()  # self.GetOrthoCenter()
        normal = self._Plane.GetNormal()

        # after transform
        transform = self._Transform
        wc = transform.TransformPoint(center)
        wn = transform.TransformNormal(normal)

        # radius vector (from Ortho Center to cursor position)
        rv = (lx - wc[0], ly - wc[1], lz - wc[2])

        # distance between Ortho Center and cursor location
        rs = math.sqrt(rv[0] * rv[0] + rv[1] * rv[1] + rv[2] * rv[2])

        # normalize radius vector
        rv = [old_div(rv[0], rs), old_div(rv[1], rs), old_div(rv[2], rs)]

        # spin direction
        wn_cross_rv = (wn[1] * rv[2] - wn[2] * rv[1],
                       wn[2] * rv[0] - wn[0] * rv[2],
                       wn[0] * rv[1] - wn[1] * rv[0])

        # spin angle
        dw = 57.2957804904 * (dx * wn_cross_rv[0] +
                              dy * wn_cross_rv[1] +
                              dz * wn_cross_rv[2]) / rs

        # Translate the plane ceter to origin of world coords
        transform.PostMultiply()
        # transform.Translate(-center[0],-center[1],-center[2])
        transform.Translate(-wc[0], -wc[1], -wc[2])

        # Rotate around plane normal
        transform.RotateWXYZ(dw, wn[0], wn[1], wn[2])

        # Translate back
        # transform.Translate(center[0],center[1],center[2])
        transform.Translate(wc[0], wc[1], wc[2])

        self._LastX = event.x
        self._LastY = event.y

        self.Modified()

    def DoRotation(self, event):
        if (self._Plane == None):
            return

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX,
                                                      self._LastY,
                                                      renderer)

        # find depth-buffer value for intersection point
        renderer.SetWorldPoint(lx, ly, lz, 1.0)
        renderer.WorldToDisplay()
        z = renderer.GetDisplayPoint()[2]

        # and use it to find the world coords of the current x,y coord
        # (i.e. the mouse moves solely in x,y plane)
        renderer.SetDisplayPoint(event.x, event.y, z)
        renderer.DisplayToWorld()
        wx, wy, wz, w = renderer.GetWorldPoint()
        wx, wy, wz = (old_div(wx, w), old_div(wy, w), old_div(wz, w))

        # mouse motion vector, in world coords
        dx, dy, dz = (wx - lx, wy - ly, wz - lz)

        # plane center before transform
        # p0 = self._Plane.GetOrigin()
        p1 = self._Plane.GetPoint1()
        p2 = self._Plane.GetPoint2()
        center = [old_div((p1[0] + p2[0]), 2.0),
                  old_div((p1[1] + p2[1]), 2.0),
                  old_div((p1[2] + p2[1]), 2.0)]
        normal = self._Plane.GetNormal()

        # after transform
        transform = self._Transform
        wc = transform.TransformPoint(center)                # ortho center
        wn = self._Plane.GetTransformedNormal()              # plane normal
        ra = transform.TransformVector(self.__RotateAxis)    # rotate axis
        rv = transform.TransformVector(self.__RadiusVector)  # radius vector

        # radius of the rotating circle of the picked point
        radius = abs(rv[0] * (lx - wc[0]) +
                     rv[1] * (ly - wc[1]) +
                     rv[2] * (lz - wc[2]))

        # rotate direction ra_cross_rv
        rd = (ra[1] * rv[2] - ra[2] * rv[1],
              ra[2] * rv[0] - ra[0] * rv[2],
              ra[0] * rv[1] - ra[1] * rv[0])

        # view normal
        vnx, vny, vnz = camera.GetViewPlaneNormal()

        # view up
        vux, vuy, vuz = camera.GetViewUp()

        # view right
        vrx = vuy * vnz - vuz * vny
        vry = vuz * vnx - vux * vnx
        vrz = vux * vny - vuy * vnz

        # direction cosin between rotating direction and view normal
        rd_dot_vn = rd[0] * vnx + rd[1] * vny + rd[2] * vnz

        # 'push' plan edge when mouse move away from plan center
        # 'pull' plan edge when mouse move toward plan center
        dw = 57.28578 * \
            (dx * rv[0] + dy * rv[1] + dz * rv[2]) / radius * (-rd_dot_vn)

        # Translate the plane Ceter to origin of world coords
        transform.PostMultiply()
        # transform.Translate(-center[0],-center[1],-center[2])
        transform.Translate(-wc[0], -wc[1], -wc[2])

        # Rotate around rotation axis in the plane
        transform.RotateWXYZ(dw, ra[0], ra[1], ra[2])

        # Translate back
        # transform.Translate(center[0],center[1],center[2])
        transform.Translate(wc[0], wc[1], wc[2])

        self._LastX = event.x
        self._LastY = event.y

        self.Modified()

    def DoPush(self, event):
        if (self._Plane == None):
            return

        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX,
                                                      self._LastY,
                                                      renderer)

        # find depth-buffer value for intersection point
        renderer.SetWorldPoint(lx, ly, lz, 1.0)
        renderer.WorldToDisplay()
        z = renderer.GetDisplayPoint()[2]

        # and use it to find the world coords of the current x,y coord
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
            dd = old_div((dx * (nx - vx * n_dot_v) + dy * (ny - vy * n_dot_v) +
                  dz * (nz - vz * n_dot_v)), (1.0 - n_dot_v * n_dot_v))
        else:
            # plane is perpendicular to viewing ray, so just push by distance
            dd = math.sqrt(dx * dx + dy * dy + dz * dz)
            if (n_dot_v * (event.x + event.y - self._LastX - self._LastY) > 0):
                dd = -dd

        # check if the two parallel planes are getting too close
        plane2 = self._PlanePairs[self._Plane]
        gap = self._Plane.GetSlicePosition() - plane2.GetSlicePosition()
        if (gap < 0 and gap + dd >= -0.5) or \
           (gap > 0 and gap + dd <= 0.5):
            # not allowed, don't push
            dd = 0
            f = 0
        else:
            # do the push and find the fraction of the push that was done,
            # in case we hit bounds
            f = old_div(self._Plane.Push(dd), dd)

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

        # update cube points
        self._UpdateCubePoints(self._Plane, dd)
        self._UpdatePlanes()

        self.Modified()

    def GetPlanes(self):
        return self._Planes

    def GetPlane(self, actor, renderer=None):
        if (renderer != None):
            renderers = (renderer,)
        else:
            renderers = self._Renderers
        for renderer in renderers:
            for plane in self._Planes:
                if actor in plane.GetActors(renderer):
                    return plane

    def AddInput(self, input):
        self._Inputs.append(input)
        self._LookupTables.append(None)
        planes = self._Planes

        for plane in planes:
            plane.AddInput(input)

        i = planes[0].GetNumberOfInputs()

        if (i == 1):
            self._Bounds = self._CalcBounds(input)
            xb, yb, zb = self._Bounds
            self._CubePoints.SetPoint(0, [xb[0], yb[0], zb[0]])
            self._CubePoints.SetPoint(1, [xb[1], yb[0], zb[0]])
            self._CubePoints.SetPoint(2, [xb[0], yb[1], zb[0]])
            self._CubePoints.SetPoint(3, [xb[0], yb[0], zb[1]])

            self._CubePoints.SetPoint(4, [xb[1], yb[1], zb[1]])
            self._CubePoints.SetPoint(5, [xb[0], yb[1], zb[1]])
            self._CubePoints.SetPoint(6, [xb[1], yb[0], zb[1]])
            self._CubePoints.SetPoint(7, [xb[1], yb[1], zb[0]])
            self._UpdatePlanes()

        self.Modified()
        return i

    def SetInput(self, input, i=0):
        planes = self._Planes
        if (i == planes[0].GetNumberOfInputs()):
            self.AddInput(input)
            return
        for plane in planes:
            plane.SetInput(input, i)
            # plane.SetXResolution(1)
            # plane.SetYResolution(1)

        if (i == 0):
            self._Bounds = self._CalcBounds(input)
            self._CubeSource.SetROIBounds(self._Bounds)

            xb, yb, zb = self._Bounds
            # give each point of the cube a id
            # using the rotational symetry along <111>
            # 0: (0,0,0), 1: (1,0,0), 2: (0,1,0), 3: (0,0,1)
            # 4: (1,1,1), 5: (0,1,1), 6: (1,0,1), 7: (1,1,0)
            self._CubePoints.SetPoint(0, [xb[0], yb[0], zb[0]])
            self._CubePoints.SetPoint(1, [xb[1], yb[0], zb[0]])
            self._CubePoints.SetPoint(2, [xb[0], yb[1], zb[0]])
            self._CubePoints.SetPoint(3, [xb[0], yb[0], zb[1]])

            self._CubePoints.SetPoint(4, [xb[1], yb[1], zb[1]])
            self._CubePoints.SetPoint(5, [xb[0], yb[1], zb[1]])
            self._CubePoints.SetPoint(6, [xb[1], yb[0], zb[1]])
            self._CubePoints.SetPoint(7, [xb[1], yb[1], zb[0]])

            self._UpdatePlanes()

        self.Modified()

    def _UpdateCubePoints(self, plane, dd):
        # plane: picked plane
        # dd: pushed amount

        # eight points for the cube
        points = self._CubePoints

        # we don't want go out of the boundary of volume input
        xb, yb, zb = self._Bounds

        # When pushing a plane, we are changing the position of
        # four points of the cube. Here are the eight cases:
        if plane is self._Planes[0]:
            for i in (0, 1, 2, 7):
                lastx, lasty, lastz = points.GetPoint(i)
                z = lastz + dd
                if z < zb[0]:
                    z = zb[0]
                if z > zb[1]:
                    z = zb[1]
                points.SetPoint(i, [lastx, lasty, z])
            # self._CubeSource.SetBounds()

        if plane is self._Planes[1]:
            for i in (0, 2, 3, 5):
                lastx, lasty, lastz = points.GetPoint(i)
                x = lastx + dd
                if x < xb[0]:
                    x = xb[0]
                if x > xb[1]:
                    x = xb[1]
                points.SetPoint(i, [x, lasty, lastz])

        if plane is self._Planes[2]:
            for i in (0, 1, 3, 6):
                lastx, lasty, lastz = points.GetPoint(i)
                y = lasty + dd
                if y < yb[0]:
                    y = yb[0]
                if y > yb[1]:
                    y = yb[1]
                points.SetPoint(i, [lastx, y, lastz])

        if plane is self._Planes[3]:
            for i in (3, 4, 5, 6):
                lastx, lasty, lastz = points.GetPoint(i)
                z = lastz + dd
                if z < zb[0]:
                    z = zb[0]
                if z > zb[1]:
                    z = zb[1]
                points.SetPoint(i, [lastx, lasty, z])

        if plane is self._Planes[4]:
            for i in (1, 4, 6, 7):
                lastx, lasty, lastz = points.GetPoint(i)
                x = lastx + dd
                if x < xb[0]:
                    x = xb[0]
                if x > xb[1]:
                    x = xb[1]
                points.SetPoint(i, [x, lasty, lastz])

        if plane is self._Planes[5]:
            for i in (2, 4, 5, 7):
                lastx, lasty, lastz = points.GetPoint(i)
                y = lasty + dd
                if y < yb[0]:
                    y = yb[0]
                if y > yb[1]:
                    y = yb[1]
                points.SetPoint(i, [lastx, y, lastz])

    def _UpdatePlanes(self):
        # Define 6 planes with eight points.
        # The order of index for each plane is important here:
        # 0,3: X-Y planes, 1,4: Y-Z planes, 2,5: Z-X planes
        planes = self._Planes
        points = self._CubePoints

        planes[0].SetOrigin(points.GetPoint(0))
        planes[0].SetPoint1(points.GetPoint(1))
        planes[0].SetPoint2(points.GetPoint(2))

        planes[1].SetOrigin(points.GetPoint(0))
        planes[1].SetPoint1(points.GetPoint(2))
        planes[1].SetPoint2(points.GetPoint(3))

        planes[2].SetOrigin(points.GetPoint(0))
        planes[2].SetPoint1(points.GetPoint(3))
        planes[2].SetPoint2(points.GetPoint(1))

        planes[3].SetOrigin(points.GetPoint(4))
        planes[3].SetPoint1(points.GetPoint(5))
        planes[3].SetPoint2(points.GetPoint(6))

        planes[4].SetOrigin(points.GetPoint(4))
        planes[4].SetPoint1(points.GetPoint(6))
        planes[4].SetPoint2(points.GetPoint(7))

        planes[5].SetOrigin(points.GetPoint(4))
        planes[5].SetPoint1(points.GetPoint(7))
        planes[5].SetPoint2(points.GetPoint(5))

    def _CalcBounds(self, input):
        input.UpdateInformation()
        extent = input.GetExtent()  # VTK 6
        origin = input.GetOrigin()
        spacing = input.GetSpacing()

        """
    xbounds = [origin[0]+spacing[0]*(extent[0]-0.5),
               origin[0]+spacing[0]*(extent[1]+0.5)]
    ybounds = [origin[1]+spacing[1]*(extent[2]-0.5),
               origin[1]+spacing[1]*(extent[3]+0.5)]
    zbounds = [origin[2]+spacing[2]*(extent[4]-0.5),
               origin[2]+spacing[2]*(extent[5]+0.5)]

    """
        xbounds = [origin[0] + spacing[0] * extent[0],
                   origin[0] + spacing[0] * extent[1]]
        ybounds = [origin[1] + spacing[1] * extent[2],
                   origin[1] + spacing[1] * extent[3]]
        zbounds = [origin[2] + spacing[2] * extent[4],
                   origin[2] + spacing[2] * extent[5]]

        if spacing[0] < 0:
            xbounds.reverse()
        if spacing[1] < 0:
            ybounds.reverse()
        if spacing[2] < 0:
            zbounds.reverse()

        return tuple([xbounds, ybounds, zbounds])

    def GetInput(self, i=0):
        return self._Inputs[i]

    def GetCubePoints(self):
        """
        Return vtkPoints object consisting of eight points of a cube
        """
        return self._CubePoints

    def SetCubePoints(self, cubepoints):
        try:
            for i in range(8):
                self._CubePoints.SetPoint(i, cubepoints.GetPoint(i))
        except:
            pass
        self._UpdatePlanes()

    def SetLookupTable(self, table, i=0):
        self._LookupTables[i] = table
        for plane in self._Planes:
            plane.SetLookupTable(table, i)
        self.Modified()

    def GetLookupTable(self, i=0):
        return self._LookupTables[i]

    def SetOpacity(self, i, alpha=None):
        for plane in self._Planes:
            plane.SetOpacity(i, alpha)

    def GetOpacity(self, i=0):
        return self._Planes[0].GetOpacity(i)

    def SetImageTransform(self, transform, i=0):
        for plane in self._Planes:
            plane.SetImageTransform(transform, i)
        self.Modified()

    def GetImageTransform(self, i=0):
        return self._Planes[0].GetImageTransform(i)

    def SetClippingPlanes(self, i, clippingPlanes=None):
        if (clippingPlanes == None):
            clippingPlanes = i
            i = 0
        for plane in self._Planes:
            plane.SetClippingPlanes(i, clippingPlanes)

    def GetClippingPlanes(self, i=0):
        return self._Planes[0].GetClippingPlanes(i)

    def SetSliceInterpolate(self, val):
        for plane in self._Planes:
            plane.SetSliceInterpolate(val)
        self.Modified()

    def GetSliceInterpolate(self):
        return self._Planes[0].GetSliceInterpolate()

    def SliceInterpolateOn(self):
        self.SetSliceInterpolate(1)

    def SliceInterpolateOff(self):
        self.SetSliceInterpolate(0)

    def SetTextureInterpolate(self, val):
        for plane in self._Planes:
            plane.SetTextureInterpolate(val)
        self.Modified()

    def GetTextureInterpolate(self):
        return self._Planes[0].GetTextureInterpolate()

    def TextureInterpolateOn(self):
        self.SetTextureInterpolate(1)

    def TextureInterpolateOff(self):
        self.SetTextureInterpolate(0)

    def OrthoPlanesReset(self):
        # same as DoResetPlanes, but callable
        self._Transform.Identity()

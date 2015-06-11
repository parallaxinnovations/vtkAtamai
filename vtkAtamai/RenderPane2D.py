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
    'module_name': '$RCSfile: RenderPane2D.py,v $',
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
RenderPane2D - a RenderPane for displaying a 2D view

  You must specify a plane (either a SlicePlaneFactory or an
  ImagePlaneFactory) that the RenderPane2D will view.  The camera
  will automatically track the plane, so that the view direction
  is always perpendicular to the plane.

  The middle button will call the Push() method of the specified plane
  if the plane has a Push method.

Derived From:

  RenderPane

See Also:

  SlicePlaneFactory, ImagePlaneFactory

Initialization:

  RenderPane2D(*master*=None)

  *master*  - the PaneFrame that will hold this RenderPane

Public Methods:

  ConnectPlane(*plane*)    -- set the SlicePlaneFactory to view

  DisconnectPlane(*plane*) -- disconnect the SlicePlaneFactory

  ResetView()            -- reset so that the plane fills the view

Interaction Bindings:

  BindPushToButton(*button*,*modifier*=None)    -- use the specified button
                                                   to adjust slice

  BindResetToButton(*button*,*modifier*=None)   -- use the specified button
                                                   to reset the view

Handler Methods:

  DoStartAction(*event*)   -- for push (bind to ButtonPress)

  DoEndAction(*event*)     -- for push (bind to ButtonRelease)

  DoPush(*event*)          -- for push (bind to Motion)

"""

#======================================
from RenderPane import *
from PI.visualization.common import CoordinateSystem

# TODO: refactor so this doesn't depend on PI code

#======================================


class RenderPane2D(RenderPane):

    """A rectangular window area that depicts a 2D scene.

    A RenderPane2D draws a 2D image or a slice through a
    3D image volume.

    """

    def __init__(self, *args, **kw):
        apply(RenderPane.__init__, (self,) + args, kw)

        self._Renderer.GetActiveCamera().ParallelProjectionOn()

        # the camera is always facing this plane
        self._Plane = None

        # what style of coordinate system?
        self._coordinate_system = CoordinateSystem.CoordinateSystem.vtk_coords

        # Action is set if the window receives a click
        self._Action = 0

        # this information helps to keep camera motion consistent
        self._LastFocalPoint = (0.0, 0.0, 0.0)
        self._LastNormal = (0.0, 0.0, 0.0)
        self._LastViewUp = (0.0, 0.0, 0.0)
        self._LastS = 0.5
        self._LastT = 0.5

        # set first button to the RenderWidget's pan function
        self.BindPanToButton(1)

        # set middle button to push
        # self.BindPushToButton(2)

        # shift-middle button does a reset for now
        self.BindResetToButton(2, "Shift")

    def __del__(self):
        print 'RenderPane2D deleted!'

    def SetCoordinateSystem(self, val):
        self._coordinate_system = val

    def GetCoordinateSystem(self):
        return self._coordinate_system

    #--------------------------------------
    def SetPointOfInterest(self, position):
        if len(position) == 1:
            position = position[0]

        x, y, z = position
        self._PointOfInterest = (x, y, z)

        self._Renderer.SetWorldPoint(x, y, z, 1.0)
        self._Renderer.WorldToDisplay()
        dx, dy, dz = self._Renderer.GetDisplayPoint()

        w, h = self._Renderer.GetSize()
        ox, oy = self._Renderer.GetOrigin()

        # check for center out of window
        if w > 0 and h > 0 and \
            ((dx - ox - 0.5) / w < 0.0 or (dx - ox - 0.5) / w > 1.0 or
             ((dy - oy - 0.5) / h < 0.0 or (dy - oy - 0.5) / h > 1.0)):
            camera = self._Renderer.GetActiveCamera()
            vx, vy, vz = camera.GetDirectionOfProjection()
            d = camera.GetDistance()
            camera.SetPosition(x, y, z)
            camera.SetFocalPoint((x - vx) * d, (y - vy) * d, (z - vz) * d)

        self.Modified()

    #--------------------------------------
    def BindPushToButton(self, button=1, modifier=None):
        self.BindModeToButton((self.DoStartAction,
                               self.DoEndAction,
                               self.DoPush),
                              button, modifier)

    def BindResetToButton(self, button=1, modifier=None):
        self.BindModeToButton((lambda e, s=self: s.ResetView(),
                               lambda e: None,
                               lambda e: None),
                              button, modifier)

    #--------------------------------------
    def DoStartAction(self, event):
        self._LastX = event.x
        self._LastY = event.y
        self._Action = 1

    def DoEndAction(self, event):
        self._Action = 0
        pass

    def DoPush(self, event):
        if not self._Action or not self._Plane or \
                not hasattr(self._Plane, 'Push'):
            return

        # get the distance in world coords for the push
        self._Renderer.SetDisplayPoint(event.x, event.y, 0)
        self._Renderer.DisplayToWorld()
        x, y, z, w = self._Renderer.GetWorldPoint()
        self._Renderer.SetDisplayPoint(self._LastX, self._LastY, 0)
        self._Renderer.DisplayToWorld()
        lx, ly, lz, w = self._Renderer.GetWorldPoint()
        distance = math.sqrt((lx - x) ** 2 + (ly - y) ** 2 + (lz - z) ** 2)

        # set sign of distance (down,left is neg, up,right is pos)
        if (event.x + event.y - self._LastX - self._LastY < 0):
            distance = -distance

        self._Plane.Push(distance)

        self._LastX = event.x
        self._LastY = event.y

    #--------------------------------------
    def DoCursorMotion(self, event):
        # handle cursor motion, internal use only

        # Modified by JDG -- we return immediately here, because
        # we don't like using 3D cursors
        return

        if self._Plane:
            try:
                transform = self._Plane.GetTransform()
            except:
                transform = vtk.vtkTransform()

            p0 = transform.TransformPoint(self._Plane.GetOrigin())
            p1 = transform.TransformPoint(self._Plane.GetPoint1())
            p2 = transform.TransformPoint(self._Plane.GetPoint2())

            v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])

            n1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2])
            n2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2])

            v1 = (v1[0] / n1, v1[1] / n1, v1[2] / n1)
            v2 = (v2[0] / n2, v2[1] / n2, v2[2] / n2)

            normal = (v1[1] * v2[2] - v1[2] * v2[1],
                      v1[2] * v2[0] - v1[0] * v2[2],
                      v1[0] * v2[1] - v1[1] * v2[0])

            vector = v2

            try:
                position = self._Plane.IntersectWithViewRay(event.x, event.y,
                                                            self._Renderer)
                self._UpdateCursorTransform(position, normal, vector)
            except ZeroDivisionError:
                pass

        else:
            RenderPane.DoCursorMotion(self, event)

    #--------------------------------------
    def ConnectPlane(self, plane):
        self._Plane = plane
        self.ConnectActorFactory(plane)
        self.ResetView()

    def DisconnectPlane(self, plane):
        self._Plane = None
        self.DisconnectActorFactory(plane)

    def SetPlane(self, plane):
        self._Plane = plane
        self.ResetView()

    def GetPlane(self):
        return self._Plane

    #--------------------------------------
    def ResetView(self):

        self._Renderer.ResetCamera()

        return

        if (self._Plane):
            input_connection = self._Plane.GetInputConnection()
            if (input_connection != None):
                # TODO: port to VTK6
                # input_connection.UpdateInformation()
                extent = input.GetExtent()
                spacing = input.GetSpacing()
                maxdim = max(abs((extent[1] - extent[0] + 1) * spacing[0]),
                             abs((extent[3] - extent[2] + 1) * spacing[1]),
                             abs((extent[5] - extent[4] + 1) * spacing[2]))
                self._Renderer.GetActiveCamera().SetParallelScale(maxdim / 2.0)
            self._LastNormal = (0.0, 0.0, 0.0)
            self._LastViewUp = (0.0, 0.0, 0.0)
            self._LastS = 0.5
            self._LastT = 0.5

        self.Modified()

    #--------------------------------------
    def StartRender(self):
        # render must orient camera towards the slice
        if (self._Plane):
            transform = self._Plane.GetTransform()
            camera = self._Renderer.GetActiveCamera()

            focus = camera.GetFocalPoint()
            normal = self._Plane.GetTransformedNormal()
            vector = self._Plane.GetTransformedVector()

            # check for camera pan
            if self._LastFocalPoint != focus and \
                self._LastNormal == normal and \
                    self._LastViewUp == vector:
                try:
                    center = self._Plane.IntersectWithLine(
                        camera.GetPosition(), camera.GetFocalPoint())
                    center = transform.GetInverse().TransformPoint(center)
                except ZeroDivisionError:
                    center = self._Plane.GetCenter()

                origin = self._Plane.GetOrigin()
                v1 = self._Plane.GetPoint1()
                v2 = self._Plane.GetPoint2()
                v1 = (v1[0] - origin[0], v1[1] - origin[1], v1[2] - origin[2])
                v2 = (v2[0] - origin[0], v2[1] - origin[1], v2[2] - origin[2])

                v = (center[0] - origin[0],
                     center[1] - origin[1],
                     center[2] - origin[2])

                s = (v1[0] * v[0] + v1[1] * v[1] + v1[2] * v[2]) / \
                    (v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
                t = (v2[0] * v[0] + v2[1] * v[1] + v2[2] * v[2]) / \
                    (v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)

                if (abs(s - self._LastS) + abs(t - self._LastT) > 1e-5):
                    self._LastS = s
                    self._LastT = t

            s = self._LastS
            t = self._LastT

            # set up camera
            origin = self._Plane.GetOrigin()
            v1 = self._Plane.GetPoint1()
            v2 = self._Plane.GetPoint2()
            v1 = (v1[0] - origin[0], v1[1] - origin[1], v1[2] - origin[2])
            v2 = (v2[0] - origin[0], v2[1] - origin[1], v2[2] - origin[2])

            center = (origin[0] + s * v1[0] + t * v2[0],
                      origin[1] + s * v1[1] + t * v2[1],
                      origin[2] + s * v1[2] + t * v2[2])
            center = transform.TransformFloatPoint(center)

            # use DICOM coordinate system?
            if self.GetCoordinateSystem() == CoordinateSystem.CoordinateSystem.dicom_coords:
                _m = -1
            else:
                _m = 1

            camera.SetFocalPoint(center)
            camera.SetPosition(center[0] + _m * (normal[0] * 251),
                               center[1] + _m * (normal[1] * 251),
                               center[2] + _m * (normal[2] * 251))
            camera.ComputeViewPlaneNormal()
            camera.SetViewUp(vector[0], _m * vector[1], vector[2])

            self._LastNormal = normal
            self._LastViewUp = vector
            self._LastFocalPoint = focus

            d = camera.GetDistance()
            # p = camera.GetParallelScale()*0.05
            p = 0.7 + camera.GetParallelScale() / 95

            camera.SetClippingRange(d - p, d + p)

        RenderPane.StartRender(self)

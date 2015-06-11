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
    'module_name': '$RCSfile: ObliquePlaneFactory.py,v $',
    'creator': 'Hua Qian <hqian@irus.rri.ca>',
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
ObliquePlaneFactory - provide mouse interaction with a single slice plane

Derived From:

  ActorFactory

See Also:

  SlicePlaneFactory, OrthoPlanesFactory

Initialization:

  ObliquePlaneFactory()

Public Methods:

  Specify the image volume:

    SetInput(*imagedata*,*i*=0)   -- set a vtkImageData to slice through

    GetInput(*i*=0)               -- get input *i*

    AddInput(*imagedata*)         -- add an input after the last input

    RemoveInput(*i*=0)            -- remove an input

    GetNumberOfInputs()           -- current number of inputs

  Change the display of the image:

    SetLookupTable(*table*,*i*=0) -- change the lookup table for image *i*

    GetLookupTable(*i*=0)         -- get the lookup table

"""

from ActorFactory import *
from SlicePlaneFactory import *
from PlaneOutlineFactory import *
from OutlineFactory import *
import math


class ObliquePlaneFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self._Inputs = []
        self._LookupTables = []
        self._Plane = SlicePlaneFactory()
        self.AddChild(self._Plane)
        self._Plane._Transform = self._Transform
        self._Plane.RestrictPlaneToVolumeOn()

        self._TagList = []
        self._MarkerList = []

        # colors for different user interaction
        self._PushColor = [0, 1, 0]
        self._RotateColor = [1, 0, 0]
        self._SpinColor = [0, 1, 1]

        self._DefaultOutlineColor = [0.5000, 0.6196, 0.6196]

        self._Plane.OutlineOn()
        self._Plane.SetOutlineColor(self._DefaultOutlineColor)

        self.BindEvent("<ButtonPress>", self.DoStartAction)
        self.BindEvent("<ButtonRelease>", self.DoEndAction)
        self.BindEvent("<Motion>", self.DoAction)
        self.BindEvent("<B1-ButtonPress>", self.DoResetPlane)
        self.BindEvent("<B2-ButtonPress>", self.DoResetPlane)
        self.BindEvent("<B3-ButtonPress>", self.DoResetPlane)

    def AddInput(self, input, i=0):
        self._Inputs.append(input)
        self._LookupTables.append(None)
        self._Plane.AddInput(input)
        i = self._Plane.GetNumberOfInputs()
        if (i == 1):
            self._Plane.SetPlaneOrientationToXY()

        self.Modified()
        return i

    def SetInput(self, input, i=0):
        if (i == self._Plane.GetNumberOfInputs()):
            self.AddInput(input)
            return
        self._Plane.SetInput(input, i)
        if (i == 0):
            self._Plane.SetPlaneOrientationToXY()
        self.Modified()

    def GetNumberOfInputs(self):
        return len(self._Inputs)

    def SetLookupTable(self, table, i=0):
        self._LookupTables[i] = table
        self._Plane.SetLookupTable(table, i)
        self.Modified()

    def GetPlane(self):
        return self._Plane

    def SetVisibility(self, yesno, i=0, renderer=None):
        self._Plane.SetVisibility(yesno, i, renderer)

    def SetImageTransform(self, transform, i=0):
        self._Plane.SetImageTransform(transform, i)
        self.Modified()

    def GetImageTransform(self, i=0):
        return self._Plane.GetImageTransform(i)

    def DoResetPlane(self, event):
        self._Transform.Identity()
        self.Modified()

    def DoStartAction(self, event):
        if event.actor in self._Plane.GetActors(event.renderer):
            self._LastX = event.x
            self._LastY = event.y

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

        ux, uy, uz = self._Plane.GetVector1()
        vx, vy, vz = self._Plane.GetVector2()
        ox, oy, oz = self._Plane.GetOrigin()
        us = self._Plane.GetSize1()
        vs = self._Plane.GetSize2()

        # use dot-product to convert to 2D X,Y values between [0,1]
        X = ((lx - ox) * ux + (ly - oy) * uy + (lz - oz) * uz) / us
        Y = ((lx - ox) * vx + (ly - oy) * vy + (lz - oz) * vz) / vs

        # divide plane into three zones for different user interactions:
        # four corns  -- spin around plane normal at ortho center
        # four edges  -- rotate around one of the plane axes at ortho center
        # center area -- push

        if ((X < 0.05 or X > 0.95) and (Y < 0.05 or Y > 0.95)):
            self.__UserAction = 'Spin'
        elif (X < 0.05 or X > 0.95):
            self.__UserAction = 'Rotate'
            self.__RotateAxis = (vx, vy, vz)
            self.__RadiusVector = (ux, uy, uz)
        elif (Y < 0.05 or Y > 0.95):
            self.__UserAction = 'Rotate'
            self.__RotateAxis = (ux, uy, uz)
            self.__RadiusVector = (vx, vy, vz)
        else:
            self.__UserAction = 'Push'

        # Make Plane Outline visible
        self._Plane.OutlineOn()
        if self.__UserAction == 'Push':
            self._Plane.SetOutlineColor(self._PushColor)
            # self._PlaneGuides.SetColor(self._PushColor)
        elif self.__UserAction == 'Rotate':
            self._Plane.SetOutlineColor(self._RotateColor)
            # self._PlaneGuides.SetColor(self._RotateColor)
        elif self.__UserAction == 'Spin':
            self._Plane.SetOutlineColor(self._SpinColor)
            # self._PlaneGuides.SetColor(self._SpinColor)
        else:
            pass

        self.Modified()

    def DoEndAction(self, event):
        self._Plane.DoEndAction(event)

        # Make Plane Outline Invisible
        try:
            self._Plane.SetOutlineColor(self._DefaultOutlineColor)
            self._Plane.OutlineOn()
        except:
            self._Plane.OutlineOff()

        self.__UserAction = None
        self.__RotateAxis = None
        self.__RadiusVector = None

        self.Modified()

    def DoAction(self, event):
        if self.__UserAction == 'Push':
            self.DoPush(event)
        elif self.__UserAction == 'Spin':
            self.DoSpin(event)
        elif self.__UserAction == 'Rotate':
            self.DoRotation(event)
        else:
            pass

    def DoSpin(self, event):
        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX, self._LastY,
                                                      renderer)

        # new intersection
        nx, ny, nz = self._Plane.IntersectWithViewRay(event.x, event.y,
                                                      renderer)

        # mouse motion vector, in world coords
        dx, dy, dz = (nx - lx, ny - ly, nz - lz)

        # ortho Center and plane normal before transform
        # center = self._Plane.GetCenter()
        p1 = self._Plane.GetPoint1()
        p2 = self._Plane.GetPoint2()
        center = [(p1[0] + p2[0]) / 2.0,
                  (p1[1] + p2[1]) / 2.0,
                  (p1[2] + p2[2]) / 2.0]
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
        rv = [rv[0] / rs, rv[1] / rs, rv[2] / rs]

        # spin direction
        wn_cross_rv = (wn[1] * rv[2] - wn[2] * rv[1],
                       wn[2] * rv[0] - wn[0] * rv[2],
                       wn[0] * rv[1] - wn[1] * rv[0])

        # spin angle
        dw = 57.2957804904 * (dx * wn_cross_rv[0] +
                              dy * wn_cross_rv[1] +
                              dz * wn_cross_rv[2]) / rs

        # Translate the OrthoPlanes Ceter to origin of world coords
        transform.PostMultiply()
        transform.Translate(-wc[0], -wc[1], -wc[2])

        # Rotate around plane normal
        transform.RotateWXYZ(dw, wn[0], wn[1], wn[2])

        # Translate back
        transform.Translate(wc[0], wc[1], wc[2])

        self._LastX = event.x
        self._LastY = event.y

        self.Modified()

    def DoRotation(self, event):
        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX, self._LastY,
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
        wx, wy, wz = (wx / w, wy / w, wz / w)

        # mouse motion vector, in world coords
        dx, dy, dz = (wx - lx, wy - ly, wz - lz)

        # plane center before transform
        p1 = self._Plane.GetPoint1()
        p2 = self._Plane.GetPoint2()
        center = [(p1[0] + p2[0]) / 2.0,
                  (p1[1] + p2[1]) / 2.0,
                  (p1[2] + p2[2]) / 2.0]

        # plane normal before transform
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

        # direction cosin between rotating direction and view normal
        rd_dot_vn = rd[0] * vnx + rd[1] * vny + rd[2] * vnz

        # 'push' plan edge when mouse move away from plan center
        # 'pull' plan edge when mouse move toward plan center
        dw = 57.28578 * \
            (dx * rv[0] + dy * rv[1] + dz * rv[2]) / radius * (-rd_dot_vn)

        # Translate the OrthoPlanes Ceter to origin of world coords
        transform.PostMultiply()
        transform.Translate(-wc[0], -wc[1], -wc[2])

        # Rotate around rotation axis in the plane
        transform.RotateWXYZ(dw, ra[0], ra[1], ra[2])

        # Translate back
        transform.Translate(wc[0], wc[1], wc[2])

        self._LastX = event.x
        self._LastY = event.y

        # self._PlaneOutline.SetColor(1,0,0)
        self.Modified()

    def DoPush(self, event):
        renderer = event.renderer
        camera = renderer.GetActiveCamera()

        # find intersection of viewing ray from LastX,LastY with the plane
        lx, ly, lz = self._Plane.IntersectWithViewRay(self._LastX, self._LastY,
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
        wx, wy, wz = (wx / w, wy / w, wz / w)

        # mouse motion vector, in world coords
        dx, dy, dz = (wx - lx, wy - ly, wz - lz)

        # check to make sure that plane is not facing camera
        nx, ny, nz = self._Plane.GetTransformedNormal()
        vx, vy, vz = camera.GetViewPlaneNormal()
        n_dot_v = nx * vx + ny * vy + nz * vz

        if (abs(n_dot_v) < 0.9):
            # drag plane to exactly match cursor motion
            dd = (dx * (nx - vx * n_dot_v) + dy * (ny - vy * n_dot_v) + dz * (nz - vz * n_dot_v)) / \
                 (1.0 - n_dot_v * n_dot_v)
        else:
            # plane is perpendicular to viewing ray, so just push by distance
            dd = math.sqrt(dx * dx + dy * dy + dz * dz)
            if (n_dot_v * (event.x - event.y - self._LastX + self._LastY) > 0):
                dd = -dd

        # find the fraction of the push that was done, in case we hit bounds
        f = self._Plane.Push(dd) / dd

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

    def ObliqueReset(self, renderer):
        # same as DoResetPlane, but callable
        self._Transform.Identity()
        self.Modified()

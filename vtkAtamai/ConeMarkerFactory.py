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
    'module_name': '$RCSfile: ConeMarkerFactory.py,v $',
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
ConeMarkerFactory - produce cone shaped markers

Derived From:

  ActorFactory

Public Methods:

  SetSize(*size*) -- Set marker size in world dimensions.
    This method should be called after the actor was made
    to display the marker in suitable size.

  SetColor(*r*,*g*,*b*) -- set marker color.

  SetOpacity(*alpha*) -- set marker opacity.

  SetPosition(*position*) -- set marker position.

  SetNormal(*normal*) -- set conemaker normal.

"""

from ActorFactory import *
from math import *


class ConeMarkerFactory(ActorFactory):

    def __init__(self):
        ActorFactory.__init__(self)

        self.__cone = vtk.vtkConeSource()
        self.__transform = vtk.vtkTransform()
        # self.__coneMatrix = self.GetTransform().GetMatrix()

        self.__property = vtk.vtkProperty()

    def SetSize(self, size):
        self.__cone.SetHeight(size)
        self.__cone.SetRadius(0.5 * size)

        self.__cone.SetResolution(10)
        self.__cone.Update()

        # Hack the cone source so origin is at tip
        points = self.__cone.GetOutput().GetPoints()
        h = self.__cone.GetHeight()
        for i in range(points.GetNumberOfPoints()):
            p = points.GetPoint(i)
            points.SetPoint(i, p[0] - 0.5 * h, p[1], p[2])
        del points
        self.Modified()

    def UpdateTransform(self, position, normal):
        self.SetNormal(normal)
        self.SetPosition(position)

    def SetNormal(self, normal):
        norm = sqrt(normal[0] * normal[0] +
                    normal[1] * normal[1] +
                    normal[2] * normal[2])
        if(norm != 0):
            n_x = normal[0] / norm
            n_y = normal[1] / norm
            n_z = normal[2] / norm
        else:
            n_x = 1.0
            n_y = 0.0
            n_z = 0.0

        if (n_x * n_x > n_y * n_y and n_x * n_x > n_z * n_z):
            o_x = n_z / sqrt(n_x * n_x + n_z * n_z)
            o_y = 0
            o_z = -n_x / sqrt(n_x * n_x + n_z * n_z)

            p_x = -n_x * n_y / sqrt(n_x * n_x + n_z * n_z)
            p_y = 1
            p_z = -n_y * n_z / sqrt(n_x * n_x + n_z * n_z)

        elif (n_y * n_y > n_z * n_z):
            o_y = n_x / sqrt(n_y * n_y + n_x * n_x)
            o_z = 0
            o_x = -n_y / sqrt(n_y * n_y + n_x * n_x)

            p_y = -n_y * n_z / sqrt(n_y * n_y + n_x * n_x)
            p_z = 1
            p_x = -n_z * n_x / sqrt(n_y * n_y + n_x * n_x)

        else:
            o_z = n_y / sqrt(n_z * n_z + n_y * n_y)
            o_x = 0
            o_y = -n_z / sqrt(n_z * n_z + n_y * n_y)

            p_z = -n_z * n_x / sqrt(n_z * n_z + n_y * n_y)
            p_x = 1
            p_y = -n_x * n_y / sqrt(n_z * n_z + n_y * n_y)

        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy(self.__transform.GetMatrix())
        matrix.SetElement(0, 0, n_x)
        matrix.SetElement(1, 0, n_y)
        matrix.SetElement(2, 0, n_z)
        matrix.SetElement(0, 1, o_x)
        matrix.SetElement(1, 1, o_y)
        matrix.SetElement(2, 1, o_z)
        matrix.SetElement(0, 2, p_x)
        matrix.SetElement(1, 2, p_y)
        matrix.SetElement(2, 2, p_z)
        self.__transform.SetMatrix(matrix)
        self.Modified()

    def GetPosition(self):
        matrix = self.__transform.GetMatrix()
        return tuple((matrix.GetElement(0, 3),
                      matrix.GetElement(1, 3),
                      matrix.GetElement(2, 3)))

    def SetPosition(self, position):
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy(self.__transform.GetMatrix())
        matrix.SetElement(0, 3, position[0])
        matrix.SetElement(1, 3, position[1])
        matrix.SetElement(2, 3, position[2])
        self.__transform.SetMatrix(matrix)
        self.Modified()

    def SetOpacity(self, theOpacity):
        self.__property.SetOpacity(theOpacity)
        self.Modified()

    def SetColor(self, *args):
        apply(self.__property.SetColor, args)
        self.Modified()

    def GetColor(self):
        return self.__property.GetColor()

    def _MakeActors(self):
        actor = self._NewActor()
        actor.SetProperty(self.__property)
        return [actor]

    def _NewActor(self):
        actor = ActorFactory._NewActor(self)
        actor.SetUserTransform(self.__transform)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(self.__cone.GetOutput())
        actor.SetMapper(mapper)
        return actor

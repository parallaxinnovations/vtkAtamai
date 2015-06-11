"""
LandmarkRegistration - register two point sets

  Calculate the rigid-body transformation and the similarity transformation
  which best matches a set of source landmarks to a homologous set of
  target landmarks.

  The solution is based on

  Berthold K. P. Horn (1987)

  Closed-form solution of absolute orientation using unit quaternions

  _Journal of the Optical Society of America A_, 4:629-642

Public Methods:

  SetSourceLandmarks(*points*) -- set a list of source landmarks

  SetTargetLandmarks(*points*) -- set a list of target landmarks

  Register()                 -- do the least-squares registration
                               (this computes the matrices)

  GetRigidBodyMatrix()       -- return the rigid-body matrix

  GetRigidBodyResidual()     -- return the residual of the fit

  GetSimilarityMatrix()      -- return the similarity matrix

  GetSimilarityResidual()    -- return the residual of the fit

"""
import numpy
from LinearAlgebra import *


class LandmarkRegistration(object):

    """
    Find the transformation which maps one list of points (the 'FromPoints')
    to another set of points (the 'ToPoints').
    The algorithm is limited to rigid-body and rigid-body*uniform-scale
    transformations (which is generally what you want, anyway).
    """

    def __init__(self):
        self.__SourceLandmarks = []
        self.__TargetLandmarks = []

    def Register(self):
        # convert to arrays
        APoints = numpy.array(self.__SourceLandmarks, Float)
        BPoints = numpy.array(self.__TargetLandmarks, Float)
        # number of points
        n = APoints.shape[0]
        # find centroids
        APointsCentroid = sum(APoints, 0) / n
        BPointsCentroid = sum(BPoints, 0) / n

        A = numpy.array((APoints[:, 0] - APointsCentroid[0],
                         APoints[:, 1] - APointsCentroid[1],
                         APoints[:, 2] - APointsCentroid[2]))

        B = numpy.array((BPoints[:, 0] - BPointsCentroid[0],
                         BPoints[:, 1] - BPointsCentroid[1],
                         BPoints[:, 2] - BPointsCentroid[2]))

        # calculate the 3x3 M matrix as described in Horn's paper
        M = dot(A, transpose(B))
        Mdiag = diagonal(M)

        # calculate the 4x4 N matrix as described in Horn's paper
        N = numpy.zeros((4, 4), Float)

        # diagnonal elements of N
        N[0, 0] = dot((1, 1, 1), Mdiag)
        N[1, 1] = dot((1, -1, -1), Mdiag)
        N[2, 2] = dot((-1, 1, -1), Mdiag)
        N[3, 3] = dot((-1, -1, 1), Mdiag)

        # off-diagonal elements
        N[0, 1] = N[1, 0] = M[1][2] - M[2][1]
        N[0, 2] = N[2, 0] = M[2][0] - M[0][2]
        N[0, 3] = N[3, 0] = M[0][1] - M[1][0]

        N[1, 2] = N[2, 1] = M[0][1] + M[1][0]
        N[1, 3] = N[3, 1] = M[2][0] + M[0][2]
        N[2, 3] = N[3, 2] = M[1][2] + M[2][1]

        # find the eigenvalues, eigenvectors
        lam, vec = eigenvectors(N)
        # find the index of the maximum eigenvalue
        maxi = lam.tolist().index(maximum.reduce(lam))
        # find the corresponding eigenvector, which
        # is the quaternion of interest
        quat = vec[maxi]

        # decompose the quaternion, make a 3x3 matrix
        w, x, y, z = quat
        ww, xx, yy, zz = w * w, x * x, y * y, z * z
        wx, wy, wz = w * x, w * y, w * z
        xy, xz, yz = x * y, x * z, y * z

        M = numpy.array(
            [[ww + xx - yy - zz, 2.0 * (-wz + xy),  2.0 * (wy + xz)],
             [2.0 * (wz + xy),   ww - xx + yy - zz, 2.0 * (
              -wx + yz)],
             [2.0 * (
              -wy + xz),  2.0 * (wx + yz),   ww - xx - yy + zz]],
            Float)

        # find the scale
        S = trace(dot(B, transpose(dot(M, A)))) / trace(dot(A, transpose(A)))

        # rotation+scale matrix
        MS = M * S

        # the independant components of the registration:
        self.__Quaterion = quat
        self.__Rotation = M
        self.__Scale = S
        self.__PreTranslation = -APointsCentroid
        self.__PostTranslation = BPointsCentroid

        # find the residuals
        diff = dot(MS, A) - B
        self.__SimilarityResidual = sqrt(sum(
            sum(dot(diff, transpose(diff)) / n)))

        diff = dot(M, A) - B
        self.__RigidBodyResidual = sqrt(
            sum(sum(dot(diff, transpose(diff)) / n)))

    # set the source landmarks
    def SetSourceLandmarks(self, points):
        self.__SourceLandmarks = points

    # set the target landmarks
    def SetTargetLandmarks(self, points):
        self.__TargetLandmarks = points

    # get the quaternion
    def GetQuaternion(self):
        return self.__Quaternion

    # get just the 3x3 rotation matrix
    def GetRotation(self):
        return self.__Rotation

    # get just the uniform scale factor
    def GetScale(self):
        return self.__Scale

    # get the distance from the centroid of the 'From' points to the origin
    def GetPreTranslation(self):
        return self.__PreTranslation

    # get the distance from the origin to the centroid of the 'To' points
    def GetPostTranslation(self):
        return self.__PostTranslation

    # get the Procrustes residual for the rigid-body transformation
    def GetRigidBodyResidual(self):
        return self.__RigidBodyResidual

    # get the Procrustes residual for the rigid-body*scale transformation
    def GetSimilarityResidual(self):
        return self.__SimilarityResidual

    # get the 4x4 rigid body matrix
    def GetRigidBodyMatrix(self):
        M = self.__Rotation
        t = dot(M, self.__PreTranslation) + self.__PostTranslation
        return numpy.array(((M[0, 0], M[0, 1], M[0, 2], t[0]),
                            (M[1, 0], M[1, 1], M[1, 2], t[1]),
                            (M[2, 0], M[2, 1], M[2, 2], t[2]),
                            (0.0,   0.0,   0.0,   1.0)))

    # get the 4x4 matrix that incorporates scaling
    def GetSimilarityMatrix(self):
        M = self.__Rotation * self.__Scale
        t = dot(M, self.__PreTranslation) + self.__PostTranslation
        return numpy.array(((M[0, 0], M[0, 1], M[0, 2], t[0]),
                            (M[1, 0], M[1, 1], M[1, 2], t[1]),
                            (M[2, 0], M[2, 1], M[2, 2], t[2]),
                            (0.0,   0.0,   0.0,   1.0)))

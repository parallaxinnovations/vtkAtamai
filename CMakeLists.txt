PROJECT(vtkAtamai)

cmake_minimum_required(VERSION 2.8)

FIND_PACKAGE(PythonInterp)

IF(NOT DEFINED DIST_DIRECTORY)
SET(DIST_DIRECTORY "./dist")
ENDIF(NOT DEFINED DIST_DIRECTORY)

IF(NOT TARGET packages)
ADD_CUSTOM_TARGET(packages)
ENDIF()

ADD_DEPENDENCIES(packages vtkAtamai_egg)

ADD_CUSTOM_TARGET(vtkAtamai_egg
  ${PYTHON_EXECUTABLE} setup.py bdist_egg --dist-dir ${DIST_DIRECTORY}
)

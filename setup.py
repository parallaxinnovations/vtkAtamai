import os
import sys
from setuptools import setup

requires = [
  "future",
  "numpy",
  "vtk",
  "zope.interface"
]

setup(name="vtkAtamai",
      version="2.6.0",
      description="Atamai VTK/Python visualization classes",
      long_description="""
  Core VTK/Python classes used by MicroView.

  This package contains VTK/Python classes developed by Atamai Inc.
  and released under an Open Source license.  The classes have been
  repackaged for use in MicroView.

  """,
      url="https://github.com/parallaxinnovations/vtkAtamai",
      packages=['vtkAtamai'],
      license="BSD",
      maintainer="Jeremy Gill",
      maintainer_email="jgill@parallax-innovations.com",
      requires=requires,
      tests_require=['pytest', 'pytest-cov', 'tempdir>=0.7.1', 'future', 'codecov'],
      )

import os
import sys
from distutils.core import setup

requires = []

setup(name="vtkAtamai",
      version="2.5.0",
      description="Atamai VTK/Python visualization classes",
      long_description="""
  Core VTK/Python classes used by MicroView.

  This package contains VTK/Python classes developed by Atamai Inc.
  and released under an Open Source license.  The classes have been
  repackaged for use in MicroView.

  """,
      url="http://microview.sourceforge.net/vtkAtamai",
      packages=['vtkAtamai'],
      license="BSD",
      maintainer="Jeremy Gill",
      maintainer_email="jgill@parallax-innovations.com",
      )

# =========================================================================
#
# Copyright (c) 2000-2009 GE Healthcare
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
# EXCEPT WHEN OTHERWISE STATED IN WRITING BY THE COPYRIGHT HOLDERS AND/OR
# OTHER PARTIES, THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
# SOFTWARE "AS IS" WITHOUT EXPRESSED OR IMPLIED WARRANTY INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  IN NO EVENT UNLESS AGREED TO IN WRITING WILL
# ANY COPYRIGHT HOLDER OR OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
# THE SOFTWARE UNDER THE TERMS OF THIS LICENSE BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, LOSS OF DATA OR DATA BECOMING INACCURATE OR LOSS OF PROFIT OR
# BUSINESS INTERRUPTION) ARISING IN ANY WAY OUT OF THE USE OR INABILITY TO
# USE THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
#
# =========================================================================

"""
vtkAtamai - core VTK/Python classes from <A href="http://www.atamai.com">Atamai Inc.</A>

<A href="http://microview.sourceforge.net/vtkAtamai">vtkAtamai</A> contains core VTK/Python classes written by Atamai Inc.
They have been repackaged into a form directly useable in MicroView.  The vtkAtamai distribution can be downloaded
from the MicroView sourceforge project page located <A href="http://www.sourceforge.net/projects/microview">here</A>.
"""

#
# Add shared library path to sys.path.
# This action means that all classes under vtkMultiIO can be directly
# imported, if desired, for backward compatibility.
#
import os
import sys
sys.path.append(os.path.split(__file__)[0])
del os

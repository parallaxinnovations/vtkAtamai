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
    'module_name': '$RCSfile: qtPaneFrame.py,v $',
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
qtPaneFrame - a PaneFrame that is also a qt QWidget

  This class allows RenderPane to be used with qt from
  http://www.trolltech.com and PyQt from
  http://www.river-bank.demon.co.uk

  This class now works under both UNIX and Windows.

Derived From:

  RenderPane, QWidget

"""

#======================================
from qt import *
from PaneFrame import *

#======================================


class qtPaneFrame(PaneFrame, QWidget):

    # convert from schedule ID to QTimer
    _ScheduleIdDict = {}

    # long names for all codes in the latin1 character set
    KeySymFromLatin1 = [  # see X11/keysymdef.h
        "??", "??", "??", "??", "??", "??", "??", "??",
        "BackSpace", "Tab", "??", "??", "??", "Return", "??", "??",
        "??", "??", "??", "??", "??", "??", "??", "??",
        "??", "??", "??", "Escape", "??", "??", "??", "??",
        "space", "exclam", "quotedbl", "numbersign",
        "dollar", "percent", "ampersand", "quoteright",
        "parenleft", "parenright", "asterisk", "plus",
        "comma", "minus", "period", "slash",
        "0", "1", "2", "3", "4", "5", "6", "7",
        "8", "9", "colon", "semicolon",
        "less", "equal", "greater", "question",
        "at", "A", "B", "C", "D", "E", "F", "G",
        "H", "I", "J", "K", "L", "M", "N", "O",
        "P", "Q", "R", "S", "T", "U", "V", "W",
        "X", "Y", "Z", "bracketleft",
        "backslash", "bracketright", "asciicircum", "underscore",
        "quoteleft", "a", "b", "c", "d", "e", "f", "g",
        "h", "i", "j", "k", "l", "m", "n", "o",
        "p", "q", "r", "s", "t", "u", "v", "w",
        "x", "y", "z", "braceleft",
        "bar", "braceright", "asciitilde", "Delete",

        "nobreakspace", "exclamdown", "cent", "sterling",
        "currency", "yen", "brokenbar", "section",
        "diaeresis", "copyright", "ordfeminine", "guillemotleft",
        "notsign", "hyphen", "registered", "macron",
        "degree", "plusminus", "twosuperior", "threesuperior",
        "acute", "mu", "paragraph", "periodcentered",
        "cedilla", "onesuperior", "masculine", "guillemotright",
        "onequarter", "onehalf", "threequarters", "questiondown",
        "Agrave", "Aacute", "Acircumflex", "Atilde",
        "Adiaeresis", "Aring", "AE", "Ccedilla",
        "Egrave", "Eacute", "Ecircumflex", "Ediaeresis",
        "Igrave", "Iacute", "Icircumflex", "Idiaeresis",
        "ETH", "Ntilde", "Ograve", "Oacute",
        "Ocircumflex", "Otilde", "Odiaeresis", "multiply",
        "Ooblique", "Ugrave", "Uacute", "Ucircumflex",
        "Udiaeresis", "Yacute", "THORN", "ssharp",
        "agrave", "aacute", "acircumflex", "atilde",
        "adiaeresis", "aring", "ae", "ccedilla",
        "egrave", "eacute", "ecircumflex", "ediaeresis",
        "igrave", "iacute", "icircumflex", "idiaeresis",
        "eth", "ntilde", "ograve", "oacute",
        "ocircumflex", "otilde", "odiaeresis", "division",
        "ooblique", "ugrave", "uacute", "ucircumflex",
        "udiaeresis", "yacute", "thorn", "ydiaeresis"
    ]

    # convert from Qt key code to X key name
    KeySymFromKey = {
        0x1000: "Escape",
        0x1001: "Tab",
        0x1002: "??",  # BackTab
        0x1003: "BackSpace",
        0x1004: "Return",
        0x1005: "Enter",
        0x1006: "Insert",
        0x1007: "Delete",
        0x1008: "Pause",
        0x1009: "Print",
        0x100a: "Sys_Req",

        0x1010: "Home",
        0x1011: "End",
        0x1012: "Left",
        0x1013: "Up",
        0x1014: "Right",
        0x1015: "Down",
        0x1016: "Next",  # also PageDown
        0x1017: "Prior",  # also PageUp

        0x1020: "Shift_L",
        0x1021: "Control_L",
        0x1022: "Meta_L",
        0x1023: "Alt_L",
        0x1024: "Caps_Lock",
        0x1025: "Num_Lock",
        0x1026: "Scroll_Lock",

        0x1030: "F1",
        0x1031: "F2",
        0x1032: "F3",
        0x1033: "F4",
        0x1034: "F5",
        0x1035: "F6",
        0x1036: "F7",
        0x1037: "F8",
        0x1038: "F9",
        0x1039: "F10",
        0x103a: "F11",
        0x103b: "F12",
        0x103c: "F13",
        0x103d: "F14",
        0x103e: "F15",
        0x103f: "F16",

        0x1040: "F17",
        0x1041: "F18",
        0x1042: "F19",
        0x1043: "F20",
        0x1044: "F21",
        0x1045: "F22",
        0x1046: "F23",
        0x1047: "F24",
        0x1048: "F25",
        0x1049: "F26",
        0x104a: "F27",
        0x104b: "F28",
        0x104c: "F29",
        0x104d: "F30",
        0x104e: "F31",
        0x104f: "F32",

        0x1050: "F33",
        0x1051: "F34",
        0x1052: "F35",
        0x1053: "??",  # Super_L
        0x1054: "??",  # Super_R
        0x1055: "Menu",
        0x1056: "??",  # Hyper_L
        0x1057: "??",  # Hyper_R
        0x1058: "Help",

        0xffff: "KP_Begin"  # middle key on keypad
    }

    def __init__(self, parent=None, name=None, width=400, height=400, stereo=0):

        # if no parent, create an app for the user
        if parent is None:
            try:
                qApp.argv()  # generate an exception if qApp not allocated
            except:
                self._qtApp = QApplication(['qtPaneFrame'])

        # create qt-level widget
        QWidget.__init__(self, parent, None)

        # create our render window
        self._RenderWindow = vtk.vtkRenderWindow()
        self._RenderWindow.SetSize(width, height)
        if stereo:
            self._RenderWindow.StereoCapableWindowOn()
            self._RenderWindow.SetStereoTypeToCrystalEyes()

        # superclass must be initialized after self._RenderWindow is set
        PaneFrame.__init__(self)

        # set up some state variables
        self.__connected = 0  # is QT->VTK connection done?
        self.__lastState = 0  # state of last event
        self.__lastX = 0      # mouse x of last event
        self.__lastY = 0      # mouse y of last event
        self.__inside = 0     # is mouse inside window?
        self.__oldFocus = None
        self.__hintSize = QSize(width, height)

        # do all the necessary qt setup
        self.setBackgroundMode(2)  # NoBackground
        self.setMouseTracking(1)  # get all mouse events
        self.setFocusPolicy(2)  # ClickFocus
        if parent is None:
            self.show()

        if self.isVisible():
            self.polish()

    def polish(self):
        if not self.__connected:
            size = self.size()
            self._RenderWindow.SetSize(size.width(), size.height())
            self._RenderWindow.SetWindowInfo(str(int(self.winId())))
            self.__connected = 1

    def paintEvent(self, ev):
        if self.isVisible():
            self.polish()
        if self.__connected:
            if not self.Render():
                self._RenderWindow.Render()

    def sizePolicy(self):
        return QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self):
        return self.__hintSize

    def _state(self, ev):
        # convert qt state to tk state
        qtbits = ev.state()
        state = 1 * ((qtbits & 8) != 0) | \
            4 * ((qtbits & 16) != 0) | \
            ALTBIT * ((qtbits & 32) != 0) | \
            256 * ((qtbits & 1) != 0) | \
            512 * ((qtbits & 4) != 0) | \
            1024 * ((qtbits & 2) != 0) | \
            1 * ((qtbits & 256) != 0) | \
            4 * ((qtbits & 512) != 0)

        self.__lastState = state
        return state

    def _keysym(self, ev):
        # convert qt event keycode to tk keysym
        key = ev.key()
        keysym = '??'
        if key >= 65 and key <= 90:  # between A and Z
            keysym = chr(ev.ascii())  # get upper vs. lower case right
        elif key < 256:
            if (ev.state() & 0x4000) != 0:  # key is on keypad
                try:
                    keysym = {'/': "KP_Divide",
                              '*': "KP_Multiply",
                              '-': "KP_Subtract",
                              '+': "KP_Add",
                              ',': "KP_Separator",
                              '.': "KP_Delete",
                              '=': "KP_Equal",
                              '0': "KP_Insert",
                              '1': "KP_End",
                              '2': "KP_Down",
                              '3': "KP_Next",
                              '4': "KP_Left",
                              '5': "KP_Begin",
                              '6': "KP_Right",
                              '7': "KP_Home",
                              '8': "KP_Up",
                              '9': "KP_Prior"}[chr(key)]
                except:
                    pass
            else:
                keysym = self.KeySymFromLatin1[key]
        else:
            try:
                keysym = self.KeySymFromKey[key]
                if (ev.state() & 0x4000) != 0:  # key is on keypad
                    keysym = "KP_" + keysym
            except KeyError:
                pass

        return keysym

    def keyPressEvent(self, ev):
        ev.accept()
        e = Event()
        e.type = '2'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = self._state(ev)
        e.num = 0
        e.keysym = self._keysym(ev)
        e.char = str(ev.text())
        self.HandleEvent(e)

    def keyReleaseEvent(self, ev):
        ev.accept()
        e = Event()
        e.type = '3'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = self._state(ev)
        e.num = 0
        e.keysym = self._keysym(ev)
        # qt doesn't report the character on KeyRelease, so
        #  we must generate it from the key code
        key = ev.key()
        if key >= 65 and key <= 90 and (e.state & 3) == 0:
            e.char = chr(key + 32)
        elif key < 256:
            e.char = chr(key)
        else:
            try:
                e.char = {0x1000: '\033',
                          0x1001: '\t',
                          0x1003: '\b',
                          0x1004: '\n',
                          0x1005: '\n',
                          0x1007: '\177'}[key]
            except KeyError:
                e.char = '\0'

        self.HandleEvent(e)

    def mousePressEvent(self, ev):
        e = Event()
        e.type = '4'
        e.x = self.__lastX = ev.x()
        e.y = self.__lastY = self.height() - ev.y() - 1
        e.state = self._state(ev)
        e.num = (0, 1, 3, 0, 2)[ev.button()]
        self.HandleEvent(e)

    def mouseReleaseEvent(self, ev):
        e = Event()
        e.type = '5'
        e.x = self.__lastX = ev.x()
        e.y = self.__lastY = self.height() - ev.y() - 1
        e.state = self._state(ev)
        e.num = (0, 1, 3, 0, 2)[ev.button()]
        self.HandleEvent(e)

    def mouseDoubleClickEvent(self, ev):
        e = Event()
        e.type = '4'
        e.x = self.__lastX = ev.x()
        e.y = self.__lastY = self.height() - ev.y() - 1
        e.state = self._state(ev) | 8192
        e.num = (0, 1, 3, 0, 2)[ev.button()]
        self.HandleEvent(e)

    def wheelEvent(self, ev):
        ev.ignore()

    def mouseMoveEvent(self, ev):
        e = Event()
        e.type = '6'
        e.x = self.__lastX = ev.x()
        e.y = self.__lastY = self.height() - ev.y() - 1
        e.state = self._state(ev)
        e.num = (0, 1, 3, 0, 2)[ev.button()]
        # QT can screw up enter/leave events, so generate them ourselves
        if (e.x >= 0 and e.x < self.width() and
                e.y >= 0 and e.y < self.height()):
            if not self.__inside:
                self.enterEvent(ev)
        else:
            if not self.__inside:
                self.leaveEvent(ev)
        self.HandleEvent(e)

    def enterEvent(self, ev):
        if self.__inside:
            return
        self.__inside = 1

        # change focus?
        # if not self.hasFocus():
        #    self.__oldFocus = self.focusWidget()
        #    self.setFocus()

        e = Event()
        e.type = '7'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = self.__lastState
        e.num = 0
        self.HandleEvent(e)

    def leaveEvent(self, ev):
        if not self.__inside:
            return
        self.__inside = 0

        e = Event()
        e.type = '8'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = self.__lastState
        e.num = 0
        self.HandleEvent(e)

        # change focus?
        # if (e.state & 0x700) == 0 and self.__oldFocus: # no keys held down
        #    self.__oldFocus.setFocus()
        #    self.__oldFocus = None

    def focusInEvent(self, ev):
        e = Event()
        e.type = '9'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = 0
        e.num = 0
        self.HandleEvent(e)

    def focusOutEvent(self, ev):
        e = Event()
        e.type = '10'
        e.x = self.__lastX
        e.y = self.__lastY
        e.state = 0
        e.num = 0
        self.HandleEvent(e)

    def resizeEvent(self, ev):
        e = Event()
        e.type = '22'
        size = ev.size()
        # if widget isn't visible, we need to manually set RenderWindow
        if self.__connected == 1 and not self.isVisible():
            self._RenderWindow.SetSize(size.width(), size.height())
        e.width = size.width()
        e.height = size.height()
        e.x = self.x()
        e.y = self.y()
        e.num = 0
        e.state = self.__lastState
        self.HandleEvent(e)

    def closeEvent(self, ev):
        ev.accept()

    def timerEvent(self, ev):
        id = ev.timerId()
        try:
            func, oneshot = qtPaneFrame._ScheduleIdDict[id]
        except KeyError:
            return
        if oneshot:
            self.killTimer(id)
            del qtPaneFrame._ScheduleIdDict[id]
        func()

    #--------------------------------------
    def SetTitle(self, title):
        self.setCaption(QString(title))

    def GetTitle(self):
        return str(self.caption())

    #--------------------------------------
    def ScheduleOnce(self, millisecs, func):
        id = self.startTimer(millisecs)
        qtPaneFrame._ScheduleIdDict[id] = (func, 1)
        return id

    def ScheduleEvery(self, millisecs, func):
        id = self.startTimer(millisecs)
        qtPaneFrame._ScheduleIdDict[id] = (func, 0)
        return id

    def UnSchedule(self, id):
        try:
            del qtPaneFrame._ScheduleIdDict[id]
            self.killTimer(id)
        except KeyError:
            pass

    #--------------------------------------
    def Start(self):
        try:
            qApp.setMainWidget(self)
            qApp.exec_loop()
        except:
            return

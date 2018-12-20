from __future__ import division
from future import standard_library
standard_library.install_aliases()
from past.utils import old_div
import tkinter


class SplashScreen(tkinter.Toplevel):

    def __init__(self, master, imagefile):
        tkinter.Toplevel.__init__(
            self, master, relief=tkinter.RAISED, borderwidth=5)
        self.main = master
        if self.main.master is not None:
            self.main.master.withdraw()
        self.imagefile = imagefile
        self.main.withdraw()
        self.overrideredirect(1)
        self.CreateWidgets()
        self.after_idle(self.CenterOnScreen)
        self.update()

    def CenterOnScreen(self):
        self.update_idletasks()
        xmax = self.winfo_screenwidth()
        ymax = self.winfo_screenheight()
        x0 = old_div((xmax - self.winfo_reqwidth()), 2)
        y0 = old_div((ymax - self.winfo_reqheight()), 2)
        self.geometry("+%d+%d" % (x0, y0))

    def CreateWidgets(self):
        imgfile = self.imagefile
        self.splashimage = tkinter.PhotoImage(file=imgfile)
        self.Tkinter.Canvas = tkinter.Canvas(
            self, height=self.splashimage.height(), width=self.splashimage.width())
        self.Tkinter.Canvas.create_image(
            0, 0, anchor=tkinter.NW, image=self.splashimage)
        self.Tkinter.Canvas.grid(row=0, column=0)
        self.status = tkinter.StringVar(self)
        self.status.set('Loading Program...')
        tkinter.Label(self, textvariable=self.status).grid(
            row=1, column=0, sticky=tkinter.W)

    def SetMessage(self, message):
        self.status.set(message)
        self.Tkinter.Canvas.update()

    def Destroy(self):
        self.main.update()
        self.main.deiconify()
        self.withdraw()

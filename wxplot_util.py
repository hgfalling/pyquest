import wx
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class PlotPanel(wx.Panel):
    """
    The PlotPanel has a Figure and a Canvas. 
    """
    def __init__(self,parent,obj_id):
        # initialize Panel
        wx.Panel.__init__(self,parent,obj_id)

        # initialize matplotlib stuff
        self.figure = Figure(None,None,tight_layout=True)
        self.canvas = FigureCanvasWxAgg(self,wx.ID_ANY,self.figure)
        rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.canvas,1,wx.EXPAND)
        self.SetSizer(self.sizer)

    def draw(self): 
        pass # abstract, to be overridden by child classes

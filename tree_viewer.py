import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure

import cPickle
import sys
_version = 1.00

from plot_utils import *

class TVApp(wx.App):
    def __init__(self, datadict):
        self.datadict = datadict
        wx.App.__init__(self,False)        

    def OnInit(self):
        self.frame = TVFrame(None,wx.ID_ANY,self.datadict)
        return True
    
class TVFrame(wx.Frame):
    def __init__(self,parent,obj_id,datadict):
        wx.Frame.__init__(self,parent,obj_id,size=(800,800),pos=(0,0))
        self.SetTitle("Tree Viewer {}".format(_version))
        
        self.main_panel = TVMainPanel(self,wx.ID_ANY,datadict)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.main_panel,1,wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.Layout()
        self.Show(1)
        
class TVMainPanel(wx.Panel):
    def __init__(self,parent,obj_id,datadict):
        wx.Panel.__init__(self,parent,obj_id)

        self.tree_panel = TVTreePanel(self,wx.ID_ANY,datadict["tree"],
                                      datadict["tree_desc"])
        self.data_panel = TVDataPanel(self,wx.ID_ANY,datadict)
        self.embed_panel = TVEmbedSuperPanel(self,wx.ID_ANY,datadict)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tree_panel,2,wx.EXPAND|wx.BOTTOM,5)
        self.sizer.Add(self.data_panel,1,wx.EXPAND|wx.ALL, border=5)
        self.sizer.Add(self.embed_panel,3,wx.EXPAND|wx.TOP, border=5)
        self.SetSizer(self.sizer)

    def update(self,tree_node):
        self.data_panel.update(tree_node)
        self.embed_panel.update(tree_node=tree_node)
        
class TVDataPanel(wx.Panel):
    def __init__(self,parent,obj_id,datadict):
        wx.Panel.__init__(self,parent,obj_id)
        self.tree_node = 0
        self.tree = datadict["tree"]
        self.data_descs = datadict["data_descs"]
        self.data_txt = wx.TextCtrl(self,wx.ID_ANY,
                                 style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.update(self.tree_node)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.data_txt,1,wx.EXPAND|wx.LEFT|wx.RIGHT,border=10)
        self.SetSizer(self.sizer)
        self.Layout()
        
    def update(self,tree_node):
        self.tree_node = tree_node
        self.folder_label = u'\n'.join([self.data_descs[x] for x in 
                                        self.tree[tree_node].elements])
        self.data_txt.SetValue(self.folder_label)
        self.data_txt.Refresh()
        self.Refresh()
        
class PlotPanel(wx.Panel):
    """
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actual resizing of the figure is triggered by an Idle event.
    """
    def __init__(self,parent,obj_id):
        # initialize Panel
        wx.Panel.__init__(self,parent,obj_id)

        # initialize matplotlib stuff
        self.figure = Figure(None,None)
        self.canvas = FigureCanvasWxAgg(self,wx.ID_ANY,self.figure)
        rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )
        
        self.Bind(wx.EVT_SIZE, self._on_size)
        
    def _on_size( self, event ):
        self._set_size()
    
    def _set_size( self ):
        pixels = tuple( self.GetClientSize() )
        self.SetSize( pixels )
        self.canvas.SetSize( pixels )
        self.figure.set_size_inches( float( pixels[0] )/self.figure.get_dpi(),
                                     float( pixels[1] )/self.figure.get_dpi() )

    def draw(self): 
        pass # abstract, to be overridden by child classes

class TVTreePanel(PlotPanel):
    def __init__(self,parent,obj_id,tree,tree_title):
        PlotPanel.__init__(self,parent,obj_id)
        self.parent = parent
        self.tree = tree
        self.tree_node = 0
        self.title = tree_title
        self.marker = []
        self.ax = self.figure.add_subplot(111)
        self.draw_tree()
        
        self.click_id = self.canvas.mpl_connect("button_release_event",
                                                 self.on_click)
        self.key_id = self.canvas.mpl_connect("key_release_event", self.on_key)

    def draw_tree(self):
        self.node_locs = plot_tree(self.tree,ax=self.ax,useplt=False,
                                   nodelocs=True)
        self.draw_marker()
        self.draw()

    def draw(self):
        self.canvas.draw()
    
    def set_marker(self,tree_node):
        self.tree_node = tree_node
        self.draw_marker()
    
    def draw_marker(self):
        if self.marker:
            self.ax.lines.remove(self.marker[0])
        x1,y1 = self.node_locs[self.tree_node,:]
        self.marker = self.ax.plot(x1,y1,'s',markersize=6,
                                   markerfacecolor='None',
                                   markeredgecolor='k',markeredgewidth=2)
        self.canvas.draw()
    
    def on_key(self,evt):
        if evt.key == "w":
            node = self.tree[self.tree_node]
            if node.parent is not None:
                self.set_marker(node.parent.idx)
                self.parent.update(self.tree_node)
        if evt.key == "s":
            node = self.tree[self.tree_node]
            if node.children != []:
                self.set_marker(node.children[0].idx)
                self.parent.update(self.tree_node)
        if evt.key == "d":
            node = self.tree[self.tree_node]
            node_order = [x.idx for x in self.tree.dfs_level(node.level)]
            idx = node_order.index(node.idx)
            if idx != len(node_order)-1:
                self.set_marker(node_order[idx+1])
                self.parent.update(self.tree_node)
        if evt.key == "a":
            node = self.tree[self.tree_node]
            node_order = [x.idx for x in self.tree.dfs_level(node.level)]
            idx = node_order.index(node.idx)
            if idx != 0:
                self.set_marker(node_order[idx-1])
                self.parent.update(self.tree_node)
        
    def on_click(self,evt):
        if evt.xdata is None or evt.ydata is None:
            pass
        else:
            click_loc = np.array([evt.xdata,evt.ydata])
            distances = np.sum((self.node_locs - click_loc)**2,axis=1)
            self.set_marker(np.argmin(distances))
            self.parent.update(self.tree_node)

class TVEmbedSuperPanel(wx.Panel):
    def __init__(self,parent,obj_id,datadict):
        wx.Panel.__init__(self,parent,obj_id)
        self.parent = parent
        
        n_vecs = np.shape(datadict["vecs"])[1]
        
        self.n_vec = {}
        self.n_vec[0] = wx.SpinCtrl(self,value="2",min=2,max=n_vecs)
        self.n_vec[1] = wx.SpinCtrl(self,value="3",min=2,max=n_vecs)
        self.n_vec[2] = wx.SpinCtrl(self,value="4",min=2,max=n_vecs)

        self.leftpanel = TVEmbeddingPanel(self,wx.ID_ANY,datadict)
        
        self.rightpanel = wx.BoxSizer(wx.VERTICAL)
        self.rightpanel.AddSpacer((15,15)) 

        for (idx,text) in enumerate("xyz"):
            tempsizer = wx.BoxSizer(wx.HORIZONTAL)
            templabel = wx.StaticText(self,wx.ID_ANY,label=text+":")
            tempsizer.Add(templabel)
            tempsizer.Add(self.n_vec[idx])
            self.rightpanel.Add(tempsizer)
           
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.leftpanel,1,wx.EXPAND)
        self.sizer.Add(self.rightpanel,0)
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_SPINCTRL,self.on_vec_chg,self.n_vec[0])
        self.Bind(wx.EVT_SPINCTRL,self.on_vec_chg,self.n_vec[1])
        self.Bind(wx.EVT_SPINCTRL,self.on_vec_chg,self.n_vec[2])
    
    def update(self,tree_node=None,level=None):
        kwargs = {}
        if tree_node is not None:
            kwargs["tree_node"] = tree_node
        if level is not None:
            kwargs["level"] = level
            
        self.leftpanel.update(**kwargs)

    def on_vec_chg(self,evt):
        self.leftpanel.x_vec = self.n_vec[0].GetValue()
        self.leftpanel.y_vec = self.n_vec[1].GetValue()
        self.leftpanel.z_vec = self.n_vec[2].GetValue()
        self.leftpanel.draw()
            
class TVEmbeddingPanel(PlotPanel):
    def __init__(self,parent,obj_id,datadict):
        PlotPanel.__init__(self,parent,obj_id)
        self.vecs = datadict['vecs']
        self.vals = datadict['vals']
        self.tree = datadict['tree']
        self.title = datadict['tree_desc']
        
        self.x_vec = 2
        self.y_vec = 3
        self.z_vec = 4
        
        self.level = 1 
        self.tree_node = 0
        self.parent = parent
        self.tree_node = 0
        self.draw()

    def draw(self,diff_time=None,nodecolors=None):
        node = self.tree[self.tree_node]
        points = self.tree.size

        vec_indices = [0,self.x_vec-1,self.y_vec-1,self.z_vec-1]
        vecs = self.vecs[:,vec_indices]
        vals = self.vals[vec_indices]

        if hasattr(self,"ax"):
            elev,azim = self.ax.elev,self.ax.azim
        else:
            elev,azim = None,None

        c = []
        for i in xrange(points):
            if i in node.elements:
                c.append("r")
            else:
                c.append('w')

        self.figure.clear()
        self.ax = self.figure.add_subplot(111,projection="3d")
        plot_embedding(vecs, vals, title="Embedding", 
                       ax=self.ax, elev=elev, azim=azim, nodecolors=c)
        
        self.canvas.draw()        
    def update(self,tree_node=None):
        if tree_node is not None:  
            self.tree_node = tree_node
        self.draw()        

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        print "specify a file name..."
        exit()
    fin = open(filename,'rb')
    datadict = cPickle.load(fin)
    fin.close()
    
    app = TVApp(datadict)
    app.MainLoop()        
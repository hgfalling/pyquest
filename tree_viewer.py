"""
datadict should contain the following keys:
'tree' : a ClusterTreeNode object containing the tree of the data.
'data_descs': a description of each element in the data.
'tree_desc': a description of the tree
'vecs': the eigenvectors of the embedding.
'vals': the corresponding eigenvalues.
"""


#display/plotting things
import wx
from wx.lib.buttons import GenButton
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import numpy as np
import barcode
import tree_util

import sys
_version = 0.01

cmap = plt.get_cmap("RdBu_r")
cnorm = matplotlib.colors.Normalize(vmin=-1,vmax=1,clip=False)
cmap.set_under('blue')
cmap.set_over('red') 

class TVApp(wx.App):
    def __init__(self, datadict):
        self.datadict = datadict
        wx.App.__init__(self,False)        

    def OnInit(self):
        self.frame = TVFrame(None,wx.ID_ANY,self.datadict)
        return True

class TVFrame(wx.Frame):
    def __init__(self,parent,obj_id,datadict):
        wx.Frame.__init__(self,parent,obj_id,size=(600,500),pos=(0,100))
        self.SetTitle("Tree Viewer {}".format(_version))
        
        self.tree_panel = TVTreePanel(self,wx.ID_ANY,datadict["tree"],datadict["tree_desc"])
        self.data_panel = TVDataPanel(self,wx.ID_ANY,datadict)
        self.embed_panel = TVEmbedSuperPanel(self,wx.ID_ANY,datadict)
        
        self.leftsizer = wx.BoxSizer(wx.VERTICAL)
        self.leftsizer.Add(self.tree_panel,2,wx.EXPAND)
        self.leftsizer.Add(self.data_panel,1,wx.EXPAND)
        self.leftsizer.Add(self.embed_panel,3,wx.EXPAND)

        self.SetSizer(self.leftsizer)
        
        self.Layout()
        self.Show(1)
        
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
                                 style=wx.TE_MULTILINE|wx.TE_READONLY,size=(1000,115))
        self.update(self.tree_node)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddSpacer((25,25))
        self.sizer.Add(self.data_txt)
        self.SetSizer(self.sizer)
        
    def update(self,tree_node):
        self.tree_node = tree_node
        self.folder_label = u''
        for node in self.tree.traverse():
            if node.idx == tree_node:
                for i in node.elements:
                    self.folder_label += self.data_descs[i] + u'\n'
                break
        self.data_txt.SetValue(self.folder_label)
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
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.canvas,1,wx.EXPAND)
        self.SetSizer(self.sizer)

    def draw(self): 
        pass # abstract, to be overridden by child classes

class TVTreePanel(PlotPanel):
    def __init__(self,parent,obj_id,tree,tree_title):
        PlotPanel.__init__(self,parent,obj_id)
        self.parent = parent
        self.tree_node = 0
        self.calculate(tree)
        self.title = tree_title
        self.init_draw()
        
        self.click_id = self.canvas.mpl_connect("button_release_event", self.OnClick)
        self.key_id = self.canvas.mpl_connect("key_release_event", self.OnKey)

    def calculate(self,tree):
        self.tree = tree
        #calculate the node locations
        self.node_locs = np.zeros([tree.tree_size,2])

        for level in xrange(1,tree.tree_depth+1):
            nodes = tree.dfs_level(level)
            node_idxs = np.array([node.idx for node in nodes])
            x_intervals = np.cumsum(np.array([0]+[node.size for node in nodes])*1.0/tree.size)
            node_xs = x_intervals[:-1] + np.diff(x_intervals)/2.0
            node_ys = (tree.tree_depth - level)*np.ones(np.shape(node_xs))
            self.node_locs[node_idxs,:] = np.hstack([node_xs[:,np.newaxis],node_ys[:,np.newaxis]])

    def init_draw(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(self.title)
        self.ax.scatter(self.node_locs[:,0],self.node_locs[:,1],marker='.',color='b',s=40)
        for node in self.tree.traverse():
            if node.parent is not None:
                x1,y1 = self.node_locs[node.idx,:]
                x2,y2 = self.node_locs[node.parent.idx,:]
                self.ax.plot((x1,x2),(y1,y2),'r')
        self.ax.set_xlim([0.0,1.0])
        self.ax.set_ylim([-0.2,self.tree.tree_depth + 0.2])
        x1,y1 = self.node_locs[self.tree_node,:]
        self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)
        self.figure.tight_layout()
        self.canvas.draw()
                                    
    def draw(self):
        self.ax.lines.remove(self.marker[0])
        x1,y1 = self.node_locs[self.tree_node,:]
        self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)

        self.figure.tight_layout()
        self.canvas.draw()
    
    def OnKey(self,evt):
        if evt.key == "up":
            node = [x for x in self.tree.traverse() if x.idx == self.tree_node]
            if node[0].parent is not None:
                self.tree_node = node[0].parent.idx
                self.draw()
                self.parent.update(self.tree_node)
        if evt.key == "down":
            node = [x for x in self.tree.traverse() if x.idx == self.tree_node]
            if node[0].children != []:
                self.tree_node = node[0].children[0].idx
                self.draw()
                self.parent.update(self.tree_node)
        if evt.key == "right":
            node = [x for x in self.tree.traverse() if x.idx == self.tree_node]
            if node[0].parent is not None:
                self.tree_node = node[0].parent.children[1].idx
                self.draw()
                self.parent.update(self.tree_node)
        if evt.key == "left":
            node = [x for x in self.tree.traverse() if x.idx == self.tree_node]
            if node[0].parent is not None:
                self.tree_node = node[0].parent.children[0].idx
                self.draw()
                self.parent.update(self.tree_node)
        
    def OnClick(self,evt):
        if evt.xdata is None or evt.ydata is None:
            pass
        else:
            click_loc = np.array([evt.xdata,evt.ydata])
            distances = np.sum((self.node_locs - click_loc)**2,axis=1)
            self.tree_node = np.argmin(distances)
            self.draw()
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
           
#        self.rightpanel.Add(self.x_vec)
#        self.rightpanel.Add(self.y_vec)
#        self.rightpanel.Add(self.z_vec)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.leftpanel,1,wx.EXPAND)
        self.sizer.Add(self.rightpanel)
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[0])
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[1])
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[2])
    
    def update(self,tree_node=None,level=None):
        kwargs = {}
        if tree_node is not None:
            kwargs["tree_node"] = tree_node
        if level is not None:
            kwargs["level"] = level
            
        self.leftpanel.update(**kwargs)

    def OnColorChange(self,evt):
        self.leftpanel.draw()
        
    def OnVecChange(self,evt):
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

    def draw(self,diff_time=None):

        self.figure.clear()
        
        COLORS = "bgrcmykv"
        
        if diff_time is None:
            diff_time = 1.0/(1-self.vals[1])
        
        node = [x for x in self.tree.traverse() if x.idx == self.tree_node][0]
        
        x=self.vecs[:,self.x_vec-1] * (self.vals[self.x_vec-1] ** diff_time)
        y=self.vecs[:,self.y_vec-1] * (self.vals[self.y_vec-1] ** diff_time)
        z=self.vecs[:,self.z_vec-1] * (self.vals[self.z_vec-1] ** diff_time)

        points = np.shape(self.vecs)[0]
        c = []
        for i in xrange(points):
            if i in node.elements:
                c.append("r")
            else:
                c.append('w')

        if hasattr(self,"ax"):
            old_elev,old_azim = self.ax.elev,self.ax.azim
        else:
            old_elev,old_azim = None,None
        self.ax = self.figure.add_subplot(111,projection="3d")
        self.ax.set_title(self.title + " (Embedding)")
        self.ax.scatter3D(x,y,z,c=c,cmap=cmap,norm=cnorm)
        self.ax.view_init(old_elev,old_azim)
        
        self.figure.subplots_adjust(left=0.0,right=1.0,top=1.0,bottom=0.0)
        self.figure.tight_layout()
        self.canvas.draw()
        
    def update(self,tree_node=None,level=None):
        if tree_node is not None:  
            self.tree_node = tree_node
        if level is not None:
            self.level = level
        self.draw()
        
        
if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "aq_tree.pickle"
    import cPickle
    fin = open(filename,'rb')
    datadict = cPickle.load(fin)
    fin.close()
    
    app = TVApp(datadict)
    app.MainLoop()
    
    
    
    
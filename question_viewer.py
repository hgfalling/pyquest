#display/plotting things
import wx
from wx.lib.buttons import GenButton
import matplotlib
#matplotlib.interactive(True)
#matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import numpy as np
import barcode
import tree_util

import sys
_version = 0.10

cmap = plt.get_cmap("RdBu_r")
cnorm = matplotlib.colors.Normalize(vmin=-1,vmax=1,clip=False)
cmap.set_under('blue')
cmap.set_over('red') 

class QVApp(wx.App):
    def __init__(self, datadict):
        self.datadict = datadict
        wx.App.__init__(self,False)        

    def OnInit(self):
        self.frame = QVFrame(None,wx.ID_ANY,self.datadict)
        return True

class QVFrame(wx.Frame):
    def __init__(self,parent,obj_id,datadict):
        wx.Frame.__init__(self,parent,obj_id,size=(600,500),pos=(0,100))
        self.SetTitle("Question Viewer {}".format(_version))
        
        self.tree_panel = QVTreePanel(self,wx.ID_ANY,datadict["row_tree"],"Questions Tree")
        self.heatmap_panel = QVTreeHeatMapPanel(self,wx.ID_ANY,datadict)
        self.data_panel = QVDataPanel(self,wx.ID_ANY,datadict)
        self.embed_panel = QVEmbedSuperPanel(self,wx.ID_ANY,datadict)
        #self.embed_panel = QVEmbeddingPanel(self,wx.ID_ANY,datadict,"cols")
        
        self.leftsizer = wx.BoxSizer(wx.VERTICAL)
        self.leftsizer.Add(self.tree_panel,2,wx.EXPAND)
        self.leftsizer.Add(self.data_panel,1,wx.EXPAND)
        self.leftsizer.Add(self.embed_panel,3,wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.leftsizer,5,wx.EXPAND)
        self.sizer.Add(self.heatmap_panel,3,wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.Layout()
        self.Show(1)
        
    def update(self,q_node):
        self.heatmap_panel.update(q_node)
        self.data_panel.update(q_node)
        self.embed_panel.update(q_node=q_node)

class QVDataPanel(wx.Panel):
    def __init__(self,parent,obj_id,datadict):
        wx.Panel.__init__(self,parent,obj_id)
        
        self.q_node = 0
        self.row_tree = datadict["row_tree"]
        self.q_descs = datadict["q_descs"]
        self.q_txt = wx.TextCtrl(self,wx.ID_ANY,
                                 style=wx.TE_MULTILINE|wx.TE_READONLY,size=(800,115))
        self.update(self.q_node)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.AddSpacer((25,25))
        self.sizer.Add(self.q_txt)
        self.SetSizer(self.sizer)
        
    def update(self,q_node):
        self.q_node = q_node
        self.folder_label = u''
        for node in self.row_tree.traverse():
            if node.idx == q_node:
                for i in node.elements:
                    self.folder_label += self.q_descs[i] + u'\n'
                break
        self.q_txt.SetValue(self.folder_label)
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

class QVTreeHeatMapPanel(PlotPanel):
    def __init__(self,parent,obj_id,datadict):
        PlotPanel.__init__(self,parent,obj_id)
        self.parent = parent
        self.q_node = 0
        self.calculate(datadict)
        self.draw()
    
    def update(self,q_node):
        self.q_node = q_node
        self.draw()
    
    def calculate(self,datadict):
        self.data = datadict["data"]
        self.q_descs = datadict["q_descs"]
        self.p_score_descs = datadict["p_score_descs"]
        self.p_scores = datadict["p_scores"]
        self.col_tree = datadict["col_tree"]
        self.row_tree = datadict["row_tree"] 

        avgs = barcode.level_avgs(self.data,self.col_tree)
        node_avgs = tree_util.tree_averages(avgs,self.row_tree)
        orig_shape = np.shape(node_avgs)
        r_avgs = np.reshape(node_avgs,(-1,orig_shape[-1]))
        #br_avgs = barcode.organize_cols(self.col_tree,r_avgs)
        #self.q_image = np.reshape(br_avgs,orig_shape)
        self.q_image = np.reshape(r_avgs,orig_shape)
        self.q_image_mg = np.zeros(np.shape(self.q_image))
        self.q_image_mg[:,1:,:] = np.diff(self.q_image,axis=1)
        self.q_image_top = np.zeros(np.shape(self.q_image))
        self.q_image_top = self.q_image - self.q_image[:,0,:][:,np.newaxis,:] 

    def draw(self):
        self.figure.clear()

        self.ax1 = self.figure.add_subplot(3,1,1)
        self.ax2 = self.figure.add_subplot(3,1,2)
        self.ax3 = self.figure.add_subplot(3,1,3)
        self.ax1.set_title('Mean Response')
        self.ax2.set_title('Difference from Parent')
        self.ax3.set_title('Difference from Top')

        #title = u'Question {}'.format(self.q_descs[self.q_node])

        #self.figure.suptitle(title,fontsize=14)
#        self.ax1.imshow(self.q_image[self.q_node],aspect='auto',
#                        interpolation="nearest",cmap=cmap,norm=cnorm)
#        self.ax2.imshow(self.q_image_mg[self.q_node],aspect='auto',
#                        interpolation="nearest",cmap=cmap,norm=cnorm)
#        self.ax3.imshow(self.q_image_top[self.q_node],aspect='auto',
#                        interpolation="nearest",cmap=cmap,norm=cnorm)
        self.ax1.imshow(barcode.organize_cols(self.col_tree, 
                        self.q_image[self.q_node]),aspect='auto',
                        extent = (0.5,self.col_tree.size,self.col_tree.tree_depth+0.5,1.),
                        interpolation="nearest",cmap=cmap,norm=cnorm)
        self.ax2.imshow(barcode.organize_cols(self.col_tree, 
                        self.q_image_mg[self.q_node]),aspect='auto',
                        extent = (0.5,self.col_tree.size,self.col_tree.tree_depth+0.5,1.),
                        interpolation="nearest",cmap=cmap,norm=cnorm)
        self.ax3.imshow(barcode.organize_cols(self.col_tree, 
                        self.q_image_top[self.q_node]),aspect='auto',
                        extent = (0.5,self.col_tree.size,self.col_tree.tree_depth+0.5,1.),
                        interpolation="nearest",cmap=cmap,norm=cnorm)
        y_ticks = np.arange(self.col_tree.tree_depth,0,-2)
        self.ax1.set_yticks(y_ticks)
        self.ax2.set_yticks(y_ticks)
        self.ax3.set_yticks(y_ticks)
        self.figure.subplots_adjust(right=0.8)
        cbar_ax = self.figure.add_axes([0.85, 0.15, 0.05, 0.7])
        matplotlib.colorbar.ColorbarBase(cbar_ax,cmap,cnorm)
        
        self.canvas.draw()

class QVTreePanel(PlotPanel):
    def __init__(self,parent,obj_id,tree,tree_title):
        PlotPanel.__init__(self,parent,obj_id)
        self.parent = parent
        self.q_node = 0
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
        x1,y1 = self.node_locs[self.q_node,:]
        self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)
        self.figure.tight_layout()
        self.canvas.draw()
                                    
    def draw(self):
        self.ax.lines.remove(self.marker[0])
        x1,y1 = self.node_locs[self.q_node,:]
        self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)

        self.figure.tight_layout()
        self.canvas.draw()
    
    def OnKey(self,evt):
        if evt.key == "up":
            node = [x for x in self.tree.traverse() if x.idx == self.q_node]
            if node[0].parent is not None:
                self.q_node = node[0].parent.idx
                self.draw()
                self.parent.update(self.q_node)
        if evt.key == "down":
            node = [x for x in self.tree.traverse() if x.idx == self.q_node]
            if node[0].children != []:
                self.q_node = node[0].children[0].idx
                self.draw()
                self.parent.update(self.q_node)
        if evt.key == "right":
            node = [x for x in self.tree.traverse() if x.idx == self.q_node]
            if node[0].parent is not None:
                self.q_node = node[0].parent.children[1].idx
                self.draw()
                self.parent.update(self.q_node)
        if evt.key == "left":
            node = [x for x in self.tree.traverse() if x.idx == self.q_node]
            if node[0].parent is not None:
                self.q_node = node[0].parent.children[0].idx
                self.draw()
                self.parent.update(self.q_node)

        
    def OnClick(self,evt):
        if evt.xdata is None or evt.ydata is None:
            pass
        else:
            click_loc = np.array([evt.xdata,evt.ydata])
            distances = np.sum((self.node_locs - click_loc)**2,axis=1)
            self.q_node = np.argmin(distances)
            self.draw()
            self.parent.update(self.q_node)

class QVEmbedSuperPanel(wx.Panel):
    def __init__(self,parent,obj_id,datadict):
        wx.Panel.__init__(self,parent,obj_id)
        self.parent = parent
        levels = datadict["col_tree"].tree_depth
        self.level = wx.SpinCtrl(self,value="1",min=1,max=levels)
        
        options_list = ["Mean Response","Difference from Parent","Difference from Top"]
        self.color_type = wx.RadioBox(self,wx.ID_ANY,choices=options_list,label="Color options",
                                      style=wx.RA_VERTICAL)
        
        n_vecs = np.shape(datadict["col_vecs"])[1]
        
        self.n_vec = {}
        self.n_vec[0] = wx.SpinCtrl(self,value="2",min=2,max=n_vecs)
        self.n_vec[1] = wx.SpinCtrl(self,value="3",min=2,max=n_vecs)
        self.n_vec[2] = wx.SpinCtrl(self,value="4",min=2,max=n_vecs)

        self.leftpanel = QVEmbeddingPanel(self,wx.ID_ANY,datadict,"cols")
        
        self.rightpanel = wx.BoxSizer(wx.VERTICAL)
        self.rightpanel.AddSpacer((15,15)) 
        self.rightpanel.Add(self.level)
        self.rightpanel.Add(self.color_type)

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
        
        self.Bind(wx.EVT_SPINCTRL,self.OnLevelChange,self.level)
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[0])
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[1])
        self.Bind(wx.EVT_SPINCTRL,self.OnVecChange,self.n_vec[2])
        self.Bind(wx.EVT_RADIOBOX,self.OnColorChange,self.color_type)
    
    def update(self,q_node=None,level=None):
        kwargs = {}
        if q_node is not None:
            kwargs["q_node"] = q_node
        if level is not None:
            kwargs["level"] = level
            
        self.leftpanel.update(**kwargs)

    def OnLevelChange(self,evt):
        self.leftpanel.level = self.level.GetValue()
        self.leftpanel.draw()

    def OnColorChange(self,evt):
        self.leftpanel.draw()
        
    def OnVecChange(self,evt):
        self.leftpanel.x_vec = self.n_vec[0].GetValue()
        self.leftpanel.y_vec = self.n_vec[1].GetValue()
        self.leftpanel.z_vec = self.n_vec[2].GetValue()
        self.leftpanel.draw()
            
class QVEmbeddingPanel(PlotPanel):
    def __init__(self,parent,obj_id,datadict,tree_type):
        PlotPanel.__init__(self,parent,obj_id)
        self.col_vecs = datadict["col_vecs"]
        self.col_vals = datadict["col_vals"]
        self.row_vecs = datadict["row_vecs"]
        self.row_vals = datadict["row_vals"]
        self.col_tree = datadict["col_tree"]
        self.row_tree = datadict["row_tree"]
        
        self.x_vec = 2
        self.y_vec = 3
        self.z_vec = 4
        
        self.level = 1 
        self.tree_type = tree_type
        self.q_node = 0
        self.parent = parent
        self.q_node = 0
        self.draw()

    def draw(self,diff_time=None):
        self.figure.clear()
        
        COLORS = "bgrcmykv"
        
        if self.tree_type == "cols":
            vecs = self.col_vecs
            vals = self.col_vals
            tree = self.col_tree
        else:
            vecs = self.row_vecs
            vals = self.row_vals
            tree = self.row_tree
            
        if diff_time is None:
            diff_time = 1.0/(1-vals[1])
        
        x=vecs[:,self.x_vec-1] * (vals[self.x_vec-1] ** diff_time)
        y=vecs[:,self.y_vec-1] * (vals[self.y_vec-1] ** diff_time)
        z=vecs[:,self.z_vec-1] * (vals[self.z_vec-1] ** diff_time)

        color_type = self.parent.color_type.GetSelection() 
        
        if color_type == 0:
            c = self.parent.parent.heatmap_panel.q_image[self.q_node,self.level-1,:]
        elif color_type == 1:
            c = self.parent.parent.heatmap_panel.q_image_mg[self.q_node,self.level-1,:]
        if color_type == 2:
            c = self.parent.parent.heatmap_panel.q_image_top[self.q_node,self.level-1,:]

        if hasattr(self,"ax"):
            old_elev,old_azim = self.ax.elev,self.ax.azim
        else:
            old_elev,old_azim = None,None
        self.ax = self.figure.add_subplot(111,projection="3d")
        if self.tree_type == "cols":
            self.ax.set_title('People Embedding')
        else:
            self.ax.set_title('Questions Embedding')

        self.ax.scatter3D(x,y,z,c=c,cmap=cmap,norm=cnorm,edgecolors='none')
        self.ax.view_init(old_elev,old_azim)
        
        self.figure.subplots_adjust(left=0.0,right=1.0,top=1.0,bottom=0.0)
        self.figure.tight_layout()
        self.canvas.draw()
        
    def update(self,q_node=None,level=None):
        if q_node is not None:  
            self.q_node = q_node
        if level is not None:
            self.level = level
        self.draw()
        
        
if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "datadict.pickle"
    import cPickle
    fin = open(filename,'rb')
    datadict = cPickle.load(fin)
    fin.close()
    
    app = QVApp(datadict)
    app.MainLoop()
    
    
    
    
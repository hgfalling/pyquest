"""
plot_utils.py: Defines a number of useful plotting functions with respect to 
               binary questionnaire data, especially for interactive sessions.
""" 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.mplot3d import Axes3D

#rbmap is a continuous gradient color map from red (+1) to blue (-1)
#binnorm is the norm on [-1,1]
rbmap = plt.get_cmap("RdBu_r")
rbmap.set_under('blue')
rbmap.set_over('red') 

binnorm = matplotlib.colors.Normalize(vmin=-1,vmax=1,clip=False)

#bwmap is a grayscale norm. bwnorm is the norm on [0,1]
bwmap = plt.get_cmap("binary_r")
bwmap.set_under('black')
bwmap.set_over('white') 
bwnorm = matplotlib.colors.Normalize(vmin=0,vmax=1,clip=False)

#these are useful functions for interactive plotting of images which I do a lot.
def bwplot(data,**kwargs):
    """
    Plot [0,1] data in grayscale.
    """
    _mplot(data,bwmap,bwnorm,**kwargs)

def bwplot2(data, **kwargs):
    """
    Plot [-1,1] data in grayscale.
    """
    _mplot(data,bwmap,binnorm,**kwargs)
    
def cplot(data, **kwargs):
    """
    Plot [-1,1] data in the blue/red gradient.
    """
    _mplot(data,rbmap,binnorm,**kwargs)
        
def _mplot(data,cmap,norm,**kwargs):
    """
    Plot [-1,1] data in the blue/red gradient.
    """
    if "ax" in kwargs:
        plt.sca(kwargs['ax'])
    plt.imshow(data,interpolation='nearest',aspect='auto',cmap=cmap,norm=norm)
    if "colorbar" in kwargs:
        if kwargs["colorbar"]:
            plt.colorbar()
    if "title" in kwargs:
        plt.title(kwargs["title"])

def plot_tree(t,**kwargs):
    """
    Plots a tree (from module tree.py)
    kwargs that do something:
    nodecolors = color the nodes
    leafcolors = color just the leaf nodes
    title = set the title
    ax = plot on the given axis
    useplt = default true, if False, then ax must be specified and will 
             plot directly to ax.
    """
    node_locs = np.zeros([t.tree_size,2])
    node_order = []
    
    for level in xrange(1,t.tree_depth+1):
        nodes = t.dfs_level(level)
        node_order.extend([x.idx for x in nodes])
        node_idxs = np.array([node.idx for node in nodes])
        x_intervals = np.cumsum(np.array([0]+[node.size for node in nodes])*1.0/t.size)
        node_xs = x_intervals[:-1] + np.diff(x_intervals)/2.0
        node_ys = (t.tree_depth - level)*np.ones(np.shape(node_xs))
        node_locs[node_idxs,:] = np.hstack([node_xs[:,np.newaxis],node_ys[:,np.newaxis]])
    
    useplt = True
    if "useplt" in kwargs:
        if not kwargs["useplt"]:
            useplt = False
            ax = kwargs["ax"]
    
    if "ax" in kwargs:
        if useplt:
            plt.sca(kwargs["ax"])
    
    if "nodecolors" in kwargs:
        nc = kwargs["nodecolors"]
        if useplt:
            plt.scatter(node_locs[:,0],node_locs[:,1],marker='.',
                        edgecolors='none',c=nc,norm=binnorm,cmap=rbmap,s=80)
        else:
            ax.scatter(node_locs[:,0],node_locs[:,1],marker='.',
                        edgecolors='none',c=nc,norm=binnorm,cmap=rbmap,s=80)
    elif "leafcolors" in kwargs:
        lc = kwargs["leafcolors"]
        nonleaves = (t.tree_size - t.size)
        nc = ['k']*nonleaves
        if useplt:
            plt.scatter(node_locs[0:nonleaves,0],node_locs[0:nonleaves,1],
                        edgecolors='none',marker='.',c=nc,s=80)
            plt.scatter(node_locs[nonleaves:,0],node_locs[nonleaves:,1],
                        edgecolors='none',marker='.',c=lc,s=80)
        else:
            ax.scatter(node_locs[0:nonleaves,0],node_locs[0:nonleaves,1],
                        edgecolors='none',marker='.',c=nc,s=80)
            ax.scatter(node_locs[nonleaves:,0],node_locs[nonleaves:,1],
                        edgecolors='none',marker='.',c=lc,s=80)
    else:
        nc = 'k'
        if useplt:
            plt.scatter(node_locs[:,0],node_locs[:,1],marker='.',c=nc,s=80)
        else:
            ax.scatter(node_locs[:,0],node_locs[:,1],marker='.',c=nc,s=80)
    for node in t:
        if node.parent is not None:
            x1,y1 = node_locs[node.idx,:]
            x2,y2 = node_locs[node.parent.idx,:]
            if useplt:
                plt.plot((x1,x2),(y1,y2),'r')
            else:
                ax.plot((x1,x2),(y1,y2),'r')
                
    if useplt:
        plt.yticks(np.arange(0,t.tree_depth,1))
        plt.xlim([0.0,1.0])
        plt.ylim([-0.2,(t.tree_depth - 1) + 0.2])
    else:
        ax.set_yticks(np.arange(0,t.tree_depth,1))
        ax.set_xlim([0.0,1.0])
        ax.set_ylim([-0.2,(t.tree_depth - 1) + 0.2])
    if "title" in kwargs:
        if useplt:
            plt.title(kwargs["title"])
        else:
            ax.set_title(kwargs["title"])
    
    if "nodelocs" in kwargs:
        return node_locs
    
def plot_embedding(vecs,vals,**kwargs):
    """
    kwargs that do something:
    diff_time: diffusion time
    nodecolors = color the nodes
    leafcolors = color just the leaf nodes
    title = set the title (will append t=whatever to this)
    partition: define a partition and color it by the std colors
    ax: axis to plot the partition to.
    azim,elev = azimuth angle, elevation angle  (need both)
    """
    if "diff_time" not in kwargs:
        diff_time = 1.0/(1.0 - vals[1])
    else:
        diff_time = kwargs["diff_time"]
    
    x=vecs[:,1] * (vals[1] ** diff_time)
    y=vecs[:,2] * (vals[2] ** diff_time)
    z=vecs[:,3] * (vals[3] ** diff_time)
    
    if "ax" not in kwargs:
        fig = plt.figure()
        ax = fig.add_subplot(111,projection="3d")
    else:
        ax = kwargs["ax"]
    
    if "title" in kwargs:
        title = kwargs["title"]
    else:
        title="Diffusion Embedding: "
    
    if "partition" in kwargs:
        COLORS = "krcmybg"
        c = [COLORS[w % len(COLORS)] for w in kwargs["partition"]]
    elif "nodecolors" in kwargs:
        c = kwargs["nodecolors"]
    else:
        c = 'b'
    
    ax.scatter3D(x,y,z,c=c,norm=binnorm,cmap=rbmap)
    if "nodt" not in kwargs:
        ax.set_title("{0} $t={1:1.3}$".format(title,diff_time))
    else:
        ax.set_title(title)
        
    if "azim" in kwargs:
        ax.view_init(kwargs["elev"],kwargs["azim"])

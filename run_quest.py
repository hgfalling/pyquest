import numpy as np
import scipy.spatial as spsp
import datetime
from wx.lib.pubsub import Publisher
import affinity
import markov
import tree_building
import bintree_construct
import dual_affinity

INIT_AFF_COS_SIM = 0
INIT_AFF_GAUSSIAN = 1
    
DEFAULT_INIT_AFF_THRESHOLD = 0.1
DEFAULT_INIT_AFF_EPSILON = 1.0

TREE_TYPE_BINARY = 0
TREE_TYPE_FLEXIBLE = 1

DEFAULT_TREE_BAL_CONSTANT = 1.0
DEFAULT_TREE_CONSTANT = 0.2

DUAL_EMD = 2
DUAL_GAUSSIAN = 3

DEFAULT_DUAL_EPSILON = 1.0
DEFAULT_DUAL_ALPHA = 0.5
DEFAULT_DUAL_BETA = 1.0

DEFAULT_N_ITERS = 3
DEFAULT_N_TREES = 1

class PyQuestParams(object):
    
    def __init__(self,init_aff_type,tree_type,dual_row_type,dual_col_type,
                 **kwargs):
        
        self.set_init_aff(init_aff_type,**kwargs)
        self.set_tree_type(tree_type,**kwargs)
        self.set_dual_aff(dual_row_type,dual_col_type,**kwargs)
        self.set_iters(**kwargs)
    
    def set_init_aff(self,affinity_type,**kwargs):
        self.init_aff_type = affinity_type
        if self.init_aff_type == INIT_AFF_COS_SIM:
            if "threshold" in kwargs:
                self.init_aff_threshold = kwargs["threshold"]
            else:
                self.init_aff_threshold = DEFAULT_INIT_AFF_THRESHOLD
                
        elif self.init_aff_type == INIT_AFF_GAUSSIAN:
            if "epsilon" in kwargs:
                self.init_aff_epsilon = kwargs["epsilon"]
            else:
                self.init_aff_epsilon = DEFAULT_INIT_AFF_EPSILON                  
        
    def set_tree_type(self,tree_type,**kwargs):
        self.tree_type = tree_type
        if self.tree_type == TREE_TYPE_BINARY:
            if "bal_constant" in kwargs:
                self.tree_bal_constant = kwargs["bal_constant"]
            else:
                self.tree_bal_constant = DEFAULT_TREE_BAL_CONSTANT
                
        if self.tree_type == TREE_TYPE_FLEXIBLE:
            if "tree_constant" in kwargs:
                self.tree_constant = kwargs["tree_constant"]
            else:
                self.tree_constant = DEFAULT_TREE_CONSTANT
        
    def set_dual_aff(self,row_affinity_type,col_affinity_type,**kwargs):
        self.row_affinity_type = row_affinity_type
        self.col_affinity_type = col_affinity_type
        
        if self.row_affinity_type == DUAL_GAUSSIAN:
            if "row_epsilon" in kwargs:
                self.row_epsilon = kwargs["epsilon"]
            else:
                self.row_epsilon = DEFAULT_DUAL_EPSILON                  
                
        if self.row_affinity_type == DUAL_EMD:
            if "row_alpha" in kwargs:
                self.row_alpha = kwargs["row_alpha"]
            else:
                self.row_alpha = DEFAULT_DUAL_ALPHA
            if "row_beta" in kwargs:
                self.row_beta = kwargs["row_beta"]
            else:
                self.row_beta = DEFAULT_DUAL_BETA
            
        if self.col_affinity_type == DUAL_GAUSSIAN:
            if "col_epsilon" in kwargs:
                self.col_epsilon = kwargs["epsilon"]
            else:
                self.col_epsilon = DEFAULT_DUAL_EPSILON                  
                
        if self.col_affinity_type == DUAL_EMD:
            if "col_alpha" in kwargs:
                self.col_alpha = kwargs["col_alpha"]
            else:
                self.col_alpha = DEFAULT_DUAL_ALPHA
            if "col_beta" in kwargs:
                self.col_beta = kwargs["col_beta"]
            else:
                self.col_beta = DEFAULT_DUAL_BETA

    def set_iters(self,**kwargs):
        print kwargs
        if "n_iters" in kwargs:
            self.n_iters = kwargs["n_iters"]
        else:
            print "default n_iters"
            self.n_iters = DEFAULT_N_ITERS
        
        if "n_trees" in kwargs:
            self.n_trees = kwargs["n_trees"]
        else:
            self.n_trees = DEFAULT_N_TREES
            
class PyQuestRun(object):
    def __init__(self,run_desc,row_trees,col_trees,row_tree_descs,col_tree_descs,params):
        self.run_desc = run_desc
        self.row_trees = row_trees
        self.col_trees = col_trees
        self.row_tree_descs = row_tree_descs
        self.col_tree_descs = col_tree_descs
        self.params = params
        

def pyquest(data,params):
    #params should be a PyQuestParams object

    Publisher.sendMessage("status.bar", "Calculating initial affinity...")
    if params.init_aff_type == INIT_AFF_COS_SIM:
        init_row_aff = affinity.mutual_cosine_similarity(
                            data.T,False,0,threshold=params.init_aff_threshold)
    elif params.init_aff_type == INIT_AFF_GAUSSIAN:
        #add KNN to the page
        init_row_aff = affinity.gaussian_euclidean(
                            data.T, 5, params.init_aff_epsilon)
    
    #Compute diffusion embedding of initial affinities
    init_row_vecs,init_row_vals = markov.markov_eigs(init_row_aff, 12)
    init_row_vals[np.isnan(init_row_vals)] = 0.0
    row_embedding = init_row_vecs.dot(np.diag(init_row_vals))
    row_distances = spsp.distance.squareform(spsp.distance.pdist(row_embedding))
    row_affinity = np.max(row_distances) - row_distances
    
    #Generate initial tree
    #print "call1 tree_constant:{}".format(tree_constant)
    Publisher.sendMessage("status.bar", "Calculating initial row tree...")

    if params.tree_type == TREE_TYPE_BINARY:
        init_row_tree = bintree_construct.median_tree(
                                init_row_vecs,init_row_vals,max_levels=12)
    elif params.tree_type == TREE_TYPE_FLEXIBLE:
        init_row_tree = tree_building.make_tree_embedding(
                                row_affinity,params.tree_constant)
    
    dual_col_trees = []
    dual_row_trees = [init_row_tree]
    
    row_tree_descs = ["Initial tree"]
    col_tree_descs = []
    
    for i in xrange(params.n_iters):
        message = "Iteration {}: calculating column affinity...".format(i)
        Publisher.sendMessage("status.bar", message)

        #print "Beginning iteration {}".format(i)
        if params.col_affinity_type == DUAL_EMD:
            col_emd = dual_affinity.calc_emd(data,dual_row_trees[-1],
                     params.col_alpha,params.col_beta)
            col_aff = dual_affinity.emd_dual_aff(col_emd)
        elif params.col_affinity_type == DUAL_GAUSSIAN:
            print "Gaussian dual affinity not supported at the moment."
            return None
        
        message = "Iteration {}: calculating column tree...".format(i)
        Publisher.sendMessage("status.bar", message)

        if params.tree_type == TREE_TYPE_BINARY:
            col_tree = bintree_construct.eigen_tree(data,dual_row_trees[-1],
                    params.col_alpha,params.col_beta,params.tree_bal_constant)
        elif params.tree_type == TREE_TYPE_FLEXIBLE:
            col_tree = tree_building.make_tree_embedding(col_aff,
                                     params.tree_constant)
        dual_col_trees.append(col_tree)
        col_tree_descs.append("Iteration {}".format(i))

        message = "Iteration {}: calculating row affinity...".format(i)
        Publisher.sendMessage("status.bar", message)

        if params.row_affinity_type == DUAL_EMD:
            row_emd = dual_affinity.calc_emd(data.T,dual_col_trees[-1],
                     params.row_alpha,params.row_beta)
            row_aff = dual_affinity.emd_dual_aff(row_emd)
        elif params.row_affinity_type == DUAL_GAUSSIAN:
            print "Gaussian dual affinity not supported at the moment."
            return None
 
        message = "Iteration {}: calculating row tree...".format(i)
        Publisher.sendMessage("status.bar", message)
       
        if params.tree_type == TREE_TYPE_BINARY:
            row_tree = bintree_construct.eigen_tree(data.T,dual_col_trees[-1],
                    params.row_alpha,params.row_beta,params.tree_bal_constant)
        elif params.tree_type == TREE_TYPE_FLEXIBLE:
            row_tree = tree_building.make_tree_embedding(row_aff,
                                     params.tree_constant)
        dual_row_trees.append(row_tree)
        row_tree_descs.append("Iteration {}".format(i))
        quest_run_desc = "{}".format(datetime.datetime.now())

    return PyQuestRun(quest_run_desc,dual_row_trees,dual_col_trees,
                      row_tree_descs,col_tree_descs,params)

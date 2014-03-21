"""
dual_affinity.py: Functions for calculating dual affinity based on Earth 
                  Mover's Distance.
"""

import numpy as np
import tree_util
import scipy.spatial as spsp
import collections

def emd_dual_aff(emd,eps=1.0):
    """
    Calculates the EMD affinity from a distance matrix
    by normalizing by the median EMD and taking exp^(-EMD)
    without thresholding.
    """
   
    epall = eps*np.median(emd)
    if epall == 0.0:
        epall = 1.0
    
    return np.exp(-emd/epall)

def calc_emd(data,row_tree,alpha=1.0,beta=0.0,exc_sing=False):
    """
    Calculates the EMD on the *columns* from data and a tree on the rows.
    each level is weighted by 2**((1-level)*alpha)
    each folder size (fraction) is raised to the beta power for weighting.
    """
    rows,_ = np.shape(data)
    assert rows == row_tree.size, "Tree size must match # rows in data."

    folder_fraction = np.array([((node.size*1.0/rows)**beta)*
                                (2.0**((1.0-node.level)*alpha))
                                 for node in row_tree])
    if exc_sing:
        for node in row_tree:
            if node.size == 1:
                folder_fraction[node.idx] = 0.0
    coefs = tree_util.tree_averages(data,row_tree)
    
    ext_vecs = np.diag(folder_fraction).dot(coefs)
    
    pds = spsp.distance.pdist(ext_vecs.T,"cityblock")
    distances = spsp.distance.squareform(pds)

    return distances
    
def calc_emd_ref(ref_data,data,row_tree,alpha=1.0,beta=0.0):
    """
    Calculates the EMD from a set of points to a reference set of points
    The columns of ref_data are each a reference set point.
    The columns of data are each a point outside the reference set.
    """
    ref_rows,ref_cols = np.shape(ref_data)
    rows,cols = np.shape(data)
    assert rows == row_tree.size, "Tree size must match # rows in data."
    assert ref_rows == rows, "Mismatched row #: reference and sample sets."

    emd = np.zeros([ref_cols,cols])
    ref_coefs = tree_util.tree_averages(ref_data, row_tree)
    coefs = tree_util.tree_averages(data, row_tree)
    level_elements = collections.defaultdict(list)
    level_sizes = collections.defaultdict(int)
    
    for node in row_tree:
        level_elements[node.level].append(node.idx)
        level_sizes[node.level] += node.size
        
    folder_fraction = np.array([node.size for node in row_tree],np.float)
    for level in xrange(1,row_tree.tree_depth+1):
        fsize = np.sum(folder_fraction[level_elements[level]])
        folder_fraction[level_elements[level]] /= fsize
    
    folder_fraction = folder_fraction**beta
    coefs = np.diag(folder_fraction).dot(coefs)
    ref_coefs = np.diag(folder_fraction).dot(ref_coefs)
    for level in xrange(1,row_tree.tree_depth+1):
        distances = spsp.distance.cdist(coefs[level_elements[level],:].T,
                                        ref_coefs[level_elements[level],:].T,
                                        "cityblock").T
        emd += (2**((1.0-level)*alpha))*distances

    return emd
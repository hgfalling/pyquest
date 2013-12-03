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

def calc_emd(data,row_tree,alpha=1.0,beta=0.0):
    """
    Calculates the EMD on the *columns* from data and a tree on the rows.
    each level is weighted by 2**((1-level)*alpha)
    each folder size is raised to the beta power for weighting.
    """
    rows,cols = np.shape(data)
    assert rows == row_tree.size, "Tree size must match # rows in data."

    emd = np.zeros([cols,cols])
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
    for level in xrange(1,row_tree.tree_depth+1):
        distances = spsp.distance.cdist(coefs[level_elements[level],:].T,
                                        coefs[level_elements[level],:].T,
                                        "cityblock")
        emd += (2**((1.0-level)*alpha))*distances

    return emd


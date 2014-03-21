"""
tree_util.py: Defines various tree transforms and averages.
"""
import numpy as np

def bitree_sums(data,row_tree,col_tree):
    """
    data is a 2d matrix. row_tree is a tree on the rows (size m)
    col_tree is a tree on the columns (size n)
    Calculates sum on every bifolder.
    Returns mxn matrix of bifolder sums (indices are the node.idx values)
    """
    
    sums = np.zeros([row_tree.tree_size,col_tree.tree_size],data.dtype)
    m,n = np.shape(data)
    
    col_singletons_start = col_tree.tree_size - n
    row_singletons_start = row_tree.tree_size - m
    
    sums[row_singletons_start:,col_singletons_start:] = data
    
    for row_node in reversed(row_tree[0:row_singletons_start]):
        sums[row_node.idx,:] = np.sum(sums[[x.idx for x in 
                                            row_node.children],:],axis=0)
    
    for col_node in reversed(col_tree[0:col_singletons_start]):
        sums[:,col_node.idx] = np.sum(sums[:,[x.idx for x in 
                                            col_node.children]],axis=1)
    
    return sums

def bifolder_sizes(row_tree,col_tree):
    """
    Returns the raw sizes of the rectangles implied by the folders in 
    row_tree and col_tree.
    """

    row_sizes = np.array([x.size for x in row_tree])
    col_sizes = np.array([x.size for x in col_tree])

    return np.outer(row_sizes,col_sizes)

def bitree_averages(data,row_tree,col_tree):
    """
    data is a 2d matrix. row_tree is a tree on the rows (tree_size m)
    col_tree is a tree on the columns (tree_size n)
    Calculates mean on every bifolder.
    Returns mxn matrix of bifolder means (indices are the node.idx values)
    """
    
    return 1.0*bitree_sums(data,row_tree,col_tree)/bifolder_sizes(row_tree,col_tree)

def bitree_transform(data,row_tree,col_tree):
    """
    data is a 2d matrix. row_tree is a tree on the rows (size m)
    col_tree is a tree on the columns (size n)
    Calculates the bitree transform on every bifolder.
    This transform is the martingale difference transform.
    Returns mxn matrix of bifolder means (indices are the node.idx values)
    """
    avs = bitree_averages(data,row_tree,col_tree)
    coefs = np.zeros([row_tree.tree_size,col_tree.tree_size])

    adjs = np.zeros([row_tree.tree_size,col_tree.tree_size])
    
    for node in row_tree:
        if node.parent is None:
            coefs[node.idx,:] = avs[node.idx,:]
        else:
            coefs[node.idx,:] = avs[node.idx,:] - avs[node.parent.idx,:]

    for node in col_tree: 
        if node.parent is None:
            adjs[:,node.idx] += coefs[:,node.idx]
        else:
            coefs[:,node.idx] -= adjs[:,node.parent.idx]
            adjs[:,node.idx] = coefs[:,node.idx] + adjs[:,node.parent.idx]
                
    return coefs

def inverse_bitree_transform(coefs,row_tree,col_tree,threshold=0.0):
    """
    coefs is an mxn matrix of bitree coefficients
    row_tree is a tree on the rows (size m)
    col_tree is a tree on the columns (size n)
    threshold is on [0,1]. Folders that are less than threshold*matrix size
    are excluded from the reconstruction.
    """ 
    new_coefs = coefs.copy()
    bsizes = bifolder_sizes(row_tree,col_tree)      
    folder_frac = 1.0*bsizes/bsizes[0,0]
    new_coefs *= folder_frac > threshold
    return inverse_tree_transform(inverse_tree_transform(new_coefs.T,col_tree).T,row_tree)

def inverse_bitree_transform_level(coefs,row_tree,col_tree,row_level,col_level):
    """
    coefs is an mxn matrix of bitree coefficients
    row_tree is a tree on the rows (size m)
    col_tree is a tree on the columns (size n)
    Excludes martingale coefficients corresponding to folders whose row_level
    or col_level exceeds the thresholds.
    """ 
    new_coefs = coefs.copy()
    if row_level < row_tree.tree_depth:
        m = [x.idx for x in row_tree if x.level > row_level]
        new_coefs[m,:] = 0.0
    if col_level < col_tree.tree_depth:
        n = [x.idx for x in col_tree if x.level > col_level]
        new_coefs[:,n] = 0.0
    return inverse_tree_transform(inverse_tree_transform(new_coefs.T,col_tree).T,row_tree)

def tree_sums(data,row_tree):
    """
    data is a vector or matrix of size d or (dxm) 
    row_tree is a tree on the rows. tree_size is n. 
    Returns a vector (size n) or a matrix (size nxm) containing sums on folders.
    """
    
    if data.ndim == 1:
        sums = np.zeros([row_tree.tree_size])
        for node in row_tree.traverse():
            sums[node.idx] = np.sum(data[node.elements])
    else:
        sums = np.zeros([row_tree.tree_size]+list(np.shape(data)[1:]))
        for node in row_tree.traverse():
            sums[node.idx,...] = np.sum(data[node.elements,:],axis=0)
    
    return sums
    
def tree_averages(data,row_tree):
    """
    data is a vector or matrix of size d or (dxm) 
    row_tree is a tree on the rows. tree_size is n. 
    Returns a vector (size n) or a matrix (size nxm) containing avgs on folders.
    """
    averages = tree_sums(data,row_tree)
    if data.ndim == 1:
        for node in row_tree.traverse():
            averages[node.idx] /= node.size
    else:
        for node in row_tree.traverse():
            averages[node.idx,:] /= node.size
    
    return averages

def tree_transform(data,row_tree):
    """
    data is a vector or matrix of size d or (dxm) 
    row_tree is a tree on the rows. tree_size is n. 
    Returns a vector (size n) or a matrix (size nxm) containing coefs.
    """
    avs = tree_averages(data,row_tree)
    coefs = np.zeros(np.shape(avs))
    if avs.ndim == 1:
        for node in row_tree:
            if node.parent is None:
                coefs[node.idx] = avs[node.idx]
            else:
                coefs[node.idx] = avs[node.idx] - avs[node.parent.idx]
    else:
        for node in row_tree:
            if node.parent is None:
                coefs[node.idx,:] = avs[node.idx,:]
            else:
                coefs[node.idx,:] = avs[node.idx,:] - avs[node.parent.idx,:]
    return coefs


def inverse_tree_transform(coefs,row_tree,threshold=0.0):
    """
    coefs is a set of tree_transform coefficients (size n)
    row_tree is a tree on the rows (tree_size n)
    Reconstructs a data matrix from the coefs and tree, ignoring coefficients
    on folders whose fraction of the total data matrix < threshold.
    """
    n = row_tree.size
    if coefs.ndim == 1:
        mat = np.zeros([row_tree.size],np.float)
        for node in row_tree:
            if node.size*1.0/n >= threshold:
                mat[node.elements] += coefs[node.idx]
    else:
        mat = np.zeros([row_tree.size,np.shape(coefs)[1]])
        for node in row_tree:
            if node.size*1.0/n >= threshold:
                mat[node.elements,:] += coefs[node.idx,:]
    
    return mat

def normalize_tree_coefs(coefs,row_tree):
    """
    Multiplies each coefficient from a tree transform by its fraction 
    of the total tree size. Could use for thresholding: only coefs > some 
    threshold survive (small folders would be suppressed).
    """
    n = row_tree.tree_size
    folder_sizes = np.zeros(n)
    for node in row_tree.traverse():
        folder_sizes[node.idx] = 1.0*node.size / row_tree.size 
        
    return np.diag(folder_sizes).dot(coefs)

def normalize_bitree_coefs(coefs,row_tree,col_tree):
    """
    Multiplies each coefficient from a bitree transform by its fraction 
    of the total bitree size. Could use for thresholding: only coefs > some 
    threshold survive (small folders would be suppressed).
    """
    row_n,col_n = row_tree.tree_size,col_tree.tree_size
    rows_frac = np.array([node.size*1.0/row_n for node in row_tree.traverse()])
    cols_frac = np.array([node.size*1.0/col_n for node in col_tree.traverse()])
    folder_frac = np.outer(rows_frac,cols_frac)

    return folder_frac*coefs
       
        
    
    
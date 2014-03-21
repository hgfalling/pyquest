"""
haar.py: Functions for describing Haar, Haarlike, and tensor Haar bases on
         discrete spaces and products of discrete spaces.
""" 

import numpy as np

def haar_vectors(n,node_sizes,norm="L2"):
    """
    Returns a matrix of haar basis vectors for a tree with n subnodes of 
    sizes given in node_sizes.
    norm should be either "L2" or "L1"; L2 gives an orthonormal basis
    while L1 shifts the normalization to the inverse transform. 
    """

    haar_basis = np.zeros([n,n])
    haar_basis[:,0] = 1.0

    #if we want the orthonormal basis, then we normalize by 1/sqrt(n) on the
    #constant vector.
    if norm == "L2":
        haar_basis[:,0] /= np.sqrt(n)

    for i in xrange(1,n):
        pluses = node_sizes[i-1]
        minuses = np.sum(node_sizes[i:])
        
        haar_basis[i-1,i] = minuses
        haar_basis[i:,i] = -1.0*pluses
        
        if norm == "L2":
            norm_i = np.sqrt(np.sum((haar_basis[:,i]**2) * (node_sizes)))
        elif norm == "L1":
            norm_i = 2.0*(minuses*pluses)/(minuses+pluses)

        haar_basis[:,i] /= norm_i
       
    return haar_basis

def compute_haar(t,return_nodes=False,norm="L2"):
    """
    Takes a full tree of type ClusterTreeNode and computes the canonical 
    Haar-like basis.
    return_nodes specifies whether we want to return parent node.idx associated
    with each basis vector. (-1 means this is the root ie constant vector)
    """
    
    n = t.size
    haar_basis = np.zeros([n,n])
    node_ids = np.zeros(n,np.int)
    node_ids[0] = -1
    cur_col = 1
    haar_basis[:,0] = 1.0
    if norm == "L2":
        haar_basis[:,0] /= np.sqrt(n)
    
    for node in t:
        node_size = len(node.children)
        schildren = list(reversed(sorted(node.children,key=lambda x:x.size)))
        if node_size > 0:
            basis_vecs = haar_vectors(node_size,
                                      np.array([x.size for x in schildren]),
                                      norm)
            
            for i in xrange(1,node_size):
                #each basis vector will be a column of the basis
                for j,child in enumerate(schildren):
                    haar_basis[child.elements,cur_col] = basis_vecs[j,i]
                    node_ids[cur_col] = node.idx
                cur_col += 1
            

    if return_nodes:
        return haar_basis, node_ids
    else:
        return haar_basis
    
def haar_transform(data,row_tree,norm="L2"):
    """
    Computes the Haar transform of data with respect to row_tree. (nothing
    fancy here, can go faster).
    """
    basis = compute_haar(row_tree,False,norm)
    return basis.T.dot(data)
    
def inverse_haar_transform(coefs,row_tree,norm="L2"):
    """
    Computes the inverse Haar transform of coefficients with respect to 
    row_tree. Again nothing fancy here.
    """
    basis = compute_haar(row_tree)
    if norm == "L1":
        norm_vec = np.sum(np.abs(basis),axis=0)
        for col in xrange(basis.shape[1]):
            basis[:,col] /= norm_vec[col]
    return basis.dot(coefs)
    
def level_correspondence(row_tree):
    """
    Returns a vector of the correspondence of the haar basis vectors to the 
    levels of the tree.
    """
    level_counts = [[x.size for x in row_tree.dfs_level(i)] for i in 
                    xrange(1,row_tree.tree_depth+1)]
    marks = [0]+[row_tree.size-sum([y-1 for y in x]) for x in level_counts]
    z = np.zeros(row_tree.size,np.int)
    for (idx,t) in enumerate(marks):
        if idx == len(marks) - 1:
            z[t:] = idx+1
        else:
            z[t:marks[idx+1]] = idx+1
    return z
        
def bihaar_transform(data,row_tree,col_tree,folder_sizes=False):
    """
    Computes the bi-Haar transform into the basis induced by row_tree and 
    col_tree jointly.
    """
    if folder_sizes:
        row_hb, row_parents = compute_haar(row_tree,folder_sizes)
        row_parents[row_parents == -1] = 0
        col_hb, col_parents = compute_haar(col_tree,folder_sizes)
        col_parents[col_parents == -1] = 0
    else:
        row_hb = compute_haar(row_tree,folder_sizes)
        col_hb = compute_haar(col_tree,folder_sizes)
    row_transform = row_hb.T.dot(data)
    coefs = col_hb.T.dot(row_transform.T)
    if folder_sizes:
        row_sizes = np.array([row_tree[x].size for x in row_parents])
        col_sizes = np.array([col_tree[x].size for x in col_parents])
        return coefs.T, np.outer(row_sizes,
                                 col_sizes)/(1.0*row_tree.size*col_tree.size)
    else:
        return coefs.T
    
def inverse_bihaar_transform(coefs,row_tree,col_tree):
    """
    Computes the inverse bi-Haar transform of coefs. 
    """
    row_hb = compute_haar(row_tree)
    col_hb = compute_haar(col_tree)
    row_transform = row_hb.dot(coefs)
    matrix = col_hb.dot(row_transform.T)
    return matrix.T
    
    
    
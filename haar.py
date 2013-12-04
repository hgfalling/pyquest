import numpy as np

def haar_vectors(n,node_sizes):
    """
    returns a matrix of haar basis vectors for a tree which divides into n subnodes. 
    Still needs to be scaled to the size of the nodes.
    Example: haar_coeffs(2) returns 
    [1/sqrt(2)  1/sqrt(2)
     1/sqrt(2) -1/sqrt(2)]
    """
    
    haar_basis = np.zeros([n,n])
    haar_basis[:,0] = 1.0/np.sqrt(np.sum(node_sizes))
    for i in xrange(1,n):
        haar_basis[i-1,i] = np.sum(node_sizes[i:])
        haar_basis[i:,i] = -1*node_sizes[i-1]
        
        norm_i = np.sqrt(np.sum((haar_basis[:,i]**2) * (node_sizes)))
        if norm_i < 1e-15:
            print i
        haar_basis[:,i] = haar_basis[:,i] / norm_i
    return haar_basis

def compute_haar(tree,return_nodes=False):
    """
    Takes a full tree of type ClusterTreeNode and computes the canonical Haar-like basis.
    """
    
    n = len(tree.dfs_leaves())
    haar_basis = np.zeros([n,n])
    node_ids = np.zeros(n,np.int)
    node_ids[0] = -1
    cur_col = 1
    haar_basis[:,0] = 1/np.sqrt(n)
    
    for node in tree:
        node_size = len(node.children)
        if node_size > 0:
            basis_vectors = haar_vectors(node_size,
                                         np.array([x.size for x in node.children]))
            
            for i in xrange(1,node_size):
                #each basis vector will be a column of the basis
                for j in xrange(node_size):
                    haar_basis[node.children[j].elements,cur_col] = basis_vectors[j,i]
                    node_ids[cur_col] = node.idx
                cur_col += 1
            

    if return_nodes:
        return haar_basis, node_ids
    else:
        return haar_basis

def haar_transform(data,row_tree,hb=None):
    if hb is None:
        basis = compute_haar(row_tree)
        return basis.T.dot(data)
    else:
        return hb.T.dot(data)
    
def inverse_haar_transform(coefs,row_tree,hb=None):
    if hb is None:
        basis = compute_haar(row_tree)
        return basis.dot(coefs)
    else:
        return hb.dot(coefs)
    
def level_correspondence(row_tree):
    """
    Returns a vector of the correspondence of the haar basis vectors to the 
    levels of the tree.
    """
    level_counts = [[x.size for x in row_tree.dfs_level(i)] for i in xrange(1,row_tree.tree_depth+1)]
    #print level_counts
    marks = [0]+[row_tree.size-sum([y-1 for y in x]) for x in level_counts]
    #print marks
    z = np.zeros(row_tree.size,np.int)
    for (idx,t) in enumerate(marks):
        if idx == len(marks) - 1:
            z[t:] = idx+1
        else:
            z[t:marks[idx+1]] = idx+1
    return z
        
def bihaar_transform(data,row_tree,col_tree):
    row_hb = compute_haar(row_tree)
    col_hb = compute_haar(col_tree)
    #print row_hb.shape, col_hb.shape, data.shape
    row_transform = row_hb.T.dot(data)
    #print row_transform.shape
    coefs = col_hb.T.dot(row_transform.T)
    return coefs.T
    
def inverse_bihaar_transform(coefs,row_tree,col_tree):
    row_hb = compute_haar(row_tree)
    col_hb = compute_haar(col_tree)
    #print row_hb.shape, col_hb.shape, data.shape
    row_transform = row_hb.dot(coefs)
    #print row_transform.shape
    matrix = col_hb.dot(row_transform.T)
    return matrix.T
    
    
    
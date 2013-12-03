import numpy as np
import tree_util
import sklearn.neighbors as sknn
import scipy.spatial as spsp
import markov

def bifolder(row_folder,col_folder,data):
    """
    row_folder and col_folder are nodes of their respective trees.
    Returns the submatrix of 2d matrix data corresponding to the product folder.
    """
    return data[row_folder.elements,:][:,col_folder.elements]

def bifolder_average(row_folder,col_folder,data):
    """
    row_folder and col_folder are nodes of their respective trees.
    Returns the *column* vector that is the average of the submatrix of 2d matrix 
    data corresponding to the product folder.
    """
    submatrix = bifolder(row_folder,col_folder,data)
    row_sums = 1.0*np.sum(submatrix,axis=1)
    row_counts = np.sum(submatrix!=0,axis=1)
    return row_sums / row_counts

def organize_folders(row_tree,col_tree,data):
    """
    row_tree and col_tree are trees on the rows and columns.
    Returns the 2d matrix data with rows/columns sorted by 
    the tree structures.
    """
    row_order = [x.elements[0] for x in row_tree.dfs_leaves()]
    col_order = [x.elements[0] for x in col_tree.dfs_leaves()]
    return data[row_order,:][:,col_order]

def predictability(row_folder,col_folder,data):
    """
    row_folder and col_folder are nodes of their respective trees.
    Returns the L1 norm of the bifolder_average column vector divided by its 
    size. This is a measure of the predictability of this folder size for data 
    that is 1s/-1s.  (if the data is all 1s or all -1s, L1 norm will be high.)
    """
    bavg = bifolder_average(row_folder,col_folder,data)
    return np.linalg.norm(bavg,1) / np.shape(bavg)[0]

def organize_cols(col_tree,data):
    """
    col_tree is a tree on the columns.
    Returns the 2d matrix data with columns sorted by the tree structures.
    """
    col_order = [x.elements[0] for x in col_tree.dfs_leaves()]
    return data[:,col_order]

def organize_rows(row_tree,data):
    """
    row_tree is a tree on the columns.
    Returns the 2d matrix data with rows sorted by the tree structures.
    """
    row_order = [x.elements[0] for x in row_tree.dfs_leaves()]
    return data[row_order,:]

def _level_avgs(data,col_tree):
    """
    data is a vector of length n.
    col_tree is a tree with n leaves. 
    Calculates the average of data for each node of col_tree.
    Return value is an dxn matrix, where d is the depth of the col_tree
    """
    tavg = tree_util.tree_averages(data.T,col_tree)
    averages = np.zeros([col_tree.tree_depth,col_tree.size])
    
    for node in col_tree:
        averages[node.level-1,node.elements] = tavg[node.idx]

    return averages

def level_avgs(data,col_tree):
    """
    data is a matrix mxn.
    col_tree is a tree with n leaves and d levels.
    Return value is an mxdxn matrix, where d is the depth of the col_tree.
    Entry (i,j,k) is the average response of the ith row to the 
    folder containing k at the jth level.
    """
    if data.ndim == 1:
        return _level_avgs(data,col_tree)
    m,n = np.shape(data)
    averages = np.zeros([m,col_tree.tree_depth,n])
    
    tavg = tree_util.tree_averages(data.T,col_tree)
    for node in col_tree:
        averages[:,node.level-1,node.elements] = np.tile(tavg[node.idx],
                                                         (len(node.elements),1)).T
        
    return averages 

def coef_levels(coefs,tree):
    """
    Takes the coefs from the tree_transform and converts them to the 
    martingale difference picture.
    """
    mdiffs = np.zeros([tree.tree_depth,tree.size])
    for node in tree:
        mdiffs[node.level-1,node.elements] = coefs[node.idx]
    
    return mdiffs

def nn_param(data,start=0):
    n = data.shape[0]
    knn = sknn.NearestNeighbors(n_neighbors=n)
    knn.fit(data)
    distances,neighbors = knn.kneighbors(data)
    order = []
    order.append(start)
    for _ in xrange(n):
        nn = [x for x in neighbors[order[-1]] if x not in order]
        #print "neighbors of {}: {}".format(order[-1],nn)
        if nn:
            order.append(nn[0])
    return order

import tree_util
import numpy as np
import haar
import wallenius

def shrink_coefs(coefs,t):
    return np.sign(coefs)*(np.abs(coefs) - t)*(np.abs(coefs) > t)

def recon_1d_folder_size(data,tree,threshold=0.0):
    coefs = tree_util.tree_transform(data, tree)
    return tree_util.inverse_tree_transform(coefs, tree, threshold)

def recon_2d_folder_size(data,row_tree,col_tree,threshold=0.0):
    coefs = tree_util.bitree_transform(data,row_tree,col_tree)
    return tree_util.inverse_bitree_transform(coefs,row_tree,col_tree,threshold)

def sure(haar_coefs,t,estimated_var=1.0):
    term1 = len(haar_coefs)
    term2 = 2*(np.sum(np.abs(haar_coefs) <= t))
    term3 = np.sum(np.minimum(np.abs(haar_coefs),t)**2)
    return estimated_var*(term1 - term2) + term3,(term1,term2,term3)

def recon_1d_sure(data,tree,estimated_var=1.0):
    haar_coefs = haar.haar_transform(data, tree)
    new_haar_coefs = np.zeros(haar_coefs.shape)
    coef_levels = haar.level_correspondence(tree)
    for level in np.unique(coef_levels):
        hc = haar_coefs[coef_levels==level]
        if len(hc) == 1:
            t = 0
        else:
            x = np.arange(0,6.0,0.1)
            estimates = []
            for threshold in x:
                estimate = sure(hc,threshold,estimated_var)
                estimates.append(estimate[0])
            t = x[np.argmin(estimates)]
        new_haar_coefs[coef_levels==level] = shrink_coefs(hc,t)
    return haar.inverse_haar_transform(new_haar_coefs, tree)

def recon_2d_sure(data,row_tree,col_tree,estimated_var=1.0):
    bihaar_coefs = haar.bihaar_transform(data, row_tree, col_tree)
    new_bihaar_coefs = np.zeros(bihaar_coefs.shape)
    row_levels = haar.level_correspondence(row_tree)
    col_levels = haar.level_correspondence(col_tree)
    coef_levels = np.add.outer(row_levels,col_levels)
    for level in np.unique(coef_levels):
        hc = bihaar_coefs[coef_levels==level]
        if len(hc) == 1:
            t = 0
        else:
            x = np.arange(0,6.0,0.1)
            estimates = []
            for threshold in x:
                estimate = sure(hc,threshold,estimated_var)
                estimates.append(estimate[0])
            t = x[np.argmin(estimates)]
        new_bihaar_coefs[coef_levels==level] = shrink_coefs(hc,t)
    return haar.inverse_bihaar_transform(new_bihaar_coefs, row_tree, col_tree)

def recon_2d_dyadic_haar_hypo_test(data,row_tree,col_tree,alpha):
    _,row_nodes = haar.compute_haar(row_tree,True)
    _,col_nodes = haar.compute_haar(col_tree,True)
    coefs = haar.bihaar_transform(data,row_tree,col_tree)
    k_values = tree_util.bitree_sums(data*(data > 0),row_tree,col_tree).astype(np.int)
    tests = 0
    for i in xrange(coefs.shape[0]):
        for j in xrange(coefs.shape[1]):
            #always testing against the big folder.
            if row_nodes[i] == -1 and col_nodes[j] == -1:
                continue
            elif row_nodes[i] == -1:
                row_parent = row_tree
                col_parent = col_tree[col_nodes[j]]
                n_child = row_parent.size*col_parent.children[0].size
                actual_k = k_values[row_parent.idx,col_parent.children[0].idx]
            elif col_nodes[j] == -1:
                row_parent = row_tree[row_nodes[i]]
                col_parent = col_tree
                n_child = row_parent.children[0].size*col_parent.size
                actual_k = k_values[row_parent.children[0].idx,col_parent.idx]
            else:
                row_parent = row_tree[row_nodes[i]]
                col_parent = col_tree[col_nodes[j]]
    
                n_child = row_parent.children[0].size*col_parent.children[0].size + row_parent.children[1].size*col_parent.children[1].size
                actual_k = k_values[row_parent.children[0].idx,col_parent.children[0].idx] + k_values[row_parent.children[1].idx,col_parent.children[1].idx]
    
            n_parent = row_parent.size*col_parent.size
            k_parent = k_values[row_parent.idx,col_parent.idx]
            
            p_test = wallenius.partition_htest_value(n_parent,k_parent,n_child,actual_k,alpha)
            tests += 1
            #print "{},{} htest: N={} K={}, n={}, k={}, {}".format(row_parent.level,col_parent.level,n_parent,k_parent,n_child,actual_k,p_test)
            if not p_test: 
                coefs[i,j] = 0.0
    #print "tests performed: {}".format(tests)
    return haar.inverse_bihaar_transform(coefs, row_tree, col_tree), coefs  

def recon_2d_haar_htest(data,row_tree,col_tree,alpha):
    
    pass

    

cache = {}

def calc_hg_p_values_haar(data,row_tree,col_tree):
    _,row_nodes = haar.compute_haar(row_tree,True)
    _,col_nodes = haar.compute_haar(col_tree,True)
    p_values = np.zeros(data.shape)
    k_values = tree_util.bitree_sums(data*(data > 0),row_tree,col_tree).astype(np.int)
    tests = 0
    for i in xrange(p_values.shape[0]):
        for j in xrange(p_values.shape[1]):
            #always testing against the big folder.
            if row_nodes[i] == -1 and col_nodes[j] == -1:
                continue
            elif row_nodes[i] == -1:
                row_parent = row_tree
                col_parent = col_tree[col_nodes[j]]
                n_child = row_parent.size*col_parent.children[0].size
                k_child = k_values[row_parent.idx,col_parent.children[0].idx]
            elif col_nodes[j] == -1:
                row_parent = row_tree[row_nodes[i]]
                col_parent = col_tree
                n_child = row_parent.children[0].size*col_parent.size
                k_child = k_values[row_parent.children[0].idx,col_parent.idx]
            else:
                row_parent = row_tree[row_nodes[i]]
                col_parent = col_tree[col_nodes[j]]
    
                n_child = row_parent.children[0].size*col_parent.children[0].size + row_parent.children[1].size*col_parent.children[1].size
                k_child = k_values[row_parent.children[0].idx,col_parent.children[0].idx] + k_values[row_parent.children[1].idx,col_parent.children[1].idx]
    
            n_parent = row_parent.size*col_parent.size
            k_parent = k_values[row_parent.idx,col_parent.idx]
            
            if (n_parent,k_parent,n_child,k_child) in cache:
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
            else:
                cache[(n_parent,k_parent,n_child,k_child)] = wallenius.hg_p_value(n_parent,k_parent,n_child,k_child)
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
                tests += 1
            #print "{},{} htest: N={} K={}, n={}, k={}, {}".format(row_parent.level,col_parent.level,n_parent,k_parent,n_child,actual_k,p_test)
    print "tests performed: {}".format(tests)
    return p_values

def calc_hg_p_values_bitree(data,row_tree,col_tree):
    p_values = np.zeros([row_tree.tree_size,col_tree.tree_size])
    k_values = tree_util.bitree_sums(data*(data > 0),row_tree,col_tree).astype(np.int)
    tests = 0
    for i in xrange(row_tree.tree_size):
        for j in xrange(col_tree.tree_size):
            row_node = row_tree[i]
            col_node = col_tree[j]
            if i == 0 and j == 0:
                continue
            elif i==0:
                col_parent = col_node.parent
                n_parent = col_parent.size*row_node.size
                k_parent = k_values[row_node.idx,col_parent.idx]
                n_child = col_node.size*row_node.size
                k_child = k_values[row_node.idx,col_node.idx]
            elif j==0:
                row_parent = row_node.parent
                n_parent = row_parent.size*col_node.size
                k_parent = k_values[row_parent.idx,col_node.idx]
                n_child = col_node.size*row_node.size
                k_child = k_values[row_node.idx,col_node.idx]
            else:
                row_parent = row_node.parent
                col_parent = col_node.parent
                n_parent = col_parent.size*row_parent.size
                k_parent = k_values[row_parent.idx,col_parent.idx]
                n_child = n_parent - (col_parent.size*row_node.size + col_node.size*row_parent.size) + 2*col_node.size*row_node.size
                k_child = k_parent - k_values[row_node.idx,col_parent.idx] - k_values[row_parent.idx,col_node.idx] + 2*k_values[row_node.idx,col_node.idx] 
            if (n_parent,k_parent,n_child,k_child) in cache:
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
            else:
                cache[(n_parent,k_parent,n_child,k_child)] = wallenius.hg_p_value(n_parent, k_parent, n_child, k_child)
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
                tests += 1
    print "tests performed: {}".format(tests)
    return p_values

def calc_hg_p_values_bitree2(data,row_tree,col_tree):
    p_values = np.zeros([row_tree.tree_size,col_tree.tree_size])
    k_values = tree_util.bitree_sums(data*(data > 0),row_tree,col_tree).astype(np.int)
    tests = 0
    for i in xrange(row_tree.tree_size):
        for j in xrange(col_tree.tree_size):
            row_node = row_tree[i]
            col_node = col_tree[j]
            if i == 0 and j == 0:
                continue
            elif i==0:
                col_parent = col_node.parent
                n_parent = col_parent.size*row_node.size
                k_parent = k_values[row_node.idx,col_parent.idx]
                n_child = col_node.size*row_node.size
                k_child = k_values[row_node.idx,col_node.idx]
            elif j==0:
                row_parent = row_node.parent
                n_parent = row_parent.size*col_node.size
                k_parent = k_values[row_parent.idx,col_node.idx]
                n_child = col_node.size*row_node.size
                k_child = k_values[row_node.idx,col_node.idx]
            else:
                row_parent = row_node.parent
                col_parent = col_node.parent
                n_parent = col_parent.size*row_parent.size
                k_parent = k_values[row_parent.idx,col_parent.idx]
                n_child = row_node.size*col_node.size
                k_child = k_values[row_node.idx,col_node.idx] 
            if (n_parent,k_parent,n_child,k_child) in cache:
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
            else:
                cache[(n_parent,k_parent,n_child,k_child)] = wallenius.hg_p_value(n_parent, k_parent, n_child, k_child)
                p_values[i,j] = cache[(n_parent,k_parent,n_child,k_child)]
                tests += 1
    print "tests performed: {}".format(tests)
    return p_values
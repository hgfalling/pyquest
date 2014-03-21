"""
bin_tree_build.py: Functions for building trees based on cuts of the first
                   nontrivial eigenvector of a diffusion.
"""

import tree
import markov
import numpy as np

def bin_tree_build(affinity,cut_type="r_dyadic",bal_constant=1.0):
    """
    Takes a static, square, symmetric nxn affinity on n nodes and 
    applies the second eigenvector binary cut algorithm to it.
    cut_types currently supported are: 
    r_dyadic:   random dyadic; uniform distribution on the legal splits
                based on the balance constant.
    zero:       splits the eigenvector at zero, subject to the balance constant 
    """
    
    _,n = affinity.shape

    root = tree.ClusterTreeNode(range(n))
    queue = [root]

    while max([x.size for x in queue]) > 1:
        new_queue = []
        for node in queue:
            if node.size > 2:
                #cut it
                if cut_type == "zero":
                    cut = zero_eigen_cut(node,affinity)
                elif cut_type == "r_dyadic":
                    left,right = bal_cut(node.size,bal_constant)
                    cut = random_dyadic_cut(node, affinity, left, right)
                node.create_subclusters(cut)
            else:
                #make the singletons
                node.create_subclusters(np.arange(node.size))
            new_queue.extend(node.children)
        queue = new_queue

    root.make_index()                
    return root    

def zero_eigen_cut(node,affinity):
    """
    Returns the cut of the affinity matrix (cutting at zero) 
    corresponding to the elements in node, under the condition of bal_constant.
    """ 
    new_data = affinity[node.elements,:][:,node.elements]
    
    vecs,_ = markov.markov_eigs(new_data, 2)
    labels = vecs[:,1] < 0.0
    
    return labels

def random_dyadic_cut(node,affinity,left,right):
    """
    Returns a randomized cut of the affinity matrix (cutting at zero) 
    corresponding to the elements in node, under the condition of bal_constant.
    """ 
    new_data = affinity[node.elements,:][:,node.elements]
    
    vecs,_ = markov.markov_eigs(new_data, 2)
    eig = vecs[:,1]
    eig_sorted = eig.argsort().argsort()
    cut_loc = np.random.randint(left,right+1)
    labels = eig_sorted < cut_loc
    
    return labels
    
def bal_cut(n,balance_constant):
    """
    Given n nodes and a balance_constant, returns the endpoints of the 
    interval of legal cutpoints for a binary tree.
    """ 
    if n==1:
        return 0,1
    left = int(np.ceil((1.0/(1.0+balance_constant))*n))
    right = int(np.floor((balance_constant/(1.0+balance_constant))*n))
    if left > right and n % 2 == 1:
        left = int(np.floor(n/2.0))
        right = int(np.ceil(n/2.0))
    elif left > right:
        left = right
    return left,right    

def random_binary_tree(n,bal_constant):
    """
    Creates a random binary tree on n nodes that conforms to the balance
    constant.
    """
    root = tree.ClusterTreeNode(range(n))
    queue = [root]
    while queue:
        if (max([x.size for x in queue]) == 1 and 
            max([x.level for x in queue]) == min([x.level for x in queue])):
            break
        node = queue.pop(0)
        left,right = bal_cut(node.size, bal_constant)
        cut_loc = np.random.randint(left,right+1)
        labels = np.array(node.elements).argsort().argsort() < cut_loc
        node.create_subclusters(labels)
        queue.extend(node.children)
    root.make_index()
    return root
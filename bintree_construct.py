import tree
import dual_affinity
import markov
import numpy as np

def median_tree(eigvecs,eigvals,max_levels=0):
    """
    Crude tree construction method (suitable for initial affinity)
    Split at level n is determined by the taking the median of the nth 
    non-trivial eigenvector from the original embedding.
    """
    
    #check to see if the all ones vector has been removed yet.
    if np.std(eigvecs[:,0]) == 0.0:
        eigvecs = eigvecs[:,1:]
        eigvals = eigvals[1:]
        
    d,n = np.shape(eigvecs)
    
    #default max_levels
    if max_levels == 0:
        max_levels = min(n,np.floor(np.log(d/5.0)/np.log(2.0))+2)

    vecs = eigvecs.dot(np.diag(eigvals))

    root = tree.ClusterTreeNode(range(d))
    queue = [root]

    while max([x.size for x in queue]) > 1:
        #work on one level at a time to match how the matlab trees are created
        new_queue = []
        for node in queue:
            if node.size >= 4 and node.level + 1 < max_levels:
                #cut it
                cut = median_cut(node,vecs)
                node.create_subclusters(cut)
            else:
                #make the singletons
                node.create_subclusters(np.arange(node.size))
            new_queue.extend(node.children)
        queue = new_queue

    root.make_index()                
    return root

def median_cut(node,vec):
    """
    node is a tree node. vec is an entire eigenvector. 
    takes vec on just the node elements, and returns the partition resulting
    from cutting at the median of the subvector.
    """
    cut_data = vec[node.elements,node.level-1]
    cut_loc = np.median(cut_data)
    labels = np.ones(len(node.elements))*(cut_data > cut_loc)

    return labels

def old_eigen_tree(data,row_tree,alpha=1.0,beta=0.0,noise=0.0,min_folder_size=4.0):
    """
    Constructs binary tree on columns of data with respect to dual affinity
    on row_tree by cutting at the median the first nontrivial eigenvector at 
    each node (reconstructing the eigenvector for only the rows at that node).
    Returns a tree.
    """
    
    col_emd = dual_affinity.calc_emd(data,row_tree,alpha,beta)
    _,n = data.shape

    #default max levels    
    max_levels = np.floor(np.log(n)/np.log(2.0))

    root = tree.ClusterTreeNode(range(n))
    queue = [root]

    while max([x.size for x in queue]) > 1:
        new_queue = []
        for node in queue:
            if node.size >= min_folder_size and node.level < max_levels:
                #cut it
                cut = eigen_cut(node,col_emd,noise)
                node.create_subclusters(cut)
            else:
                #make the singletons
                node.create_subclusters(np.arange(node.size))
            new_queue.extend(node.children)
        queue = new_queue

    root.make_index()                
    return root

def eigen_cut(node,emd,noise,eps=1.0):
    affinity = dual_affinity.emd_dual_aff(emd[node.elements,:][:,node.elements]
                                          ,eps)
    
    try:
        vecs,_ = markov.markov_eigs(affinity,2)
    except:
        print affinity
        print emd
        print node.elements
        raise
    eig = vecs[:,1]
    eig_sorted = np.sort(eig)
    n = len(eig_sorted)
    rnoise = np.random.uniform(-noise,noise)
    if noise < 1e-8:
        labels = np.zeros(n)
        labels[np.argsort(eig)[0:int(n/2)]] = 1
    else:
        cut_loc = eig_sorted[int((n/2)+(rnoise*n))]
        labels = np.ones(n)*(eig > cut_loc)
    
    return labels

def bal_eigen_cut(node,emd,bal_constant=1.0,eps=1.0):
    affinity = dual_affinity.emd_dual_aff(emd[node.elements,:][:,node.elements]
                                          ,eps)
    
    try:
        vecs,_ = markov.markov_eigs(affinity,2)
    except:
        print affinity
        print emd
        print node.elements
        raise
    eig = vecs[:,1]
    eig_sorted = np.argsort(eig)
    n = len(eig)
    l,r = bal_cut(n,bal_constant)
    cut_loc = np.random.randint(l,r+1)
    labels = np.zeros(n,np.int)
    labels[eig_sorted[0:cut_loc]] = 1
    
    return labels

def eigen_tree(data,row_tree,alpha=1.0,beta=0.0,bal_constant=1.0):
    """
    Constructs binary tree on columns of data with respect to dual affinity
    on row_tree by cutting at the median the first nontrivial eigenvector at 
    each node (reconstructing the eigenvector for only the rows at that node).
    Returns a tree.
    """
    
    col_emd = dual_affinity.calc_emd(data,row_tree,alpha,beta)
    _,n = data.shape

    root = tree.ClusterTreeNode(range(n))
    queue = [root]

    while max([x.size for x in queue]) > 1:
        new_queue = []
        for node in queue:
            if node.size > 2:
                #cut it
                cut = bal_eigen_cut(node,col_emd,bal_constant)
                node.create_subclusters(cut)
            else:
                #make the singletons
                node.create_subclusters(np.arange(node.size))
            new_queue.extend(node.children)
        queue = new_queue

    root.make_index()                
    return root

def bal_cut(n,balance_constant):
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

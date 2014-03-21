"""
flex_tree_build.py: Functions for building flexible trees based on affinities
                    between points.
"""
import numpy as np
import markov
import tree
import scipy.spatial as spsp

class Cluster(object):
    """
    Cluster objects are just sets of elements, with a couple of methods 
    added for prettiness and usefulness. But you could just use sets instead.
    """
    def __init__(self,elements):
        self.elements = set(elements)
    
    @property
    def size(self):
        return len(self.elements)
    
    def __len__(self):
        return len(self.elements)
    
    
    def __repr__(self):
        return str(list(self.elements))
    
class Clustering(object):
    """
    A Clustering is a level of a tree, which clusters the level below it.
    So there are n nodes, which could be clusters at the lower level, and
    the Clustering object contains up to n Clusters that give the 
    hierarchical partition for the level.
    """
    def __init__(self,n):
        self.n = n
        self.cluster_lookup = {}
        for i in xrange(n):
            self.cluster_lookup[i] = i
        self._clusters = []
        for i in xrange(n):
            self._clusters.append(Cluster([i]))
    
    def __len__(self):
        return len([x for x in self._clusters if x.size > 0])
    
    def join_clusters(self,n1,n2):
        c1 = self._clusters[self.cluster_lookup[n1]]
        c2 = self._clusters[self.cluster_lookup[n2]]
        for x in c2.elements:
            self.cluster_lookup[x] = n1
        c1.elements = c1.elements.union(c2.elements)
        c2.elements = set([])
        
    def find(self,idx):
        return self._clusters[self.cluster_lookup[idx]]
    
    def test_join(self,edge_wt,e1,e2,penalty):
        c1 = self.find(e1)
        c2 = self.find(e2)
        pen_thres = penalty*(c1.size*c2.size-1)
        if edge_wt > pen_thres:
            self.join_clusters(e1, e2)
            return True
        else:
            return False

    def test_join_distance(self,dist,e1,e2,penalty):
        c1 = self.find(e1)
        c2 = self.find(e2)
        if c1.size + c2.size == 2:
            self.join_clusters(e1,e2)
            return True
        pen_thres = penalty*(2**(-c1.size*c2.size+1))
        if dist < pen_thres:
            self.join_clusters(e1, e2)
            return True
        else:
            return False

    @property
    def clusters(self):
        return [x for x in self._clusters if x.size > 0]

class ClusteringPartition(Clustering):
    def __init__(self,partition):
        """
        takes a list of lists and makes those the clusters.
        """
        self.n = sum([len(x) for x in partition])
        self._clusters = []
        self.cluster_lookup = {}
        for (idx,cluster) in enumerate(partition):
            self._clusters.append(Cluster(cluster))
            for element in cluster:
                self.cluster_lookup[element] = idx

def cluster_transform(diffusion,clustering):
    Q = np.zeros([len(clustering),diffusion.shape[0]],np.float)
    for (idx,center) in enumerate(clustering.clusters):
        Q[idx,np.array(list(center.elements))] = 1.0
    Qi = Q.T
    Q = markov.make_markov_row_stoch(Q)
    return Q.dot(diffusion).dot(Qi)

def cluster_transform_matrices(clustering):
    Q = np.zeros([len(clustering),clustering.n],np.float)
    for (idx,center) in enumerate(clustering.clusters):
        Q[idx,np.array(list(center.elements))] = 1.0
    Qi = Q.T
    Q = markov.make_markov_row_stoch(Q)
    return Q,Qi

def clusterlist_to_tree(cluster_list):

    n_leaves = sum([x.size for x in cluster_list[0].clusters])
    clusters = [tree.ClusterTreeNode([i]) for i in xrange(n_leaves)]
        
    for clustering in cluster_list:
        new_clusters = [tree.ClusterTreeNode([]) for i in xrange(len(clustering))]
        for (idx,cluster) in enumerate(clustering.clusters):
            for element in cluster.elements:
                clusters[element].assign_to_parent(new_clusters[idx])
        clusters = new_clusters
        
    if len(clusters) == 1:
        clusters[0].make_index()
        return clusters[0]
    else:
        root = tree.ClusterTreeNode([])
        for cluster in clusters:
            cluster.assign_to_parent(root)
        root.make_index()
        return root

def cluster_from_affinity(affinity,eps=1.0,threshold=1e-8):
    #print "eps: {}".format(eps)
    A = affinity.copy()
    A -= np.diag(np.diag(A))
    
    Alocs = np.argmax(A,axis=1)  #stores the location of the max entry in this row
    Amaxes = A[range(A.shape[0]),Alocs] #stores the max entry in this row
    
    penalty = np.median(A[A>threshold])*eps
    #print "penalty: {}".format(penalty)
    clustering = Clustering(affinity.shape[0])
    joins = 0
    while 1:
        row = np.argmax(Amaxes)
        col = Alocs[row]
        #print "row: {} col: {}".format(row,col)
        if Amaxes[row] <= penalty and joins > 0:
            break
        if clustering.test_join(A[row,col],row,col,penalty):
            Amaxes[row] = 0.0
            Amaxes[col] = 0.0
            joins += 1
        else:
            A[row,col] = 0.0
            Alocs[row] = np.argmax(A[row,:])
            Amaxes[row] = A[row,Alocs[row]]        
    return clustering

def cluster_from_distance(distance_matrix,eps=1.0):
    #print "eps: {}".format(eps)
    A = distance_matrix.copy()
    A += 999.0*np.eye(A.shape[0])
    
    Alocs = np.argmin(A,axis=1)  #stores the location of the min dist in row
    Amins = A[range(A.shape[0]),Alocs] #stores the min entry in this row
    
    med = np.median(A)
    penalty = np.median(A)/eps
    #print "penalty: {}".format(penalty)
    clustering = Clustering(A.shape[0])
    joins = 0
    while 1:
        row = np.argmin(Amins)
        col = Alocs[row]
        #print "row: {} col: {} dist: {}".format(row,col,Amins[row])
        if Amins[row] >= med and joins > 0:
            break
        if clustering.test_join_distance(A[row,col],row,col,penalty):
            Amins[row] = 999.0
            Amins[col] = 999.0
            joins += 1
        else:
            A[row,col] = 999.0
            Alocs[row] = np.argmin(A[row,:])
            Amins[row] = A[row,Alocs[row]]        
    return clustering

def flex_tree(affinity,penalty_constant,threshold=1e-8):
    """
    Takes affinity, a square matrix of positive entries representing an 
    affinity between n nodes, and creates a flexible tree based on 
    that affinity. This is *static* because it uses the same affinity 
    at all levels and doesn't compute a diffusion. All it does is join things
    based on their closeness (higher affinity). Cluster affinity to each other
    is the average affinity between elements.
    """ 
    #print "***starting***"
    q = np.eye(affinity.shape[0]) #initialize q for code brevity.
    cluster_list = []
    i=0
    while 1:
        #print "clustering at level {}".format(i)
        i+=1 
        new_affinity = q.dot(affinity).dot(q.T)
        cluster_list.append(cluster_from_affinity(new_affinity,
                                                  penalty_constant,
                                                  threshold))
        #print "clusters: {}".format(len(cluster_list[-1]))
        if len(cluster_list[-1]) == 1:
            break
        temp_tree = clusterlist_to_tree(cluster_list)
        cpart = ClusteringPartition([x.elements for x in temp_tree.dfs_level(2)])
        q,_ = cluster_transform_matrices(cpart)
    return clusterlist_to_tree(cluster_list)    

def flex_tree_diffusion(affinity,penalty_constant,n_eigs=12):
    """
    affinity is an nxn affinity matrix.
    Creates a flexible tree by calculating the diffusion on the given affinity.
    Then clusters at each level by the flexible tree algorithm. For each level
    up, doubles the diffusion time.
    penalty_constant is the multiplier of the median diffusion distance.
    """
    #First, we calculate the first n eigenvectors and eigenvalues of the 
    #diffusion
    cluster_list = []
    vecs,vals = markov.markov_eigs(affinity,n_eigs)
    diff_time = 1.0
    q = np.eye(affinity.shape[0])
    while 1:
        #now we calculate the diffusion distances between points at the 
        #current diffusion time.
        diff_vecs = vecs.dot(np.diag(vals**diff_time)) 
        diff_dists = spsp.distance.squareform(spsp.distance.pdist(diff_vecs))
        #we take the affinity between clusters to be the average diffusion 
        #distance between them.
        avg_dists = q.dot(diff_dists).dot(q.T)
        #now we cluster the points based on this distance
        cluster_list.append(cluster_from_distance(avg_dists,penalty_constant))
        #if there is only one node left, then we are done.
        #otherwise, add another level to the tree, double the diffusion time
        #and keep going.
        if len(cluster_list[-1]) == 1:
            break
        temp_tree = clusterlist_to_tree(cluster_list)
        cpart = ClusteringPartition([x.elements for x in temp_tree.dfs_level(2)])
        q,_ = cluster_transform_matrices(cpart)
        diff_time *= 2.0
    return clusterlist_to_tree(cluster_list)
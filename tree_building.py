import numpy as np
import markov
import tree

class Cluster(object):
    def __init__(self,elements):
        self.elements = set(elements)
    
    @property
    def size(self):
        return len(self.elements)
    
class Clustering(object):
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

def cluster_from_affinity(affinity,eps=1.0):
    #print "eps: {}".format(eps)
    A = affinity.copy()
    A -= np.diag(np.diag(A))
    
    Alocs = np.argmax(A,axis=1)  #stores the location of the max entry in this row
    Amaxes = A[range(A.shape[0]),Alocs] #stores the max entry in this row
    
    penalty = np.median(A[A>0.0])*eps
    #print "penalty: {}".format(penalty)
    clustering = Clustering(affinity.shape[0])
    joins = 0
    while 1:
        row = np.argmax(Amaxes)
        col = Alocs[row]
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

def make_tree_diffusion(affinity,penalty_constant):
    clusters_list = []
    A = markov.make_markov_symmetric(affinity)
    clusters = cluster_from_affinity(A,penalty_constant)
    while len(clusters) > 1:
        new_diff = cluster_transform(A,clusters)
        clusters_list.append(clusters)
        A = markov.make_markov_symmetric(new_diff.dot(new_diff.T))
        clusters = cluster_from_affinity(A,penalty_constant)
    return clusters

def make_tree_embedding(affinity,penalty_constant):
    q = np.eye(affinity.shape[0]) #initialize q for code brevity.
    cluster_list = []
    i=0
    while 1:
        #print "clustering at level {}".format(i)
        i+=1 
        new_affinity = q.dot(affinity).dot(q.T)
        cluster_list.append(cluster_from_affinity(new_affinity,penalty_constant))
        #print "clusters: {}".format(len(cluster_list[-1]))
        if len(cluster_list[-1]) == 1:
            break
        temp_tree = clusterlist_to_tree(cluster_list)
        cpart = ClusteringPartition([x.elements for x in temp_tree.dfs_level(2)])
        q,_ = cluster_transform_matrices(cpart)
    return clusterlist_to_tree(cluster_list)

def make_tree_embedding2(affinity,penalty_constant):
    q = np.eye(affinity.shape[0]) #initialize q for code brevity.
    cluster_list = []
    i=0
    new_affinity = affinity.copy()
    while 1:
        #print "clustering at level {}".format(i)
        i+=1 
        new_affinity = q.dot(new_affinity).dot(q.T)
        cluster_list.append(cluster_from_affinity(new_affinity,penalty_constant))
        #print "clusters: {}".format(len(cluster_list[-1]))
        if len(cluster_list[-1]) == 1:
            break
        temp_tree = clusterlist_to_tree(cluster_list)
        cpart = ClusteringPartition([x.elements for x in temp_tree.dfs_level(2)])
        q,_ = cluster_transform_matrices(cpart)
        new_affinity = new_affinity.dot(new_affinity.T)
    return clusterlist_to_tree(cluster_list)
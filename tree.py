"""
tree.py: Defines a tree structure for use in the questionnaire.
"""

import copy

class ClusterTreeNode(object):
    def __init__(self,elements,parent=None):
        self.parent = parent
        self.elements = sorted(set(elements))
        self.children = []
    
    def __getitem__(self,key):
        """
        Allows lookup of tree nodes by index, like row_tree[17].
        """
        return self.nodes_list[key]
    
    def __iter__(self):
        """
        Allows iteration of the tree without using traverse(), ie:
        for node in tree:
            <do whatever>
        """
        for x in self.nodes_list:
            yield x
            
    def __len__(self):
        return self.tree_size
    
    def iterkeys(self):
        return self.__iter__()
    
    def compare(self,other):
        """
        Compares this tree to a different tree. 
        Returns True if for every node x in this tree, the set of elements
        in x is equal to the set of elements in some node in the other tree.
        """  
        nodelists = [x.elements for x in other.traverse()]
        for node in self.nodes_list:
            if node.elements not in nodelists:
                return False
        return True
    
    def __eq__(self,other):
        return self.compare(other) and other.compare(self)
    
    def create_subclusters(self,partition):
        """
        Divides a tree node into pieces based on partition. 
        partition should be a group indicator for each element of the node.
        So partition should have the same length as self.elements.
        Useful for top-down clustering.
        """
        assert len(partition) == len(self.elements)
        p_elements = set(partition)
        for subcluster in sorted(p_elements):
            sc_elements = [x for (x,y) in zip(self.elements,partition) 
                           if y == subcluster]
            self.children.append(ClusterTreeNode(sc_elements,self))

    def assign_to_parent(self,parent):
        """
        Assigns a subcluster to a parent cluster.
        Will add the elements of self to the elements of parent if they
        are not already there.
        Useful for bottom-up clustering.
        """
        self.parent = parent
        parent.children.append(self)
        parent.elements.extend(self.elements)
        parent.elements = sorted(set(parent.elements))

    def traverse(self,floor_level=None):
        """
        Performs a BFS traversal of the tree.
        External use is deprecated now, use the iterator methods instead.
        Left here for compatibility reasons, may become a _ method later.
        Later note: okay to use for non-root nodes of the tree.
        """
        #BFS
        queue = []
        traversal = []
        queue.append(self)
        while len(queue) > 0:
            node = queue.pop(0)
            traversal.append(node)
            if floor_level is None:
                queue.extend(node.children)
            elif node.level <= floor_level - 1:
                queue.extend(node.children)
        traversal.sort(key=lambda x:x.level*1e10+min(x.elements))    
        return traversal
    
    def dfs_leaves(self):
        """
        Depth-first leaves search.
        Returns all nodes in depth-first search order.
        """
        traversal = []
        if len(self.children) == 0:
            traversal.append(self)
        else:
            for child in self.children:
                traversal.extend(child.dfs_leaves())
        return traversal

    def dfs_level(self,level=None):
        """
        Returns the set of all nodes at the level specified.
        Also accepts negative indices (so the bottom level is -1)
        """
        if level is None:
            level = self.tree_depth
        if level < 0:
            level = self.tree_depth + level
        traversal = []
        if self.level == level:
            traversal.append(self)
        else:
            for child in self.children:
                traversal.extend(child.dfs_level(level))
        return traversal
    
    def leaves(self):
        """
        Returns the set of all leaves.
        """
        leaves_list = []
        for node in self.nodes_list:
            if len(node.children) == 0:
                leaves_list.append(node)
        return leaves_list
    
    @property
    def tree_size(self):
        """
        Returns the total size of the tree rooted at this node.
        """
        if self.parent is None:
            return len([x for x in self.nodes_list])
        else:
            return len(self.traverse())

    @property
    def level(self):
        """
        Returns the level of the tree at which this node sits.
        Indexed starting at 1. This might be changed in the future.
        """
        if self.parent is None:
            return 1
        else:
            return 1+self.parent.level
    
    @property
    def tree_depth(self):
        """
        Returns the depth in levels of the tree rooted at this node.
        """
        if self.children == []:
            return 1
        else:
            return 1 + self.children[0].tree_depth
                        
    @property
    def size(self):
        """
        Returns the size of this node (in elements).
        """
        return len(self.elements)

    def sublevel_elements(self,level):
        """
        Returns a list of lists of the elements in level 
        """
        elist = []
        for x in self.nodes_list:
            if x.level + 1 - self.level == level:
                elist.append(x.elements)
        return elist
    
    def level_nodes(self,level=None):
        """
        Returns the set of all nodes at the level specified.
        Also accepts negative indices (so the bottom level is -1)
        """
        if level is None:
            level = self.tree_depth
        if level < 0:
            level = self.tree_depth + level
        return [x for x in self.nodes_list if x.level == level]
    
    def make_index(self):
        """
        Precalculates some things and makes the tree much easier to use.
        Needs to be called after tree construction is finished in all cases.
        """
        idx = 0
        self.nodes_list = self.traverse()
        for node in self.nodes_list:
            node.idx = idx
            idx += 1
            
    def disp_tree(self):
        """
        Prints out crude representation of tree structure by elements in folders.
        No return value.
        """
        for i in xrange(self.tree_depth):
            print i,self.sublevel_elements(i+1)
            
    def disp_tree_folder_sizes(self):
        """
        Prints out crude representation of tree structure by folder sizes.
        No return value.
        """
        for i in xrange(self.tree_depth):
            print i,sorted([len(x) for x in self.sublevel_elements(i+1)])
            
    def folder_set(self,element):
        """
        Returns the index set of all parents of element.
        """
        return [x.idx for x in self.nodes_list if element in x.elements]
    
    def level_partition(self,level):
        """
        Returns the entire partition of the tree at the specified level
        as an array of tree.size with the index of the partition containing
        a particular point in each position.
        """
        partition = [0]*self.size
        els = self.sublevel_elements(level)
        for (idx,l) in enumerate(els):
            for m in l:
                partition[m] = idx
        return partition
    
    def all_ancestors(self):
        """
        Returns a list of the indices of all the ancestors of a given node.
        """
        curnode = self
        parents = []
        while curnode.parent is not None:
            parents.append(curnode.parent.idx)
            curnode = curnode.parent
        return parents
    
    def all_descendants(self):
        """
        Returns a list of the indices of all the descendants of a given node.
        """
        if len(self.children) == 0:
            return []
        else:
            return [x.idx for x in self.traverse()[1:]]

    def tree_distance(self,i,j):
        """
        Returns the tree distance between elements i and j.
        """
        if i==j:
            return 0.0
                
        curnode = self
        while curnode.parent is not None:
            curnode = curnode.parent
        tree_size = curnode.size
        if i in self.elements and j in self.elements:
            for child in self.children:
                if i in child.elements and j in child.elements:
                    return child.tree_distance(i,j)
            return 1.0*self.size/tree_size
    
    def copy(self):
        return copy.deepcopy(self)

def dyadic_tree(n):
    """
    Generates the basic dyadic tree on 2**n elements
    """
    elements = range(2**n)
    tree_list = [ClusterTreeNode([element]) for element in elements]
    tree_list2 = []

    for _ in xrange(n):
        while len(tree_list) > 0:
            tree_list2.append(ClusterTreeNode([]))
            tree_list[0].assign_to_parent(tree_list2[-1])
            tree_list[1].assign_to_parent(tree_list2[-1])
            tree_list = tree_list[2:]
        tree_list = tree_list2
        tree_list2 = []

    tree_list[0].make_index()

    return tree_list[0]
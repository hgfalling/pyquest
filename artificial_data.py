"""
implements a multi-scale Gaussian mixture model for
generating artificial 2D data.
"""

import numpy as np
import tree
import random

#ok what are we going to do.
#suppose we have N people and K basic profiles.
#what's a profile? it's a set of basic answers to a question class.

#so for each person we will do the following:
#pick a profile 1->K
#then pick noise levels up the chain.

#so say we have 64 people, and we want 4 basic people profiles.
#about 16 end up in each category.
#so they each have a pure profile.
#now we want to further subdivide them into some # of groups
#and put some noise on those groups.
#so we assign them each a subgroup, and pick gaussian noise for each subgroup
#then we keep going until there are no more divisions possible.

def make_profile(profile_index,n_questions,means):
    radix = len(means)
    digits = [means[(profile_index / (radix**i)) % radix] for i in xrange(n_questions)]
    return tuple(digits)

class ProbabilityField(object):
    def __init__(self,means_matrix):
        assert np.sum(means_matrix > 1.0) == 0
        assert np.sum(means_matrix < 0.0) == 0
        self.means = means_matrix

    def permute(self):
        if self.means.ndim == 1:
            np.random.shuffle(self.means)
        else:
            assert self.means.ndim == 2
            np.random.shuffle(self.means)
            np.random.shuffle(self.means.T)
    
    def realize(self):
        r = np.random.rand(*self.means.shape)
        data = -1*np.ones(self.means.shape)
        data += 2*(r < self.means)
        return data

class ArtificialQuestionnaire(object):
    
    mean_choices = None
    question_count = None
    question_levels = []
    question_noise_base = 0.01
    question_noise_alpha = 0.25
    
    people_count = None
    people_levels = []
    people_noise_base = 0.01
    people_noise_alpha = 0.25
    
    def __init__(self,**kwargs):
        sqrt_flag= False
        for key,val in kwargs.items():
            if hasattr(self,key):
                setattr(self,key,val)
            if key == "sqrt":
                sqrt_flag = val
        if self.make_trees(sqrt_flag):
            self.gen_means()

    def _verify(self):
        if self.mean_choices is None:
            return False
        if self.question_count is None:
            return False
        if self.question_levels == []:
            return False
        if self.people_count is None:
            return False
        if self.people_levels == []:
            return False
        return True
    
    def make_trees(self,sqrt_flag=False):
        if self._verify():
            people_tree = tree.ClusterTreeNode(range(self.people_count))
            for idx,level in enumerate(self.people_levels):
                for y in people_tree.dfs_level(idx+1):
                    if level == 0:
                        y.create_subclusters(range(y.size))
                    else:
                        if sqrt_flag:
                            y.create_subclusters(np.sqrt(np.random.randint(0,level**2,size=y.size)).astype(np.int))
                        else:
                            y.create_subclusters(np.random.randint(0,level,size=y.size))
            people_tree.make_index()
            
            question_tree = tree.ClusterTreeNode(range(self.question_count))
            for idx,level in enumerate(self.question_levels):
                for y in question_tree.dfs_level(idx+1):
                    if level == 0:
                        y.create_subclusters(range(y.size))
                    else:
                        if sqrt_flag:
                            y.create_subclusters(np.sqrt(np.random.randint(0,level**2,size=y.size)).astype(np.int))
                        else:
                            y.create_subclusters(np.random.randint(0,level,size=y.size))
            question_tree.make_index()

            self.question_tree = question_tree
            self.people_tree = people_tree
            return True
        else:
            print "couldn't make trees, some data missing..."
            return False

    def gen_means(self):
        people_profiles = len(self.people_tree.dfs_level(2))
        question_profiles = len(self.question_tree.dfs_level(2))
        
        for node in self.people_tree:
            people_noise_var = self.people_noise_base*(self.people_noise_alpha**(node.level-2))
            if node.idx == 0:
                node.noise = np.zeros(question_profiles)
            else:
                node.noise = np.random.multivariate_normal(np.zeros(question_profiles,np.float),np.eye(question_profiles)*people_noise_var)
            if node.level == 1:
                node.mean = np.zeros(question_profiles)
            elif node.level == 2:
                max_profile = len(self.mean_choices)**question_profiles
                bits = len(bin(max_profile))
                node.profile = random.getrandbits(bits)
                while node.profile > max_profile:
                    node.profile = random.getrandbits(bits)
                node.mean = np.array(make_profile(node.profile,question_profiles,self.mean_choices))
            else:
                node.mean = node.parent.mean + node.noise
        
        people_means = np.vstack([node.mean for node in self.people_tree.leaves()]).T
        
        for node in self.question_tree:
            question_noise_var = self.question_noise_base*(self.question_noise_alpha**(node.level-2))
            if node.idx == 0:
                node.noise = np.zeros(people_profiles)
            else:
                node.noise = np.random.multivariate_normal(np.zeros(people_profiles,np.float),np.eye(people_profiles)*question_noise_var)
            if node.level == 1:
                node.mean = np.zeros(people_profiles)
            else:
                node.mean = node.parent.mean + node.noise
        
        question_noise = np.vstack([node.mean for node in self.question_tree.leaves()])
        
        self.means = np.zeros([self.question_count,self.people_count])
        
        for question in self.question_tree.dfs_level(2):
            self.means[question.elements,:] = people_means[question.idx-1,:]
        for person in self.people_tree.dfs_level(2):
            self.means[:,person.elements] += np.tile(question_noise[:,person.idx-1],(len(person.elements),1)).T
        
        self.data = self.means.copy()
        self.data = self.data*2 - 1.0
        self.data[self.data > 1.0] = 1.0
        self.data[self.data < -1.0] = -1.0

    def realize(self):
        data = np.zeros(self.means.shape)
        r = np.random.rand(*self.means.shape)
        data[r<self.means] = 1.0
        data[data==0] = -1.0
        return data
    
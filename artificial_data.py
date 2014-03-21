"""
artificial_data.py: short implementation of a probability field of binary 
                    questionnaire type.
"""

import numpy as np

class ProbabilityField(object):
    def __init__(self,means_matrix):
        assert np.sum(means_matrix > 1.0) == 0
        assert np.sum(means_matrix < 0.0) == 0
        self.means = means_matrix

    def realize(self):
        r = np.random.rand(*self.means.shape)
        data = -1*np.ones(self.means.shape)
        data += 2*(r < self.means)
        return data
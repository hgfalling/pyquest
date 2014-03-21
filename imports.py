"""
includes imports commonly used in questionnaire process, and a couple of 
useful functions.
"""

""" TO BE CLEANED: """
import viewer_files

""" CLEAN: """
#builtin imports
import contextlib
import cPickle
import itertools
import numpy as np
import scipy as sp

import affinity
import artificial_data
import barcode
import bin_tree_build
import dual_affinity
import flex_tree_build
import haar
import markov
import question_tree
import questionnaire
import tree
import tree_recon
import tree_util

from plot_utils import *

def write_data_file(filename,*args,**kwargs):
    """
    Writes a data file in the numpy compressed format.
    filename is the filename to be written.
    kwargs contains the names of variables in the written file and their values.
    """
    
    fout = open(filename,"wb")
    np.savez_compressed(fout,*args,**kwargs)
    fout.close()
    
@contextlib.contextmanager
def printoptions(*args,**kwargs):
    """
    A short context manager to control numpy options.
    I typically use it like this:
    with printoptions(precision=3):
        print some matrix
    Then this will print a numpy matrix with only 3 digits of precision.
    """ 
    original = np.get_printoptions()
    np.set_printoptions(*args,**kwargs)
    yield
    np.set_printoptions(**original)
    
    
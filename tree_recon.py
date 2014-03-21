"""
tree_recon.py: Functions for reconstruction of functions from given trees.
"""

import numpy as np
import haar

def shrink_coefs(coefs,t):
    """
    Shrinks coefficients toward 0 with a soft threshold of t.
    That is, if |c| < t, set to zero. Otherwise, move it by t toward 0.
    """
    return np.sign(coefs)*(np.abs(coefs) - t)*(np.abs(coefs) > t)

def recon_2d_haar_folder_size(data,row_tree,col_tree,threshold=0.0):
    """
    Reconstruction of a function in two variables (data) by the following:
    Find the bi-Haar expansion of data in terms of the row_tree/col_tree
    basis. Then set all coefficients corresponding to folders of
    size < threshold to 0.0, and perform the inverse transform.
    """
    coefs, folder_sizes = haar.bihaar_transform(data,row_tree,col_tree,True)
    coefs[folder_sizes < threshold] = 0.0
    return haar.inverse_bihaar_transform(coefs,row_tree,col_tree)

def threshold_recon(data,min_val,max_val):
    """
    Truncates a matrix by setting everything less than min_val to min_val and
    everything greater than max_val to max_val.
    """
    data[data < min_val] = min_val
    data[data > max_val] = max_val
    return data

def sure(haar_coefs,t,estimated_var=1.0):
    """
    Calculates Stein's unbiased risk estimator for some set of coefficients
    and some threshold t.
    """
    term1 = len(haar_coefs)
    term2 = 2*(np.sum(np.abs(haar_coefs) <= t))
    term3 = np.sum(np.minimum(np.abs(haar_coefs),t)**2)
    return estimated_var*(term1 - term2) + term3,(term1,term2,term3)

def recon_1d_sure(data,tree,estimated_var=1.0):
    """
    Reconstruction of a function in one dimension using SURE wavelet shrinkage.
    """
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
    """
    Reconstruction of a function in two dimensions using SURE wavelet shrinkage.
    """
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
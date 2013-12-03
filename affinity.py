import numpy as np
import scipy.spatial as spsp
import sklearn.neighbors as sknn

def _norm_ip_abs_aff(data):
    """
    data: mxn numpy array.
    
    Treats columns of data as functions on R^m. values are expected to be 1/-1.
    Calculates affinity between columns of data as absolute value of inner
    product between columns divided by number of entries non-zero in both 
    columns.
    Returns nxn symmetric matrix of affinities on [0,1]
    """
    
    inner_products = data.T.dot(data)
    temp = np.abs(data)
    norm_constants = temp.T.dot(temp) + 1e-14
    
    return np.abs(inner_products) / norm_constants

def mutual_cosine_similarity(data, take_abs=False,no_data_value=None,threshold=0.0):
    """
    data: mxn numpy array.
    
    Treats columns of data as functions on R^m. 
    Calculates affinity between columns of data as cosine similarity between 
    columns, floored at 0 if take_abs == False, otherwise the absolute value. 
    If either vector has a value == no_data_value, then that dimension is 
    ignored. Automatically treats np.nan as no_data_value.
    Returns nxn symmetric matrix of affinities on [0,1]
    """
    
    mask = np.logical_or(np.isnan(data),data==no_data_value)
    madata = np.ma.MaskedArray(data,mask)
    
    valid = np.ones(np.shape(data)) * np.logical_not(madata.mask)
     
    inner_products = np.ma.dot(madata.T,madata)
    madata = madata**2
    ji_norm = np.ma.dot(valid.T,madata)
    ij_norm = np.ma.dot(madata.T,valid)
    mcs = inner_products/np.sqrt(ij_norm*ji_norm)
    
    if take_abs:
        return np.abs(np.array(mcs))
    else:
        if threshold is None:
            return np.array(mcs)
        else:
            mcs[mcs < threshold] = 0.0
            return np.array(mcs)

def cosine_similarity(data, take_abs=False):
    """
    data: mxn numpy array.
    
    Treats columns of data as functions on R^m. 
    Calculates affinity between columns of data as cosine similarity between 
    columns, floored at 0 if take_abs == False, otherwise the absolute value. 
    Counts 0 as a data value.
    Returns nxn symmetric matrix of affinities on [0,1]
    """

    norms = np.sqrt(np.sum(data**2,axis=0))
    inner_products = (data/norms).T.dot(data/norms)
    
    if take_abs:
        return np.abs(inner_products)
    else:
        inner_products[inner_products < 0.0] = 0.0
        return inner_products

def correlation(data, take_abs=False):
    """
    data: mxn numpy array.
    
    Treats columns of data as functions on R^m. values are expected to be 1/-1.
    Calculates affinity between columns of data as cosine similarity between 
    columns, floored at 0. Counts 0 as a data value.
    Returns nxn symmetric matrix of affinities on [0,1]
    """

    data2 = remove_mean(data)
    return cosine_similarity(data2,take_abs)

def remove_mean(data):
    """
    data : mxn numpy ARRAY
    
    Returns data, with the mean of each column subtracted.
    """
    
    means = np.mean(data,axis=0)
    return data - means

def gaussian_euclidean(data,knn=5,eps=1.0):
    row_distances = spsp.distance.squareform(spsp.distance.pdist(data))
    nn = sknn.NearestNeighbors(n_neighbors=knn)
    nn.fit(data)
    dists,_ = nn.kneighbors(data,knn,True)
    print dists[0:10]
    medians = eps*np.median(dists,1)
    return np.exp(-(row_distances**2/(medians**2)))

        



    
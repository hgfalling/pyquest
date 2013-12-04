import numpy as np
import scipy.optimize
import scipy.stats as spst

_h_test_dict = {}

def wnc_dist(n_parent,k_parent,n_child,t):
    
    m1 = k_parent
    m2 = n_parent - k_parent
    
    f = np.zeros([n_child+1,n_child+1])
    f[0,0] = 1.0
    for n in xrange(1,n_child+1):
        for k in xrange(n+1):
            w1 = 1.0*(t*(m1-k+1))/(t*(m1-k+1)+m2+k-n)
            w2 = 1.0*(m2+k-n+1)/(t*(m1-k)+m2+k-n+1)
            if k==0:
                f[n,k] = w2*f[n-1,k]
            else:
                f[n,k] = w1*f[n-1,k-1] + w2*f[n-1,k]
    return f[-1,:]

def wnc_mean(n_parent,k_parent,n_child,t):
    f = lambda x: 1.0/k_parent*x + (1 - (n_child - 1.0*x)/(n_parent-k_parent))**t - 1
    f_prime = lambda x: 1.0/k_parent + (1.0/(n_parent-k_parent))*(t)*((n_child-x)/(n_parent-k_parent))**(t-1.0)
    try:
        result = scipy.optimize.newton(f,((t/(1+t))*k_parent/n_parent),f_prime,maxiter=200)
    except:
        result = scipy.optimize.brentq(f,0,n_child)
    finally:
        return result

def hg_p_value(n_parent,k_parent,n_child,k_child):
    """
    one-tailed hypothesis test.
    H0: The partition is random.
    """
    hg = spst.hypergeom(n_parent,k_parent,n_child)
    parent_mean = n_child*(k_parent*1.0/n_parent)
    
    if k_child <= parent_mean:
        #then we want to know what the probability is
        #that we would observe a result as extreme as this one.
        return max(0.0,hg.cdf(k_child))
    else:
        return max(1-hg.cdf(k_child-1),0.0)    

def partition_htest_value(n_parent,k_parent,n_child,k_child,alpha,cache=False):
    """
    tests a partition of k_parent +1s in n_parent (+1/-1)s.
    Returns (min,max) which are endpoints of (1-alpha)% 
    confidence interval for H0 = partition is random.
    """
    if n_child == 1:
        if 1.0*k_parent/n_parent < alpha/2.0 and k_parent == 1:
            return True
        elif 1.0*k_parent/n_parent > 1-alpha/2.0 and k_parent == 0:
            return True
        else:
            return False
    
    if cache==False:
        hg = spst.hypergeom(n_parent,k_parent,n_child)
        c = hg.cdf([k_child-1,k_child])
        #okay, so c is the cdf INCLUDING k.
        #if that's greater than alpha/2, then we throw away the coeff.
        #if that's less than 1-alpha/2 we don't know. But if the cdf for one
        #less is less than 1-alpha/2, we throw away the coeff.  
        return not ((c[1] > alpha/2.0) and (c[0] < (1.0-alpha/2.0)))
    else:
        hgt = (n_parent,k_parent,n_child,alpha)
        print hgt
        if hgt in _h_test_dict:
            left,right = _h_test_dict[hgt]
            print "saved one"
        else:
            left,right = partition_htest(*hgt)
            _h_test_dict[hgt] = (left,right)
        if left == -1 and right == -1:
            return False
        elif left == -1 and k_child > right:
            return True
        elif k_child < left and right == -1:
            return True
        elif k_child < left or k_child > right:
            return True
        else:
            return False
        
joint_cache = {}

def _jd_at_once(n1,k1,n2,k2,n3):
    if (n1,k1,n2,k2,n3) in joint_cache:
        return joint_cache[(n1,k1,n2,k2,n3)] 
    hg1 = spst.hypergeom(n1,k1,n3)
    hg2 = spst.hypergeom(n2,k2,n3)
    range1 = np.arange(0,min(n3+1,k1+1))
    range2 = np.arange(0,min(n3+1,k2+1))
    #print range1,range2
    if k1 == 0:
        pmf1 = np.zeros(len(range1))
        pmf1[0] = 1.0
    else:
        pmf1 = hg1.pmf(range1)
    if k2 == 0:
        pmf2 = np.zeros(len(range2))
        pmf2[0] = 1.0
    else:
        pmf2 = hg2.pmf(range2)
    #print pmf1,pmf2
    jpmf = np.outer(pmf1,pmf2)
    mrange1 = np.minimum.outer(range1,range2)
    mrange0 = np.minimum.outer(n3-range1,n3-range2)
    #print mrange1
    #print mrange0
    no_ops = np.logical_and(mrange1==0,mrange0==0)
    #print no_ops
    jpmf[no_ops] = 0.0
    jpmf/=np.sum(jpmf)
    joint_cache[(n1,k1,n2,k2,n3)] = (jpmf,mrange1,mrange0)
    return jpmf, mrange1, mrange0

def jd_at_once(n1,k1,n2,k2,n3,show=False):
    print "jdatonce: {} {} {} {} {}".format(n1,k1,n2,k2,n3)
    p_matrix = np.zeros([n3+1,n3+1])
    jpmf,mrange1,mrange0 = _jd_at_once(n1,k1,n2,k2,n3)
    if show:
        print "jpmf:"
        print jpmf
    for i in xrange(jpmf.shape[0]):
        for j in xrange(jpmf.shape[1]):
            if show:
                print "allocating {}".format(jpmf[i,j])
            #print i,j, jpmf[i,j]
            
            if jpmf[i,j] < 1e-15:
                continue
            
            new_n3 = n3 - mrange1[i,j] - mrange0[i,j]
            
            if new_n3 == 0:
                p_matrix[mrange1[i,j],mrange0[i,j]] += jpmf[i,j]
                if show:
                    print "p_matrix"
                    print p_matrix
                continue
            
            new_n1 = n1 - mrange1[i,j] - mrange0[i,j]
            new_k1 = k1 - mrange1[i,j]
            new_n2 = n2 - mrange1[i,j] - mrange0[i,j]
            new_k2 = k2 - mrange1[i,j]
            p_matrix[mrange1[i,j]:mrange1[i,j]+new_n3+1,mrange0[i,j]:mrange0[i,j]+new_n3+1] += jpmf[i,j]*jd_at_once(new_n1,new_k1,new_n2,new_k2,new_n3)
            if show:
                print "p_matrix"
                print p_matrix
    return p_matrix 


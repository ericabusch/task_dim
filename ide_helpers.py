import numpy as np
from sklearn.metrics import pairwise_distances
from skdim import id
import tphate
from numpy import linalg
from scipy.linalg import svd
from sklearn.decomposition import PCA
      
def diffop_eig_ide(X, threshold=0.9, knn=5):
    eigenvalues, _ = np.linalg.eig(X)
    eigenvalues = eigenvalues[1:] 
    # sort eigenvalues, keep real components
    sorted_eigenvalues = np.real(np.sort(eigenvalues)[::-1])
    # retain only positive
    # discard negatives & the first eigenvalue
    sorted_eigenvalues = sorted_eigenvalues[sorted_eigenvalues>0]
    explained_variance_ratio = sorted_eigenvalues / np.sum(sorted_eigenvalues)
    cumulative_variance = np.cumsum(explained_variance_ratio)
    n = np.where(cumulative_variance>threshold)[0][0]+1
    return n

def compute_tphate_optt(X, threshold=0.9,knn=5):
    tph=tphate.TPHATE(verbose=0, knn=knn)
    _=tph.fit_transform(X)
    return tph.optimal_t

def compute_tphate_ide(X, threshold=0.9,knn=5):
    tph=tphate.TPHATE(verbose=0, knn=knn)
    tph.fit(X)
    return diffop_eig_ide(tph.diff_op, threshold)

def compute_PCA_dim(X, threshold=0.9, knn=5):
    pca = PCA()
    pca.fit(X)
    cum_var_exp = np.cumsum(pca.explained_variance_ratio_)
    return np.where(cum_var_exp >= threshold)[0][0]

def compute_MiND_ML(X, threshold=0.9, knn=5):
    mod = id.MiND_ML()
    return mod.fit_transform(X)

def compute_MLE(X, threshold=0.9, knn=5):
    mod = id.MLE()
    return mod.fit_transform(X)

def compute_KNN(X, threshold=0.9, knn=5):
    mod = id.KNN()
    return mod.fit_transform(X)

def compute_FisherS(X, threshold=0.9, knn=5):
    mod = id.FisherS()
    return mod.fit_transform(X)

def compute_lPCA(X, threshold=0.9, knn=5):
    mod = id.lPCA()
    return mod.fit_transform(X)

def compute_CorrInt(X, threshold=0.9, knn=5):
    mod = id.CorrInt()
    return mod.fit_transform(X)

def compute_tphate_dim(X, threshold=0.9, knn=5):
    tph = tphate.TPHATE(verbose=0, knn=knn).fit(X)
    entropy = compute_vne_curve(tph.diff_op, tmax=100)
    loc = find_elbow_point(entropy)
    return loc

def compute_phate_dim(X, threshold=0.9, knn=5):
    ph=tphate.TPHATE(verbose=0, knn=knn).fit(X)
    entropy = compute_vne_curve(ph.phate_diffop, tmax=100)
    loc = find_elbow_point(entropy)
    return loc

def compute_vne_curve(X, tmax=100):
    eigenvalues, _ = np.linalg.eig(X)
    entropy=np.empty(tmax)
    eigenvalues_t = np.copy(eigenvalues)
    for i in range(tmax):
        prob = eigenvalues_t / np.sum(eigenvalues_t)
        prob += np.finfo(float).eps
        entropy[i] = -np.sum(prob*np.log(prob))
        eigenvalues_t *= eigenvalues
    return entropy

def find_elbow_point(y, x=None):
    if x == None:
        x = np.arange(len(y))
    if not x.shape == y.shape:
        raise ValueError('x and y must be same shape')
    # assure they are sorted
    idx = np.argsort(x)
    x=x[idx]
    y=y[idx]
    n=np.arange(2,len(y)+1).astype(np.float32)
    
    # figure out the slope (M) and intercept (B) for left of elbow
    sigma_xy = np.cumsum(x*y)[1:]
    sigma_x = np.cumsum(x)[1:]
    sigma_y=np.cumsum(y)[1:]
    sigma_xx=np.cumsum(x*x)[1:]
    det = n*sigma_xx - sigma_x*sigma_x
    mfwd = (n*sigma_xy - sigma_x*sigma_y) / det
    bfwd = -(sigma_x * sigma_xy - sigma_xx * sigma_y) / det
    
    # figure out the slope (M) and intercept (B) for right of elbow
    x_rev, y_rev = x[::-1], y[::-1] 
    sigma_xy = np.cumsum(x_rev * y_rev )[1:]
    sigma_x = np.cumsum(x_rev)[1:]
    sigma_y = np.cumsum(y_rev)[1:]
    sigma_xx = np.cumsum(x_rev * x_rev)[1:]
    det = n * sigma_xx - sigma_x * sigma_x
    mbkwd = ((n * sigma_xy - sigma_x * sigma_y) / det)[::-1]
    bbkwd = (-(sigma_x * sigma_xy - sigma_xx * sigma_y) / det)[::-1]
    
    # figure out sum of per-point errors for left and right of knee fits
    error_curve = np.full_like(y,np.nan)
    for breakpt in np.arange(1,len(y)-1):
        delsfwd = (mfwd[breakpt - 1] * x[:breakpt+1] + bfwd[breakpt - 1]) - y[:breakpt+1]
        delsbkwd = (mbkwd[breakpt - 1] * x[breakpt:] + bbkwd[breakpt - 1]) - y[breakpt:]
        error_curve[breakpt] = np.sum(np.abs(delsfwd))+np.sum(np.abs(delsbkwd))
    # find the min of the error curve
    loc = np.argmin(error_curve[1:-1])+1
    return x[loc] 

METHODS = {'TPHATE_DiffOp_IDE':compute_tphate_ide,
           'TPHATE_VNE_IDE': compute_tphate_dim,
           'PHATE_VNE_IDE':compute_phate_dim,
          'MiND_ML':compute_MiND_ML, 
          'MLE': compute_MLE, 
          #'KNN': compute_KNN,
          'FisherS':compute_FisherS, 
          #'CorrInt':compute_CorrInt, 
          'lPCA':compute_lPCA,
           'PCA':compute_PCA_dim,
          }

METHOD_NAMES = sorted(METHODS.keys())

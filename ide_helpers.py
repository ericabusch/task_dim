import numpy as np
from sklearn.metrics import pairwise_distances
from skdim import id
import tphate
from numpy import linalg
from scipy.linalg import svd
from sklearn.decomposition import PCA
      
def diffop_eig_ide(X, threshold=0.9):
    eigenvalues, _ = np.linalg.eig(X)
    sorted_eigenvalues = np.real(np.sort(eigenvalues)[::-1])
    explained_variance_ratio = sorted_eigenvalues / np.sum(sorted_eigenvalues)
    cumulative_variance = np.cumsum(explained_variance_ratio)
    n = np.where(cumulative_variance>threshold)[0][0]+1
    return n

def compute_tphate_ide(X, threshold=0.9,knn=5):
    tph=tphate.TPHATE(verbose=0, knn=knn)
    tph.fit(X)
    if tph.dropoff == 1:
        print('found no autocorr; looking over a broader window')
        tph=tphate.TPHATE(verbose=0, knn=knn, smooth_window=4)
        tph.fit(X)
        print(f'AC is now {tph.dropoff}; continuing')
    D=tph.diff_op
    return diffop_eig_ide(D, threshold)

def compute_phate_ide(X, threshold=0.9, knn=5):
    tph=tphate.TPHATE(verbose=0, knn=knn)
    tph.fit(X)
    D=tph.phate_diffop
    return diffop_eig_ide(D, threshold)

def compute_PCA_dim(X, threshold=0.9, knn=5):
    pca = PCA()
    pca.fit(X)
    cum_var_exp = np.cumsum(pca.explained_variance_ratio_)
    return np.where(cum_var_exp > threshold)[0][0]+1

def compute_MiND_ML(X, threshold=0.9, knn=5):
    mod = id.MiND_ML()
    return mod.fit_transform(X)

def compute_MLE(X, threshold=0.9, knn=5):
    mod = id.MLE()
    return mod.fit_transform(X)

def compute_lPCA(X, threshold=0.9, knn=5):
    mod = id.lPCA()
    return mod.fit_transform(X)


METHODS = {'TPHATE_DiffOp_IDE':compute_tphate_ide,
           "PHATE_DiffOp_IDE":compute_phate_ide,
          'MiND_ML':compute_MiND_ML, 
          'MLE': compute_MLE, 
          'lPCA':compute_lPCA,
           'PCA':compute_PCA_dim,
          }

METHOD_NAMES = sorted(METHODS.keys())

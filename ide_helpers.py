import numpy as np
from sklearn.metrics import pairwise_distances
from skdim import id
import phate, tphate
from numpy import linalg
from sklearn.decomposition import PCA
      
def diffop_eig_ide(P, threshold=0.9, knn=5):
    eigvals, _ = np.linalg.eig(P)
    eigvals_sorted=np.squeeze(sorted((eigvals))[::-1])
    eig_norm=eigvals_sorted/np.sum(eigvals_sorted)
    i=np.where(np.cumsum(eig_norm) >= threshold)[0][0]+1
    return i

def compute_tphate_phate_ide(X, threshold=0.9, knn=5):
    tph=tphate.TPHATE(verbose=0,knn=knn)
    y=tph.fit_transform(X)
    tph_eigh_i = diffop_eig_ide(tph.diff_op,threshold)
    ph_eigh_i = diffop_eig_ide(tph.phate_diffop,threshold)
    return tph_eigh_i, ph_eigh_i, tph.optimal_t

def other_eig_diffop(P, threshold=0.9, knn=5, eps=1e-3):
    eigvals, _ = np.linalg.eig(P)
    eigvals = eigvals[eigvals>eps]
    eigvals_sorted=np.squeeze(sorted((eigvals))[::-1])
    eig_norm=eigvals_sorted/np.sum(eigvals_sorted)
    i=np.where(np.cumsum(eig_norm) >= threshold)[0][0]+1
    return i

def compute_tphate_ide(X,threshold=0.9,knn=5):
    tph=tphate.TPHATE(verbose=0,knn=knn)
    y=tph.fit_transform(X)
    if tph.dropoff==1:
        return tph.optimal_t
    else:
        return diffop_eig_ide(tph.diff_op,threshold)

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

def compute_tphate_t(X, threshold=0.9, knn=5):
    tph=tphate.TPHATE(verbose=0, knn=knn)
    y=tph.fit_transform(X)
    return tph.optimal_t

METHODS = {'TPHATE_DiffOp_IDE':compute_tphate_ide,
          'MiND_ML':compute_MiND_ML, 
          'MLE': compute_MLE, 
          #'KNN': compute_KNN,
          'FisherS':compute_FisherS, 
          #'CorrInt':compute_CorrInt, 
          'lPCA':compute_lPCA,
           'PCA':compute_PCA_dim,
           'TPHATE_optt':compute_tphate_t
          }

METHOD_NAMES = sorted(METHODS.keys())

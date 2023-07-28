import numpy as np
from sklearn.metrics import pairwise_distances
from skdim import id
import phate, tphate
from numpy import linalg

def compute_diffusion_matrix(X : np.array, knn: int=5, density_norm_pow: float = 1.0):
    """
    Adapted from
    https://github.com/professorwug/diffusion_curvature/blob/master/diffusion_curvature/core.py

    Given input X returns a diffusion matrix P, as an numpy ndarray.
    Using "adaptive anisotropic" kernel
    Inputs:
        X: a numpy array of size n x d
        k: k-nearest-neighbor parameter
        density_norm_pow: a float in [0, 1]
            == 0: classic Gaussian kernel
            == 1: completely removes density and provides a geometric equivalent to
                  uniform sampling of the underlying manifold
    Returns:
        P: a numpy array of size n x n that is the diffusion matrix
    """
    # Construct the distance matrix.
    D = pairwise_distances(X)

    # In case N <= K
    assert X.shape[0] > 1
    k = min(knn, X.shape[0] - 1)

    # Get the distance to the k-th neighbor.
    distance_to_k_neighbor = np.partition(D, k)[:, k]

    # Populate matrices with this distance for easy division.
    div1 = np.ones(len(D))[:, None] @ distance_to_k_neighbor[None, :]
    div2 = distance_to_k_neighbor[:, None] @ np.ones(len(D))[None, :]

    # Compute the gaussian kernel with an adaptive bandwidth
    W = (1 / np.sqrt(2 * np.pi)) * (np.exp(-D**2 / (2 * div1**2)) / div1 +
                                    np.exp(-D**2 / (2 * div2**2)) / div2)

    # Anisotropic density normalization.
    if density_norm_pow > 0:
        Deg = np.diag(1 / np.sum(W, axis=1)**density_norm_pow)
        W = Deg @ W @ Deg

    # Turn affinity matrix into diffusion matrix.
    Deg = np.diag(1 / np.sum(W, axis=1))
    P = Deg @ W

    return P

def compute_phate_diffusion_operator(X, knn=5, t=0):
    if t == 0: t = 'auto'
    op = phate.PHATE(verbose=0, knn=knn, t=t)
    y = op.fit_transform(X)
    print('phate t: ',op.optimal_t)
    return op.diff_op

def compute_tphate_diffusion_operator(X, knn=5, t=0):
    if t == 0: t = 'auto'
    op = tphate.TPHATE(verbose=0, knn=knn, t=t)
    y = op.fit_transform(X)
    print('tphate t: ',op.optimal_t)
    return op.diff_op


def spectral_entropy(P, eps=1e-3):
    eigenvalues, _ = np.linalg.eig(P)
    # Drop the trivial eigenvalue corresponding to the indicator eigenvector.
    eigenvalues = np.abs(np.array(sorted(eigenvalues)[::-1])[1:])
    # Drop the close-to-zero eigenvalue(s).
    eigenvalues = eigenvalues[eigenvalues >= eps]
    normalized_eigenvalues = eigenvalues / np.sum(eigenvalues)
    entropy = -np.sum(normalized_eigenvalues * np.log(normalized_eigenvalues))
    return entropy

def compute_phate_SE(X):
    P = compute_phate_diffusion_operator(X)
    ide = spectral_entropy(P)
    return ide

def compute_tphate_SE(X):
    P = compute_tphate_diffusion_operator(X)
    ide = spectral_entropy(P)
    return ide

def compute_diffusion_matrix_SE(X):
    P = compute_diffusion_matrix(X)
    ide = spectral_entropy(P)
    return ide

def compute_MiND_ML(X):
    mod = id.MiND_ML()
    return mod.fit_transform(X)

def compute_MLE(X):
    mod = id.MLE()
    return mod.fit_transform(X)

def compute_KNN(X):
    mod = id.KNN()
    return mod.fit_transform(X)

def compute_FisherS(X):
    mod = id.FisherS()
    return mod.fit_transform(X)

def compute_lPCA(X):
    mod = id.lPCA()
    return mod.fit_transform(X)

def compute_CorrInt(X):
    mod = id.CorrInt()
    return mod.fit_transform(X)

METHODS = {'PHATE_SE': compute_phate_SE, 
           'TPHATE_SE': compute_tphate_SE,
          'DIFF_MAP_SE': compute_diffusion_matrix_SE, 
          'MiND_ML':compute_MiND_ML, 
          'MLE': compute_MLE, 
          'KNN': compute_KNN,
          'FisherS':compute_FisherS, 
          'CorrInt':compute_CorrInt, 
          'lPCA':compute_lPCA}

METHOD_NAMES = sorted(METHODS.keys())

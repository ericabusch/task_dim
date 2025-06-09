from random import choices, choice
import numpy as np
from sklearn.utils import check_random_state
from joblib import Parallel, delayed
from scipy.stats import pearsonr, spearmanr, kendalltau


def permutation_test(data, n_iterations, alternative='greater'):
    """
    permutation test for comparing the means of two distributions 
    where the samples between the two distributions are paired
    
    """
    
    def less(null_distribution, observed):
        cmps = null_distribution <= observed + gamma
        pvalues = (cmps.sum(axis=0) + 1) / (n_iterations + 1)
        return pvalues

    def greater(null_distribution, observed):
        cmps = null_distribution >= observed - gamma
        pvalues = (cmps.sum(axis=0) + 1) / (n_iterations + 1)
        return pvalues

    def two_sided(null_distribution, observed):
        pvalues_less = less(null_distribution, observed)
        pvalues_greater = greater(null_distribution, observed)
        pvalues = np.minimum(pvalues_less, pvalues_greater) * 2
        return pvalues
    
    compare = {'less': less, 'greater': greater, 'two-sided': two_sided}
    n_samples = data.shape[1]
    observed_difference = data[0] - data[1]
    observed = np.mean(observed_difference)
    
    
    null_distribution = np.empty(n_iterations)
    for i in range(n_iterations):
        weights = [choice([-1, 1]) for d in range(n_samples)]
        null_distribution[i] = (weights*observed_difference).mean()
        
    eps = 1e-14
    gamma = np.maximum(eps, np.abs(eps * observed))
    
    pvalue = compare[alternative](null_distribution, observed)
    return observed, pvalue, null_distribution

def fisher_r_to_z(r):
    """Use Fisher transformation to convert correlation to z score"""

    # return .5*np.log((1 + r)/(1 - r))
    return np.arctanh(r)

def fisher_z_to_r(z):
    """Use Fisher transformation to convert correlation to z score"""
    return np.tanh(z)

def timeseries_correlation_permutation(
    data1,
    data2,
    method="time_shift",
    n_permute=1000,
    metric="pearson",
    tail=2,
    n_jobs=-1,
    return_perms=False,
    random_state=None,
):
    """Compute correlation and calculate p-value using permutation methods.

    'permute' method randomly shuffles one of the vectors. This method is recommended
    for independent data. For timeseries data we recommend using 'time_shift' 

    Args:

        data1: (pd.DataFrame, pd.Series, np.array) dataset 1 to permute
        data2: (pd.DataFrame, pd.Series, np.array) dataset 2 to permute
        n_permute: (int) number of permutations
        metric: (str) type of association metric ['spearman','pearson', 'kendall']
        method: (str) type of permutation ['permute', 'time_shift']
        random_state: (int, None, or np.random.RandomState) Initial random seed (default: None)
        tail: (int) either 1 for one-tail or 2 for two-tailed test (default: 2)
        n_jobs: (int) The number of CPUs to use to do the computation.
                -1 means all CPUs.
        return_parms: (bool) Return the permutation distribution along with the p-value; default False
    Returns:
        stats: (dict) dictionary of permutation results ['correlation','p']
    """
    if len(data1) != len(data2):
        raise ValueError("Make sure that data1 is the same length as data2")

    if method not in ["permute", "time_shift"]:
        raise ValueError(
            "Make sure that method is ['permute', 'time_shift']"
        )

    random_state = check_random_state(random_state)

    data1 = np.array(data1)
    data2 = np.array(data2)
    assert data1.shape == data2.shape, "data shapes must match"

    correlation_metrics = {
        "spearman": spearmanr,
        "pearson": pearsonr,
        "kendalltau": kendalltau,
    }
    
    if data1.ndim > 1 or data2.ndim > 1:
        stats = {k:func(data1.ravel(),data2.ravel())[0] for k, func in correlation_metrics.items()} 
    else:
        stats = {k:func(data1, data2)[0] for k, func in correlation_metrics.items()} 
    
    correlation = stats[metric]

    if method == "permute":
        null_correlations = Parallel(n_jobs=n_jobs)(
            delayed(correlation)(random_state.permutation(data1), data2, metric=metric)
            for _ in range(n_permute)
        ) 
    elif method == "time_shift":
        null_correlations = Parallel(n_jobs=n_jobs)(
            delayed(circular_shift_correlation)(data1, data2, correlation_metrics[metric], p)  for p in range(n_permute)
        )

    stats["p"] = calc_pvalue(null_correlations, correlation, tail)
    stats["correlation"] = correlation
    if return_perms:
        stats["perm_distribution"] = null_correlations
    return stats

def circular_shift_correlation(data1, data2, correlation_function, repetition_number=1):
    """
    Generate a null distribution by circularly shifting a timeseries by multiples of step_size.

    Parameters
    ----------
    
    Returns
    -------
    null_dist : np.ndarray, shape (n_repetitions, T)
        Array of shifted timeseries (each row is a shifted version).
    """
    shifted = np.roll(data1.T, repetition_number).T.ravel()
    return correlation_function(shifted, data2.ravel())[0]



def calc_pvalue(null_stats, true_stat, tail):
    """Calculates p value based on distribution of correlations
    This function is called by the permutation functions
        all_p: list of correlation values from permutation
        stat: actual value being tested, i.e., stats['correlation'] or stats['mean']
        tail: (int) either 2 or 1 for two-tailed p-value or one-tailed
    """

    denom = float(len(null_stats)) + 1
    if tail == 1:
        numer = np.sum(null_stats >= true_stat) + 1 if true_stat >= 0 else np.sum(null_stats <= true_stat) + 1
    elif tail == 2:
        numer = np.sum(np.abs(null_stats) >= np.abs(true_stat)) + 1
    else:
        raise ValueError("tail must be either 1 or 2")
    return numer / denom



def false_discovery_control(ps, *, axis=0, method='bh'):
    """Adjust p-values to control the false discovery rate.

    The false discovery rate (FDR) is the expected proportion of rejected null
    hypotheses that are actually true.
    If the null hypothesis is rejected when the *adjusted* p-value falls below
    a specified level, the false discovery rate is controlled at that level.

    Parameters
    ----------
    ps : 1D array_like
        The p-values to adjust. Elements must be real numbers between 0 and 1.
    axis : int
        The axis along which to perform the adjustment. The adjustment is
        performed independently along each axis-slice. If `axis` is None, `ps`
        is raveled before performing the adjustment.
    method : {'bh', 'by'}
        The false discovery rate control procedure to apply: ``'bh'`` is for
        Benjamini-Hochberg [1]_ (Eq. 1), ``'by'`` is for Benjaminini-Yekutieli
        [2]_ (Theorem 1.3). The latter is more conservative, but it is
        guaranteed to control the FDR even when the p-values are not from
        independent tests.

    Returns
    -------
    ps_adusted : array_like
        The adjusted p-values. If the null hypothesis is rejected where these
        fall below a specified level, the false discovery rate is controlled
        at that level.
    BASED OFF : https://github.com/scipy/scipy/blob/v1.15.1/scipy/stats/_morestats.py#L4385
    """
    ps = np.asarray(ps)
    NAN_ADJUST=False
    if np.sum(ps != ps ) > 0:
        print(f'found {np.sum(ps != ps )} nans, adjusting')
        results_mask = ps == ps
        results_mask = results_mask.astype(int)
        # EXCLUDES NANS
        ps = ps[ps == ps]
        NAN_ADJUST=True

    ps_in_range = (np.issubdtype(ps.dtype, np.number)
                   and np.all(ps == np.clip(ps, 0, 1)))
    if not ps_in_range:
        raise ValueError("`ps` must include only numbers between 0 and 1.")

    methods = {'bh', 'by'}
    if method.lower() not in methods:
        raise ValueError(f"Unrecognized `method` '{method}'."
                         f"Method must be one of {methods}.")
    method = method.lower()

    if axis is None:
        axis = 0
        ps = ps.ravel()

    axis = np.asarray(axis)[()]
    if not np.issubdtype(axis.dtype, np.integer) or axis.size != 1:
        raise ValueError("`axis` must be an integer or `None`")

    if ps.size <= 1 or ps.shape[axis] <= 1:
        return ps[()]

    ps = np.moveaxis(ps, axis, -1)
    m = ps.shape[-1]

    # Main Algorithm
    # Equivalent to the ideas of [1] and [2], except that this adjusts the
    # p-values as described in [3]. The results are similar to those produced
    # by R's p.adjust.

    # "Let [ps] be the ordered observed p-values..."
    order = np.argsort(ps, axis=-1)
    ps = np.take_along_axis(ps, order, axis=-1)  # this copies ps

    # Equation 1 of [1] rearranged to reject when p is less than specified q
    i = np.arange(1, m+1)
    ps *= m / i

    # Theorem 1.3 of [2]
    if method == 'by':
        ps *= np.sum(1 / i)

    # accounts for rejecting all null hypotheses i for i < k, where k is
    # defined in Eq. 1 of either [1] or [2]. See [3]. Starting with the index j
    # of the second to last element, we replace element j with element j+1 if
    # the latter is smaller.
    np.minimum.accumulate(ps[..., ::-1], out=ps[..., ::-1], axis=-1)

    # Restore original order of axes and data
    np.put_along_axis(ps, order, values=ps.copy(), axis=-1)
    ps = np.moveaxis(ps, -1, axis)
    ps = np.clip(ps, 0, 1)

    if NAN_ADJUST:
        # plug back into larger array
        i=0
        temp = np.ones_like(results_mask)
        for j in range(len(results_mask)):
            if results_mask[j] == 1:
                temp[j] = ps[i]
                i+=1
        ps = temp
    return ps
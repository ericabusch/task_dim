from random import choices, choice
import numpy as np
from sklearn.utils import check_random_state
from joblib import Parallel, delayed
from scipy.stats import pearsonr, spearmanr, kendalltau, ttest_rel, ttest_1samp
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf
import pandas as pd
import pingouin as pg
import sys
import re

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

def overlap_coefficient(a, b, *, treat_nan_as_false=True, empty_value=np.nan):
    """Compute the overlap (Szymkiewicz–Simpson) coefficient between two sets/masks.

    Overlap coefficient:
        |A ∩ B| / min(|A|, |B|)

    Parameters
    ----------
    a, b : array-like or set
        Inputs representing membership. If array-like, nonzero/True values count as members.
        If sets, elements are treated as members directly.
    treat_nan_as_false : bool, default=True
        If inputs are array-like and contain NaNs, treat NaN as False (not a member).
    empty_value : float, default=np.nan
        Return value when either set is empty (i.e., min(|A|,|B|)==0).

    Returns
    -------
    float
        Overlap coefficient in [0, 1], or `empty_value` if undefined.
    """
    # Set inputs
    if isinstance(a, set) and isinstance(b, set):
        A, B = a, b
        den = min(len(A), len(B))
        if den == 0:
            return empty_value
        return len(A.intersection(B)) / den

    # Array-like inputs
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)

    if a_arr.shape != b_arr.shape:
        raise ValueError(f"Shape mismatch: a {a_arr.shape} vs b {b_arr.shape}")

    if treat_nan_as_false:
        # Make NaNs false before boolean conversion
        if np.issubdtype(a_arr.dtype, np.floating):
            a_arr = np.nan_to_num(a_arr, nan=0.0)
        if np.issubdtype(b_arr.dtype, np.floating):
            b_arr = np.nan_to_num(b_arr, nan=0.0)

    A = a_arr.astype(bool)
    B = b_arr.astype(bool)

    inter = np.count_nonzero(A & B)
    sizeA = np.count_nonzero(A)
    sizeB = np.count_nonzero(B)
    den = min(sizeA, sizeB)
    if den == 0:
        return empty_value
    return inter / den

def timeseries_correlation_permutation(
    data1,
    data2,
    method="time_shift",
    n_permute=1000,
    metric="pearson",
    tail='two-tailed',
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

    z, p = calc_pval_zstat(null_correlations, correlation, tail)
    stats["correlation"] = correlation
    stats["p"]=p
    stats["zstat"]=z
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

def calc_pval_zstat(null_stats, true_stat, tail='two-tailed'):
    """Calculates p value based on distribution of correlations
    This function is called by the permutation functions
        all_p: list of correlation values from permutation
        stat: actual value being tested, i.e., stats['correlation'] or stats['mean']
        tail: (int) either 2 or 1 for two-tailed p-value or one-tailed
    """
    mu = np.mean(null_stats)
    sigma = np.std(null_stats)
    z = (true_stat - mu) / sigma

    if tail == 'two-tailed':
        p = 2 * min(np.mean(null_stats >= true_stat), np.mean(null_stats <= true_stat))
    elif tail == 'greater':
        p = np.mean(null_stats >= true_stat)
    elif tail == 'less':
        p = np.mean(null_stats <= true_stat)
    else:
        raise ValueError("tail must be 'two-tailed', 'greater', or 'less'")
    return z, p
    
def paired_difference_ttest(arr1, arr2, alpha=0.05, alternative='greater'):
    """
    Compute within-sample differences, test if difference > 0 using related samples t-test,
    and apply FDR correction.

    Parameters
    ----------
    arr1, arr2 : np.ndarray, shape (N, M)
        Paired data arrays (N samples, M features).
    alpha : float
        FDR threshold for significance.

    Returns
    -------
    mean_diff : np.ndarray, shape (M,)
        Mean difference (arr1 - arr2) for each feature.
    pvals : np.ndarray, shape (M,)
        P-values from Wilcoxon signed-rank test for each feature.
    sig_mask : np.ndarray, shape (M,)
        Boolean array, True if FDR-corrected p < alpha.
    """
    if arr2 is None:
        #assume arr2 is a zero array of the same shape as arr1
        arr2 = np.zeros_like(arr1)
    arr1 = np.asarray(arr1)
    arr2 = np.asarray(arr2)
    assert arr1.shape == arr2.shape, "Arrays must have the same shape"
    N, M = arr1.shape

    mean_diff = np.mean(arr1 - arr2, axis=0)
    pvals = np.zeros(M)
    for i in range(M):
        stat, p = ttest_rel(arr1[:, i], arr2[:, i], alternative=alternative)
        pvals[i] = p

    # FDR correction
    reject, pvals_corr, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')
    sig_mask = reject

    return mean_diff, pvals, sig_mask

def paired_difference_null_distribution(arr1, arr2, alpha=0.05, n_perm=1000, random_state=None, alternative='two-sided'):
    """
    Compute within-sample differences, test if difference > 0 using a permutation test,
    and apply Benjamini-Hochberg FDR correction.

    Parameters
    ----------
    arr1, arr2 : np.ndarray, shape (N, M)
        Paired data arrays (N samples, M features).
    alpha : float
        FDR threshold for significance.
    n_perm : int
        Number of permutations.
    random_state : int or None
        Seed for reproducibility.

    Returns
    -------
    mean_diff : np.ndarray, shape (M,)
        Mean difference (arr1 - arr2) for each feature.
    pvals : np.ndarray, shape (M,)
        P-values from permutation test for each feature.
    sig_mask : np.ndarray, shape (M,)
        Boolean array, True if FDR-corrected p < alpha.
    """
    if arr2 is None:
        #assume arr2 is a zero array of the same shape as arr1
        arr2 = np.zeros_like(arr1)
    rng = np.random.default_rng(random_state)
    arr1 = np.asarray(arr1)
    arr2 = np.asarray(arr2)
    assert arr1.shape == arr2.shape, "Arrays must have the same shape"
    N, M = arr1.shape

    diffs = arr1 - arr2
    mean_diff = np.mean(diffs, axis=0)
    pvals = np.zeros(M)

    for i in range(M):
        observed = mean_diff[i]
        # Permutation: randomly flip sign of each paired difference
        perm_diffs = np.empty(n_perm)
        for p in range(n_perm):
            signs = rng.choice([1, -1], size=N)
            perm_diffs[p] = np.mean(diffs[:, i] * signs)
        if alternative == 'greater':
            pvals[i] = (np.sum(perm_diffs >= observed) + 1) / (n_perm + 1)
        elif alternative == 'less':
            pvals[i] = (np.sum(perm_diffs <= observed) + 1) / (n_perm + 1)
        elif alternative == 'two-sided':
            pvals[i] = (np.sum(np.abs(perm_diffs) >= np.abs(observed)) + 1) / (n_perm + 1)
        else:
            raise ValueError("alternative must be 'greater', 'less', or 'two-sided'")

    reject, pvals_corr, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')

    return mean_diff, pvals, reject

def permute_pattern(data0, data1, n_permutations=1000, random_state=None, corr_func=spearmanr):
    """Generate spatially permuted versions of a pattern.

    Args:
        pattern (np.ndarray): 1D array of brain values to permute.
        n_permutations (int): Number of permutations to generate.
        method (str): Method for spatial permutation ('spin' or other).
        random_state (int or None): Random seed for reproducibility.

    Returns:
        np.ndarray: 2D array of shape (n_permutations, len(pattern)) with permuted patterns.
    """
    

    if random_state is not None:
        np.random.seed(random_state)
    permuted_pattern = data0.copy()
    null_correlations = np.zeros(n_permutations)
    for i in range(n_permutations):
        # Generate a random permutation of indices
        perm_indices = np.random.permutation(len(data0))
        permuted_data0 = data0[perm_indices]
        # Compute correlation with data1
        corr, _ = corr_func(permuted_data0, data1)
        null_correlations[i] = corr
    true_correlation, _ = corr_func(data0, data1)
    p_value = (np.sum(np.abs(null_correlations) >= np.abs(true_correlation)) + 1) / (n_permutations + 1)
    zscored = (true_correlation - np.mean(null_correlations)) / np.std(null_correlations)
    return p_value, true_correlation, zscored


def within_subject_spearman(df, x_col='delta_ID', y_col='ISC', subject_col='subject_id',
                             n_permutations=1000, random_state=None, extra_cols=None):
    """Compute within-subject Spearman correlation between two parcel-level measures.

    For each subject, correlates x_col vs y_col across parcels using a permutation
    test (see permute_pattern). Returns one row per subject with rho, p-value, and
    z-score.

    Args:
        df: Long-format DataFrame with one row per subject × parcel.
        x_col: Column name for the first measure (e.g. 'delta_ID').
        y_col: Column name for the second measure (e.g. 'ISC').
        subject_col: Column identifying subjects.
        n_permutations: Number of permutations for the null distribution.
        random_state: Optional random seed.
        extra_cols: List of subject-level columns to carry into the output
            (e.g. ['age', 'dataset']). Values are taken from the first row per subject.

    Returns:
        pd.DataFrame with columns: subject_col, 'rho', 'pval', 'zscore',
        plus any extra_cols.
    """
    extra_cols = extra_cols or []
    records = []
    for subject, grp in df.groupby(subject_col):
        grp = grp.dropna(subset=[x_col, y_col])
        if len(grp) < 10:
            continue
        pval, rho, zscore = permute_pattern(
            grp[x_col].values, grp[y_col].values,
            n_permutations=n_permutations, random_state=random_state
        )
        row = {subject_col: subject, 'rho': rho, 'pval': pval, 'zscore': zscore}
        for col in extra_cols:
            row[col] = grp[col].iloc[0]
        records.append(row)
    return pd.DataFrame(records)

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

def parcelwise_regression(score_df, xname, yname='score', covariates=None, formula=None, 
                         region_col='region_name', region_order=[], 
                         alpha=0.05, fdr_method='fdr_bh', lme=False):
    """
    Perform linear regression for each parcel/region and return coef, t, p for
    every predictor (including covariates). Perform multiple-comparison (FDR)
    correction separately for each predictor name across regions.

    Notes
    - Predictor column names in results are created with underscores:
        coef_<predictor>, t_<predictor>, p_<predictor>
    - FDR-corrected p-values and significance flags are:
        p_<predictor>_fdr, sig_<predictor>_fdr
    - Predictor names are taken from the regression parameter names
      (i.e., model.params index) except the intercept. This handles numeric
      predictors and expanded categorical parameter names created by patsy.
    """

    df = score_df.copy()
    # Build formula if not provided
    if formula is None:
        if covariates is None or covariates == [None]:
            formula = f'{yname} ~ {xname}'
        else:
            cov_str = ' + '.join(covariates)
            # If xname is a list/tuple, join them
            if isinstance(xname, (list, tuple)):
                xstr = ' + '.join(xname)
            else:
                xstr = str(xname)
            formula = f'{yname} ~ {xstr} + {cov_str}'
    print(f'Using formula: {formula}')
    # Get region list
    if len(region_order) == 0:
        region_order = sorted(df[region_col].unique())

    rows = []
    # We'll collect all observed parameter names across regions to ensure columns exist
    observed_params = set()

    for reg in region_order:
        df_reg = df[df[region_col] == reg].copy().reset_index(drop=True)
        if lme:
            #remove all whitespace in formula to simplify parsing
            formula = formula.replace(' ', '')
            grouping = formula.split("+(1|")[1].replace(')','')
            revised_formula = formula.split("+(1|")[0].strip()
            model = smf.mixedlm(revised_formula, data=df_reg, groups=df_reg[grouping]).fit()
        else:
            model = smf.ols(formula, data=df_reg).fit()
        try:
            entry = {region_col: reg, 'n': int(model.nobs)}
            # For each parameter in the fitted model (except Intercept) record coef/t/p
            for param in model.params.index:
                if param == 'Intercept':
                    continue
                safe = re.sub(r'[^0-9a-zA-Z]+', '_', str(param))
                observed_params.add((param, safe))
                entry[f'coef_{safe}'] = model.params.get(param, np.nan)
                entry[f'tstat_{safe}'] = model.tvalues.get(param, np.nan)
                entry[f'p_{safe}'] = model.pvalues.get(param, np.nan)

            rows.append(entry)

        except Exception as e:
            # If regression fails, create an entry with NA values for any parameters we have seen so far
            print(f"Warning: Regression failed for region {reg}: {e}")
            sys.exit()
            entry = {region_col: reg, 'r2': np.nan, 'n': 0}
            # fill placeholders for previously observed params
            for param, safe in observed_params:
                entry[f'coef_{safe}'] = np.nan
                entry[f'tstat_{safe}'] = np.nan
                entry[f'p_{safe}'] = np.nan
            rows.append(entry)

    results_df = pd.DataFrame(rows)

    # Ensure all observed parameters have their columns in the dataframe (in case some regions failed before any param seen)
    for param, safe in observed_params:
        for col_prefix in ('coef_', 'tstat_', 'p_'):
            col = f'{col_prefix}{safe}'
            if col not in results_df.columns:
                results_df[col] = np.nan

    # Identify all predictor-safe-names from p_ columns
    p_cols = [c for c in results_df.columns if c.startswith('p_')]
    # Perform FDR correction within each predictor (i.e., for each p_ column independently)
    for p_col in p_cols:
        safe = p_col[len('p_'):]
        p_fdr_col = f'p_{safe}_fdr'
        sig_col = f'sig_{safe}_fdr'

        valid_mask = results_df[p_col].notna()
        if valid_mask.sum() > 0:
            reject, pvals_fdr, _, _ = multipletests(
                results_df.loc[valid_mask, p_col].values,
                alpha=alpha,
                method=fdr_method
            )
            # assign corrected p-values and boolean significance
            results_df.loc[valid_mask, p_fdr_col] = pvals_fdr
            results_df.loc[valid_mask, sig_col] = reject
            # for rows without valid p, set defaults
            results_df.loc[~valid_mask, p_fdr_col] = np.nan
            results_df.loc[~valid_mask, sig_col] = False
        else:
            # no valid pvals for this predictor
            results_df[p_fdr_col] = np.nan
            results_df[sig_col] = False

    # Reorder columns: region_col, n, r2, then sorted predictor blocks
    other_cols = [region_col, 'n', 'r2']
    predictor_blocks = []
    # sort observed_params by safe name for deterministic order
    safes = sorted({safe for _, safe in observed_params})
    for safe in safes:
        predictor_blocks.extend([f'coef_{safe}', f'tstat_{safe}', f'p_{safe}', f'p_{safe}_fdr', f'sig_{safe}_fdr'])
    # Keep any extra columns that may exist
    remaining = [c for c in results_df.columns if c not in other_cols + predictor_blocks]
    ordered_cols = [c for c in other_cols + predictor_blocks + remaining if c in results_df.columns]
    results_df = results_df[ordered_cols]

    return results_df

def parcelwise_partial_correlation(score_df, xname, yname='score', covariates=None, 
                                   participant_df=None, region_col='region_name', 
                                   region_order=[], subject_col='subject',
                                   alpha=0.05, fdr_method='fdr_bh', method='spearman'):
    """
    Compute partial correlation for each parcel/region using Pingouin.
    
    Parameters
    ----------
    score_df : pd.DataFrame
        DataFrame containing score data with columns for region, subject, and dependent variable.
    xname : str
        Name of the primary predictor variable (e.g., 'Age').
    yname : str, default='score'
        Name of the dependent variable column.
    covariates : list of str or None
        List of covariate names to partial out. If None or empty, returns simple correlation.
    participant_df : pd.DataFrame or None
        DataFrame with participant-level data (for merging covariates if needed).
    region_col : str, default='region_name'
        Name of the column containing region/parcel identifiers.
    region_order : list, default=[]
        Ordered list of regions to process. If empty, uses sorted unique regions.
    subject_col : str, default='subject'
        Name of the column containing subject identifiers.
    alpha : float, default=0.05
        Significance threshold for FDR correction.
    fdr_method : str, default='fdr_bh'
        Method for FDR correction.
    method : str, default='spearman'
        Correlation method: 'spearman' or 'pearson'.
    
    Returns
    -------
    results_df : pd.DataFrame
        DataFrame with one row per region containing partial correlations and statistics.
    """
    
    df = score_df.copy()
    
    # Merge participant-level covariates if needed
    if covariates is not None and covariates != [None]:
        missing_cols = [c for c in covariates if c not in df.columns]
        if missing_cols and participant_df is not None:
            merge_cols = [subject_col] + missing_cols
            temp = participant_df[merge_cols].copy()
            df = df.merge(temp, left_on=subject_col, right_on=subject_col, how='left')
    
    # Merge X variable if needed
    if xname not in df.columns and participant_df is not None:
        if xname in participant_df.columns:
            temp = participant_df[[subject_col, xname]].copy()
            df = df.merge(temp, left_on=subject_col, right_on=subject_col, how='left')
    
    if len(region_order) == 0:
        region_order = sorted(df[region_col].unique())
    
    rows = []
    for reg in region_order:
        df_reg = df[df[region_col] == reg].copy()
        
        # Determine required columns
        cols_needed = [xname, yname]
        if covariates is not None and covariates != [None]:
            cols_needed.extend(covariates)
        
        # Drop missing values
        df_reg = df_reg.dropna(subset=cols_needed)
        
        if len(df_reg) < 3:
            rows.append({
                region_col: reg,
                'rho': np.nan,
                'p': np.nan,
                'n': len(df_reg)
            })
            continue
        
        try:
            # Use Pingouin's partial_corr
            if covariates is None or covariates == [None] or len(covariates) == 0:
                # Simple correlation (no covariates)
                result = pg.corr(df_reg[xname], df_reg[yname], method=method)
                rho = result['r'].values[0]
                pval = result['p-val'].values[0]
                n = result['n'].values[0]
            else:
                # Partial correlation
                result = pg.partial_corr(
                    data=df_reg,
                    x=xname,
                    y=yname,
                    covar=covariates,
                    method=method
                )
                rho = result['r'].values[0]
                pval = result['p-val'].values[0]
                n = result['n'].values[0]
            
            rows.append({
                region_col: reg,
                'rho': rho,
                'p': pval,
                'n': int(n)
            })
            
        except Exception as e:
            print(f"Warning: Partial correlation failed for region {reg}: {e}")
            rows.append({
                region_col: reg,
                'rho': np.nan,
                'p': np.nan,
                'n': len(df_reg)
            })
    
    results_df = pd.DataFrame(rows)
    
    # Apply FDR correction
    if results_df.shape[0] > 0:
        valid_pvals = results_df['p'].notna()
        if valid_pvals.sum() > 0:
            reject, pvals_fdr, _, _ = multipletests(
                results_df.loc[valid_pvals, 'p'].values,
                alpha=alpha,
                method=fdr_method
            )
            results_df.loc[valid_pvals, 'p_fdr'] = pvals_fdr
            results_df.loc[valid_pvals, 'sig_fdr'] = reject
        else:
            results_df['p_fdr'] = np.nan
            results_df['sig_fdr'] = False
    
    return results_df
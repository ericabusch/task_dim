import numpy as np
import random
from scipy.stats import zscore
import scipy.stats
from sklearn.svm import LinearSVC, SVC
import random
from sklearn.model_selection import ShuffleSplit, train_test_split, cross_val_score, KFold, GridSearchCV

parameters = {'C':10, 'kernel':'rbf'}

def clf_wrapper(X, y, n_folds=5, num_reps=100, balance=True):
    if num_reps == 0:
        n_samples, n_features = X.shape
        acc = []
        folder = KFold(n_splits=n_folds, shuffle=True)
        for fold, (train, test) in enumerate(folder.split(np.arange(n_samples))):
            X_train, y_train = X[train], y[train]
            if balance:
                X_train, y_train = balance_train_data(X_train, y_train, verbose=False)
            svc = SVC(kernel=parameters['kernel'], C=parameters['C'])
            svc.fit(X_train, y_train)
            acc.append(svc.score(X[test], y[test]))
        return np.mean(acc), None
    shift_by = int(X.shape[0] / num_reps)
    zstat, pval = shift_labels_and_run_clf(X, y, n_folds, shift_by, num_reps)
    return zstat, pval

def shift_labels_and_run_clf(X, y, num_folds_per_shift, shift_by, num_reps):
    n_samples, n_features = X.shape
    results = np.zeros((num_reps, num_folds_per_shift))
    # for each repetition, then fold, then shift the training labels 
    for rep in range(num_reps):
        folder = KFold(n_splits=num_folds_per_shift, shuffle=True)
        for fold, (train, test) in enumerate(folder.split(np.arange(n_samples))):
            # now that we are here, rolls the training labels according to the rep 
            y_train = shift_labels(y[train], shift_by, rep)
            if np.sum(np.isnan(y_train)) == 1:
                results[rep, fold]=np.nan
                continue
            # now balance the training data to have equal exemplars from class
            # even though we've broken the structure between X and y
            X_train, y_train = balance_train_data(X[train], y_train, verbose=False)
            svc = SVC(kernel=parameters['kernel'], C=parameters['C'])
            svc.fit(X_train, y_train)
            results[rep, fold]=svc.score(X[test], y[test])
    acc_per_roll = np.nanmean(results,axis=1)
    zscored_acc = zscore(acc_per_roll)
    true_score_zstat = zscored_acc[0]
    p_value = scipy.stats.norm.sf(true_score_zstat)
    return true_score_zstat, p_value

def shift_labels(labels, shift_by, rep_number):
    TRs_total = np.arange(labels.shape[0])
    TRs_to_shift = np.arange(0, shift_by*rep_number)
    TRs_to_keep = np.setdiff1d(TRs_total, TRs_to_shift)
    shifted_TRs = np.concatenate((TRs_to_keep, TRs_to_shift))
    try:
        shifted_labels = labels[shifted_TRs]
    except:
        shifted_labels = np.array([labels[i]  for i in shifted_TRs if i < len(labels)])
    return shifted_labels

def balance_train_data(X_train, Y_train, verbose=False):
    (unique, counts) = np.unique(Y_train, return_counts=True)
    num_classes = len(unique)
    num_timepoints = sum(counts)
    orig_proportions = counts/sum(counts)
    ind_max = np.where(counts == max(counts))
    max_class = unique[ind_max]
    goal = max(counts)
    train_indices = []
    for ind, classs in enumerate(unique):
        if counts[ind] != goal:
            num2add = goal - counts[ind]
            where_this_class = np.where(Y_train == classs)
            chosen_indices = list(random.choices(where_this_class[0], k=num2add)) + list(where_this_class[0])
            train_indices = train_indices + chosen_indices
        else:
            train_indices += list(np.where(Y_train == classs)[0])
    train_indices.sort()
    X_train = X_train[train_indices]
    Y_train = Y_train[train_indices]
    (new_unique, new_counts) = np.unique(Y_train, return_counts=True)
    new_proportions = new_counts/sum(new_counts)
    if verbose:
        print(f'original_counts: {counts} | original proportions: {orig_proportions}')
        print(f'new_counts: {new_counts} |new proportions: {new_proportions}')
        print(f'new shape: {X_train.shape}, {Y_train.shape}')
    return X_train, Y_train
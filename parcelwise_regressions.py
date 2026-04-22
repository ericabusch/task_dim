import numpy as np
import pandas as pd
import os, sys, glob, argparse
import stats_helpers as sh
import plotting_helpers as ph

def load_results_dataframe():
    try:
        df = utils.load_ide_isc_atlas_df()
    except:
        try: 
            df = pd.read_csv(utils.get_results_dir()+f'/parcelwise_ide_isc_atlas_df.csv')
        except:
            print('Could not load results dataframe'); sys.exit(1)
    return df

def clean_difference_dataframe(dataframe):
    # be robust to task naming (e.g. 'movieTP' vs 'movie')
    tasks = dataframe['task'].dropna().unique().tolist()
    movie_task = next((t for t in tasks if 'movie' in t.lower()), None)
    rest_task = next((t for t in tasks if 'rest' in t.lower()), None)
    if movie_task is None or rest_task is None:
        raise RuntimeError(f"Could not find both movie and rest tasks rows. found tasks: {tasks}")

    # pivot so each row = subject x region, columns for rest and movie scores
    pivot = dataframe.pivot_table(index=['subject', 'region_name'], columns='task', values='score').reset_index()

    # ensure expected columns exist
    pivot = pivot.rename(columns={movie_task: 'movie_score', rest_task: 'rest_score'})

    # keep only rows with both scores and compute difference (rest - movie)
    pivot = pivot.dropna(subset=['movie_score', 'rest_score']).copy()
    pivot['RestMovieDiff'] = pivot['rest_score'] - pivot['movie_score']
    # Add back in age, motion columns
    temp = dataframe[['subject', 'Age','AgeGroup', 'movie_FD', 'rest_FD','sex','session']].drop_duplicates()
    pivot = pivot.merge(temp, on='subject', how='inner')
    return pivot[['subject', 'region_name', 'rest_score', 'movie_score','AgeGroup', 'RestMovieDiff', 'movie_FD', 'rest_FD', 'Age','sex','session']]


def join_results_participant_info(results_df, participant_df, dataset):
    # merge results and participant dataframes
    if dataset == 'hbn':
        participant_df = participant_df[['subject_id','movie_FD','rest_FD','sex','session']]
        # rename columns to match
        participant_df = participant_df.rename(columns={'sex':'sex','session':'session',
                                                        'subject_id':'subject', 'movie_FD':'movie_FD','rest_FD':'rest_FD'})
    elif dataset == 'partlycloudy':
        participant_df = participant_df[['participant_id','mean_FD','Gender']]
        # rename columns to match
        participant_df = participant_df.rename(columns={'participant_id':'subject', 'Gender':'sex', 'mean_FD':'mean_FD'})

    merged_df = results_df.merge(participant_df, on='subject', how='inner')
    return merged_df

def run_simple_ide_isc_analyses(dataframe, output_directory, tasks, plot=0, verbose=1):
    # This assumes there's tasks with matched IDE and ISC measures, no age or motion covariates
    results_df = []
    for task in tasks:
        task_df = dataframe[dataframe['task']==task]
        # Build a new dataframe with only the relevant columns
        df_pivot = task_df.pivot_table(index=['region_name','subject'], 
                                                columns='measure', values='score').reset_index()
        
        for measure in ['TPHATE_DiffOp_IDE','PCA']:
            formula = f"{measure} ~ ISC"
            if verbose: print(f'Running parcelwise regression for task {task}, {formula}')
            results = sh.parcelwise_regression(df_pivot, 'ISC', yname=measure, covariates=None, formula=formula, 
                         region_col='region_name', region_order=REGION_ORDER,
                         alpha=0.05, fdr_method='fdr_bh')
            results_df.append(results)
            if plot:
                ph.plot_parcelwise_regression_results(results, 
                                                      title=f'{task}:  {formula}',
                                                      output_file=output_directory+f'parcelwise_regression_{task}_{measure}_vs_ISC.png',
                                                      region_order=REGION_ORDER)
                if verbose: print(f'Plotted {output_directory}/parcelwise_regression_{task}_{measure}_vs_ISC.png')
    return pd.concat(results_df, axis=0)
            
def run_regression_analyses(dataframe, xname, yname, formula, covariates, output_directory, root_filename, title='', region_order=[], plot=0, verbose=1):
    # Pass to this function a formula that includes the entire model you want to run
    # Make sure it only includes the task and measures you want to analyze
    if len(region_order) == 0:
        region_order=REGION_ORDER
    try:
        df_pivot = dataframe.pivot_table(index=['region_name','subject'], 
                                                columns='measure', values='score').reset_index()
        temp = dataframe[['subject']+covariates].drop_duplicates()
        df_pivot = df_pivot.merge(temp, on='subject', how='inner')
    except:
        df_pivot = dataframe  
    results = sh.parcelwise_regression(df_pivot, xname, yname=yname, formula=formula, 
                         region_order=region_order, alpha=0.05, fdr_method='fdr_bh')
    

    if plot:
        # determine from the results column names what stats to plot
        stats_to_plot = []
        stats_to_plot.append('r2')
        for col in results.columns:
            # Skip if col contains any of the covariate names
            if any(a in col for a in ['Age', "ISC"]) and (('coef' in col or 'tstat' in col)):
                stats_to_plot.append(col)
            elif any(cov in col for cov in covariates):
                continue
        print(f'Stats to plot: {stats_to_plot}')
        if root_filename is None: output_path = None  
        else: output_path = output_directory+f'parcelwise_regression_{root_filename}.png'
        ph.plot_parcelwise_regression_results(results, 
                                                title=f'{title}:  {formula}', stats_to_plot=stats_to_plot,
                                                output_path=output_path,
                                                region_order=region_order)
        if verbose: print(f'Plotted {output_directory}/parcelwise_regression_{root_filename}_vs_ISC.png')
    return results


def drive_analyses(dataframe, output_directory, dataset, plot=1, verbose=1):
    if dataset in ['narratives']:
        results = run_simple_ide_isc_analyses(dataframe, output_directory, utils.get_tasks(), plot=plot, verbose=verbose)
        results.to_csv(output_directory+f'parcelwise_ide_isc_relationships_{dataset}.csv', index=False)
        if verbose: print(f'Saved results to {output_directory}/parcelwise_ide_isc_relationships_{dataset}.csv')
    elif dataset == 'partlycloudy':
        # Want to run: 
        # # MOVIE: ID ~ ISC + Age + motion + ISC:Age + Age:motion
        formula = f"ISC ~ Age + mean_FD + sex"
        this_dataframe = dataframe[dataframe['measure'].isin(['ISC'])]
        results = run_regression_analyses(this_dataframe, 'Age', "ISC", formula, ['Age','mean_FD','sex'], 
                                            output_directory, root_filename=f'movie_ISC_vs_Age_MS',
                                            title='PartlyCloudy', plot=plot, verbose=verbose)
        results.to_csv(f'{output_directory}/movie_ISC_vs_Age_MS.csv', index=False)
        print(f"Finished {formula}\n")
        for id_type in ['TPHATE_DiffOp','PCA']:
            this_dataframe = dataframe[dataframe['measure'].isin([id_type, 'ISC'])]
            formula1 = f"{id_type} ~ Age + ISC + mean_FD + sex"
            results1 = run_regression_analyses(this_dataframe, 'ISC', id_type, formula1, ['Age','mean_FD','sex'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_AgeISC_MS',
                                              title='PartlyCloudy', plot=plot, verbose=verbose)
            results1.to_csv(f'{output_directory}/movie_{id_type}_vs_AgeISC_MS.csv', index=False)
            print(f"Finished {formula1}\n")

            formula2 = f"{id_type} ~ Age + mean_FD + sex"
            results2 = run_regression_analyses(this_dataframe, 'Age', id_type, formula2, ['mean_FD','sex','Age'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_Age_MS',
                                              title='PartlyCloudy', plot=plot, verbose=verbose)
            results2.to_csv(f'{output_directory}/movie_{id_type}_vs_Age_MS.csv', index=False)
            print(f"Finished {formula2}\n")

            formula2 = f"{id_type} ~ ISC + mean_FD + sex"
            results2 = run_regression_analyses(this_dataframe, 'ISC', id_type, formula2, ['mean_FD','sex'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_ISC_MS',
                                              title='PartlyCloudy', plot=plot, verbose=verbose)
            results2.to_csv(f'{output_directory}/movie_{id_type}_vs_ISC_MS.csv', index=False)
            print(f"Finished {formula2}\n")

    
    elif dataset == 'hbn':
        # Want to run: 
        # MOVIE: ID ~ ISC + Age + motion + ISC:Age + Age:motion
        # MOVIE: ID ~ Age + motion + Age:motion
        # REST: ID ~ Age + motion + Age:motion
        # DIFF: ID_DIFF ~ ISC + motion + ISC:motion
        # DIFF: ID_DIFF ~ Age + motion + Age:motion
        formula = f"ISC ~ Age + movie_FD  "
        dataframe = dataframe[dataframe['Age']<18]
        results = run_regression_analyses(dataframe, 'Age', "ISC", formula, ['Age','movie_FD','sex','session'], 
                                            output_directory, root_filename=f'movie_ISC_vs_Age_motion_child',
                                            title='Movie', plot=plot, verbose=verbose)
        results.to_csv(f'{output_directory}/movie_ISC_vs_Age_MSS_child.csv', index=False)
        print(f"Finished {formula}\n")

        for id_type in ['TPHATE_DiffOp']:#, 'PCA']:
            this_dataframe = dataframe[dataframe['measure'].isin([id_type, 'ISC'])]
            # # Movie analyses
            formula1 = f"{id_type} ~ Age + ISC + movie_FD  "
            results1 = run_regression_analyses(this_dataframe[this_dataframe['task']=='movieTP'], 'ISC', id_type, formula1, ['Age','movie_FD','sex','session'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_AgeISC_MSS_child',
                                              title='Movie', plot=plot, verbose=verbose)
            results1.to_csv(f'{output_directory}/movie_{id_type}_vs_AgeISC_MSS_child.csv', index=False)
            print(f"Finished {formula1}\n")

            # # Movie analyses
            formula1 = f"{id_type} ~ ISC + movie_FD   "
            results1 = run_regression_analyses(this_dataframe[this_dataframe['task']=='movieTP'], 'ISC', id_type, formula1, ['movie_FD','sex','session'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_ISC_MSS_child',
                                              title='Movie', plot=plot, verbose=verbose)
            results1.to_csv(f'{output_directory}/movie_{id_type}_vs_ISC_MSS_child.csv', index=False)
            print(f"Finished {formula1}\n")    

            formula2 = f"{id_type} ~ Age + movie_FD  "
            results2 = run_regression_analyses(this_dataframe[this_dataframe['task']=='movieTP'], 'Age', id_type, formula2, ['Age','movie_FD','sex','session'], 
                                              output_directory, root_filename=f'movie_{id_type}_vs_Age_MSS',
                                              title='Movie', plot=plot, verbose=verbose)
            results2.to_csv(f'{output_directory}/movie_{id_type}_vs_Age_MSS.csv', index=False)
            print(f"Finished {formula1}\n")
            
            # Rest analyses
            formula3 = f"{id_type} ~ Age + rest_FD  "
            results3 = run_regression_analyses(this_dataframe[this_dataframe['task']=='rest'], 'Age', id_type, formula3, ['Age','rest_FD', 'sex','session'],
                                              output_directory, root_filename=f'rest_{id_type}_vs_Age_MSS_child',
                                              title='Rest', plot=plot, verbose=verbose)
            # save this to a csv
            results3.to_csv(f'{output_directory}/rest_{id_type}_vs_Age_MSS_child.csv', index=False)
            print(f"Finished {formula3}\n")

            # Difference analyses
            temp_df = this_dataframe[this_dataframe['measure']==id_type]
            difference_df = clean_difference_dataframe(temp_df)
            # Merge in ISC values based on subject and region_name
            isc_df = this_dataframe[this_dataframe['measure']=='ISC'][['subject','region_name','score']]
            isc_df = isc_df.rename(columns={'score':'ISC'})

            difference_df = difference_df.merge(isc_df, on=['subject','region_name'], how='inner')
            formula4 = f"RestMovieDiff ~ ISC + movie_FD + rest_FD  "
            results4 = run_regression_analyses(difference_df, 'ISC', 'RestMovieDiff', formula4, ['movie_FD','rest_FD','sex','session'],
                                              output_directory, root_filename=f'RestMovieDiff_{id_type}_vs_ISC_MSS_child',
                                              title='Rest-Movie ', plot=plot, verbose=verbose)
            results4.to_csv(f'{output_directory}/RestMovieDiff_{id_type}_vs_ISC_MSS_child.csv', index=False)
            print(f'Finished {formula4}\n')

            formula5 = f"RestMovieDiff ~ Age + movie_FD + rest_FD + sex + session"
            results5 = run_regression_analyses(difference_df, 'Age', 'RestMovieDiff', formula5, ['movie_FD','rest_FD','sex','session', 'Age'], 
                                              output_directory, root_filename=f'RestMovieDiff_{id_type}_vs_Age_MSS_child',
                                              title='Rest-Movie ', plot=plot, verbose=verbose)
            results5.to_csv(f'{output_directory}/RestMovieDiff_{id_type}_vs_Age_MSS_child.csv', index=False)
            print(f'Finished {formula5}\n')

            formula5 = f"RestMovieDiff ~ Age + ISC + Age:ISC + movie_FD + rest_FD  "
            results5 = run_regression_analyses(difference_df, 'Age', 'RestMovieDiff', formula5, ['movie_FD','rest_FD','sex','session', 'Age'], 
                                              output_directory, root_filename=f'RestMovieDiff_{id_type}_vs_AgeISC_MSS_child',
                                              title='Rest-Movie ', plot=plot, verbose=verbose)
            results5.to_csv(f'{output_directory}/RestMovieDiff_{id_type}_vs_AgeISC_MSS_child.csv', index=False)
            print(f'Finished {formula5}\n')
    


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    p = parser.parse_args()


    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose : print(f'loaded {p.dataset}_utils')
    dataframe = load_results_dataframe()
    REGION_ORDER = dataframe['region_name'].values[:400].tolist()
    if p.dataset in ['hbn', 'partlycloudy']:
        # Join on the following covariates
        participant_df = utils.load_participant_df()
        dataframe = join_results_participant_info(dataframe, participant_df, p.dataset)
        if p.verbose: print(f'loaded and merged participant dataframe; shape : {dataframe.shape}')

    output_directory = utils.get_results_dir()+'/parcelwise_regression/'
    os.makedirs(output_directory, exist_ok=True)
    drive_analyses(dataframe, output_directory, dataset=p.dataset, plot=p.plot, verbose=p.verbose)



    
    
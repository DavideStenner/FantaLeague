import os
import cvxpy as cp
import numpy as np
import pandas as pd

from typing import Dict, Any, Tuple
from src.utils.import_utils import import_mapping_artists, import_results, import_results_api

def rescale_series(df: pd.Series) -> pd.Series:
    return (df - df.min())/(df.max()-df.min())

def fantasenrmo_composition_v1(df: pd.DataFrame, number_suggestion: int, config: dict[str, Any]) -> Tuple[
        cp.Problem, cp.Variable
    ]:
    #dummy variable for selection
    selection = cp.Variable(number_suggestion, boolean=True)

    #score
    score = cp.Constant(df['score'].values.tolist())
    
    #weight for constraint
    quotazione = cp.Constant(df['quotazione'].values.tolist())

    problem_knapsack = sum(cp.multiply(score, selection))

    constraint_list = [
        sum(cp.multiply(selection, quotazione)) <= config['num_baudi'],
        sum(selection) == config['num_selection'],
    ]
    fanta_problem = cp.Problem(
        cp.Maximize(problem_knapsack), constraint_list
    )
    return fanta_problem, selection

def fantasenrmo_composition_v2(df: pd.DataFrame, number_suggestion: int, config: dict[str, Any]) -> Tuple[
        cp.Problem, cp.Variable, cp.Variable
    ]:
    #dummy variable for selection
    selection = cp.Variable(number_suggestion, boolean=True)
    reserve = cp.Variable(number_suggestion, boolean=True)

    #score reserve
    weight_reserve: float = config['weight_reserve']
    
    score_reserve = cp.Constant(
        (df['score'] * weight_reserve).values.tolist()
    )
    #score
    score = cp.Constant(df['score'].values.tolist())
    
    #weight for constraint
    quotazione = cp.Constant(df['quotazione'].values.tolist())

    artist_score =(
        cp.multiply(
            score, 
            selection
        ) +
        #if reserve -> score reserve
        cp.multiply(
            reserve,
            score_reserve
        )
    )
    problem_knapsack = sum(artist_score)

    constraint_list = [
        sum(cp.multiply(selection, quotazione)) + sum(cp.multiply(reserve, quotazione))<= config['num_baudi'],
        sum(selection) == config['num_selection'],
        sum(reserve) == config['num_reserve'],
        selection + reserve <= 1
    ]
    fanta_problem = cp.Problem(
        cp.Maximize(problem_knapsack), constraint_list
    )
    return fanta_problem, selection, reserve

def get_artists_composition(
        df: pd.DataFrame, config: Dict[str, Any],
    ) -> Tuple[pd.DataFrame, float]:
    
    number_suggestion = df.shape[0]

    fanta_problem, selection, reserve = fantasenrmo_composition_v2(
        df=df, number_suggestion=number_suggestion, config=config
    )
    score = fanta_problem.solve(solver=cp.SCIPY)
    selection_results = np.round(selection.value).astype(int)
    reserve_results = np.round(reserve.value).astype(int)

    #assign reserve
    df['reserve'] = False
    df.loc[reserve_results==1, 'reserve'] = True
    
    results = df.loc[
        (selection_results==1) |
        (reserve_results==1)
    ]
    assert results['quotazione'].sum() <= config['num_baudi']

    return results, score

def calculate_score(
        df: pd.DataFrame, use_spotify: bool
    ):
    #score
    df['choose_score'] = rescale_series(
        df['weight']/(df['frequency'] * 5)
    )
    df['captain_score'] = rescale_series(
        df['captain']/df['frequency']
    )

    if use_spotify:
        #rescale
        df['popularity'] = df['popularity'] / 100 

        df['score'] = (
            df['score_captain'] * .3 + 
            df['popularity'] * .6 +
            
            #collinearity with score_captain
            df['softmax_quotazione'] * .0
        ) 
    else:
        df['score'] = (
            #has they choose and in what order
            (2/3 * df['choose_score']) +
            
            #is it the chaptain?
            (1/3 * df['captain_score'])
        )

        
    return df    

def get_best_team(
    config: Dict[str, Any], league: str, 
    print_all: bool, 
    use_leaderboard: bool, 
    use_spotify: bool, save_df: bool
):
    if use_leaderboard:
        save_folder = os.path.join(
            config['path_leaderboard_result'], 
            league
        )
    else:
        save_folder = os.path.join(
            config['path_save_optimization'], 
            league
        )

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    mapping_artits = import_mapping_artists()

    results = import_results_api(league=league)

    df = pd.DataFrame(results).reset_index().rename(columns={'index': 'artist_scrape_id'})

    df['artist'] = df['artist_scrape_id'].map(
        {
            artist_url.split('/')[-1].split('-')[0]: artist_name
            for artist_url, artist_name in mapping_artits['artists_mapping'].items()
        }
    )
    df = df.loc[
        (~df['artist'].isin(mapping_artits['banned_artists'])) &
        (~df['artist'].isnull())
    ].reset_index(drop=True)

    df['quotazione'] = df['artist'].map(mapping_artits['quotazioni'])
    df['rank'] = df['quotazione'].rank(method='average')
    df = df[
        ['artist'] + [col for col in df if col!='artist']
    ].drop('artist_scrape_id', axis=1)
    
    if use_spotify:
        spotify_result = pd.read_csv('spotify_result/spotify_results.csv')
        df = df.merge(spotify_result)
    
    #rank medio
    if use_leaderboard:
        leaderboard_results = mapping_artits['classifica_artisti']
        df['score'] = df['artista'].map(leaderboard_results)

        #inspect
        df['score_quotazione'] = df['score']/df['quotazione']

    else:
        df = calculate_score(df, use_spotify=use_spotify)
    
    if save_df:
        df.to_csv('data_feature/results.csv', index=False)

    composition, score = get_artists_composition(df, config=config)
    composition = (
        composition
        .sort_values('score', ascending=False)
        .reset_index(drop=True)
    )
    if print_all:
        print('\n\n')
        print(df.sort_values('score', ascending=False).to_markdown())
        print('\n\n')

    print(f'\n\nScore of after optimization: {score}\n\n')
    print(composition.to_markdown())
    
    composition.to_csv(
        os.path.join(save_folder, league+'.csv'), 
        index=False
    )

def get_best_spotify_team(
    config: Dict[str, Any],
    print_all: bool, 
):

    save_folder = os.path.join(
        config['path_save_optimization'], 
        'spotify'
    )

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    mapping = import_mapping_artists()
    df = pd.read_csv('spotify_result/spotify_results.csv')

    df['quotazione'] = df['artista'].map(mapping['quotazioni'])
    df['score'] = df['popularity']
    
    composition, score = get_artists_composition(df, config=config)
    composition = (
        composition
        .sort_values('score', ascending=False)
        .reset_index(drop=True)
    )
    if print_all:
        print('\n\n')
        print(df.sort_values('score', ascending=False).to_markdown())
        print('\n\n')

    print(f'\n\nScore of after optimization: {score}\n\n')
    print(composition.to_markdown())
    
    composition.to_csv(
        os.path.join(save_folder + 'spotify.csv'), 
        index=False
    )

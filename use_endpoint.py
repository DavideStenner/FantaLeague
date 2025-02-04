if __name__=='__main__':
    import os
    import time
    import json
    import requests
    import argparse
    from collections import Counter
    
    from tqdm import tqdm
    from typing import Any, Type
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--league', type=str, default="TicketOne")
    args = parser.parse_args()

    from src.utils.import_utils import import_config, import_credential
    
    bear_token_list = import_credential()['bear_token']
    
    config_dict: dict[str, Any] = import_config()
    league_id: str = config_dict['league_dict'][args.league]
    
    endpoint_: str = config_dict['endpoing_url']
    
    result_total = requests.get(
        endpoint_.format(
            league_id=league_id,
            limit=10,
            skip=0    
        ),
        headers={
            'accept': 'application/json',
            'authorization': bear_token_list[0]
        }
    )
    total_user = json.loads(result_total.content)['totalUsers']

    users_list = []
    has_next: bool = True
    skip: int = 0
    limit: int = 6000
    pbar = tqdm(total=int(total_user//limit))

    results_counter: Type[Counter] = Counter()
    captain_counter: Type[Counter] = Counter()
    score_selection_counter: Type[Counter] = Counter()

    current_password = 0
    retry: int = 5
    
    while (has_next) & (retry>0):

        result = requests.get(
            endpoint_.format(
                league_id=league_id,
                limit=limit,
                skip=skip
            ),
            headers={
                'accept': 'application/json',
                'authorization': bear_token_list[current_password]
            }
        )
        if result_total.status_code == 200:
            parsed_result = json.loads(result.content)
            
            if 'hasNext' in parsed_result:
                has_next = parsed_result['hasNext']
                skip += limit
                for user_ in parsed_result['users']:
                    if user_['team']['settings']['secret']:
                        continue
                    
                    team_ = user_['team']['artistIds']

                    results_counter.update(team_)
                    captain_counter.update([team_[0]])
                    
                    for weight, artists in enumerate(team_):
                        score_selection_counter[artists] += (7 - weight)
                                        
                pbar.update()
                time.sleep(0.2)
                retry = 5
            
            else:
                print(parsed_result)
                print('retring')
                current_password = 1 - current_password
                skip += limit
                retry -= 1
                time.sleep(60)

        else:
            print(parsed_result)
            print('retring')
            current_password = 1 - current_password
            time.sleep(30)
    
    save_results = {
        'frequency': results_counter,
        'captain': captain_counter,
        'weight': score_selection_counter,
    }
    if not os.path.exists(f'data/{args.league}'):
        os.makedirs(f'data/{args.league}')

    with open(f'data/{args.league}/result_api.json', 'w') as file:
        json.dump(
            save_results, 
            file
        )
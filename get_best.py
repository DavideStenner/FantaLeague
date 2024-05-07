if __name__=='__main__':
    import argparse
    
    from src.utils.import_utils import import_config
    from src.optimization.best_team import get_best_team, get_best_spotify_team
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--league', type=str, default="TicketOne")
    parser.add_argument('--print_all', action='store_true')
    parser.add_argument('--use_leaderboard', action='store_true')
    parser.add_argument('--use_spotify', action='store_true')
    parser.add_argument('--use_only_spotify', action='store_true')
    parser.add_argument('--save_df', action='store_true')

    args = parser.parse_args()
    config = import_config()
    
    if args.use_only_spotify:
        get_best_spotify_team(
            config=config, print_all=args.print_all
        )
    else:
        get_best_team(
            config=config, **vars(args)
        )
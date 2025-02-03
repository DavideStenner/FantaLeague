if __name__=='__main__':
    import argparse
    
    from src.utils.import_utils import import_config
    from src.scraper.fanta.scraper import ScraperFanta
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--league', type=str, default="TicketOne")
    parser.add_argument('--number_page_scrape', type=int, default=None)
    parser.add_argument('--pct_scrape', type=float, default=0.7)
    parser.add_argument('--backup', type=int, default=1000)
    parser.add_argument('--keep_active_pc_iteration', type=int, default=None)
    parser.add_argument('--check_unique_name', action='store_true')
    parser.add_argument('--keep_no_pic', action='store_true')
    parser.add_argument('--scrape_all_league', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    if args.scrape_all_league:
        del args.league
        del args.scrape_all_league
        league_dict = import_config()['league_dict']
            
        
        for league_name, league_id in league_dict.items():
            print(f'\n\nStarting {league_name}')
            
            scraper = ScraperFanta(
                league=league_name,
                **vars(args)
            )
            scraper()
    else:
        del args.scrape_all_league
        print(f'\n\nStarting {args.league}')
        scraper = ScraperFanta(
            **vars(args)
        )
        scraper()

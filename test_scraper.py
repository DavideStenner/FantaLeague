#%%
from scraper import ScraperFanta

# %%
scraper = ScraperFanta(number_page_scrape = 5, test=True, backup=1)
scraper.activate_bot()

#%%
scraper.quit()

import os
import json
import numpy as np
import pyautogui

from bs4 import BeautifulSoup
from tqdm import tqdm
from glob import glob
from time import sleep
from math import floor
from typing import Dict, Any, Type, Optional
from collections import Counter

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager

from src.utils.import_utils import set_key_env, import_config

class ScraperFanta():
    def __init__(
        self,
        league: str,
        number_page_scrape: int=None, pct_scrape: float =.6, 
        backup: int = 500, keep_active_pc_iteration: int = 25,
        check_unique_name: bool=False, keep_no_pic:bool=False,
        test: bool =False, overwrite: bool = True

    ):
        pyautogui.FAILSAFE = False
        
        self.league: str = league
        self.config: Dict[str, Any] = import_config()

        self.backup: int = backup
        self.test: bool = test
        self.check_unique_name: bool = check_unique_name 

        self.keep_no_pic: bool = keep_no_pic
        
        self.number_page_scrape: int = number_page_scrape
        self.keep_active_pc_iteration: Optional[int] = keep_active_pc_iteration
        self.pct_scrape: float =pct_scrape
        self.overwrite: bool = overwrite
        
        self.driver: Type[webdriver.Chrome] = None
        self.path_save: str = f"data/{league}/"

        self.create_folder_structure()
        self.initialize_config()
        

    def create_folder_structure(self) -> None:
        if not os.path.exists(self.path_save):
            os.makedirs(self.path_save)

        if not os.path.exists(os.path.join(self.path_save, 'backup')):
            os.makedirs(os.path.join(self.path_save, 'backup'))

        if self.overwrite:
            list_file = glob(
                os.path.join(self.path_save, '**/results*.json'), 
                recursive=True
            )
            for file_path in list_file:
                os.remove(file_path)

    def initialize_config(self) -> None:
        set_key_env()
        
        self.email = os.getenv('email')
        self.password = os.getenv('password')

        assert self.league in self.config["league_dict"].keys()
        
        self.results: Type[Counter] = Counter()
        self.captain: Type[Counter] = Counter()
        self.score_selection: Type[Counter] = Counter()

        self.unique_team_set: set = set([self.config['personal_team_name']])

        self.league_id: str  = self.config["league_dict"][self.league]
        
    def initialize_driver(self) -> None:
        chrome_options = Options()
        if not self.test:
            chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options = chrome_options
        )
        driver.get(self.config['link'])
        self.driver = driver

    def wait_and_click_by(
        self, by_: str, pattern: str, 
    ) -> None:
        element_ = self.wait_and_get(by_, pattern, EC.element_to_be_clickable, return_element=True)

        actions = webdriver.ActionChains(self.driver)
        actions.move_to_element(element_)
        actions.click(element_)
        actions.perform()

    def wait_and_get(self, by_: str, pattern: str, conditions: callable, return_element: bool =False)-> WebElement:
        element_ = (
            WebDriverWait(
                self.driver, 
                self.config['wait_time']
            )
            .until(
                conditions(
                    (by_, pattern)
                )
            )
        )
        if return_element:
            return element_
    
    def quit(self) -> None:
        self.driver.quit()

    def handle_cookie(self) -> None:
        #find cookie
        refusal_cookie = self.wait_and_get(
            By.XPATH, 
            self.config['xpath_dict']['coockie'], 
            EC.presence_of_element_located, 
            return_element=True
        )
        if refusal_cookie.is_displayed():
            self.wait_and_click_by(
                By.XPATH, 
                self.config['xpath_dict']['coockie']
            )

    def login(self) -> None:
        print('Login')
        self.handle_cookie()
        
        actions = webdriver.ActionChains(self.driver)

        input_email = self.wait_and_get(
            By.XPATH, 
            self.config['xpath_dict']['login_email'], 
            EC.presence_of_element_located,
            return_element=True
        )
        actions.move_to_element(input_email)
        actions.perform()
        input_email.send_keys(self.email)

        input_password = self.wait_and_get(
            By.XPATH, self.config['xpath_dict']['login_password'],
            EC.presence_of_element_located,
            return_element=True
        )
        
        actions.move_to_element(input_password)
        actions.perform()
        input_password.send_keys(self.password)

        self.wait_and_click_by(By.XPATH, self.config['xpath_dict']['accept_credential'])
        
        #skip tutorial
        self.wait_and_click_by(
            By.XPATH, self.config['xpath_dict']['skip_tutotial']
        )
        
        #go to league page
        self.driver.get(f"{self.config['base_link']}/league?id={self.config['league_dict'][self.league]}")
        
        if self.number_page_scrape is None:
            
            self.calculate_total_page()
            
    def calculate_total_page(self) -> None:
        #calculate number of page to scraper
        print('Calculating total number of page')
        #wait element
        self.wait_and_get(By.XPATH, self.config['xpath_dict']['total_team'], EC.presence_of_element_located)
        soup = self.get_html_source()

        total_team_label: str = soup.find(
                'h6', 
                {"class": self.config["class_dict"]['number_total_team']}
            ).getText().replace(self.config['language_config']['team_box_text'], '')
        
        if 'k' in total_team_label.lower():
            total_team_label = total_team_label.lower().replace('k', '00').replace('.', '')
            
        total_number_team = floor(int(total_team_label)/1000) * 1000
                                
        used_number_team = int(total_number_team * self.pct_scrape)

        self.number_page_scrape = int(used_number_team//self.config["number_element_by_page"])
        print(f'Number of different teams: {total_number_team}')
        print(f'Number of scraped teams for {self.pct_scrape*100:.1f}%: {used_number_team}')
        
        print(f'Number of pages to scrape: {self.number_page_scrape}')

    def get_html_source(self) -> BeautifulSoup:
        html_current_page = self.driver.page_source
        soup = BeautifulSoup(html_current_page, features="html.parser")
        return soup

    def keep_team(self, team_box: BeautifulSoup) -> bool:
        box_pic = team_box.find(
            'div', {'class': self.config['class_dict']['team_pic']}
        )
        if box_pic is None:
            return False
        
        image_url = box_pic.find('img')['src']
        keep_it = self.config['no_pic_url'] not in image_url
        return keep_it
                    
    def get_statistics(self) -> None:
        sleep(.5)
        soup = self.get_html_source()

        team_box_list = soup.find_all('div', {"class": self.config["class_dict"]['box_info']})

        if not self.keep_no_pic:

            team_box_list = [
                team_box for team_box in team_box_list
                if self.keep_team(team_box=team_box)
            ]
            
        for team_box in team_box_list:
            team_name = team_box.find('div', {'class': self.config["class_dict"]['team_info']}).getText().strip()
            
            if self.check_unique_name:
                if (team_name not in self.unique_team_set) & (team_name != ''):
                    self.unique_team_set.add(team_name)

                    artists_list = [
                        x.get('src')
                        for x in team_box.find_all('img')
                        if ('artists/' in x.get('src')) or ('assets/' in x.get('src'))
                    ]

                    artists_counter = Counter(artists_list)

                    for weight, artists in enumerate(artists_list):
                        self.score_selection[artists] += (self.config["num_selection"] - weight)

                    self.captain.update(set([artists_list[0]]))
                    self.results.update(artists_counter)
            else:
                artists_list = [
                    x.get('src')
                    for x in team_box.find_all('img')
                    if ('artists/' in x.get('src')) or ('assets/' in x.get('src'))
                ]

                artists_counter = Counter(artists_list)

                for weight, artists in enumerate(artists_list):
                    self.score_selection[artists] += (self.config["num_selection"] - weight)

                self.captain.update(set([artists_list[0]]))
                self.results.update(artists_counter)

    def get_next_page(self) -> None:
        #not necessary to scan every button -> next page is the last loaded
        self.wait_and_click_by(By.XPATH, self.config["xpath_dict"]['next_page'])

    def random_sleep(self) -> None:
        sleep_time = np.random.uniform(.1, .25, 1)[0]
        sleep(sleep_time)

    def save_results(self, iteration=None) -> None:

        save_results = {
            'frequency': self.results,
            'captain': self.captain,
            'weight': self.score_selection,
        }
        path_save = (
            os.path.join(self.path_save, 'backup', f"results_{iteration}.json") 
            if iteration is not None 
            else os.path.join(self.path_save, "results.json")
        )
        with open(
            path_save, 
            "w"
        ) as outfile:
            json.dump(dict(save_results), outfile)

    def keep_pc_active(self) -> None:

        pyautogui.press('volumedown')
        sleep(.01)
        pyautogui.press('volumeup')

    def activate_bot(self) -> None:
        self.login()

        self.get_statistics()
        self.random_sleep()

        for iteration in tqdm(range(self.number_page_scrape)):
            if (iteration % self.backup == 0) & (iteration > 0):
                self.save_results(iteration)
            
            if self.keep_active_pc_iteration is not None:
                if (iteration % self.keep_active_pc_iteration == 0) & (iteration > 0):
                    self.keep_pc_active()

            self.get_next_page()
            self.get_statistics()
            self.random_sleep()

        self.save_results()

    def __call__(self):
        self.initialize_driver()
        try:
            self.activate_bot()
            self.quit()
            
        except Exception as e:
            self.quit()
            raise e
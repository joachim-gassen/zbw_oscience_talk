from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import pandas as pd

SCRAPE_URLS = False
SCRAPE_REPO_INFO = False

root_url = "https://www.openicpsr.org/openicpsr/search/aea/studies"

def dload_dta_rep(driver, url):
    cit = views = dloads = pubs = last_mod = pub_refs = None
    try: 
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH,'//*[@id="projectUsage"]/div/div[1]/div[1]/div')
            )
        )
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        views = int(soup.find('span', attrs={"data-reactid": ".1.2.0.0.0"}).text)
        dloads = int(soup.find('span', attrs={"data-reactid": ".1.2.1.0.0"}).text)
        pubs = int(soup.find('span', attrs={"data-reactid": ".1.2.2.0.0"}).text)

        last_mod = soup.select(
            "#mainContent > article > div.row > div.col-md-8 > div.table-responsive > table > tbody > tr > td:nth-child(4)"
        )[0].text
        cit = soup.find('div', attrs={"class": "csl-entry"}).text.strip()
  
    except:
        logging.warning(f"Failed to scrape url: '{url}'")
        return {
            'cit': cit, 'views': views, 'dloads': dloads, 'pubs': pubs,
            'last_mod': last_mod, 'pub_refs': pub_refs
        }

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="imeta_publications_datacite:isSupplementedBy_0propertyWrapper"]')
            )
        )
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        pub_refs = soup.find('div', attrs={"id": "bibliography"}).text 
        logging.debug(f"Successfully scraped url: '{url}'")  
        return {
            'cit': cit, 'views': views, 'dloads': dloads, 'pubs': pubs,
            'last_mod': last_mod, 'pub_refs': pub_refs
        }
    
    except:
        logging.warning(f"Failed to scrape pub refs for url: '{url}'")
        return {
            'cit': pub_refs, 'views': views, 'dloads': dloads, 'pubs': pubs,
            'last_mod': last_mod, 'pub_refs': pub_refs
        }


def read_urls_on_page(driver):
  html = driver.page_source
  soup = BeautifulSoup(html, 'html.parser')
  urls = []
  for i in range(25):
    lnk = soup.find(
        'a', attrs={"data-reactid": f".0.0.1.7.0.2:${i}.1.0.0.0.0.0"}
    )
    if lnk == None: break
    urls.append(lnk['href'])
  return urls

if SCRAPE_URLS or SCRAPE_REPO_INFO:
  chromedriver_autoinstaller.install()
  driver = webdriver.Chrome()

if SCRAPE_URLS:
  driver.get(root_url)

  urls = []

  while True:
    urls = urls + read_urls_on_page(driver)
    next_page_element = driver.find_element(
      By.XPATH, '//span[@data-reactid=".0.0.1.8.2.0.2.0.0"]' 
    )
    if next_page_element == None: break
    next_page_element.click()

  pd.DataFrame({'url': urls}).to_csv("data/openicpsr_aea_urls.csv", index = False) 

else: urls = pd.read_csv("data/openicpsr_aea_urls.csv")['url'].values.tolist()

if SCRAPE_REPO_INFO:
    dta = []
    for url in urls:
        dta.append(dload_dta_rep(driver, url))

    dta = pd.DataFrame(dta)
    dta.to_csv("data/openicpsr_aea_repo_info.csv", index=False) 

else: 
  dta = pd.read_csv("data/openicpsr_aea_repo_info.csv")

dta.insert(0, "url", urls)

def clean_pub_ref_str(prstr):
    if not isinstance(prstr, str): return ''
    prstr = prstr.replace(
        'The following publications are supplemented by the data in this project.\n', ''
    )
    prstr = prstr.replace(
        '\n  ×CloseDelete Citation?Are you sure? Click yes to delete citation.YesNo', ''
    )
    return prstr

dta['pub_refs'] = [clean_pub_ref_str(x) for x in dta['pub_refs'].values.tolist()]

dta.to_csv("data/openicpsr_aea_data.csv", index=False) 


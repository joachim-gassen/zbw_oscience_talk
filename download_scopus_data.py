import pandas as pd
import re
from itertools import chain
from pybliometrics.scopus import ScopusSearch

dta = pd.read_csv("data/openicpsr_aea_data.csv")
pub_refs = dta['pub_refs'].values.tolist()
pub_urls = []
for r in pub_refs:
    if not isinstance(r, str): pub_urls.append([])
    else: pub_urls.append(re.findall("https?://[^\s]*[^\s.]", r))

dois = list(chain.from_iterable(pub_urls))
dois = [x.lstrip("https://doi.org/") for x in dois]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

for chunk in chunks(dois, 40):
    q = f"DOI({') or DOI ('.join(chunk)})"  
    s = ScopusSearch(q, refresh = 30)  
    pubs = s.results  
    new_pubs = pd.DataFrame.from_dict(pubs)
    if 'df_pubs' in locals():
        df_pubs = pd.concat([df_pubs, new_pubs], ignore_index = True, sort = False)
    else: df_pubs = new_pubs 

df_pubs.to_csv("data/scopus_data.csv", index = False)

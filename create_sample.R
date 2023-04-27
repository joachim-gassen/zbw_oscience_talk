library(tidyverse)
library(lubridate)

dta <- read_csv("data/openicpsr_aea_data.csv", col_types = cols()) 
doi_urls <- str_extract_all(
  dta$pub_refs, "https?://[^\\s]*[^\\s.]", simplify = TRUE
)
colnames(doi_urls) <-paste0("doi", 1:7)
urls <- bind_cols(url = dta$url, doi_urls ) %>% 
  pivot_longer(cols = starts_with("doi"), values_to = "doi") %>%
  filter(!is.na(doi) & doi != "") %>% select(-name) %>%
  mutate(doi = substr(doi, 17, nchar(doi))) %>%
  distinct()

citation_data <- read_csv("data/scopus_data.csv", col_types = cols()) %>% 
  select(
    doi, journal = publicationName, date = coverDate, cites = citedby_count
  )

smp <- dta %>% left_join(urls, by = "url", multiple = "all") %>% 
  left_join(citation_data, by = c("doi") , multiple = "all")

write_csv(smp, "data/talk_smp.csv")

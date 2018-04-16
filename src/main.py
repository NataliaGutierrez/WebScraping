from vaacscraper import VAACScraper

from datetime import datetime

# Date limits for the dataset
idate=datetime(2017,10,1)
edate=datetime(2018,3,31,23,59,59)
idate.isoformat(' ')
edate.isoformat(' ')

# All volcanoes VAA will be scraped between specified dates, and dataset stored
# in the provided file
scraper = VAACScraper(idate,edate,filename="dataset.csv");
scraper.scraping();
from vaacscraper import VAACScraper

from datetime import datetime

output_file = "dataset.csv"

idate=datetime(2018,3,31)
edate=datetime.utcnow()
idate.isoformat(' ')
edate.isoformat(' ')
scraper = VAACScraper(idate,edate);
html=scraper.download_html(scraper.url)
#scraper.scraping();
#scraper.write_csv(output_file);

from vaacscraper import VAACScraper

from datetime import datetime

output_file = "dataset.csv"

idate=datetime(2018,4,11,13,00,00)
edate=datetime.utcnow()

#idate=datetime(2017,6,21)
#edate=datetime(2017,6,25)
idate.isoformat(' ')
edate.isoformat(' ')
scraper = VAACScraper(idate,edate);
#html=scraper.download_html(scraper.url)
data=scraper.scraping();
scraper.write_csv(output_file);

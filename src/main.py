from vaacscraper import VAACScraper

output_file = "dataset.csv"


scraper = VAACScraper(idate,edate);
scraper.scraping();
scraper.write_csv(output_file);

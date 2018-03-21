from vaacrawler import VAACrawler

output_file = "dataset.csv"


crawler = VAACrawler(idate,edate);
crawler.crawl();
crawler.write_csv(output_file);

import urllib
import urllib.robotparser
from datetime import datetime
from time import strptime
from time import mktime
from bs4 import BeautifulSoup

class VAACScraper():
    """Documentation"""
    def __init__(self, idate, edate, useragent="wswp"):
        	# Inicialitzar parametres sobre webpage
        	# Si no tenim etime com input, considerar data actual
        self.idate = idate
        self.edate = edate
        self.domain = "http://www.ssd.noaa.gov/"
        self.url = self.domain + "VAAC/messages.html"
        self.useragent = useragent
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(self.domain + "robots.txt")
        self.rp.read()
    def __checking_useragent(self, url):
        return self.rp.can_fetch(self.useragent, url)
    
    def download_html(self, url, num_retries=2):
        headers = {'User-agent': self.useragent}
        request = urllib.request.Request(url, headers=headers)
        try:
            html = urllib.request.urlopen(request).read()
        except urllib.URLError as e:
            print('Download error:', e.reason)
            html = None
            if num_retries > 0:
                # Retry if there is a server problem
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    # recursively retry 5xx HTTP errors
                    return self.__download_html(url, num_retries-1)
        return html

    def __crawling_links(self, html):
        # En la pagina principal dels VAAC, hem de trobar els links pels anys que volem
        years=range(self.edate.year,self.idate.year-1,-1)
        
        soup = BeautifulSoup(html, "lxml")
        
        # List of links for all required years
        ylinks = []
        for year in years:
            tmp = soup.find(name='a',text=str(year))
            if tmp:
                ylinks.append(tmp.get('href'))
            else:
                print('there is no link for year %d',year)
                
    
        # webpage for current year has different format. 
        if datetime.utcnow().year == years[0]:
            # Search in special format
            
            # The general loop will be from second element, set initial index
            fidx = 1
        else:
            # THe general loop will be from first element, set initial index
            fidx = 0
        
        for idx in range(fidx,len(ylinks),1):
            url = self.domain + ylinks[idx]
            html = self.__download_html(url)
            tags = soup.find_all("table")
            cols = tags[-1].find_all('td',attrs={"valign": "top"})
            for col in cols:
                valid = False
                for child in col.children:
                    if (child.name=='dt'):
                        # Child is name of section
                        # Check wrong section
                        title = child.find('em').get_text().lower()
                        if ('user message' in title)|('test ' in title):
                            valid= False
                        else:
                            valid= True
                    if (child.name=='dd'&valid):
                        tmp = child.find('em').get_text() + child.find('a').get_text()
                        mydate=datetime.fromtimestamp(mktime(strptime(tmp,"%d %b %Y - %H%M UTC")))
                        if (mydate>idate & mydate<edate):
                             child.find('a').get('href')
                                
                            
                        
                        
                
            
        
        # Del html descarregat, trobar els links d'on descarregar els volcanic 
        # ash advisories.
        # Només descarregar els informes dins de l'interval de temps (self.idate,self.edate)
        return ylinks
    def __scraping_advisory(self,html):
        # Extreure les dades interessants. Insertar registre en dataframe
        a=1
    def scraping(self):
        if self.__checking_useragent(self.url):
            html = self.__download_html(self.url)
            links = self.__crawling_links(html)
            for link in links:
                print(link)

    '''
    		# Comprobar amb el robots.txt si el meu user agent no esta bloquejat
    		self.__checking_useragent();
    
    		# descarregar archive webpage
    		html = self.__download_html(self.url)
    		# Trobar els links dels advisories
    		links = self.__crawling_links(html)
    		# Extreure les dades de cada advisory
    		for url in links:
    			html = self.__download_html(url)
    			self.__scraping_advisory(html);
    '''				
    
    def write_csv(self, filename):
        # Escriure fitxer
        a=1
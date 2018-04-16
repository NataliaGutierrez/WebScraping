import urllib
import urllib.robotparser
from datetime import datetime
from time import strptime
from time import mktime
from bs4 import BeautifulSoup
import re
import os.path
import pandas as pd
import advisory

class VAACScraper():
    """Documentation"""
    def __init__(self, idate, edate, volcanoes=[], useragent="wswp"):
        	# Inicialitzar parametres sobre webpage
        self.idate = idate
        self.edate = edate
        self.domain = "http://www.ssd.noaa.gov/"
        self.url = []
        self.useragent = useragent
        # Robot parsed
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(self.domain + "robots.txt")
        self.rp.read()
        
        # Set list of volcanoes required. If is not any, all will be taken into
        # account.
        self.volcanoes = []
        for volcano in volcanoes:
            self.volcanoes.append( volcano.lower() )
            
        self.row_list=[]
    def __checking_useragent(self, url):
        return self.rp.can_fetch(self.useragent, url)
    
    def __absolute_ref( self, relativelink ):
        # Starting by / character, it is relative to website
        if (relativelink[0] == '/'):
            return self.domain + relativelink[1:]
        # otherwise, it is relative to local root
        else:
            return os.path.dirname(self.url) + '/' + relativelink
        
    def __download_html(self, url, num_retries=2):
        if not self.__checking_useragent(url):
            print("WARNING: Blocked by robots.txt")
            return []
        headers = {'User-agent': self.useragent}
        request = urllib.request.Request(url, headers=headers)
        try:
            html = urllib.request.urlopen(request).read()
        except urllib.error.URLError as e:
            print('Download error:', e.reason)
            html = None
            if num_retries > 0:
                # Retry if there is a server problem
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    # recursively retry 5xx HTTP errors
                    return self.__download_html(url, num_retries-1)
        self.url = url
        return html
    
    def __check_advisories_section( self, title ):
        name = title.lower()
        
        if len(self.volcanoes)>0:
            for volcano in self.volcanoes:
                if (volcano.lower() in name):
                    return True
            return False
        if ('user message' in name)|('test ' in name):
            return False
        return True
    
    def __find_archive(self):
        html = self.__download_html(self.domain)
        if not html:
            raise ValueError('Can not download main webpage')
        
        soup = BeautifulSoup(html, "lxml")
        
        token = soup.find(name='a',text="Volcano Information")
        token = token.find_next(name='a',text="Advisories")
        self.url = self.__absolute_ref(token.get('href'))
            
    def __crawling_links(self, html):
        # En la pagina principal dels VAAC, hem de trobar els links pels anys que volem
        years=range(self.edate.year,self.idate.year-1,-1)
        
        soup = BeautifulSoup(html, "lxml")
        
        # List of links for all required years
        ylinks = []
        for year in years:
            tmp = soup.find(name='a',text=str(year))
            if tmp:
                # TODO: path absoluto, comprobar relativo a website o root local(self.url)
                
                ylinks.append(self.__absolute_ref(tmp.get('href')))
            else:
                print('there is no link for year %d',year)
                
    
        mylinks = []
        # THe general loop will be from first element, set initial index
        fidx = 0
        # Check if webpage for first year has different format.
        if datetime.utcnow().year == years[0]:
            # Search in special format
            html = self.__download_html(ylinks[0])
            if not html:
                raise ValueError("Can not download "+ylinks[0])
            soup = BeautifulSoup(html, "lxml")
            
            token = soup.find(name="strong", text=re.compile("^Advisories Last Updated"))
            
            # Find term lists as siblings
            sectnodes = token.find_next_siblings("dt")
            # If there is any, html is in odd format. So the general loop will 
            # be from second year
            if (len(sectnodes)>1):
                fidx = 1
                
            for section in sectnodes:
                title = section.find('em').get_text()
                    # If section is wrong section, advisories in this section will 
                    # not be read. Also filter by volcano if there is input 
                    # list
                if (self.__check_advisories_section( title ) == False):
                    continue
                
                for sibling in section.next_siblings:
                    if getattr(sibling, 'name', None) == 'dt':
                        # It is next section already
                        break
                    if getattr(sibling, 'name', None) == 'dd':
                        tmp = sibling.find('em').get_text() + sibling.find('a').get_text()
                        mydate=datetime.fromtimestamp(mktime(strptime(tmp,"%d %b %Y - %H%M UTC")))
                        # Filter by date
                        if (mydate>self.edate):
                            continue
                        if (mydate<self.idate):
                            break
                        
                        mylinks.append(self.__absolute_ref(sibling.find('a').get('href')))
        # TODO: rediseñar
        # Crawling for rest of years
        for idx in range(fidx,len(ylinks),1):
            # No hace falta root, conseguirlo desde self.url que siempre estara actualizado.
            # POner update del self.url primera linea de download_html. 
            html = self.__download_html(ylinks[idx])
            if not html:
                raise ValueError("Can not download "+ylinks[idx])
                
            soup = BeautifulSoup(html, "lxml")
            # Regular format, the data is in a table with columns(cells).
            tags = soup.find_all("table")
            # In last table there are the data
            cols = tags[-1].find_all('td',attrs={"valign": "top"})
            for col in cols:
                valid = False
                for child in col.children:
                    if (child.name=='dt'): # Child is name of section
                        title = child.find('em').get_text()
                        # If section is wrong section, next sdvisry record will 
                        # not be read. Also filter by volcano if there is input 
                        # list
                        valid = self.__check_advisories_section( title )
                        
                    if ((child.name=='dd') & valid): # Child is advisory record
                        tmp = child.find('em').get_text() + child.find('a').get_text()
                        mydate=datetime.fromtimestamp(mktime(strptime(tmp,"%d %b %Y - %H%M UTC")))
                        # Filter by date
                        if ((mydate>self.idate) & (mydate<self.edate)):
                            mylinks.append(self.__absolute_ref(child.find('a').get('href')))
                        if (mydate<self.idate):
                            valid = False;
                             
        return mylinks
    
    def __scraping_advisory(self,html):
        '''
        Scrape required information from single advisory webpage.
        Add the record in dataframe
        '''
        soup = BeautifulSoup(html,"lxml")
        try:
            text = soup.find(name="pre").text
        except AttributeError as e:
            print("WARNING: VAA FORMAT NOT RECOGNIZED IN '" + self.url + "'. VAA DISCARDED")
            return

        row = advisory.parse( text, self.url )
        if (row):
            self.row_list.append(row)
            
    def scraping(self):
        # Find where is VAA archive in website
        self.__find_archive()
        
        # Get archive
        html = self.__download_html(self.url)
        if not html:
            raise ValueError('Can not download archive webpage')
            
        links = self.__crawling_links(html)
        for link in links:
            html = self.__download_html(link)
            if not html:
                print("WARNING: Blocked for '" +link+ "'. VAA discarded")
                continue
            self.__scraping_advisory(html)
                
        return self.row_list
    
    def write_csv(self, filename):
        if not self.row_list:
            print('WARNING: There is no record for volcano and/or dates provided. THERE IS NOT OUTPUT')
        data = pd.DataFrame(self.row_list,columns=advisory.fields())
        # Escriure fitxer
        data.to_csv(filename,index=False)
        # for append, we need no save column names
        #data.to_csv(filename,mode='a')
        

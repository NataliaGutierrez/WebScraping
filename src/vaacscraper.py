'''
Aquest modul conte un scraper dels VAA publicats en la web oficial del VAAC de 
Washington.
La manera de fer-ho servir es en dos pasos:
    - Cridar el constructor.
        Els parametres requerits son:
        idate: data a partir de la qual obtenir VAA
        edate: data fins la qual obtenir VAA
        Parametres opcionals:
        volcanoes: llista de volcans dels que es vol tenir les dades. Si no hi
            ha, es generara per tots del VAAC
        filename: fitxer a on es guardara les dades. Si no hi ha, el dataframe 
            es retorna com a sortida del scraping.
        useragent: per fer-lo servir en el crawling. Per defecte, sera wswp
    - Cridar scraping.

Consideracions que s'han tingut en el scraper:
    - Es comproba que el useragent no es bloquejat pel lloc web
    - S'aplica un delay entre descarregues si esta marcat pel robots.txt
    - Les dades es van volcant a disc a mesura que es recullen mostres per evitar
      la seva perdua total si es produeix algun problema.
    - En la descarrega es realitza reintents si es produeix un error de servidor.
'''
import urllib
import urllib.robotparser
from datetime import datetime
import time
from time import strptime
from time import mktime
from bs4 import BeautifulSoup
import re
import os.path
import pandas as pd
import advisory


class VAACScraper():
    """Constructor"""
    def __init__(self, idate, edate, volcanoes=[], filename=[], useragent="wswp"):
        	# Inicialitzar parametres sobre webpage
        self.idate = idate
        self.edate = edate
        self.domain = "http://www.ssd.noaa.gov/"
        self.url = []
        self.useragent = useragent
        # Robot parser
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(self.domain + "robots.txt")
        self.rp.read()
        # If required, set a delay between crawlings
        self.crawl_delay = self.rp.crawl_delay(useragent)
        self.last_access = []
        
        if not self.crawl_delay:
            self.crawl_delay = 0
            
        # Set list of volcanoes required. If is not any, all will be taken into
        # account.
        self.volcanoes = []
        for volcano in volcanoes:
            self.volcanoes.append( volcano.lower() )
        
        # List of records
        self.row_list=[]
        
        # Number of records to proceed file writing
        self.maxcount = 25
        self.filecreated = False
        self.filename = filename
        
    '''Mirar si el useragent es acceptat'''    
    def __checking_useragent(self, url):
        return self.rp.can_fetch(self.useragent, url)
    
    ''' Construir path absolut '''
    def __absolute_ref( self, relativelink ):
        # Starting by / character, it is relative to website
        if (relativelink[0] == '/'):
            return self.domain + relativelink[1:]
        # otherwise, it is relative to local root
        else:
            return os.path.dirname(self.url) + '/' + relativelink
        
    ''' Funcio per esperar si es necessari entre descarregues '''    
    def __wait(self):
        if self.crawl_delay == 0:
            return
        
        sleep_secs = 0
        if self.last_access is not None:
            sleep_secs = self.crawl_delay - (datetime.datetime.now() -
                                             self.last_access).seconds
        if sleep_secs > 0:
            # domain has been accessed recently so need to sleep
            time.sleep(sleep_secs)
        # update the last accessed time
        self.last_access = datetime.datetime.now()
    
    ''' Descarrega del url '''
    def __download_html(self, url, num_retries=2):
        if not self.__checking_useragent(url):
            print("WARNING: Blocked by robots.txt")
            return []
        
        self.__wait();
              
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
    
    ''' Comprobar si la seccio de VAA en la web es valida '''
    def __check_advisories_section( self, title ):
        # in section, there is volcano name
        name = title.lower()
        
        # If we have volcanoes list, check the current one
        if len(self.volcanoes)>0:
            for volcano in self.volcanoes:
                if (volcano.lower() in name):
                    return True
            return False
        # Sections not required (they are not about volcanoes)
        if ('user message' in name)|('test ' in name):
            return False
        return True
    
    ''' Trobar el link per l'arxiu de VAA '''
    def __find_archive(self):
        html = self.__download_html(self.domain)
        if not html:
            raise ValueError('Can not download main webpage')
        
        soup = BeautifulSoup(html, "lxml")
        
        token = soup.find(name='a',text="Volcano Information")
        token = token.find_next(name='a',text="Advisories")
        self.url = self.__absolute_ref(token.get('href'))
            
    ''' Recollir tots els links de VAA que ens interessa '''
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
    
    ''' Extreure les dades del VAA que hi ha en el html '''
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
    
    ''' Escriure a fitxer '''        
    def __write_csv(self):
        if not self.row_list:
            if not self.filecreated:
                print('WARNING: There is no record for volcano and/or dates provided. THERE IS NOT OUTPUT')
            return
        
        data = pd.DataFrame(self.row_list,columns=advisory.fields())
        if self.filecreated:
            data.to_csv(self.filename,header=False,index=False,mode='a')
        else:
            data.to_csv(self.filename,index=False)
            self.filecreated=True
        self.row_list = []
    
    ''' Proces complet de scraping '''    
    def scraping(self):
        # Find where is VAA archive in website
        self.__find_archive()
        
        # Get archive
        html = self.__download_html(self.url)
        if not html:
            raise ValueError('Can not download archive webpage')
        
        # Gather all the VAA links
        links = self.__crawling_links(html)
        
        # VAA loop
        for link in links:
            html = self.__download_html(link)
            if not html:
                print("WARNING: Blocked for '" +link+ "'. VAA discarded")
                continue
            self.__scraping_advisory(html)
            
            # Dump into disk
            if len(self.row_list)==self.maxcount:
                self.__write_csv()
        # Dump the rest into disk
        if self.filename:
            self.__write_csv()
        else: 
            return pd.DataFrame(self.row_list,columns=advisory.fields())
    
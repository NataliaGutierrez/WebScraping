class VAACScraper():

	def __init__(self, idate, edate)
		# Inicialitzar parametres sobre webpage
		# Si no tenim etime com input, considerar data actual

	def __download_html(self, url):
		# Codi per descarregar web page

	def __crawling_links(self, html):
		# Del html descarregat, trobar els links d'on descarregar els volcanic 
		# ash advisories.
		# Només descarregar els informes dins de l'interval de temps (self.idate,self.edate)

	def __scraping_advisory(self,html):
		# Extreure les dades interessants. Insertar registre en dataframe 

	def scraping(self):

		# descarregar archive webpage
		html = self.__download_html(self.url)
		# Trobar els links dels advisories
		links = self.__crawling_links(html)
		# Extreure les dades de cada advisory
		for url in links:
			html = self.__download_html(url)
			self.__scraping_advisory(html);
				

	def write_csv(self, filename):
		
		# Escriure fitxer

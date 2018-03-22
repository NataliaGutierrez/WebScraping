import urllib2

class VAACScraper():
	"""Documentation"""

	def __init__(self, idate, edate, useragent="wswp")
		# Inicialitzar parametres sobre webpage
		# Si no tenim etime com input, considerar data actual
		self.domain = "http://www.ssd.noaa.gov/"
		self.url = self.domain + "VAAC/archive.html"
		self.useragent = useragent
	def __checking_useragent():
		# TODO

	def __download_html(self, url, num_retries=2):
		headers = {'User-agent': self.useragent}
		request = urllib2.Request(url, headers=headers)
		try:
			html = urllib2.urlopen(url).read()
		except urllib2.URLError as e:
			print 'Download error:', e.reason
			html = None
			if num_retries > 0:
				# Retry if there is a server problem
				if hasattr(e, 'code') and 500 <= e.code < 600:
					# recursively retry 5xx HTTP errors
					return self.__download_html(url, num_retries-1)
		return html

	def __crawling_links(self, html):
		# Del html descarregat, trobar els links d'on descarregar els volcanic 
		# ash advisories.
		# Només descarregar els informes dins de l'interval de temps (self.idate,self.edate)

	def __scraping_advisory(self,html):
		# Extreure les dades interessants. Insertar registre en dataframe 

	def scraping(self):
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
				

	def write_csv(self, filename):
		
		# Escriure fitxer

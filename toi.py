'''input
25/11/2016
'''
import os
import requests
from bs4 import BeautifulSoup as bs
from newspaper import Article
from jinja2 import FileSystemLoader, Environment
import re
from math import floor
from datetime import datetime
import time

old_date = -2209180870000

env = Environment(loader=FileSystemLoader('./jtemplates',followlinks=True))
template_article = env.get_template('article')

def file_dump(flname, content, dirName):
	if not os.path.exists(dirName):
		os.mkdir(dirName)
	with open(dirName + '/' + flname + '.txt', 'w', encoding= "utf-8") as fl:
		fl.write(content)

def strip_unwanted(data):
    p = re.compile(r';.*?;')
    w = p.sub('', data)
    m = re.compile(r'&lt')
    w = m.sub('\n', w)
    l = re.compile(r'&rsquo')
    return l.sub("'", w)

def striphtml(data):
    p = re.compile(r'<.*?>')
    return(p.sub('', data))

def get_start_time(year, month, date):
	d = datetime(year, month, date, 11)
	new_date = int(d.timestamp()*1000)
	return floor(((new_date-old_date)/86400000));

def get_comments(msid):
	url = 'https://timesofindia.indiatimes.com/commentsdata.cms?msid=' + str(msid) +'&curpg=1&commenttype=agree&pcode=TOI&appkey=TOI&sortcriteria=AgreeCount&order=desc&size=1&lastdeenid=123&after=true&withReward=true&medium=WEB&comment_block_count=100&pagenum=1'
	r = requests.get(url)
	size = r.json()[0]['totalcount']
	urlfinal = 'https://timesofindia.indiatimes.com/commentsdata.cms?msid=' + str(msid) +'&curpg=1&commenttype=agree&pcode=TOI&appkey=TOI&sortcriteria=AgreeCount&order=desc&size=' + str(size) + '&lastdeenid=123&after=true&withReward=true&medium=WEB&comment_block_count=100&pagenum=1'
	r1 = requests.get(urlfinal)
	soup = r1.json()[1:]
	l = {}
	for i in soup:
		l[i['A_D_N']] = strip_unwanted(i['C_T'])
	return l

def by_newspaper(url):
	article = Article(url, language="en")
	article.download()
	while article.download_state != 2:   
		time.sleep(1)
		break
	article.parse() 
	article.nlp()   
	title = article.title
	article_body = article.text
	summary = article.summary 
	keywords = article.keywords
	return title, article_body, summary, keywords

def by_scraping():
	r = requests.get(url)
	soup = bs(r.content, 'html.parser')
	title = str(soup.find_all('arttitle'))[11:-12]
	article_body = striphtml(str(soup.find_all('div',{'class':'Normal'})))
	try:
		summary = str(soup.find_all('artsummary')[0])
		while(summary.find('</li>') != -1):
			summary = summary.replace('</li>', '\n')
		summary = striphtml(summary)
	except:
		pass
	keywords = None
	return title, article_body, summary, keywords

def create_article(url, counter, date):
	msid = re.findall(r'(?<=\/)\d*(?=\.cms)', url)[0]
	flag = 0
	if url[:4]!='http':
		url = 'https://timesofindia.indiatimes.com' + url
	try:
		title, article_body, summary, keywords = by_newspaper(url)
		flag = 1
	except:
		try:
			title, article_body, summary, keywords = by_scraping(url)
			flag = 1
		except:
			pass
	try:
		comments = get_comments(msid)
	except:
		comments = None
	if flag:
		final = template_article.render(title = title, body = article_body, summary = summary, comments = comments, keywords = keywords)
		dirName = 'toi_articles/' + date[0] + '-' + date[1] + '-' + date[2]
		file_dump('article' + str(counter) ,final, dirName)
	
def get_articles(year, month, start_time, date):
	url = 'https://timesofindia.indiatimes.com/2017/11/15/archivelist/year-' + str(year) + ',month-' + str(month) + ',starttime-' + str(start_time) + '.cms'
	r = requests.get(url)
	soup = bs(r.content, "html.parser")
	x = soup.find_all('td',{'align':'left'})
	y = ''
	for i in x:
		y+=str(i)
	links = re.findall(r'(?<=<a href=").*?(?=")', y)
	links = list(set(links))
	# print(links)
	for i in range(len(links)):
		create_article(links[i].strip(), i, date)

def get_request():
	date1 = input("Enter Date (DD/MM/YYYY): ").split('/')
	date = int(date1[0])
	month = int(date1[1])
	year = int(date1[2])
	start_time = get_start_time(year, month, date)
	print('Processing')
	get_articles(year, month, start_time, date1)
	print('Completed')

get_request()
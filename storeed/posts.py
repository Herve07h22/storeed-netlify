# coding: utf-8
from __future__ import unicode_literals
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup

# this is the config data structure for parsing the html 
parser_parameters = [
    {
        'prop' : 'author',
        'param' : [ 
            {'pattern' : 'meta[name=twitter:creator]', 'result' : 'content'},
            {'pattern' : 'meta[property=author]', 'result' : 'content'},
            {'pattern' : '.author', 'result' : None},
            {'pattern' : 'span[itemprop=name]', 'result' : None},
        ] 
    },
    {
        'prop' : 'images',
        'param' : [ 
            {'pattern' : 'meta[property=og:image]', 'result' : 'content'},
            {'pattern' : 'meta[name=twitter:image]', 'result' : 'content'},
            {'pattern' : 'article img', 'result' : 'src'},
        ] 
    },
    {
        'prop' : 'title',
        'param' : [ 
            {'pattern' : 'meta[property=og:title]', 'result' : 'content'},
            {'pattern' : 'meta[name=twitter:title]', 'result' : 'content'},
            {'pattern' : 'article h1', 'result' : None},
            {'pattern' : 'title', 'result' : None},
            {'pattern' : 'h1', 'result' : None},
            {'pattern' : '.watch-title-container', 'result' : None},
        ] 
    },
    {
        'prop' : 'description',
        'param' : [ 
            {'pattern' : 'meta[name=twitter:description]', 'result' : 'content'},
            {'pattern' : 'meta[property=og:description]', 'result' : 'content'},
            {'pattern' : 'meta[name=description]', 'result' : 'content'},
            {'pattern' : 'article p', 'result' : None},
            {'pattern' : '.blog-content-container p', 'result' : None},
            {'pattern' : 'h1 ~ p', 'result' : None},
            {'pattern' : 'h2 ~ p', 'result' : None},
            {'pattern' : '.watch-title-container', 'result' : None},
            {'pattern' : 'p', 'result' : None},
        ] 
    },
    {
        'prop' : 'date',
        'param' : [ 
            {'pattern' : 'meta[article=published_time]', 'result' : 'content'},
            {'pattern' : 'meta[property=article:published_time]', 'result' : 'content'},
            {'pattern' : 'time-ago[datetime]', 'result' : 'datetime'},
            {'pattern' : 'time[datetime]', 'result' : 'datetime'},
        ] 
    },
]
def get_data(soup, search_patterns):
    result = []
    for search_pattern in search_patterns:
        if soup.select_one(search_pattern['pattern']):
            if search_pattern['result']:
                maybe_result = clean_text(soup.select_one(search_pattern['pattern']).get(search_pattern['result']))
            else:
                maybe_result = clean_text(soup.select_one(search_pattern['pattern']).get_text())
            if maybe_result:
                    result.append(maybe_result)
    return result    

def clean_text(s):
    clean_text_parameters = [
        { 'old' : 'Ã§', 'new' : 'ç' },
        { 'old' : 'Ã©', 'new' : 'é' },
        { 'old' : '\n', 'new' : ' ' },
        { 'old' : 'Ã', 'new' : 'à' },
        { 'old' : '&eacute;', 'new' : 'é'},
        { 'old' : '&quot;', 'new' : '"'},

    ]
    if not s:
        return ""
    for clean_text_parameter in clean_text_parameters:
        s = s.replace(clean_text_parameter['old'], clean_text_parameter['new'])
    s = s.expandtabs(1)
    s = s.strip()
    while s.find('  ')>0:
        s = s.replace('  ', ' ')
    return s

async def process_url(url, session):
    try:
        async with session.get(url) as response:
            body =  await response.read()
    except :
        body = None
    return body

async def process_all_url(posts):
    tasks = []
    async with ClientSession(read_timeout = 10) as session:
        for post in posts:
            print("- Requesting " + post['url'])
            task = asyncio.ensure_future(process_url(post['url'], session))
            tasks.append(task)    
        responses = await asyncio.gather(*tasks)
    print("Got the results of " + str(len(responses)) + " async requests")
    return responses

def grab_posts(posts, config):
    # launching async tasks to get all the articles
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    responses = loop.run_until_complete(process_all_url(posts))
    
    result_posts = []
    for r in responses:
        post  = posts[responses.index(r)]
        if not r :
            print("Cannot reach url " + post['url'])
        else :
            print("Processing url : {0} ".format(post['url']))
            soup = BeautifulSoup(r, "html.parser")
            for parser_parameter in parser_parameters:
                post[ parser_parameter['prop'] ].extend( get_data(soup, parser_parameter['param']) )
                #print(post[parser_parameter['prop']])
            result_posts.append(post)
    return "success", "successfully collected posts " , result_posts

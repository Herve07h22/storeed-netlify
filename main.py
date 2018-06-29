# coding: utf-8
from __future__ import unicode_literals
from storeed.get_tweets import get_tweets
from storeed.posts import grab_posts
from storeed.select_posts import select_post
from storeed.generate_html import genere_site
import json
import os

def storeed_generate():

    # load config
    config = {}
    if 'TWITTER_CONSUMER_KEY' in os.environ:
        config['TWITTER_CONSUMER_KEY'] = os.environ['TWITTER_CONSUMER_KEY']
        config['TWITTER_CONSUMER_PWD'] = os.environ['TWITTER_CONSUMER_PWD']
        config['TWITTER_ACCESS_TOKEN'] = os.environ['TWITTER_ACCESS_TOKEN']
        config['TWITTER_ACCESS_PWD'] = os.environ['TWITTER_ACCESS_PWD']
        config['TWITTER_ID'] = os.environ['TWITTER_ID']
        config['TEMPLATE'] = os.environ['TEMPLATE']
        config['MAX_POSTS'] = int(os.environ['MAX_POSTS'])
        if 'WEBHOOK_URL' in os.environ and 'WEBHOOK_BODY' in os.environ :
            print("WEBHOOK_URL : " + os.environ['WEBHOOK_URL'])
            print("WEBHOOK_BODY : " + os.environ['WEBHOOK_BODY'])
            webhook_env = json.loads(os.environ['WEBHOOK_BODY'])
            if 'TWITTER_ID' in webhook_env:
                config['TWITTER_ID'] = webhook_env['TWITTER_ID']
            

    else:
        config = json.load(open("config.json", "r"))

    # required date to build the website
    bio = {}
    posts = []

    
    # get the posts list from tweeter
    result, message, data =  get_tweets(config = config)
    print(result + " " + message)
    bio = data['bio']
    # parse each post to find data (title, author, description, date, ...)
    result, message, posts = grab_posts(data['posts'], config = config)
    print(result + " " + message)
    # make a choice to select the most relevant data
    result, message, selected_posts = select_post(config = config, posts=posts)
    print(result + " " + message)
    # build the site
    result, message = genere_site(config = config, posts=selected_posts, bio=bio)
    print(result + " "  +message)    


storeed_generate()

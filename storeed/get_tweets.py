# coding: utf-8
from __future__ import unicode_literals
import tweepy
import requests
from bs4 import BeautifulSoup
import json
import os.path

def get_api(config):
    print("----- Connecting to tweeter")
    try:
        auth = tweepy.OAuthHandler(config['TWITTER_CONSUMER_KEY'], config['TWITTER_CONSUMER_PWD'])
        auth.set_access_token(config['TWITTER_ACCESS_TOKEN'], config['TWITTER_ACCESS_PWD'])
        api = tweepy.API(auth)
    except:
        api = None

    return api

def get_bio(api, config):
    # on prélève la bio
    print("----- getting bio from user -{0}------".format(config['TWITTER_ID']))
    user  = api.get_user(config['TWITTER_ID'])
    user_bio = {
        'id' : config['TWITTER_ID'],
        'name' : user.name,
        'description' : user.description,
        'image' : user.profile_image_url.replace('normal', '400x400')
    }
    return user_bio

def get_posts(api, config):
    # on prélève les tweets comportant un lien externe
    posts = []
    new_tweets = api.user_timeline(id = config['TWITTER_ID'],count=200)
    for tweet in new_tweets:
        for extracted_url in [ url['expanded_url'] for url in tweet.entities['urls'] if url['expanded_url'].find("https://twitter.com")<0 ] :
            
            if 'media' in tweet.entities:
                medias = [media['media_url'] for media in tweet.entities['media'] if media['type'] == "photo" ]
            else:
                medias = []

            if 'hashtags' in tweet.entities:
                hashtags = [ hashtag['text'] for hashtag in tweet.entities['hashtags']]
            else:
                hashtags = []
            posts.append( {'url': extracted_url, 'retweet' : tweet.retweet_count, 'likes' : tweet.favorite_count, 'images' : medias, 'tags': hashtags, 'author':[], 'title':[], 'description':[], 'date':[str(tweet.created_at)]} )    

    if len(posts)>config['MAX_POSTS']:
        posts = posts[: config['MAX_POSTS'] ]

    return posts

def get_tweets(config):

    try:
        api = get_api(config)
    except:
        return "Error", "Cannot connect to twitter API", ""

    try:
        user_bio = get_bio(api, config)
    except:
        return "Error", "Cannot get user bio for " + config['TWITTER_ID'], ""

    try:
        user_posts = get_posts(api, config)
    except :
        return "Error", "Cannot get user posts for " + config['TWITTER_ID'], ""

    if not os.path.exists( os.path.join(os.getcwd(), "dist", config['TWITTER_ID'])):
        os.mkdir( os.path.join(os.getcwd(), "dist", config['TWITTER_ID']))

    with open( os.path.join(os.getcwd(),"dist", config['TWITTER_ID'], "bio.json"), "w", encoding='utf-8') as json_file :
        json.dump(user_bio, json_file, ensure_ascii=False)

    return "success", "successfully created posts and bio for " + config['TWITTER_ID'], {'bio' : user_bio, 'posts' : user_posts}

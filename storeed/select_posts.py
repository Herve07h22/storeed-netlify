# coding: utf-8
from __future__ import unicode_literals
import unicodedata
import asyncio
from aiohttp import ClientSession
from PIL import Image
from math import exp
import hashlib
import io
import urllib.parse
import os.path
import json

def save_image(filename, image):
    print("Save " + filename)
    with open(filename, "wb") as f:
        f.write(image.read())

async def process_image(image_name, url, session):
    try:
        async with session.get(url) as response:
            body =  await response.read()
    except :
        body = None
    return image_name, url, body

async def process_all_images(posts):
    tasks = []
    image_list = []
    async with ClientSession(read_timeout = 10) as session:
        for post in posts:
            for image_name in list(set(post['images'])):
                if not image_name.count("http") :
                    # On ajoute l'url
                    image_name_completed = urllib.parse.urljoin(post['url'], image_name)
                else :
                    image_name_completed = image_name
                print("- Requesting image " + image_name_completed)
                task = asyncio.ensure_future(process_image(image_name, image_name_completed, session))
                tasks.append(task)
        responses = await asyncio.gather(*tasks)
    print("Got the results of " + str(len(responses)) + " async requests")
    image_list = {n : b for (n, u, b) in responses}
    return image_list

def select_post(config, posts):
    # on choisit un couple titre+description
    # - on constitue des couples titre*desc
    # - on tokenise le titre, le description, la combinaison des 2
    # - on calcule les TF-IDF des 3 ensembles 

    result=[]

    # on charge toutes les images pour gagner du temps
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    image_list_content = loop.run_until_complete(process_all_images(posts))

    for post in posts:
        print("Processing post " + post['url'])
        
        # select a title and a description
        
        if len(post['title'])>0 and len(post['description'])>0:
            Titre_et_desc = [ { 'titre' : unicodedata.normalize("NFKD",t), 'description' : unicodedata.normalize("NFKD",d), 't_et_d' : unicodedata.normalize("NFKD",t + " " + d) } for t in post['title'] for d in post['description'] if d.count('GitHub is where people build software')==0 and d.count('GitHub is home to over 20 million developers working')==0]
        elif len(post['title'])>0:
            Titre_et_desc = [ { 'titre' : unicodedata.normalize("NFKD",t), 'description' : '', 't_et_d' : unicodedata.normalize("NFKD",t) } for t in post['title'] ]
        
        Vocabulary_brut = [ word for td in Titre_et_desc for word in td['t_et_d'].lower().translate(str.maketrans('”“’&.,|:/"(-)\'', '              ')).split(" ")  ]
        Vocabulary = list(set([ word for word in Vocabulary_brut if len(word)>2 and word not in ['the', 'and', 'for', 'that', 'medium'] ]))
        score_total = [ sum( [ td['titre'].lower().count(word) for word in Vocabulary]) + sum( [ td['description'].lower().count(word) for word in Vocabulary]) for td in Titre_et_desc]
        index_retenu = score_total.index(max(score_total))
        post_result = { 'titre' : Titre_et_desc[index_retenu]['titre'], 'description' : Titre_et_desc[index_retenu]['description']}
        
        # truncate description if more than 500
        if len(post_result['description'])>500:
            splitted_desc = post_result['description'].split('.')
            i = 0
            reduced_desc = ""
            while len(reduced_desc)<400 and len(splitted_desc)>i :
                reduced_desc = reduced_desc + splitted_desc[i]
                i = i +1
            if reduced_desc:
                post_result['description'] = reduced_desc
        
        # Date selection
        from dateutil.parser import parse
        from datetime import datetime
        all_date = [ parse(s, ignoretz=True) for s in post['date'] if ( s.count('2018') > 0 or s.count('2017') > 0 or s.count('2016') > 0) ]
        if all_date:
            post_result['age'] = (datetime.now() - max(all_date)).days 
        else:
            post_result['age'] = None
        
        # Author
        if post['author']:
            score_author = [ len(s) for s in post['author'] ]
            post_result['author'] = post['author'][score_author.index(max(score_author))] 

        # Image selection
        image_result = []
        
        for image_name in list(set(post['images'])):
                            
            try:
                image = Image.open(io.BytesIO(image_list_content[image_name]))
                if image.mode != "RGB" :
                    image = image.convert('RGB')
                image_result.append({ 'name' : image_name, 'image' : image, 'score' : 1.0 / exp(-(image.width/image.height - 1.3)) * (image.width + image.height) })
                print("- converting image " + image_name + " successfull !")
            except :
                print("Cannot get image " + image_name)
        
        if image_result:       
            # on trie les images par score
            image_result.sort(key = lambda x : x['score'], reverse=True)

            # la première sur la liste est à retenir
            # on la renomme et on la sauvegarde sur S3
            post_result['image'] = hashlib.sha224(image_result[0]['name'].encode("ascii", "ignore")).hexdigest()+".jpg"
            print("Storing image " +  post_result['image'])

            buffer_image_orig = io.BytesIO()
            buffer_image_150 = io.BytesIO()

            img_dir = os.path.join(os.getcwd(), "dist", "img")

            if not os.path.exists( img_dir ):
                print(" Create dirs for images" )
                os.mkdir( img_dir)
                os.mkdir( os.path.join(img_dir, "orig"))
                os.mkdir( os.path.join(img_dir, "resized-150x150"))

            image_result[0]['image'].save(buffer_image_orig, "JPEG", quality=80, optimize=True, progressive=True)
            buffer_image_orig.seek(0)
            save_image(filename = os.path.join(img_dir, "orig" , post_result['image']), image=buffer_image_orig)

            image_result[0]['image'].thumbnail((150,150))
            image_result[0]['image'].save(buffer_image_150, "JPEG", quality=80, optimize=True, progressive=True)
            buffer_image_150.seek(0)
            save_image(filename = os.path.join(img_dir, "resized-150x150" , post_result['image']), image=buffer_image_150)

        else:
            post_result['image'] = "No image"

        # popularité
        post_result['rank'] =  2*int(post['retweet']) + int(post['likes'])

        # tags
        post_result['tags'] = post['tags']

        # url
        post_result['url'] = post['url']

        # ajout à la liste si des conditions sont réunies
        if len(post_result['titre'])>0 and post_result['titre'].count('403 Forbidden')==0 and post_result['image']!='No image' and post_result['age'] and post_result['titre']!='Tumblr':
            result.append(post_result)
            print(str(post_result['titre']))
        

    # suppression des doublons
    clean_posts_list = []
    unique_list = []
    for post in result:
        if post['titre'] not in unique_list:
            unique_list.append(post['titre'])
            clean_posts_list.append(post)

    json_file = open( os.path.join(os.getcwd(),"dist",config['TWITTER_ID'],"posts.json"), "w", encoding='utf-8')
    json.dump(clean_posts_list, json_file, ensure_ascii=False)

    return "success", "successfully selected posts", clean_posts_list


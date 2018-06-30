# coding: utf-8
from __future__ import unicode_literals
from jinja2 import FileSystemLoader, Environment, select_autoescape, Template
import os.path

def genere_site(config, posts, bio):
    
    print("Generating site")
    #if len(posts)<5:
    #    return "error", "Not enough posts : " + str(len(posts)), ""
    
    env = Environment(loader=FileSystemLoader( os.path.join(os.getcwd(), "templates")), autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template(config['TEMPLATE'])
    result = template.render(posts = posts, bio = bio)
    with open( os.path.join(os.getcwd(),"dist", "index.html"), "w", encoding='utf-8') as f:
        f.write(result)

    print("Personnal landing page successfully generated for " + config['TWITTER_ID'])
    return "success", "successfully created site for " + config['TWITTER_ID']
 
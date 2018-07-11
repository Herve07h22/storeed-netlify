# Turn your tweets into a blog

To deploy yours, just click there :

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/Herve07h22/storeed-netlify)

## Settings

Firstly, you need to get [twitter apps credentials](https://apps.twitter.com/]).
You'll need 4 keys :
*TWITTER_CONSUMER_KEY
*TWITTER_CONSUMER_PWD
*TWITTER_ACCESS_TOKEN and
*TWITTER_ACCESS_PWD

Then find a twitter ID you want to turn into a blog, not necessary yours!. For example try with Seth Godin : ThisIsSethsBlog

## Customize

### URL

Once deployed on netlify, you can add a custom domain.

### Design

To build a custom design, you can freely modify layout.html file. It will be used as a [jinja2](http://jinja.pocoo.org/docs/2.10/) template fed with with 2 python dictionnaries :

* bio
* posts

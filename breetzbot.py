import json, random, urllib2 as urllib, oauth2 as oauth

def breetz_oauth_req(url, key, secret, http_method="GET", post_body='', http_headers=''):
    consumer = oauth.Consumer(key='qeqeZ6p5v6mnW95nMSIHgs5Wv', secret='dEpB3M8PfCUnOMiliJoXxMRfqQLZBE4JGtTLF8AlOD04ECMPAm')
    token = oauth.Token(key=key, secret=secret)
    client = oauth.Client(consumer, token)
    return client.request( url, method=http_method, body=post_body, headers=http_headers)[1]

def breetz_bot():
    text = []
    max_id = 0
    home_timeline = oauth_req( 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=BreetzTweetz&count=200&exclude_replies=true', '544975086-kLoThdRZjbburU8x7yUIhPhdd2Gcdq0uqMNYDdyO', 'kNScrJZZXtWWF1kohKBf6Rul3LcN9A9dtoEVidBobVOmy' )
    home_timeline = json.loads(home_timeline)
    while len(home_timeline) != 0:
        for tweet in home_timeline:
            if not re.search(r'https?:\/\/.*[\r\n]*',tweet['text']):
                tweet['text'] = re.sub(r'RT ', '', tweet['text'], flags=re.MULTILINE)
                tweet['text'] = re.sub(r'@(\S)* ', '', tweet['text'], flags=re.MULTILINE)
                text = text + tweet['text'].split(' ') + ['###']
        max_id = str(home_timeline[-1]['id'] - 1)
        home_timeline = oauth_req( 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=BreetzTweetz&count=200&exclude_replies=true&max_id=' + max_id, '544975086-kLoThdRZjbburU8x7yUIhPhdd2Gcdq0uqMNYDdyO', 'kNScrJZZXtWWF1kohKBf6Rul3LcN9A9dtoEVidBobVOmy' )
        home_timeline = json.loads(home_timeline)
    f = open('/srv/nobelyoo/static/breetz.txt', 'w')
    f.write(re.sub(r'[^\x00-\x7F]+',' ',' '.join(text)))
    f.close()

def breetz_tweets():
    f = open('/srv/nobelyoo/static/breetz.txt', 'r')
    tweets = f.read()
    tweets = tweets.split(' ')
    first = True
    indexes = [i for i, x in enumerate(tweets) if x == '###']
    word = tweets[random.choice(indexes) + 1]
    quote = word
    indexes = [i for i, x in enumerate(tweets) if x == word]
    word = tweets[random.choice(indexes) + 1]

    while word != '###':
        quote = quote + ' ' + word
        indexes = [i for i, x in enumerate(tweets) if x == word]
        word = tweets[random.choice(indexes) + 1]
    #print quote
    print breetz_oauth_req('https://api.twitter.com/1.1/statuses/update.json','2887934017-7V8PiFbKxiKcXecncvoF4NMPVoxlx5LgEXQBVZW', 'vfrFWuPyrvbMr0roDD5SVPyhv6OQlF0TLJbQ9SDNmz2xh',"POST",urllib.urlencode({'status':quote}))



#! /usr/bin/python

import tweepy, sqlite3, re



with open('keyz.txt','r') as f:
    consumerKey = f.readline().strip()
    consumerSecret = f.readline().strip()
    accessToken = f.readline().strip()
    accessTokenSecret = f.readline().strip()

auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)

api = tweepy.API(auth)

db = sqlite3.connect('db/db')

cursor = db.cursor()

def initializeDB():
    cursor.execute("CREATE TABLE Tweets(tweetId INTEGER, authorId INTEGER, text TEXT)")
    db.commit()

def updateTweetsForUser(userId):
    #get the most recent ones without getting ones we've already got.
    cursor.execute("""SELECT MAX(tweetId) as MAXID from Tweets
    WHERE authorId=?""", (userId,))
    minId = cursor.fetchone()[0]
    if minId == None:
        tweets = api.user_timeline(userId, count=200)
    else:
        tweets = api.user_timeline(userId, count=200, since_id=minId)

    while len(tweets) > 0:
        #add tweets to DB
        for tweet in tweets:
            #filter out mentions, links, RTs
            if not re.search(r'https?:\/\/.*[\r\n]*', tweet.text) and not re.search(r'RT @', tweet.text):
                
                tweet.text = re.sub('@','@.',tweet.text)

                query = """INSERT INTO Tweets(tweetId, authorId, text)
                VALUES(?,?,?)
                """
                cursor.execute(query, (tweet.id, userId, tweet.text))
                print tweet.author.screen_name, tweet.text
                print "--------------"

        #get more tweets
        maxId = tweets[-1].id
        #maxid-1 should work because there's no way one user got consecutive tweets. No way.
        tweets = api.user_timeline(userId, count=200, max_id=maxId-1, since_id=minId)
    db.commit()

def updateTweets():
    friends = api.friends_ids(api.me().id)
    for friendId in friends:
        updateTweetsForUser(friendId)

#initializeDB()
updateTweets()


    
    
    
    
    
    

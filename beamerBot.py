#! /usr/bin/python

import tweepy, sqlite3, re, random



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

currentFriend = ""

def initializeDB():
    cursor.execute("CREATE TABLE Tweets(tweetId INTEGER, authorId INTEGER, text TEXT, wordCount INT)")
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

                query = """INSERT INTO Tweets(tweetId, authorId, text, wordCount)
                VALUES(?,?,?,?)
                """
                cursor.execute(query, (tweet.id, userId, tweet.text, len(tweet.text.split()) ))
                print tweet.author.screen_name, tweet.text, len(tweet.text.split())
                print "--------------"

        #get more tweets
        maxId = tweets[-1].id
        #maxid-1 should work because there's no way one user got consecutive tweets. No way.
        tweets = api.user_timeline(userId, count=200, max_id=maxId-1, since_id=minId)
    db.commit()

def updateTweets():
    friends = api.friends_ids(api.me().id) #everyone beamerbot follows
    for friendId in friends:
        updateTweetsForUser(friendId)

def generateTweet():
    global currentFriend
    friends = api.friends_ids(api.me().id) #gets list of userIds beamerbot is following
    friend = api.get_user(random.choice(friends))
    currentFriend = friend.screen_name
    
    tweet = ""
    currentLength = 0
    nextChunk = random.randint(2,7)
    stillBuilding = True

    while(stillBuilding):
        query = """SELECT text FROM tweets
                    WHERE authorId = ?
                      AND wordCount >= ?
                 ORDER BY RANDOM() LIMIT 1"""
        cursor.execute(query, (friend.id, currentLength))
        sourceTweet = cursor.fetchone()[0].split() #the text of the fetched tweet

        if (len(sourceTweet) < currentLength + nextChunk):
            #finish out and stop
            stillBuilding = False
            sourceTweet = sourceTweet[currentLength:]
            for word in sourceTweet:
                tweet = tweet + word + ' '
            tweet = tweet.strip()
        else:
            #build and continue
            sourceTweet = sourceTweet[currentLength:currentLength+nextChunk]
            for word in sourceTweet:
                tweet = tweet + word + ' '
            currentLength += nextChunk
            nextChunk = random.randint(2,7)

        if (len(tweet) > 140):
            #start over
            tweet = ""
            currentLength = 0
            nextChunk = random.randint(2,7)
            stillBuilding = True

    print currentFriend, tweet



#initializeDB()
#updateTweets()
#generateTweet()


    
    
    
    
    
    

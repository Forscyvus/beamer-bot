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

roundOver = False
alreadyGuessed = []
currentFriend = ""
currentTweetId = 0
beamerBotId = 2865039405

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
    friends = api.friends_ids(beamerBotId) #everyone beamerbot follows
    for friendId in friends:
        updateTweetsForUser(friendId)

def generateTweet():
    global currentFriend, currentTweetId, alreadyGuessed, roundOver
    friends = api.friends_ids(beamerBotId) #gets list of userIds beamerbot is following
    friend = api.get_user(random.choice(friends))
    #currentFriend = friend.screen_name
    currentFriend = "BreetzTweetz"
    alreadyGuessed = []
    roundOver = False
    

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

    #STATS
    print currentFriend, tweet

def processMentions():
    global currentFriend, currentTweetId, alreadyGuessed, roundOver
    friends = api.friends_ids(beamerBotId) #gets list of userIds beamerbot is following
    with open('db/lastmention.txt', 'r') as f:
        lastId = long(f.read().strip())
    mentions = api.mentions_timeline(since_id=lastId, count=200)
    if len(mentions) == 0:
        return
    mostRecent = mentions[0].id
    mentions = filter(lambda x: x.text[:11].upper() == "@BEAMERBOT ", mentions)
    #filter for responding to latest tweet 
     
    #actual processing (in posting order)
    for mention in reversed(mentions):
        print "----------------------------"
        print "mentiontext", mention.text
        print "alreadyguessed", alreadyGuessed
        print "mention author", mention.author.screen_name
        text = mention.text[11:].split()
        names = filter(lambda x: x.startswith("@"), text)
        if len(names) > 0:
            if roundOver:
                #sorry, alreadyGuessed[0] already won!
                #STATS
                print 1
                continue
            if mention.author.screen_name in alreadyGuessed:
                #sorry, only one guess per round!
                #STATS
                print 2
                continue

            guess = names[0][1:]
            if guess.upper() == currentFriend.upper():
                #you win
                #STATS
                print 3
                alreadyGuessed = [mention.author.screen_name]
                roundOver = True
            else:
                #you guessed wrong!
                #STATS
                print 4
                alreadyGuessed.append(mention.author.screen_name)
        else:
            print 0
            



    with open('db/lastmention.txt', 'w') as f:
        f.write(str(mostRecent))

#initializeDB()
#updateTweets()
generateTweet()

while(raw_input("anything to process tweets, exit to exit: ") != "exit"):
    processMentions()
    
    
    
    
    

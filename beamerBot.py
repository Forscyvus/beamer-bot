#! /usr/bin/python

import tweepy, sqlite3, re, random, threading, time

#timing code from http://stackoverflow.com/questions/8600161/executing-periodic-actions-in-python

with open('keyz.txt','r') as f:
    consumerKey = f.readline().strip()
    consumerSecret = f.readline().strip()
    accessToken = f.readline().strip()
    accessTokenSecret = f.readline().strip()

auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)

api = tweepy.API(auth)


firstTime = True
roundOver = False
alreadyGuessed = []
currentFriend = ""
currentTweetId = 0
beamerBotId = 2865039405

generateTweetInterval = 900 #15 minutes
generateTweetNextCall = time.time()
processMentionsInterval = 75 #75 seconds
processMentionsNextCall = time.time()
updateTweetsInterval = 86400 #1 day
updateTweetsNextCall = time.time()

def initializeDB():
    db = sqlite3.connect('db/db')
    cursor = db.cursor()
    #cursor.execute("CREATE TABLE Tweets(tweetId INTEGER, authorId INTEGER, text TEXT, wordCount INT)")
    cursor.execute("CREATE TABLE Players(id INTEGER, wins INTEGER, losses INTEGER)")
    db.commit()
    cursor.close()

def updateTweetsForUser(userId):
    #get the most recent ones without getting ones we've already got.
    db = sqlite3.connect('db/db')
    cursor = db.cursor()
    cursor.execute("""SELECT MAX(tweetId) as MAXID from Tweets
    WHERE authorId=?""", (userId,))
    minId = cursor.fetchone()[0]
    try:
        if minId == None:
             tweets = api.user_timeline(userId, count=200)
        else:
             tweets = api.user_timeline(userId, count=200, since_id=minId)
    except:
        print "lol 1"
        return

    while len(tweets) > 0:
        #add tweets to DB
        for tweet in tweets:
            #reject beamerbot guesses
            if tweet.text[:11].upper() == "@BEAMERBOT ":
                continue
            #filter out mentions, links, RTs
            if not re.search(r'https?:\/\/.*[\r\n]*', tweet.text) and not tweet.text.startswith("RT @"):
                
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
        try:
            tweets = api.user_timeline(userId, count=200, max_id=maxId-1, since_id=minId)
        except:
            print "lol 2"
            return
    db.commit()
    cursor.close()

def updateTweets():
    global updateTweetsNextCall
    try:
        friends = api.friends_ids(beamerBotId) #everyone beamerbot follows
    except:
        print "lol 3"
        updateTweetsNextCall += updateTweetsInterval
        threading.Timer(updateTweetsNextCall - time.time(), updateTweets).start()
        return
    for friendId in friends:
        updateTweetsForUser(friendId)
    updateTweetsNextCall += updateTweetsInterval
    threading.Timer(updateTweetsNextCall - time.time(), updateTweets).start()

def generateTweet():
    global currentFriend, currentTweetId, alreadyGuessed, roundOver, firstTime, generateTweetNextCall
    print "generating Tweet"
    db = sqlite3.connect('db/db')
    cursor = db.cursor()
    previousFriend = currentFriend
    try:
        friends = api.friends_ids(beamerBotId) #gets list of userIds beamerbot is following
        friend = api.get_user(random.choice(friends))
        currentFriend = friend.screen_name
    except:
        print "lol 4"
        generateTweetNextCall += generateTweetInterval
        threading.Timer(generateTweetNextCall - time.time(), generateTweet).start()
        return
    try:
        if not roundOver and not firstTime:
            api.update_status("Nobody got it! It was @" + previousFriend, in_reply_to_status_id = currentTweetId)
        elif firstTime:
            pass
        else:
            api.update_status("The winner is @." + alreadyGuessed[0] + "! The mystery tweeter was @." + previousFriend)
    except:
        print "lellercopter"
    alreadyGuessed = []
    roundOver = False
    firstTime = False

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
    try:
        currentTweetId = api.update_status(tweet).id
    except:
        currentTweetId = -1
        print "loleleol"
    print currentFriend, tweet
    cursor.close()
    generateTweetNextCall += generateTweetInterval
    threading.Timer( generateTweetNextCall - time.time(), generateTweet).start()

def processMentions():
    global currentFriend, currentTweetId, alreadyGuessed, roundOver, processMentionsNextCall
    db = sqlite3.connect('db/db')
    cursor = db.cursor()
    print "processMentions Called"
    try:
        with open('db/lastmention.txt', 'r') as f:
            lastId = long(f.read().strip())
        mentions = api.mentions_timeline(since_id=lastId, count=200)
    except:
        print "lol 5"
        processMentionsNextCall += processMentionsInterval
        threading.Timer( processMentionsNextCall - time.time(), processMentions ).start()
        return
    if len(mentions) == 0:
        print "no replies"
        processMentionsNextCall += processMentionsInterval
        threading.Timer( processMentionsNextCall - time.time(), processMentions ).start()
        return
    mostRecent = mentions[0].id
    mentions = filter(lambda x: x.text[:11].upper() == "@BEAMERBOT ", mentions)
    mentions = filter(lambda x: x.in_reply_to_status_id == currentTweetId, mentions) 
    #actual processing (in posting order)
    if len(mentions) == 0:
        print "all filtered away"
    for mention in reversed(mentions):
        print "----------------------------"
        print "mentiontext", mention.text
        print "alreadyguessed", alreadyGuessed
        print "mention author", mention.author.screen_name
        text = mention.text[11:].split()
        names = filter(lambda x: x.startswith("@"), text)
        try:
            if len(names) > 0:
                if roundOver:
                    print 1
                    if mention.author.screen_name == alreadyGuessed[0]:
                        api.update_status("@" + mention.author.screen_name + " look you already got it stop guessing.", in_reply_to_status_id = mention.id) 
                    else:
                        api.update_status("@" + mention.author.screen_name + " sorry, " + alreadyGuessed[0] + " already won! The mystery tweeter was " + currentFriend + "!", in_reply_to_status_id = mention.id)
                    #STATS
                    continue
                if mention.author.screen_name in alreadyGuessed:
                    print 2
                    api.update_status("@" + mention.author.screen_name + " sorry, you can only guess once per round!", in_reply_to_status_id = mention.id)
                    #STATS
                    continue

                guess = names[0][1:]
                if guess.upper() == currentFriend.upper():
                    query = """SELECT wins
                                 FROM players
                                WHERE id = ?"""
                    cursor.execute(query, (mention.author.id,))
                    score = cursor.fetchone()
                    if score == None:
                        query = """INSERT INTO players(id, wins, losses)
                                        VALUES(?,?,?)"""
                        cursor.execute(query, (mention.author.id, 1, 0))
                        score = 1
                    else:
                        score = score[0]+1
                        query = """UPDATE players
                                      SET wins = ?
                                    WHERE id = ?"""
                        cursor.execute(query, (score, mention.author.id))
                    print 3
                    api.update_status("@" + mention.author.screen_name + " you got it! You win the round. This is win #" + str(score) + " for you.", in_reply_to_status_id = mention.id)
                    #STATS
                    alreadyGuessed = [mention.author.screen_name]
                    roundOver = True
                else:
                    query = """SELECT losses
                                 FROM players
                                WHERE id = ?"""
                    cursor.execute(query, (mention.author.id,))
                    score = cursor.fetchone()
                    if score == None:
                        query = """INSERT INTO players(id, wins, losses)
                                        VALUES(?,?,?)"""
                        cursor.execute(query, (mention.author.id, 0, 1))
                        score = 1
                    else:
                        score = score[0]+1
                        query = """UPDATE players
                                      SET losses = ?
                                    WHERE id = ?"""
                        cursor.execute(query, (score, mention.author.id))
                    print 4
                    api.update_status("@" + mention.author.screen_name + " nope, that's not it. Try again next round! This is loss #" + str(score) + " for you.", in_reply_to_status_id = mention.id)
                    #STATS
                    alreadyGuessed.append(mention.author.screen_name)
            else:
                print 0
        except tweepy.TweepError as e:
            print e



    with open('db/lastmention.txt', 'w') as f:
        f.write(str(mostRecent))
    db.commit()
    cursor.close()
    processMentionsNextCall += processMentionsInterval
    threading.Timer( processMentionsNextCall - time.time(), processMentions ).start()

     

#initializeDB()
threading.Timer(5, updateTweets).start()
threading.Timer(22, processMentions).start()
generateTweet()







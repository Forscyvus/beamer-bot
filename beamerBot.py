#! /usr/bin/python

import tweepy, sqlite3



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







#! /usr/bin/python

import tweepy

with open('keyz.txt','r') as f:
    consumerKey = f.readline().strip()
    consumerSecret = f.readline().strip()
    accessToken = f.readline().strip()
    accessTokenSecret = f.readline().strip()

auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)

api = tweepy.API(auth)

api.update_status("test post please ignore")

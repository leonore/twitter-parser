import tweepy
import datetime
from pymongo import MongoClient
from keys import consumer_key, consumer_secret, access_token, access_secret

CONSUMER_KEY = consumer_key
CONSUMER_SECRET = consumer_secret
ACCESS_TOKEN = access_token
ACCESS_SECRET = access_secret

client = MongoClient()
db = client.twitter_db
collection = "streaming_crawler"

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

class TwitterStream(tweepy.StreamListener):

    def on_status(self, status):
        if (status.lang == "en"):
            json_tweet = status._json
            # convert datetime
            json_tweet['created_at'] = datetime.strptime(json_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y’)
            return True

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False

listener = TwitterStream()
streamer = tweepy.Stream(auth=auth, listener=listener)

streamer.sample()

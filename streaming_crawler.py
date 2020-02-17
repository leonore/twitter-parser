import tweepy
from datetime import datetime, timedelta
from pymongo import MongoClient
from keys import consumer_key, consumer_secret, access_token, access_secret

CONSUMER_KEY = consumer_key
CONSUMER_SECRET = consumer_secret
ACCESS_TOKEN = access_token
ACCESS_SECRET = access_secret

client = MongoClient()
db = client.twitter_db
collection = "streaming_crawler_1a"

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser(), wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

class TwitterStream(tweepy.StreamListener):

    def on_status(self, status):
        json_tweet = status._json
        # convert datetime
        print(json_tweet['text'])
        json_tweet['created_at'] = datetime.strptime(json_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        db[collection].insert(json_tweet)
        return True

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False

listener = TwitterStream()
streamer = tweepy.Stream(auth=auth, listener=listener)

start = datetime.now()
one_hour = start + timedelta(minutes=60)

streamer.sample(languages=["en"], is_async=True)

while datetime.now() < one_hour:
    continue

streamer.disconnect()
print("Tweets were streamed from {} to {}".format(start, one_hour))

# Tweets were streamed from 2020-02-16 19:20:48.656979 to 2020-02-16 20:20:48.656979
# Count: 53124

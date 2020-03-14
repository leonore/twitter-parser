import argparse

parser = argparse.ArgumentParser(description='Sample tweets for one hour and store in MongoDB.')

parser.add_argument('--collection', '-c', action='store', type=str, help='Name of the collection to store the data in (in MongoDB.twitter_db)', required=True)
parser.add_argument('--time', '-t', action="store", type=int, help="How long to run the crawler for in minutes", required=False)

args = parser.parse_args()
collection = args.collection
duration = args.time
if not duration:
    duration = 60

## imports after argparse to save performance ##

import tweepy
from datetime import datetime, timedelta
from pymongo import MongoClient
from keys import consumer_key, consumer_secret, access_token, access_secret

# set up pymongo
client = MongoClient()
db = client.twitter_db # change this for different Mongo database

# set up Twitter API
CONSUMER_KEY = consumer_key
CONSUMER_SECRET = consumer_secret
ACCESS_TOKEN = access_token
ACCESS_SECRET = access_secret

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser(), wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

count = 0 # tally up number of Tweets streamed

class TwitterStream(tweepy.StreamListener):

    def on_status(self, status):
        global count
        json_tweet = status._json
        json_tweet['created_at'] = datetime.strptime(json_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y') # convert datetime for MongoDB
        db[collection].insert(json_tweet)
        count += 1
        return True

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False

listener = TwitterStream()
streamer = tweepy.Stream(auth=auth, listener=listener)

start = datetime.now()
one_hour = start + timedelta(minutes=duration)

print("Tweets being streamed in twitter_db.{} for {} minutes".format(collection, duration))

streamer.sample(languages=["en"], is_async=True)
# change your keywords if you want:
#streamer.filter(track=["coronavirus", "covid-19", "covid19", "SARS-COV-2", "SARS-COV2", "2019-nCov", "covid", "cov19"],
#                languages=["en"], is_async=True)

while datetime.now() < one_hour:
    continue

streamer.disconnect()
print("{} tweets were streamed from {} to {}".format(count, start, one_hour, collection))

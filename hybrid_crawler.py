import argparse

parser = argparse.ArgumentParser(description='Crawl tweets for one hour and store in a MongoDB.')

parser.add_argument('--collection', '-c', action='store', type=str, help='Name of the collection to store the data in (in MongoDB.twitter_db)', required=True)
parser.add_argument('--time', '-t', action="store", type=int, help="How long to run the crawler for in minutes", required=False)
parser.add_argument('--verbose', '-v', action="store_true", help="Print remaining requests left", required=False) # verbose prints number of requests left in time window

args = parser.parse_args()
collection = args.collection
duration = args.time
if not duration:
    duration = 60

## do imports after argparse for performance


from datetime import datetime, timedelta
import threading
import time
import random

import tweepy
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from keys import consumer_key, consumer_secret, access_token, access_secret
from helpers import SetQueue

# set up MongoDB connection
client = MongoClient()
db = client.twitter_db

# set up Twitter API
CONSUMER_KEY = consumer_key
CONSUMER_SECRET = consumer_secret
ACCESS_TOKEN = access_token
ACCESS_SECRET = access_secret

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# keep track of Tweet and number of duplicates
count = 0
duplicates = 0

# location coordinates for geosearch REST probe
LONDON = "51.5287352,-0.3817825,100km"
GENEVA = "46.204391,6.143158,100km"
WASHINGTON_DC = "38.907192,-77.036873,100km"
WUHAN = "30.592850,114.305542,100km"
locations = [LONDON, GENEVA, WASHINGTON_DC, WUHAN]

hashtag_queue = SetQueue()
user_queue = SetQueue()

def add_to_database(status):
    global count
    global duplicates
    json_tweet = status._json
    json_tweet['created_at'] = datetime.strptime(json_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    try:
        db[collection].insert(json_tweet)
    except DuplicateKeyError as e:
        duplicates += 1
    count += 1

def process_network(user):
    # user needs to not have suspicious following
    # if user has > 15k followers --> get friends and add to queue
    # if user has > 15k followers --> get replies
    global user_queue

    seems_legit = False
    exclude_replies = True

    if available_requests['followers'] != 0:
        followers = api.followers_ids(user)
        friends = api.friends_ids(user)

        if len(friends) > 10:
            seems_legit = True
        else:
            seems_legit = False

        # if user has > 15k followers --> get friends and add to queue
        # assume some kind of big name
        if len(followers) >= 15000:
            for friend in friends:
                user_queue.put(friend)
            exclude_replies = False
        else:
            exclude_replies = True

    return seems_legit, exclude_replies

def parse_for_entities(status):
    global hashtag_queue, user_queue
    user = status.user.id
    user_queue.put(user)
    for hashtag in status.entities['hashtags']:
        # add hashtag to list if not there
        hashtag_queue.put(hashtag['text'].lower())

def hashtag_thread():
    print("Hashtag thread started.")
    global hashtag_queue
    while not stop:
        if not hashtag_queue.empty():
            if available_requests['search'] != 0:
                for tweet in tweepy.Cursor(api.search, q=hashtag_queue.get(), lang="en", count=100, tweet_mode='extended').items():
                    add_to_database(tweet)

def location_thread():
    print("Location thread started.")
    location = random.choice(locations) # each time pick a random location to do search for
    while not stop:
        if available_requests['search'] != 0:
            for tweet in tweepy.Cursor(api.search, q="covid", geocode=location, lang="en", count=100, tweet_mode='extended').items():
                add_to_database(tweet)
            location = random.choice(locations)

def user_thread():
    print("User thread started.")
    global user_queue

    while not stop:
        if not user_queue.empty():
            if available_requests['user_timeline'] != 0:
                user = user_queue.get()
                seems_legit, replies = process_network(user)
                if seems_legit:
                    for tweet in tweepy.Cursor(api.user_timeline, id=user, include_entities=True, exclude_replies=replies, count=100, tweet_mode='extended').items():
                        add_to_database(tweet)

class TwitterStream(tweepy.StreamListener):

    def on_status(self, status):
        add_to_database(status)
        parse_for_entities(status)
        return True

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False

listener = TwitterStream()
streamer = tweepy.Stream(auth=auth, listener=listener)

start = datetime.now()
time_limit = start + timedelta(minutes=duration)
stop = False

streamer.filter(track=["coronavirus", "covid-19", "covid19", "SARS-COV-2", "SARS-COV2", "2019-nCov", "covid", "cov19", "SARSCov2"],
                languages=["en"], is_async=True) # change this for different (or no) keywords

available_requests = {
    'user_timeline': 0,
    'search': 0,
    'followers': 0
}

try:
    ut = threading.Thread(target=user_thread, daemon=True)
    lt = threading.Thread(target=location_thread, daemon=True)
    ht = threading.Thread(target=hashtag_thread, daemon=True)
    ut.start()
    lt.start()
    ht.start()
    print("Probing tweets...\n")

except Exception as e:
    print("Error encountered when launching threads: {}".format(e))

print("Looking for tweets until {}\n".format(time_limit))

while datetime.now() < time_limit:
    if args.verbose:
        limits = api.rate_limit_status()

        rate = limits['resources']['application']['/application/rate_limit_status']
        print("GET RATES: {} requests left".format(rate['remaining']))

        tl_tweets = limits['resources']['statuses']['/statuses/user_timeline']
        print("GET TIMELINE: {} requests left".format(tl_tweets['remaining']))
        available_requests['user_timeline'] = tl_tweets['remaining']

        followers = limits['resources']['followers']['/followers/ids']
        print("GET FOLLOWERS: {} requests left".format(followers['remaining']))
        available_requests['followers'] = followers['remaining']

        search = limits['resources']['search']['/search/tweets']
        print("SEARCH TWEETS: {} requests left\n".format(search['remaining']))
        available_requests['search'] = search['remaining']

    time.sleep(30) # don't run into limits for asking for number of requests left

stop = True

streamer.disconnect()
print("{} tweets were streamed from {} to {} in {}".format(count, start, time_limit, collection))
print("{} duplicates were detected.".format(duplicates))

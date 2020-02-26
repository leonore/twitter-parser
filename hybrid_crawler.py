import tweepy
from datetime import datetime, timedelta
import time
from pymongo import MongoClient
from keys import consumer_key, consumer_secret, access_token, access_secret
import random

import threading
from helpers import SetQueue

CONSUMER_KEY = consumer_key
CONSUMER_SECRET = consumer_secret
ACCESS_TOKEN = access_token
ACCESS_SECRET = access_secret

client = MongoClient()
db = client.twitter_db
collection = "hybrid_crawler_1601"

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

count = 0
LONDON_ID = 44418
hashtag_queue = SetQueue()
user_queue = SetQueue()

def add_to_database(status):
    global count
    json_tweet = status._json
    json_tweet['created_at'] = datetime.strptime(json_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    db[collection].insert(json_tweet)
    count += 1

def process_network(user):
    # user needs to not have 0 following
    # if user has > 15k followers --> get friends and add to queue
    # if user has > 15k followers --> get replies
    global user_queue

    seems_legit = True
    exclude_replies = False

    if available_requests['followers'] != 0:
        followers = api.followers_ids(user)
        friends = api.friends_ids(user)

        if len(friends) > 5:
            seems_legit = True
        else:
            seems_legit = False

        # if user has > 50k followers --> get friends and add to queue
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
                for tweet in tweepy.Cursor(api.search, q=hashtag_queue.get(), lang="en", count=100).items():
                    add_to_database(tweet)

def trend_thread():
    print("Trend thread started.")
    london_trends = api.trends_place(LONDON_ID)
    picked_trends = london_trends[0]['trends'][:10] # only top 10 trends
    picked_trends = sorted(picked_trends, key=lambda k: k.get('tweet_volume', 0) if k.get('tweet_volume', 0) else 0)
    for trend in picked_trends:
        if available_requests['search'] != 0:
            for tweet in tweepy.Cursor(api.search, q=trend['name'], lang="en", count=100).items():
                add_to_database(tweet)

def user_thread():
    print("User thread started.")
    global user_queue

    while not stop:
        if not user_queue.empty():
            if available_requests['user_timeline'] != 0:
                user = user_queue.get()
                seems_legit, replies = process_network(user)
                if seems_legit:
                    for tweet in tweepy.Cursor(api.user_timeline, id=user, include_entities=True, exclude_replies=replies, count=200).items():
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
time_limit = start + timedelta(minutes=60)
stop = False

streamer.sample(languages=["en"], is_async=True)

try:
    ut = threading.Thread(target=user_thread, daemon=True)
    tt = threading.Thread(target=trend_thread, daemon=True)
    ht = threading.Thread(target=hashtag_thread, daemon=True)
    ut.start()
    tt.start()
    ht.start()
    print("Probing tweets...\n")

except Exception as e:
    print("Error encountered when launching threads: {}".format(e))

available_requests = {
    'user_timeline': 0,
    'search': 0,
    'followers': 0
}

print("Looking for tweets until {}\n".format(time_limit))

while datetime.now() < time_limit:
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

    time.sleep(30)

stop = True

streamer.disconnect()
print("{} tweets were streamed from {} to {}".format(count, start, time_limit))

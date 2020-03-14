from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import re
import emoji

import queue


class SetQueue(queue.Queue):

    def put(self, item, block=True, timeout=None):
        if item not in self.queue: # fix join bug
            queue.Queue.put(self, item, block, timeout)

    def _init(self, maxsize):
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()

stop_words = stopwords.words('english') + ["AT_USER", "ATUSER", "URL", "AT", "USER"] + ["amp", "im"]

def parse_tweet(tweet):
    if tweet.get("retweeted_status"):
        tweet = tweet["retweeted_status"]
    if tweet.get("truncated"):
        text = tweet["extended_tweet"]["full_text"]
    else:
        try:
            text = tweet["full_text"]
        except KeyError as e:
            text = tweet["text"]
    return text


def get_body(tweet):
    if tweet.get("retweeted_status"):
        tweet = tweet["retweeted_status"]
    if tweet.get("truncated"):
        text = tweet["extended_tweet"]
    else:
        text = tweet
    return text


def _removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)


def clean_text(text):
    # some substitution rules taken from
    # https://towardsdatascience.com/creating-the-twitter-sentiment-analysis-program-in-python-with-naive-bayes-classification-672e5589a7ed
    text = text.lower()
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', text) # remove URLs
    text = re.sub('face', '', emoji.demojize(text)) # turn emojis to text but remove "face"
    text = re.sub('[:_]+', ' ', text)
    text = re.sub('@[^\s]+', 'AT_USER', text) # remove usernames
    text = re.sub(r'#([^\s]+)', r'\1', text) # remove the # in #hashtag
    text = re.sub('[^a-zA-Z ]+', ' ', text)
    text = _removeNonAscii(text)
    text = text.strip()
    return text


def tokenize(text):
    text = clean_text(text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in stop_words]
    return ' '.join(tokens)


def find_sentiment_tb(tweet):
    score = TextBlob(tweet).sentiment.polarity
    if score < 0.2 and score >= 0:
        score = 0
    elif score >= 0.2:
        score = 1
    else:
        score = -1
    return score

def get_top_n_items(s, n=10):
    """
    Function to return top n items from a paired structure
    :s -> dictionary, list of tuples
    :n -> number of items to return
    """

    if type(s) is dict:
        return [user + ": " + str(hashtag) for user, hashtag in sorted(s.items(), key=lambda item: item[1], reverse=True)[:n]]
    else:
        return [user + ": " + str(hashtag) for user, hashtag in sorted(s, key=lambda item: item[1], reverse=True)[:n]]

from nltk.probability import FreqDist

from helpers import tokenize, parse_tweet, get_body

def extract_top_entities(collection):
    """
    Extracts number of mentions, retweets, hashtags for a collection
    As well as top 20 words
    :collection -> MongoDB collection obtained with find() or JSON Tweets
    """
    mentions_count = {}
    retweets_count = {}
    hashtags_count = {}
    corpus = []

    for tweet in collection:

        corpus += tokenize(parse_tweet(tweet)).split(" ")
        tweeter = tweet["user"]

        # RETWEETS
        if tweet.get("retweeted_status"):
            rt_user = tweet["retweeted_status"]["user"]["screen_name"]
            if not retweets_count.get(rt_user):
                retweets_count[rt_user] = tweet["retweeted_status"]["retweet_count"]
            else:
                retweets_count[rt_user] += tweet["retweet_count"]

        if tweet.get("truncated"):
            tweet = tweet["extended_tweet"]

        # USER MENTIONS
        if tweet["entities"].get("user_mentions"):
            for user in tweet["entities"]["user_mentions"] + [tweeter]:
                user = user["screen_name"]
                if not mentions_count.get(user):
                    mentions_count[user] = 1
                else:
                    mentions_count[user] += 1

        # HASHTAGS
        tweet = get_body(tweet)
        if tweet["entities"].get("hashtags"):
            for h in tweet["entities"]["hashtags"]:
                hl = h["text"].lower()
                if not hashtags_count.get(hl):
                    hashtags_count[hl] = 1
                else:
                    hashtags_count[hl] += 1

    fdist = FreqDist(corpus)
    top_20 = fdist.most_common(20)

    return mentions_count, retweets_count, hashtags_count, top_20

def number_of(tweets, condition={"$exists": True}):
    """
    Gets number of tweets, retweets, quotes, replies by condition
    :tweets -> MongoDB collection name
    :condition -> sentiment condition (-1, 0, 1) obtained with text_analysis.sentiment_analysis()
    """

    total = tweets.count_documents({"sentiment": condition})
    rt = tweets.count_documents({"retweeted_status": {"$exists": True}, "sentiment": condition})
    quotes = tweets.count_documents({"is_quote_status": True, "sentiment": condition})
    replies = tweets.count_documents({"in_reply_to_status_id":{"$ne":None}, "is_quote_status": False, "sentiment": condition})
    print("Total tweets in collection: {}".format(total))
    print("{} retweets".format(rt))
    print("{} quotes".format(quotes))
    print("{} replies".format(replies))

def get_char_count(collection):
    """
    Gets average character count by Tweet in
    :collection -> MongoDB collection obtained with find() or list of JSON documents 
    """
    total_chars = 0
    count = 0

    for tweet in collection:
        total_chars += len(parse_tweet(tweet))
        count +=1

    print("Average character length is: {}".format(total_chars//count))
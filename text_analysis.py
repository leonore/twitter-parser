from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import numpy as np

from helpers import tokenize, parse_tweet, find_sentiment_tb

# file for text analysis
# either: topic extraction (https://www.kaggle.com/jbencina/clustering-documents-with-tfidf-and-kmeans)
# or sentiment analysis

def find_optimal_size(data, max_k):
    """
    Find optimal size for K-means (2 step increment)
    :max_k -> max number of clusters to consider
    """
    iters = range(2, max_k+1, 2)

    min_sse = float('inf')
    optimal_k = 0
    for k in iters:
        sse = MiniBatchKMeans(n_clusters=k, init_size=1024, batch_size=2048, random_state=2211).fit(data).inertia_
        if sse < min_sse:
            min_sse = sse
            optimal_k = k
            print("Found new optimal K: {}".format(k))

    return optimal_k

def topic_extraction(collection, max_topics=100):
    """
    :collection -> MongoDB collection obtained with find() or list of documents
    :max_topics -> max number of topics to analyse K-means performance for
    """

    corpus = []
    for tweet in collection:
        corpus.append(tokenize(parse_tweet(tweet)))

    tfidf = TfidfVectorizer(
        min_df = 5,
        max_df = 0.95,
        max_features = 8000,
    )

    tfidf.fit(corpus)
    text = tfidf.transform(corpus)
    labels = tfidf.get_feature_names()

    K = find_optimal_size(text, max_topics)

    clusters = MiniBatchKMeans(n_clusters=K, init_size=1024, batch_size=2048, random_state=2211).fit_predict(text)

    df = pd.DataFrame(text.todense()).groupby(clusters).mean()

    top = []
    for i, r in df.iterrows():
        top_words = ', '.join([labels[t] for t in np.argsort(r)[-10:]])
        top.append("Cluster {}: {}".format(i, top_words))
    return top

def sentiment_analysis(collection):
    """
    :collection -> MongoDB collection obtained with find() or list of documents
    """

    scores = []
    ids = []

    for tweet in collection:
        text = parse_tweet(tweet)
        scores.append(find_sentiment_tb(tokenize(text)))
        ids.append(tweet['_id'])
    assert len(scores) == len(ids)

    scores = np.array(scores)
    ids = np.array(ids)
    
    return scores, ids

def add_sentiment_to_db(scores, ids, collection):
    """
    :collection -> MongoDB collection reference
    :scores -> sentiment scores obtained with sentiment_analysis()
    :ids -> document ids obtained with sentiment_analysis()
    """

    for tid, score in zip(ids, scores):
        u = collection.update_one({"_id" : tid}, {"$set": {"sentiment": int(score)}})
    assert collection.count({"sentiment": {"$exists": True}}) == len(ids)

import argparse

parser = argparse.ArgumentParser(description='Analyse collection of Tweets from twitter_db in MongoDB.')

parser.add_argument('--collection', '-c', action='store', type=str, help='Name of the collection in MongoDB.twitter_db to analyse', required=True)

args = parser.parse_args()
collection = args.collection

## imports after argparse for performance saving

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from helpers import parse_tweet, get_body, tokenize, find_sentiment_tb, get_top_n_items
from text_analysis import sentiment_analysis, topic_extraction, add_sentiment_to_db
from tweet_statistics import extract_top_entities, number_of, get_char_count
from tweet_networks import user_interaction, hashtag_interaction, hashtag_network_statistics, user_network_statistics
from tweet_networks import build_interaction_graph, get_network_information

from pymongo import MongoClient

"""
Main file to run analysis on a cluster of Twitter data.
Functionality:
- topic extraction
- sentiment analysis
- tweet statistics
- network information
"""

# set up MongoDB connection
client = MongoClient()
db = client.twitter_db
tweets_db = db[collection]

## TOPIC EXTRACTION -> write to results/topics.txt
print("Running topic extraction -> sample_results/topics.txt")
cluster_top_words = topic_extraction(tweets_db.find(), 100) # can change number for max_k
with open('sample_results/topics.txt', 'w') as file:
    for cluster in cluster_top_words:
        file.write(cluster + '\n')

## SENTIMENT ANALYSIS -> save plot to results/sentiment.png
print("Running sentiment analysis -> sample_results/sentiment.png")
scores, ids = sentiment_analysis(tweets_db.find())

# visualisation
bars = plt.bar([-1, 0, 1], [len(scores[scores==-1]), len(scores[scores==0]), len(scores[scores==1])],
       color=["r", "b", "g"], tick_label=["Negative", "Neutral", "Positive"])
plt.tick_params(axis='x', which='both', bottom=False)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x()+0.255, yval, yval) # TODO remove this
plt.title("Number of tweets by sentiment")
plt.savefig("sample_results/sentiment.png", dpi=300)

add_sentiment_to_db(scores, ids, tweets_db) # add to MongoDB so it can be parsed later

# make it easier to iterate/save files
conditions = [{"$exists": True}, -1, 0, 1]
tags = ["all", "negative", "neutral", "positive"]

for idx, condition in enumerate(conditions):
    tag = tags[idx]
    print("Running Tweet analysis for {} tweets".format(tag))

    ## TOP ENTITIES: users, hashtags, mentions, concepts
    print("-> {}".format('sample_results/top_entities_' + tag + '.txt'))
    m, r, h, c = extract_top_entities(tweets_db, condition)
    entities = ["Top Mentions", "Top Retweets", "Top Hashtags", "Top concepts"]
    with open('sample_results/top_entities_' + tag + '.txt', 'w') as file:
        for name, entity in enumerate([m, r, h, c]):
            file.write(entities[name] + '\n')
            file.write(', '.join(get_top_n_items(entity, n=10)))
            file.write('\n\n')

    ## NUMBER OF: tweets, retweets, quotes, replies
    print("-> {}".format('sample_results/tweet_statistics_' + tag + '.txt'))
    n_tweets, n_retweets, n_quotes, n_replies = number_of(tweets_db, condition)
    avg_chars = get_char_count(tweets_db, condition)
    with open('sample_results/tweet_statistics_' + tag + '.txt', 'w') as file:
        file.write("Collection: {}\n".format(tag))
        file.write("Total tweets in collection: {}\n".format(n_tweets))
        file.write("{} retweets\n".format(n_retweets))
        file.write("{} quotes\n".format(n_quotes))
        file.write("{} replies\n".format(n_replies))
        file.write("Average character length is: {}".format(avg_chars))

    # Build network: get number of nodes, edges, groups
    print("-> {}".format('sample_results/network_information_' + tag + '.txt'))
    networks = [n for n in user_interaction(tweets_db, condition)] + [hashtag_interaction(tweets_db, condition)]
    graphs = [build_interaction_graph(network) for network in networks]

    # format: ties, links, transitive, triads
    connections = [user_network_statistics(n) for n in networks[:3]] + [hashtag_network_statistics(networks[3])]

    ## NETWORK ANALYSIS:
    order = ["General network", "Retweet network", "Quote network", "Hashtag network"]
    stats_order = ["Triads", "Loops", "Ties", "Transitive"]
    with open('sample_results/network_information_' + tag + '.txt', 'w') as file:
        file.write("Collection: {}\n".format(tag))
        for i in range(len(order)):
            file.write(order[i] + '\n')
            nodes, edges, subgraphs, size = get_network_information(graphs[i])
            file.write("Number of nodes: {}\n".format(nodes))
            file.write("Number of edges: {}\n".format(edges))
            file.write("Number of subgraphs: {}\n".format(subgraphs))
            file.write("Average group size: {}\n".format(size))
            file.write('\n')

            stats = connections[i]
            for j in range(len(stats)):
                file.write("{}: {}\n".format(stats_order[j], stats[j]))
            file.write('\n')

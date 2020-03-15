## Tweet crawling + Network analysis 📊
#### a.k.a. some analysis of COVID-19 Tweets in the middle of an outbreak

The code of this repository was developed for an assessment as part of the **Web Science (H) course at the University of Glasgow**. The aim was to develop a Tweet crawler and to analyse the obtained Tweets. The software developed works on any collection of Tweets, but the topic of the coronavirus outbreak was picked out of curiosity.

#### Skip to [Recap](#recap) for TL;DR


The following information was extracted from the collection of tweets:
* The number of different types of tweets: retweets, quotes, replies.
* The most retweeted users, the most mentioned users, the most used hashtags, the most reoccurring concepts.
* The size and structure of networks of users in retweets, quotes.
* The size and structure of networks of hashtags.
* The number of connections in networks of users.
* The number of connections in networks of hashtags.

Details on software development and findings are reported in `report/report.pdf`. Associated figures and files can be found in `report/figures/`.

### Running the software

```
git clone https://github.com/leonore/twitter-parser.git
```

#### Requirements

Please use Python3.

```
pip install -r requirements.txt
```

#### Setting up some sample data

A sample JSON file of 5,000 tweets is provided in `data/`. This JSON file can be dumped in a MongoDB collection, although MongoDB needs to be installed first. Instructions can be found [here](https://docs.mongodb.com/manual/installation/).

Once MongoDB + pip requirements are fulfilled, run the following command to write the sample tweets from JSON to MongoDB. The tweets will be stored in the database `twitter_db` in collection `sample_tweets`. This can be changed in file `json_to_mongo.py` if needed.
```
python json_to_mongo.py -f data/sample.json
```

Your own MongoDB collection of tweets can also be used: change the reference in files `json_to_mongo` and `sample_analysis`.      
 A final alternative would be to run the Twitter crawler with your own authentication keys. For this, add your consumer + access keys and tokens in a file called `keys.py`. Then run one of the following commands:

```bash
python streaming_crawler.py -c NAME_OF_YOUR_COLLECTION -t HOW_LONG_TO_RUN # runs 1% sampling
python hybrid_crawler.py -c NAME_OF_YOUR_COLLECTION -t HOW_LONG_TO_RUN
```

PyMongo will store tweets in the database `twitter_db`.    

Please note the hybrid crawler uses keywords related to coronavirus. This can be adapted if not needed.

#### Analysing the data

Then, all data can be analysed with the following command:

```
python sample_analysis.py -c sample_tweets # sample tweets can be any other collection in twitter_db
```

Please note this might take some time depending on the size of the collection.
All results will be saved in `sample_results/`

### Recap

```bash
pip install -r requirements.txt
python json_to_mongo.py -f data/sample.json
python sample_analysis.py -c sample_tweets
ls sample_results/  # list all files containing analysis data
```

_______________________

### Appendix: improving the software

This suite of analysis functions could be more modular. At the moment if you want to run your own analysis with this you might want to change a few things:

* Tweet sampling is done with location, user, and hashtag probes and keywords. These can be changed.
* Topic extraction with K-means looks for the optimal K until K=100. Max K can be changed.
* Sentiment analysis could be extended to take into account the subjectivity of Tweets. A more objective Tweet might help us find accounts of higher "trust factor" to relay important information.
* Right now the top 10 entities are extracted but this can be changed too.
* Analysis gets exponentially slower as the size of the data grows larger. This needs improvement.
* Visualisation tools could be improved too. Graphs built with `get_network_information()` in `tweet_networks.py` can be exported to be read by [Gephi](https://gephi.org) using `nx.write_gexf(G, '[file].gexf')`. Gephi struggles a bit with large networks, but the best layout seems to be Force Atlas 2 followed by Label Adjust.  

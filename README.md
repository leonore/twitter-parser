## Tweet crawling + analysis
#### aka. analysing COVID-19 Tweets in the middle of an outbreak

The code of this repository was developed for an assessment as part of the Web Science (H) course at the University of Glasgow. The aim was to develop a Tweet crawler and to analyse the obtained Tweets. The software developed works on any collection of Tweets, but the topic of the coronavirus outbreak was picked out of curiosity.

The following information was extracted from the collection of tweets:
* The number of different types of tweets: retweets, quotes, replies.
* The most retweeted users, the most mentioned users, the most used hashtags, the most reoccurring concepts.
* The size and structure of networks of users in retweets, quotes.
* The size and structure of networks of hashtags.
* The number of connections in networks of users.
* The number of connections in networks of hashtags.

Details on software development and findings are reported in `report/report.pdf`. Associated figures and files can be found in `report/figures/`.

### Running the software

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

Your own MongoDB collection of tweets can also be used.     
 A final alternative would be to run the Twitter crawler with your own authentication keys. For this, add your consumer + access keys and tokens in a file called `keys.py`. Then run the following command:

```bash
python streaming_crawler.py # runs 1% sampling for one hour
python hybrid_crawler -db NAME_OF_YOUR_COLLECTION -t HOW_LONG_TO_RUN
```

PyMongo will store tweets in the database `twitter_db`.    

Please note the hybrid crawler uses keywords related to coronavirus. This can be adapted if not needed.

#### Analysing the data

Then, all data can be analysed with the following command:

```
python sample_analysis.py -db sample_tweets # sample tweets can be any other collection in twitter_db
```

Please note this might take some time depending on the size of the collection.
All results will be saved in `results/`

### Recap

```bash
pip install -r requirements.txt
python json_to_mongo -f data/sample.json
python sample_analysis.py -db sample_tweets
ls results/        # list all files containing analysis data
```

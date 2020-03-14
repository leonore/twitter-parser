import argparse

parser = argparse.ArgumentParser(description='JSON file (obtained from bson) to a MongoDB.')

parser.add_argument('--file', '-f', action='store', type=str, help='Name of the file to import', required=True)
parser.add_argument('--collection', '-c', action='store', type=str, help='Collection in twitter_db to save to', required=False)

args = parser.parse_args()
file = args.file
collection = args.collection

from pymongo import MongoClient
from bson.json_util import dumps, loads

client = MongoClient()
db = client.twitter_db

if not collection:
    collection = "sample_tweets"

sample_collection = db[collection]

with open(file, 'r') as f:
    sample_tweets = loads(f.read())

sample_collection.insert_many(sample_tweets)

print("Inserted {} into collection {} in twitter_db".format(file, collection))

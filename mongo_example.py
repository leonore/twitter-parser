from pymongo import MongoClient

client = MongoClient()

db = client.twitter_db
collection = "streaming_crawler"

print(db.posts)
print(db[collection].posts)

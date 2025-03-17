from pymongo import MongoClient

class Database:
    def __init__(self, mongo_srv):
        self.mongo_srv = mongo_srv
        print('Creating database connection')
        self.client = MongoClient(mongo_srv, tls=True, tlsAllowInvalidCertificates=True)
        self.db = self.client["ajio_tracker"]
        print('Database connection created successfully')

    def get_db(self):
        return self.db
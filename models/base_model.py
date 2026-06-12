"""Model base"""
from utils.database import DatabaseConnection

class BaseModel:
    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def create_table(self, query):
        self.db.execute(query)

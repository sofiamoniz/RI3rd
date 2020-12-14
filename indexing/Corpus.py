"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""


#Class that returns chunks of Corpus
from pandas import read_csv

class CorpusReader():

    def __init__(self, csvfile):
        self.chunkSize = 150000
        self.iterator = read_csv(csvfile, chunksize=150000, iterator=True)
        self.csvfile = csvfile
        

    def nextChunk(self):
        try:
            chunk = self.iterator.get_chunk()
        except StopIteration:
            self.iterator = read_csv(self.csvfile, chunksize=self.chunkSize, iterator=True)
            return None

        chunk = chunk.dropna(subset=['abstract', 'title'])   # only documents with not empty abstract
        chunk = chunk[['cord_uid', 'title', 'abstract']] 

        return chunk.values
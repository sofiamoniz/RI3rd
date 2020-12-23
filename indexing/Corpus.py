"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from pandas import read_csv

## Class that returns chunks/blocks of Corpus
class CorpusReader():

    def __init__(self, csvfile):
        self.chunkSize = 20000 # number of lines
        self.iterator = read_csv(csvfile, chunksize=self.chunkSize, iterator=True)
        self.csvfile = csvfile
        

    def nextChunk(self):
        """
        Returns next readed chunk of Corpus
        """
        try:
            chunk = self.iterator.get_chunk()
        except StopIteration:
            self.iterator = read_csv(self.csvfile, chunksize=self.chunkSize, iterator=True)
            return None

        chunk = chunk.dropna(subset=['abstract', 'title']) # only documents with not empty abstract or title
        chunk = chunk[['cord_uid', 'title', 'abstract']] 

        return chunk.values
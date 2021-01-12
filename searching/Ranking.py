"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from indexing.ImprovedTokenizer import ImprovedTokenizer
from indexing.SimpleTokenizer import SimpleTokenizer
from collections import defaultdict
from math import pow, log10, sqrt
import time, sys, json
import itertools

## Class that calculates de scores for each document that answers a query, based on the choosen Ranking
class Ranking:

    def __init__(self, tokenizer, queries, consider_proximity):
        if tokenizer == "s":
            from indexing.SimpleTokenizer import SimpleTokenizer
            self.tokenizer = SimpleTokenizer()
        else:
            from indexing.ImprovedTokenizer import ImprovedTokenizer
            self.tokenizer = ImprovedTokenizer()
        self.queries = self.tokenize(queries) # [ query1_tokenized, ...]
        self.consider_proximity = consider_proximity

        self.weighted_index = {} # will store weighted index from disk
        self.partitions_in_memory = [] # index partitions in memory
        self.weighted_queries = [] # only for lnc.ltc
        self.scores = [] # scores of documents for each query
        self.queries_latency = {} # latency of each query
        self.latency_time_weight_queries = {} # only for lnc.ltc because the process have 2 parts

# lnc.ltc:

    def weight_queries_lnc_ltc(self):
        """
        Computes the weights for each term of the query, for all the queries
        """
        for query in self.queries:

            start_time = time.time() # latency time of this process, for each query
            temp = 0
            query_length = 0
            weighted_query = defaultdict(int) # weighted_query = { "term1": weight_of_term1_in_query, ...}  

            for term in query: 
                weighted_query[term] = weighted_query[term] + 1 # tf on query

            for term in weighted_query:

                index_in_memory = False
                for partition in self.partitions_in_memory:
                    if term[0] in self.char_range(partition[0], partition[1]):
                        index_in_memory = True
                        break
                if index_in_memory == False:
                    if self.memory_full(): # there is no memory available to store more index parts
                        self.partitions_in_memory = [] # empty all
                        self.weighted_index = {}
                    self.weighted_index.update(self.get_weighted_index(term))
                
                if term in self.weighted_index.keys(): # if the term exists on any document   
                    weighted_query[term] = (1 + log10(weighted_query[term])) * self.weighted_index[term][0] # self.weighted_index[term][0] -> idf of the term 
 
            # Normalization:
            for term,value in weighted_query.items():
                temp = temp + (pow(value, 2))
            query_length = sqrt(temp)
            for term,value in weighted_query.items():
                weighted_query[term] = value / query_length

            self.latency_time_weight_queries[self.queries.index(query)] = time.time()-start_time 

            self.weighted_queries.append(weighted_query) # self.weighted_queries = [ weighted_query1, weighted_query2, ...]
            
    def score_lnc_ltc(self):
        """
        Computes the scores for all documents that answers the query
        """
        for i in range(0, len(self.queries)): 

            start_time = time.time() # latency time of this process, for each query
            docs_scores_for_query = defaultdict(int) # docs_scores_for_query = { doc1: score1, doc2: score2, ...} for all docs that answers the query
            
            for term, term_query_weight in self.weighted_queries[i].items():  
                if term in self.weighted_index: # if term exists in any document
                    for doc_id,term_doc_weight_pos in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                        term_doc_weight = term_doc_weight_pos[0]
                        docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + (term_query_weight * term_doc_weight)

            if self.consider_proximity:                
                docs_scores_for_query = self.proximity(self.queries[i], docs_scores_for_query)
        
            docs_scores_for_query = {k: v for k, v in sorted(docs_scores_for_query.items(), key = lambda item: item[1], reverse = True)} # order by score ( decreasing order )

            self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            score_time = time.time() - start_time
            weight_time = self.latency_time_weight_queries[i]

            self.queries_latency[i + 1] = weight_time + score_time # i+1 because in the evaluation part the id for the queries starts at 1

# bm25:

    def score_bm25(self):
        """
        Computes the scores for all documents that answers the query
        """
        for query in self.queries: 
            
            start_time = time.time() # latency time for each query in the bm25 ranking, starts here
            docs_scores_for_query = defaultdict(int) # docs_score = { doc1: score1, doc2: score2, ...} for all docs that answers the query
            temp = 0
            query_length = 0      
            
            for term in query: 

                index_in_memory = False
                for partition in self.partitions_in_memory:
                    if term[0] in self.char_range(partition[0], partition[1]):
                        index_in_memory = True
                        break
                if index_in_memory == False:
                    if self.memory_full(): # there is no memory available to store more index parts
                        self.partitions_in_memory = [] # empty all
                        self.weighted_index = {}
                    self.weighted_index.update(self.get_weighted_index(term))
                
                if term in self.weighted_index:  # if term exists in any document
                        for doc_id,doc_weight_pos in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                            doc_weight = doc_weight_pos[0] * self.weighted_index[term][0] # doc weight * idf           
                            docs_scores_for_query[doc_id] += doc_weight

            if self.consider_proximity:                
                docs_scores_for_query = self.proximity(query, docs_scores_for_query)
            
            docs_scores_for_query = {k: v for k, v in sorted(docs_scores_for_query.items(), key = lambda item: item[1], reverse = True)} # order by score ( decreasing order )

            self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            query_latency_time = time.time() - start_time
            self.queries_latency[self.queries.index(query) + 1] = query_latency_time # i+1 because in the evaluation part the id for the queries starts at 1

# Proximity:

    def proximity(self, query_terms, docs_scores_for_query):
        """
        Adds proximity boost based on how many query terms occur consecutively in a document (as a phrase)
        """
        docID_term = {} # will store the terms of the query that occur in that document

        for term in query_terms:
            if term in self.weighted_index:
                for docID, doc_weight_pos in self.weighted_index[term][1].items():
                    if docID not in docID_term:
                        docID_term[docID] = [term]
                    else:
                        tmp = docID_term[docID]
                        tmp.append(term)
                        docID_term[docID] = tmp
                        
        for docID, terms in docID_term.items():
            term_pos = {}
            for term in terms:
                term_pos[term] = self.weighted_index[term][1][docID][1] # take the positions of the term for that docID
 
            window = self.calculate_window(term_pos)
            docs_scores_for_query[docID] += window * 0.1 # query proximity boost (bigger windows have a bigger query phrase)
            
        return docs_scores_for_query

    def calculate_window(self, pos_term):
        """
        Calculates how many terms occur in consecutive positions
        """
        if len(pos_term) == 0: return 0
        minWindow = 1
        all_pos = []
        for term, positions in pos_term.items():
            all_pos += positions
        for i in range(len(all_pos)):
            for j in range(i + 1, len(all_pos)):
                if all_pos[j] == all_pos[i] + 1: minWindow += 1

        return minWindow
   
## AUXILIAR FUNCTIONS:

    def tokenize(self, queries):
        """
        Returns an array with each query tokenized
        """
        tokenized_queries = []
        for query in queries:
            tokenized_query = self.tokenizer.tokenize(query)
            tokenized_queries.append(tokenized_query)
        return tokenized_queries

    def get_weighted_index(self, term):
        """
        Constructs the Weighted Index, for a certain partition, based on the first letter of term received as argument, from the files in disk
        """
        weighted_index = {} # { "term" : [ idf, {"doc1": [weight_of_term_in_doc1, [position_of_term_in_doc1, next_position_of_term_in_doc1,...]],...}],... }
        partition_file, partition = self.get_weighted_file(term[0])
        self.partitions_in_memory.append(partition)
        file = open(partition_file, 'r')
        for line in file:
            tokens=line.rstrip().split(';')
            term = tokens[0]
            idf = float(tokens[1])
            tokens[2] = tokens[2].replace('\'','\"')
            weights_pos = json.loads(tokens[2])
            weighted_index[term] = [idf,weights_pos]
        file.close()
        return weighted_index 

    def char_range(self, first_char, last_char): 
        """
        Generates the characters from first_char to last_char, inclusive.
        """
        for c in range(ord(first_char), ord(last_char)+1):
            yield chr(c)

    def get_weighted_file(self, term_char):
        """
        Returns the file with the part of Weighted Index that contains the partition where the term_char fits
        """
        if term_char in self.char_range("a","f"):
            return ("models/mergedWeighted/a-f.txt", ("a", "f"))
        elif term_char in self.char_range("g","p"):
            return ("models/mergedWeighted/g-p.txt", ("g", "p"))
        else:
            return ("models/mergedWeighted/q-z.txt", ("q", "z"))

    def memory_full(self):
        return False
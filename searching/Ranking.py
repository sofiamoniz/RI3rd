"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from indexing.ImprovedTokenizer import ImprovedTokenizer
from indexing.SimpleTokenizer import SimpleTokenizer
import math
from collections import defaultdict
import time
import sys


## Class that calculates de scores for each document that answers a query, based on the choosen Ranking
class Ranking:

    def __init__(self,tokenizer,queries,weighted_index):
        self.tokenizer_type = tokenizer
        self.queries = queries
        self.weighted_index = weighted_index

        if self.tokenizer_type=="s":
            from indexing.SimpleTokenizer import SimpleTokenizer
            self.tokenizer = SimpleTokenizer()
        else:
            from indexing.ImprovedTokenizer import ImprovedTokenizer
            self.tokenizer = ImprovedTokenizer()
        self.weighted_queries = [] # only for lnc.ltc
        self.scores = []
        self.queries_latency = {}
        self.latency_time_weight_queries = {} # only for lnc.ltc because the process have 2 parts


    # lnc.ltc:

    def weight_queries_lnc_ltc(self):
        """
        Computes the weights for each term of the query, for all the queries
        """
        for query in self.queries: # one query at a time
            start_time = time.time() # latency time of this process, for each query
            temp=0
            query_length=0
            weighted_query=defaultdict(int)    # weighted_query = { "term1": weight_of_term1_in_query, ...}   for all terms in the query

            # Tokenize the query with the same tokenizer used on the documents:
            
            query_terms = self.tokenizer.tokenize(query)

            for term in query_terms: # query terms already tokenized and processed
                weighted_query[term] = weighted_query[term]+1 # tf on query

            for term in weighted_query:
                if term in self.weighted_index.keys(): # if the term exists on any document (and so exists on the weighted index)   
                    weighted_query[term] = (1 + math.log10(weighted_query[term])) * self.weighted_index[term][0] # self.weighted_index[term][0] -> idf of the term 
 

            # Normalization:
            for term,value in weighted_query.items():
                temp = temp + (math.pow(value,2))
            query_length = math.sqrt(temp)
            for term,value in weighted_query.items():
                weighted_query[term] = value / query_length

            self.latency_time_weight_queries[self.queries.index(query)]=time.time()-start_time 

            self.weighted_queries.append(weighted_query) # self.weighted_queries = [ weighted_query1, weighted_query2, ...]
            
     
    def score_lnc_ltc(self):
        """
        Computes the scores for all documents that answers the query
        """
        for i in range(0,len(self.queries)): # one query at a time

            start_time = time.time() # latency time of this process, for each query

            docs_scores_for_query=defaultdict(int) # docs_scores_for_query = { doc1: score1, doc2: score2, ...} for all docs that answers the query

            for term,term_query_weight in self.weighted_queries[i].items():  
                if term in self.weighted_index: # if term exists in any document
                    for doc_id,term_doc_weight in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                        docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + (term_query_weight * term_doc_weight)

            docs_scores_for_query={k: v for k, v in sorted(docs_scores_for_query.items(), key=lambda item: item[1], reverse=True)} # order by score ( decreasing order )
            
            self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            score_time=time.time()-start_time
            weight_time=self.latency_time_weight_queries[i]

            self.queries_latency[i+1] = weight_time + score_time # i+1 because in the evaluation part the id for the queries starts at 1


    # bm25:

    def score_bm25(self):
        """
        Computes the scores for all documents that answers the query
        """
        for query in self.queries: # one query at a time
            start_time = time.time() # latency time for each query in the bm25 ranking, starts here
            docs_scores_for_query=defaultdict(int) # docs_score = { doc1: score1, doc2: score2, ...} for all docs that answers the query
            temp=0
            query_length=0

            # Tokenize the query with the same tokenizer used on the documents:
            
            query_terms = self.tokenizer.tokenize(query)


            for term in query_terms: # query terms already tokenized and processed
                if term in self.weighted_index:  # if term exists in any document
                    for doc_id,doc_weight in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                        docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + doc_weight
         
            docs_scores_for_query={k: v for k, v in sorted(docs_scores_for_query.items(), key=lambda item: item[1], reverse=True)} # order by score ( decreasing order )
            
            self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            query_latency_time=time.time() - start_time
            self.queries_latency[self.queries.index(query)+1] = query_latency_time # +1 because in the evaluation part the id for the queries starts at 1
           

    def contains_all_terms(self, pos_term, window): #check if a given window contains all the terms present at least once
        contains = False
        #pos_term vai ser a lista ou isso q diz o termo-posicao
        for term in pos_term:
            minPos = window[0]
            maxPos = window [1]
            for pos in pos_term[term]:
                if (pos >= minPos and pos <= maxPos):
                    contains = True
                    break
                else:
                    contains = False
            if (contains == False):
                return contains
        return contains
    
    def calc_min_window(self, pos_term): #calculates the smallest in a doc containing all terms of that query
        x=0
        y=0
        window = (x,y)
        windows = []

        #Calculate maximum position between all terms
        max_val = 0
        i = 0
        for term in pos_term:
            pos_term[term].sort() #sort positions for that term
            value = int(max(pos_term[term]))
            if (i==0): #if it's the first iteration, then it will be the max_value 
                max_val = value
            else:
                if (value > max_val):
                    max_val = value
            i = i+1

        #Calculate all possible windows
        while (y<= max_val and x<=max_val):
            if(self.contains_all_terms(pos_term,window)):
                windows.append(window)
                x+=1
                window = (x,y)
            else:
                y+=1
                window = (x,y)

        #Calculate minimum possible window
        min_window = 0
        for i in range(len(windows)):
            if(len(windows) == 0):
                break
            win = windows[i][1] - windows[i][0] + 1
            if(i == 0):
                min_window = win
            else:
                if(win < min_window):
                    min_window = win
                    
        return min_window

    def calc_short_span(self, query_terms, pos_term): #calculate the len of the shortest doc segment that covers all query
                                #term occurrences in a doc
        min_pos = sys.maxint
        max_pos = 0
        total_term_occur = 0
        no_term_occur = 0

        for term in query_terms:
            if term in pos_term:
                if(min(pos_term[term]) < min_pos):
                    min_pos = min(pos_term[term])
                if(max(pos_term[term]) > max_pos):
                    max_pos = max(pos_term[term])
                no_term_occur = no_term_occur + 1
                total_term_occur = total_term_occur + len(pos_term[term])

        window = max_pos - min_pos

        if(min_pos == sys.maxint and max_pos == 0):
            window = sys.maxint
        elif(window == 0):
            window = 1
        else:
            window = window + 1
        return [window, no_term_occur, total_term_occur]

    def get_queries_latency(self):
        """
        Returns the dictionary with latency of each query
        """
        return self.queries_latency
        
    
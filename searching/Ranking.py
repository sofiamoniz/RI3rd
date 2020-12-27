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

    def score_bm25(self, consider_proximity = True): #passar arg a true se quisermos considerar
        """
        Computes the scores for all documents that answers the query
        """
        query_windows = {}
        for query in self.queries: # one query at a time
            start_time = time.time() # latency time for each query in the bm25 ranking, starts here
            docs_scores_for_query=defaultdict(int) # docs_score = { doc1: score1, doc2: score2, ...} for all docs that answers the query
            temp=0
            query_length=0
            
            # Tokenize the query with the same tokenizer used on the documents:
            
            query_terms = self.tokenizer.tokenize(query)
            
            for term in query_terms: # query terms already tokenized and processed
                if term in self.weighted_index:  # if term exists in any document
                    
                    for doc_id,doc_weight_pos in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                        doc_weight = doc_weight_pos[0]
                        #term_positions = doc_weight_pos[1]                
                        docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + doc_weight
         
            docs_scores_for_query={k: v for k, v in sorted(docs_scores_for_query.items(), key=lambda item: item[1], reverse=True)} # order by score ( decreasing order )
            
            if consider_proximity:                
                self.scores.append(self.consider_proximity(query_terms, docs_scores_for_query))
            else:
                self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            query_latency_time=time.time() - start_time
            self.queries_latency[self.queries.index(query)+1] = query_latency_time # +1 because in the evaluation part the id for the queries starts at 1


    def get_queries_latency(self):
        """
        Returns the dictionary with latency of each query
        """
        return self.queries_latency
        
    def consider_proximity(self, query_terms , docs_scores_for_query):
        proximity_score_dict={} # dictionary that contains the document ID and its proximity score
        tp_score = {}
        for q_term in range(len(query_terms) -1):
            proximity_terms = query_terms[q_term:q_term+2] #verify the proximity of the terms 2 by 2
            if (proximity_terms[0] in self.weighted_index) & (proximity_terms[1] in self.weighted_index):
                for docID,doc_weight_pos in self.weighted_index[proximity_terms[0]][1].items():
                    numerator_score = 0
                    if docID in self.weighted_index[proximity_terms[1]][1]:                      
                        numerator_score = self.check_proximity(proximity_terms[0],proximity_terms[1],
                                                           docID)
                    try:
                        proximity_score_dict[docID]+=numerator_score
                    except KeyError:
                        proximity_score_dict[docID]=numerator_score
        #for doc_id,prox_score in proximity_score_dict.items():
        #    tp_score[doc_id] = prox_score + docs_scores_for_query[doc_id]
        for doc_id in docs_scores_for_query:
            if doc_id in proximity_score_dict:
                tp_score[doc_id] = proximity_score_dict[doc_id] + docs_scores_for_query[doc_id]
            else:
                tp_score[doc_id] = docs_scores_for_query[doc_id]
        return {k: v for k, v in sorted(tp_score.items(), key=lambda item: item[1], reverse=True)} # order by score ( decreasing order )          


    def check_proximity(self,term1,term2,DocID):
        pos_doc_term1=[]
        pos_doc_term2=[]
        total_score=0.0
        pos_doc_term1=self.weighted_index[term1][1][DocID][1] #positions of term in that doc
        pos_doc_term2=self.weighted_index[term2][1][DocID][1]
        for pos in pos_doc_term1:
            termscore=0.0
            if pos+1 in pos_doc_term2: #dar os scores q quisermos (?)
                termscore= 1.0
            elif pos+2 in pos_doc_term2:
                termscore= 0.95
            elif pos+3 in pos_doc_term2:
                termscore= 0.9
            elif pos+4 in pos_doc_term2:
                termscore= 0.60
            elif pos+5 in pos_doc_term2:
                termscore= 0.30
            elif pos+6 in pos_doc_term2:
                termscore= 0.15
            elif pos+7 in pos_doc_term2:
                termscore= 0.05
            total_score+=termscore
            #há algumas queries em q as palavras estão tão distantes q ele nem lhe dá score
            #não sei se é suposto ser assim ou se temos que atribuir mais scores super baixinhos
            #para distâncias muito altas
        
        return total_score # score of the 2 terms according to the distance between them
    
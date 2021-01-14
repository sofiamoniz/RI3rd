"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from sys import getsizeof
from math import log10, sqrt
from collections import defaultdict


## Class that creates the Weighted Index from the InvertedIndex
class WeightedIndexer:

    def __init__(self, total_docs, inverted_index, documents_len, total_terms):
        self.total_docs = total_docs
        self.inverted_index = inverted_index
        self.documents_len = documents_len
        self.total_terms = total_terms

        self.avgdl = 0     
        self.weighted_index = {}
        
    ## inverted_index = { "term" : [ doc_freq, {"doc1": [position_of_term_in_doc1, next_position_of_term_in_doc1,...],...}],...}
    ## weighted_index = { "term" : [ idf, {"doc1": [weight_of_term_in_doc1, [position_of_term_in_doc1, next_position_of_term_in_doc1,...]],...}],... }
    
    def calc_avgdl(self):
        """
        Calculate the Average Document Length for BM25
        """
        count = 0
        for doc_id in self.documents_len:
            self.avgdl += self.documents_len[doc_id]
            count += 1
        self.avgdl /= count

# lnc.ltc:

    def lnc_ltc(self):       
        """
        Calculates the lnc.ltc weights of each document
        """
        doc_pow_sum = defaultdict(int) # This will be used as the normalization factor.

        for term in self.inverted_index:
            docsWeigh = defaultdict(lambda:[0,list]) # {"doc1": [weight_of_term_in_doc1, [position_of_term_in_doc1, next_position_of_term_in_doc1,...],...}
            idf_docsWeight = [] # [idf,docWeights_with_lnc_ltc_and_positions]  
                              
            idf = log10(self.total_docs/self.inverted_index[term][0])
            idf_docsWeight.append(idf)         

            
            for doc_id in self.inverted_index[term][1]: 
                try: tf = len(self.inverted_index[term][1][doc_id]) # term frequency (tf) - number of times each term appears in a doc
                except: tf = self.inverted_index[term][1][doc_id]
                weight = 1 + log10(tf) # this calculates the weight of term-document
                doc_pow_sum[doc_id] += weight ** 2 # sum of all the weights of each document
                                                   # each weight to the pow of 2
                                                   # this will be used in the cossine normalization
                docsWeigh[doc_id][0] = weight
                docsWeigh[doc_id][1] = self.inverted_index[term][1][doc_id] # list with term positions in this doc
            
            idf_docsWeight.append(docsWeigh)
            self.weighted_index[term] = idf_docsWeight

        ## Normalization:
        for term, idf_docsWeight in self.weighted_index.items():
            for doc_id, values in idf_docsWeight[1].items():
                values[0] = values[0] * 1/sqrt(doc_pow_sum[doc_id])
                        
            

# bm25:

    def bm25(self,  k = 1.2 , b = 0.75): 
        """
        Calculates the bm25 weights of each document
        """   
        self.calc_avgdl() #calculates avgdl only when calling bm25

        for term in self.inverted_index: 
            docsWeigh = defaultdict(lambda:[0,list]) # {"doc1": [weight_of_term_in_doc1, [position_of_term_in_doc1, next_position_of_term_in_doc1,...],...} 
            idf_docsWeight = [] # [idf, docWeights_with_bm25_and_positions]  
            idf = log10(self.total_docs / self.inverted_index[term][0])
            idf_docsWeight.append(idf)
            for doc_id in self.inverted_index[term][1]: 
                
                try: tf = len(self.inverted_index[term][1][doc_id]) # term frequency (tf) - number of times each term appears in a doc
                except: tf = self.inverted_index[term][1][doc_id]
                
                docsWeigh[doc_id][0] = ((k + 1) * tf) / (k * ((1 - b) + b*(self.documents_len[int(doc_id)]) / self.avgdl) + tf) # okapi bm25 formula
                docsWeigh[doc_id][1] = self.inverted_index[term][1][doc_id] # list with term positions in this doc

            idf_docsWeight.append(docsWeigh)

            self.weighted_index[term] = idf_docsWeight


## AUXILIAR FUNCTIONS:

    def get_weighted_index(self):
        """
        Returns the dictionary with the Weighted Index
        """
        return self.weighted_index             
                
    def empty_weighted_index(self):
        """
        Empty the dictionary in memory
        """
        self.weighted_index = {} 
   


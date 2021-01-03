"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from collections import defaultdict
from statistics import mean
from math import log2

## Class to calculates the metrics, for a query, asked in the last exercice of the Assignment 2/3
class Evaluation:

    def __init__(self, relevances, scores):
        self.relevances = relevances  # { query1_id : { doc_1: relevance, doc_2: relevance,...},...} 
        self.scores = scores  # { query1_id : {doc_1 : score , doc_2: score,...},...} 

        self.queries_precision = {}
        self.queries_recall = {}
        self.queries_f1 = {}
        self.queries_average_precision = {}
        self.queries_ndcg = {}

    def precision_recall(self, query_id):
        """
        Calculates the mean precision and mean recall for this query
        """
        tp_fn = 0
        tp_fp = 0
        tp = 0
        total_precision = 0

        for doc,relevance in self.relevances[query_id].items():
            if (doc in self.scores[query_id]) and relevance > 0: # if the doc exists in our scores and has relevance
                tp += 1 # We found a true positive
            if relevance > 0: # All relevante docs
                tp_fn += 1 # We found a true_positive-false_negative

        tp_fp = len(self.scores[query_id]) # All retrieved docs
                        
        self.queries_precision[query_id] = (tp/tp_fp) # Calculates the precision for this query
        if tp_fn != 0: # If true_positive-false_negative exist, we calculate the recall for each query
            self.queries_recall[query_id] = (tp/tp_fn)
        else:
            self.queries_recall[query_id] = 0

    def f1(self, query_id):
        """
        Calculates the mean f-measure for this query
        """
        if self.queries_precision[query_id] != 0 and self.queries_recall != 0 : # if both precision and recall have a value
            self.queries_f1[query_id] = 2 * ((self.queries_precision[query_id] * self.queries_recall[query_id])
                                                     / (self.queries_precision[query_id] + self.queries_recall[query_id])) # f1 calculation
        else: # If precision and recall is 0
            self.queries_f1[query_id] = 0

    def average_precision(self, query_id):
        """
        Calculates the average precision for this query
        """
        tp_fp = 0
        tp = 0
        precisions = []
            
        for doc,score in self.scores[query_id].items(): # Iterate by the retrieved documents, in the order they were retrieved
            relevant = False
            tp_fp += 1 # All returned docs
            if doc in self.relevances[query_id] and self.relevances[query_id][doc]>0:
                relevant = True # Its a relevant document
                tp += 1
            precision = tp/tp_fp # At this position/moment
                
            if relevant == True: precisions.append(precision) # Saves the precisions where a relevant document was retrieved, in order to calculate the average precision

        if len(precisions) != 0:
            average_precision = mean(precisions) # Calculates the mean of the precisions where a relevant document was retrieved
        else:
            average_precision = 0

        self.queries_average_precision[query_id] = average_precision # Average precision for this query

    def get_returned_relevances(self, query_id):
        """
        Returns the relevances of the documents returned by the Retrieval Engine, for this query
        """
        docs_relevance = {}
        for doc,score in self.scores[query_id].items():
            if doc in self.relevances[query_id]: # If the document exists on the reference file
                docs_relevance[doc] = self.relevances[query_id][doc]
            else: docs_relevance[doc] = 0
        return docs_relevance

    def dcg(self, query_id):
        """
        Calculates the discounted cumulative gain (dcg), for this query
        """
        returned_relevances = self.get_returned_relevances(query_id) # relevances of the returned docs
        query_dcg = 0
        count = 0
        for doc,relevance in returned_relevances.items():       
            count += 1 # Count is used as the indice for each document
            query_dcg += relevance / log2(count + 1) # dcg formula
           
        return query_dcg

    def ndcg(self, query_id):
        """
        Calculates the mean normalized DCG (NDCG), for this query
        """
        query_dcg = self.dcg(query_id)

        ideal_dcg = defaultdict(int)
        relevances_ordered = {}
        count = 0
        # This time, we will order the relevant docs for each query, in decreasing order
        # Ex: query_1 : {doc1: 2, doc2:1, doc3:1 , doc4:0}
        # So that we can have the ideal elements.
        # Then, by normalizing the dcg with these values, we achive normalized DCG
        relevances_ordered[query_id] = {k: v for k, v in sorted(self.relevances[query_id].items(), key=lambda item: item[1], reverse=True)}
            
        for doc,relevance in relevances_ordered[query_id].items():
            count += 1 # Count is used as the indice for each document
            ideal_dcg[query_id] += relevance / log2(count + 1)
            if count == len(self.scores[query_id]): break # We only need the top N 
                
        if ideal_dcg[query_id] != 0:
            self.queries_ndcg[query_id] = query_dcg / ideal_dcg[query_id] # The NDCG is found by dividing the
                                                                                   # DCG values by corresponding ideal values
        else:
            self.queries_ndcg[query_id] = 0

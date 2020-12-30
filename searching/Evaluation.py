"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from statistics import mean, median
from collections import defaultdict
from math import log2

## Class to calculates the metrics asked in the last exercice of the Assignment 2/3
class Evaluation:

    def __init__(self, relevances, scores):
        self.relevances = relevances  # { query1_id : { doc_1: relevance, doc_2: relevance,...},...} 
        self.scores = scores  # { query1_id : {doc_1 : score , doc_2: score,...},...} 

        self.returned_relevances = defaultdict(dict)
        self.queries_precision = {}
        self.queries_recall = {}


    def mean_precision_recall(self):
        """
        Calculates the mean precision and mean recall 
        """
        for query_id in self.scores:
        
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

        mean_precision = mean(list(self.queries_precision.values())) # The mean of precisions of all queries
                                                                            
        mean_recall = mean(list(self.queries_recall.values())) # The mean of recals of all queries
       
        print("Mean Precision -> ", mean_precision)
        print("Mean Recall ->  ", mean_recall)



    def mean_f1(self):
        """
        Calculates the mean f-measure
        """
        queries_f1 = {}

        for query_id in self.queries_precision:
            if self.queries_precision[query_id] != 0 and self.queries_recall != 0 : # if both precision and recall have a value
                queries_f1[query_id] = 2 * ((self.queries_precision[query_id] * self.queries_recall[query_id])
                                                     / (self.queries_precision[query_id] + self.queries_recall[query_id])) # f1 calculation
            else: # If precision and recall is 0
                queries_f1[query_id] = 0

        mean_f1 = mean(list(queries_f1.values())) # The mean of f1 of all queries

        print("Mean F-Measure -> ", mean_f1)



    def average_precision(self):
        """
        Calculates the average precision
        """
        queries_average_precision = {}

        for query_id in self.scores:

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

            queries_average_precision[query_id] = average_precision # Average precision for this query
        
        return queries_average_precision




    def mean_average_precision(self): 
        """
        Calculates the mean average precision (MAP)
        """
        queries_average_precision = self.average_precision()

        #print(self.queries_average_precision)
        # The MAP value is the mean of all average precision values, calculated previously
        mean_average_precision = mean(list(queries_average_precision.values()))
        
        print("MAP -> " + str(mean_average_precision))



    def get_returned_relevances(self):
        """
        Saves the relevances of the documents returned by the Retrieval Engine, for each query
        """
        for query_id in self.relevances:
            for doc,score in self.scores[query_id].items():
                docs_relevance = self.returned_relevances[query_id]
                if doc in self.relevances[query_id]: # If the document exists on the reference file
                    docs_relevance[doc] = self.relevances[query_id][doc]
                else: docs_relevance[doc] = 0
                self.returned_relevances[query_id] = docs_relevance




    def dcg(self):
        """
        Calculates the discounted cumulative gain (dcg)
        """
        self.get_returned_relevances()

        queries_dcg = defaultdict(int)

        for query_id in self.returned_relevances:            
            count = 0
            for doc,relevance in self.returned_relevances[query_id].items():       
                count += 1 # Count is used as the indice for each document
                queries_dcg[query_id] += relevance / log2(count + 1) # dcg formula
           
        return queries_dcg


    def mean_ndcg(self):
        """
        Calculates the mean normalized DCG (NDCG)
        """
        queries_dcg = self.dcg()

        queries_ndcg = {}

        ideal_dcg = defaultdict(int)
        relevances_ordered = {}
        for query_id in self.relevances: 
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
                
        for query_id in queries_dcg: 
            if ideal_dcg[query_id] != 0:
                queries_ndcg[query_id] = queries_dcg[query_id] / ideal_dcg[query_id] # The NDCG is found by dividing the
                                                                                   # DCG values by corresponding ideal values
            else:
                queries_ndcg[query_id] = 0
        
        #print(self.queries_ndcg)
        mean_ndgc = mean(list(queries_ndcg.values()))
        
        print("Mean NDGC -> " + str(mean_ndgc))



    def query_throughput(self,total_queries_processing):
        """
        Calculates the query throughput
        """
        total_number_of_queries = len(list(self.scores.keys()))
        qt = total_number_of_queries / total_queries_processing
        
        print("Query throughput -> " + str(round(qt))+ " queries per second")



    def mean_latency(self,queries_latency):
        """
        Calculates the mean latency
        """
        #print(queries_latency)
        median_latency = median(list(queries_latency.values())) # Calculates the median of all query latency values,
                                                                           # Previously calculated at Ranking.py

        print("Median of Queries Latency -> " + str(median_latency) + " seconds")
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
        for i in range(0,len(self.queries)): 

            start_time = time.time() # latency time of this process, for each query
            docs_scores_for_query = defaultdict(int) # docs_scores_for_query = { doc1: score1, doc2: score2, ...} for all docs that answers the query
            
            for term, term_query_weight in self.weighted_queries[i].items():  
                if term in self.weighted_index: # if term exists in any document
                    for doc_id,term_doc_weight_pos in self.weighted_index[term][1].items(): # all docs ( their ids and weights for this term ) that have the term 
                        term_doc_weight = term_doc_weight_pos[0]
                        docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + (term_query_weight * term_doc_weight)

            docs_scores_for_query={k: v for k, v in sorted(docs_scores_for_query.items(), key = lambda item: item[1], reverse = True)} # order by score (decreasing order)
            
            if self.consider_proximity:                
                self.scores.append(self.proximity(self.queries[i], docs_scores_for_query))
            else:
                self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            score_time = time.time() - start_time
            weight_time = self.latency_time_weight_queries[i]

            self.queries_latency[i + 1] = weight_time + score_time # i+1 because in the evaluation part the id for the queries starts at 1

# bm25:

    def score_bm25(self): #passar arg a true se quisermos considerar
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
                            doc_weight = doc_weight_pos[0]               
                            docs_scores_for_query[doc_id] = docs_scores_for_query[doc_id] + doc_weight

            if self.consider_proximity:                
                #docs_scores_for_query = self.proximity(query, docs_scores_for_query)
                docs_scores_for_query= self.proximity_try(query, docs_scores_for_query)
            
            docs_scores_for_query = {k: v for k, v in sorted(docs_scores_for_query.items(), key = lambda item: item[1], reverse = True)} # order by score ( decreasing order )

            self.scores.append(docs_scores_for_query) # self.scores = [ docs_scores_for_query1, docs_scores_for_query2, ...]
            
            query_latency_time = time.time() - start_time
            self.queries_latency[self.queries.index(query) + 1] = query_latency_time # i+1 because in the evaluation part the id for the queries starts at 1

# Proximity:

    ##############################################################
    ## funções das combinações ##
    ##############################################################

    def proximity_try(self,query_terms, docs_scores_for_query):
        docID_term = {} #para ver quais os termos q estão no mesmo doc
        proximity_score_dict = defaultdict(int) # dictionary that contains the document ID and its proximity score
        tp_score = {}
        for term in query_terms:
            if term in self.weighted_index:
                for docID,doc_weight_pos in self.weighted_index[term][1].items():
                    #self.weighted_index[term][1][docID][1] -> pos of terms in that docID
                    if docID not in docID_term:
                        docID_term[docID] = [term]
                    else:
                        tmp = docID_term[docID]
                        tmp.append(term)
                        docID_term[docID] = tmp
        for docID, terms in docID_term.items():
            term_pos = {}
            for term in terms:
                term_pos[term] = self.weighted_index[term][1][docID][1] #ir buscar as posiçoes do termo naquele documento
            #para cada documento vamos calcular a min_window destes termos
            #ate aqui acho q faz sentido, agora calcular a min_window acho q tá mal

            ##DESCOMENTAR PARA CALCULO DA MIN WINDOW####
            #min_window = self.calculate_min_window(term_pos)
            #proximity_score_dict[docID] += self.calculate_boost(min_window)
            ######################################
            
            if (len(term_pos) > 1): #se o documento tiver mais que um termo daquela query, calcula-se a proximidade deles
                proximity_score_dict[docID] += self.check_proximity_combinations(term_pos)

        for doc_id,prox_score in proximity_score_dict.items():
            tp_score[doc_id] = prox_score + docs_scores_for_query[doc_id]
        return tp_score

    def check_proximity_combinations(self, term_pos):
        #uma forma estupida que pensei para calcular a min window 
        all_terms_pos = []
        for term, pos in term_pos.items():
            all_terms_pos.append(pos)
        possible_combinations = list(itertools.product(*all_terms_pos))  #gerar todas as combinações de posições para os termos que aparecem naquele documento
        perfect_combination = min(possible_combinations) #a minima será a melhor hipótese (????)

        min_window = abs(perfect_combination[0] - perfect_combination[len(perfect_combination)-1])

        return self.calculate_boost(min_window)

    def calculate_boost(self,min_window):

        #acho q estes valores de boost n estao a fazer muito sentido xd

        #with open("minwindows.txt","a") as file:
            #file.write("\n"+str(min_window)+"\n")
       
        if min_window >= 100:
            return 30
        elif 50 <= min_window <= 99:
            return 20
        elif 20 <= min_window <= 49:
            return 10
        elif 1 <= min_window <= 19:
            return 5
        else:
            return 0      
        
    ##############################################################
    ## estas duas funções eram as do repositorio de ontem ##
    ##############################################################

    def calculate_min_window(self, term_pos):
        x = 0
        y = 0
        window = (x, y)
        windows = []
        minWindow = 9999999

        if(len(term_pos) == 1):
            return minWindow
        
        #Calculate maximum position among all terms
        maxValue = 0
        i = 0
        for key in term_pos:
            term_pos[key].sort()
            value = int(max(term_pos[key]))
            if(i == 0):
                maxValue = value
            else:
                if(value > maxValue):
                    maxValue = value
            i=i+1

        #Calculate all possible window                      
        while(y <= maxValue and x <= maxValue):
            if(self.isFeasible(term_pos, window) == True):
                windows.append(window)
                x = x+1
                window = (x, y)
            else:
                y = y+1
                window = (x, y)

        #Calculate minimum possible window    
        minWindow = 0
        for i in range(len(windows)):
            if(len(windows) == 0):
                break
            win = windows[i][1] - windows[i][0] + 1
            if(i == 0):
                minWindow = win
            else:
                if(win < minWindow):
                    minWindow = win
                    
        return minWindow
        
    #check if given window contains all the terms present atleast once
    def isFeasible(self,pos_term, window):
        isFeasible = False
        for key in pos_term:
            minPos = window[0]
            maxPos = window[1]
            for pos in pos_term[key]:
                if(pos >= minPos and pos <= maxPos):
                    isFeasible = True
                    break
                else:
                    isFeasible = False
            if(isFeasible == False):
                return isFeasible
        return isFeasible

    ##############################################################
    ## funções iniciais de comparar os termos 2 a 2 ##
    ##############################################################

    def proximity(self, query_terms , docs_scores_for_query):
        proximity_score_dict = defaultdict(int) # dictionary that contains the document ID and its proximity score
        tp_score = {}
        for q_term in range(len(query_terms) - 1):
            proximity_terms = query_terms[q_term:q_term + 2] #verify the proximity of the terms 2 by 2
            if (proximity_terms[0] in self.weighted_index) & (proximity_terms[1] in self.weighted_index):
                for docID,doc_weight_pos in self.weighted_index[proximity_terms[0]][1].items():
                    numerator_score = 0
                    if docID in self.weighted_index[proximity_terms[1]][1]:                      
                        numerator_score = self.check_proximity(proximity_terms[0],proximity_terms[1],
                                                           docID)
                    proximity_score_dict[docID] += numerator_score
                    
        #for doc_id,prox_score in proximity_score_dict.items():
         #   tp_score[doc_id] = prox_score + docs_scores_for_query[doc_id]
        for doc_id in docs_scores_for_query:
            if doc_id in proximity_score_dict:
                tp_score[doc_id] = proximity_score_dict[doc_id] + docs_scores_for_query[doc_id]
            else:
                tp_score[doc_id] = docs_scores_for_query[doc_id]
        return tp_score

    def check_proximity(self,term1,term2,DocID):
        pos_doc_term1 = []
        pos_doc_term2 = []
        total_score = 0.0
        pos_doc_term1 = self.weighted_index[term1][1][DocID][1] # positions of term in that doc
        pos_doc_term2 = self.weighted_index[term2][1][DocID][1]
        for pos in pos_doc_term1:
            termscore = 0.0
            if pos+1 in pos_doc_term2: # dar os scores q quisermos (?)
                return True
            total_score += termscore
            #há algumas queries em q as palavras estão tão distantes q ele nem lhe dá score
            #não sei se é suposto ser assim ou se temos que atribuir mais scores super baixinhos
            #para distâncias muito altas
        
        return total_score # score of the 2 terms according to the distance between them
    

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
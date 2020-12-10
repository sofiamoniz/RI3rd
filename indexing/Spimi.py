"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys
import collections
from collections import OrderedDict


#Class that will be used as Single-pass in-memory indexer

class Spimi:

    def __init__(self, corpus):

        self.block_number=0
        self.total_docs = len(corpus)
        self.corpus = corpus
        self.term_posting_lists_dic = {} #{term-posting list}
                                        #('achiev', [[1, 1], [33, 1]])

    def spimi_indexer(self, block_size_limit):

        """
        Applies the SPIMI algorithm, by generating an inverted index for each block
        """
 
        for i in range(self.total_docs):
            generated_id=i+1 #Generates id to the present doc
            for term in self.corpus[i]: #get terms of each document - tokens are processed one by one
                
                if term not in self.term_posting_lists_dic: #if the term doesn't exist in the dictionary, a new posting
                                                            #list is created
                    self.term_posting_lists_dic[term] = [generated_id] 
                else: #if the term already exists in the dictionary of posting lists, we append it
                    self.term_posting_lists_dic[term].append(generated_id)
            if sys.getsizeof(self.term_posting_lists_dic) > block_size_limit: #if the posting list has a bigger size
                                                                            #then the allowed one (memory
                                                                            # has been exhausted), it's time to sort the terms
                                                                            #and write this block to disk
                tmp_inverted_index = self.sort_terms() #We create a temporary dictionary to sort the terms of the dictionary
                self.write_block_to_disk(tmp_inverted_index) #We write this block to disk
                tmp_inverted_index = {} #After writing to disk, we have to empty the temporary dictionary so that we can use it in the next iteration
                self.block_number += 1 #Count the block number

    def sort_terms(self):

        """
        Sorts the terms so that we can write the posting lists in lexicographic order. 
        This way, the blocks can easily be merged into the final inverted index.
        """

        sorted_inverted_index = OrderedDict() #With an ordered dictionary, we will be able to keep track of the order of insertion
                                            #Result will be {('term':[[docId, tf]])}
                                            #Ex: {...,('captur', [[6, 1], [13, 1]]), ('carlo', [[4, 1]]), ('case', [[18, 2]]),...}
        sorted_terms = sorted(self.term_posting_lists_dic) #Sort the terms of the posting list
        for term in sorted_terms:
            document_ids = [int(ids) for ids in self.term_posting_lists_dic[term]] #get the document ids in which each term occurs
            tf = self.tf_calc(document_ids)
            sorted_inverted_index[term] = tf
        return sorted_inverted_index

    def tf_calc(self, document_ids): #term frequency calculation for each term, in each document
        counter = collections.Counter(document_ids)
        tf_doc = [[int(docId), counter[docId]] for docId in counter.keys()]
        return tf_doc

    def write_block_to_disk(self,tmp_inverted_index):

        """
        Writes each block to disk in format "Term - posting list"
        Ex: 'achiev', [doc1,doc33]
        """

        tmp_for_print = {} #arranjar uma forma mais eficiente?
        for term in tmp_inverted_index:
            for lista in tmp_inverted_index[term]:
                if term not in tmp_for_print:
                    tmp_for_print[term] = [lista[0]]
                else:
                    tmp_for_print[term].append(lista[0])        

        with open("results/spimi/index_blocks/block_"+ str(self.block_number)+".txt", "w") as block_file:
            for term in tmp_for_print:
                block_file.write(str(term)+": "+str(tmp_for_print[term])+"\n")




    





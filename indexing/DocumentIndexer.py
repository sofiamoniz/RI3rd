"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

from indexing.CorpusReader import CorpusReader
from indexing.Results import Results
from indexing.InvertedIndexer import InvertedIndexer
from indexing.WeightedIndexer import WeightedIndexer
from indexing.Spimi import Spimi
import time
import os
import psutil
import sys

## Class that acts as a pipeline for the all indexing process (calls all the other classes and methods)
class DocumentIndexer:

    def __init__(self,tokenizer_type,input_file,weighted_indexer_type):
        self.tokenizer_type=tokenizer_type
        self.input_file=input_file
        self.weighted_indexer_type=weighted_indexer_type


    def document_indexer(self):

        """
        Index the documents and prints/writes the results and relevant information
        
        Follows this pipeline:

                Read Corpus     
                    |
                Tokenize
                    |             -----> Here, we already have all documents tokenized.
                Index    :  Inverted Index (one document at a time) -> Weighted Index (uses the Inverted Index structure) 
                    |             -----> Here, we already have all documents indexed.
                Store and print results
    
        """
    
        doc_ids={}
        total_docs=0
        total_terms=0
        indexing_time=0
        if self.weighted_indexer_type=="-lnc.ltc": self.weighted_indexer_type="-lnc_ltc"
        

        start_time = time.time()
        corpusReader = CorpusReader(self.input_file,self.tokenizer_type) ## Corpus Reader with Tokenization
        corpus,real_doc_ids=corpusReader.read_content() # corpus: [[doc1_terms_after_tokenization],[doc2_terms_after_tokenization]...]
                                                        # real_doc_ids: [real_doc1_id,real_doc2_id,...]
        total_docs=len(corpus)
        for j in range(total_docs):    
            total_terms=total_terms+len(corpus[j])  # vocabulary size or number of terms
 

        indexer = InvertedIndexer(total_docs) # Inverted Indexer
        for i in range(total_docs):   # Index one document at a time. The id's are auto generated by incrementation, starting at id=1 
            generated_id=i+1 
            indexer.index_document(corpus[i],generated_id)
            doc_ids[generated_id]=real_doc_ids[i]
        indexer.sort_inverted_index() # All documents have been indexed and the final ordered Inverted Indexer created!
        inverted_index=indexer.get_inverted_index()


        weighted_indexer = WeightedIndexer(total_docs, inverted_index ,indexer.get_doc_len(), total_terms)  ## Weighted Indexer
        if(self.weighted_indexer_type=="-bm25"):    # BM25
            weighted_indexer.weighted_index_bm25()
        else:
            weighted_indexer.weighted_index_lnc_ltc()  # LNC.LTC
        weighted_index=weighted_indexer.get_weighted_index()
        indexing_time=time.time()-start_time


        ## Results:

        results = Results(inverted_index,doc_ids,self.tokenizer_type,self.input_file,weighted_index,self.weighted_indexer_type[1:]) ## Results ( writes informations to files )
        #results.write_inverted_index_to_file()
        results.write_weighted_index_to_file()
        results.write_document_ids_to_file()

        memory_dic = self.format_bytes(weighted_indexer.get_size_in_mem()) # Memory occupied by the structure used


        # Print results:
        if(self.tokenizer_type=="-s"):
            print("\n    Tokenizer used: Simple     Ranking Method: "+self.weighted_indexer_type[1:]+"\n"
                    +"\n--- Indexation time:  %s seconds." % (round(indexing_time,3))
                    +"\n--- Size in memory used by the dictionary structure:  %s %s." % (round(memory_dic[0],3), memory_dic[1])
                    + "\n--- File with the Weighted Index: results/simpleTokenizer/weightedIndex_"+self.weighted_indexer_type[1:]+".txt")

        else:
            print("\n    Tokenizer used: Improved     Ranking Method: "+self.weighted_indexer_type[1:]+"\n"
                    +"\n--- Indexation time:  %s seconds." % (round(indexing_time,3))
                    +"\n--- Size in memory used by the dictionary structure:  %s %s." % (round(memory_dic[0],3), memory_dic[1])
                    + "\n--- File with the Weighted Index: results/improvedTokenizer/weightedIndex_"+self.weighted_indexer_type[1:]+".txt")




    ## AUXILIAR FUNCTION:

    def format_bytes(self,size): 

            """
            Makes the conversion of a received size to a human readable one
            """
            
            power = 2**10 # 2**10 = 1024
            n = 0
            power_labels = {0 : '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
            while size > power:
                size /= power
                n += 1
            return size, power_labels[n]+'bytes'

    def test_spimi(self):
        corpusReader = CorpusReader(self.input_file,self.tokenizer_type) ## Corpus Reader with Tokenization
        corpus,real_doc_ids=corpusReader.read_content() # corpus: [[doc1_terms_after_tokenization],[doc2_terms_after_tokenization]...]
                                                        # real_doc_ids: [real_doc1_id,real_doc2_id,...]
        spimi = Spimi(corpus)
        spimi.spimi_indexer() #o size (bytes) tem q se perguntar ao utilizador. Por default pus 150000 bytes
        #spimi.show_inverted_index()

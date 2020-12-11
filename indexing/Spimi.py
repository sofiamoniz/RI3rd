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
        self.index_file = "results/spimi/final_index_file/index.txt"
        self.inverted_index = {}
        

    def spimi_indexer(self, block_size_limit = 150000): #ir pelo block_size_limit ou outra cena mais eficiente, mas pareceu-me o melhor até agora

        """
        Applies the SPIMI invert algorithm
        First, we start by initializing a dictionary for term-postings list.
        Then, we read the terms of each document and create the postings-lists for each term.
        When the dictionary of the term-postings lists is bigger than the passed size (in bytes),
        this block has ended and we need to write this one to memory, and then empty the dictionary
        in order to start another block.
        We count the blocks so that we can create a file for each block with the number of the present block.
        Then these blocks will be merged into one.
        """

        block_files=[]
        term_posting_lists_dic={} #dictionary with term-postings list

        for i in range(self.total_docs):
            generated_id=i+1 #Generates id to the present doc            
            for term in self.corpus[i]: #get terms of each document - tokens are processed one by one
                if term not in term_posting_lists_dic:
                    postings_list = self.add_to_dict(term_posting_lists_dic, term) #When a term occurs for the first time, it is added 
                                                                                    #to the dictionary and a new postings list is created
                else:
                    postings_list = self.get_postings_list(term_posting_lists_dic,term) #returns this postings list for subsequent occurrences of the term
                self.add_to_postings_list(postings_list,generated_id) #add to postings list
            
            if sys.getsizeof(term_posting_lists_dic) > block_size_limit:
                self.block_number += 1 #count block number 
                terms = self.sort_terms(term_posting_lists_dic) #sort the terms
                block_file = "results/spimi/index_blocks/block_"+str(self.block_number)
                block_files.append(self.write_block_to_disk(terms, term_posting_lists_dic, block_file)) #write to disk
                                                                                                                    #and save block files
                                                                                                                    #in list to merge them later
                term_posting_lists_dic = {} #empty the dictionary so that another block can be started
        
        return self.merge_blocks(block_files) #Now we merge all the blocks into one singular block - index file

    ## AUXILIAR FUNCTIONS:

    def add_to_dict(self,dictionary,term):

        """
        Adds term to the dictionary
        """

        dictionary[term] = []
        return dictionary[term]

    def get_postings_list(self,dictionary,term):

        """
        Gets postings list for a given term
        """
        return dictionary[term]

    def add_to_postings_list(self, postings_list, document_id):

        """
        Adds document id to the postings list
        """

        postings_list.append(document_id)

    def sort_terms(self,dictionary):

        """
        Sort terms of the dictionary of term-postings list in lexicographic order
        """

        return [term for term in sorted(dictionary)]

    def write_block_to_disk(self,sorted_terms,dictionary, block_file):

        """
        Writes each block to disk
        """

        with open(block_file , "w") as file:
            for term in sorted_terms:
                line="%s %s\n" % (term, ' '.join([str(document_id) for document_id in dictionary[term]]))
                file.write(line)
        return block_file
           
    def merge_blocks(self, block_files):  

        """
        Merge the file blocks into one singular block
        """

        block_files = [open(block_file) for block_file in block_files] #List with all block files to be readen in sequencial order
        lines = [block_file.readline()[:-1] for block_file in block_files] #List with the first line of each block file (-1 deletes the last line that is "")
        last_term = "" #String created to save the last readen term

        index = 0
        for block_file in block_files: #Read each block file from all the files
            if lines[index] == "": #Check if the file is empty - if so, it is deleted (pop)
                block_files.pop(index)
                lines.pop(index)
            else:
                index += 1 #Otherwise, we increase the index value in one
        
        with open(self.index_file , "w") as index_file:
            while(len(block_files)>0): #while there are still blocks to read
                first_index = lines.index(min(lines)) #First, we need to find the index that comes first in lexicographic
                                                    #order - that is the minimum value of the list, once we ordered the terms before
                line=lines[first_index]
                curr_term = line.split()[0]
                curr_postings = " ".join(map(str, sorted(list(map(int, line.split()[1:])))))
                #Now we need to compare the term in the current line to the last readen term

                if (last_term != curr_term): #if they are different, we need to create in the index a new line with the new
                                            #word, and the correspondent postings that are in the block file we are reading
                    index_file.write("\n%s %s" % (curr_term, curr_postings))
                    last_term = curr_term
                else: #if they are equal, it means that we are already dealing with the most recent term, so we just need
                        #to write the current postings list to the index file
                    index_file.write(" %s" % curr_postings)

                lines[first_index] = block_files[first_index].readline()[:-1]

                if lines[first_index] == "": #If the current block doesn't have more lines, we have to pop it
                                            #so that we can pass to the next block, if there are more to read
                    block_files[first_index].close()
                    block_files.pop(first_index)
                    lines.pop(first_index)
                    
        return self.get_inverted_index() #Now, once we have the index file (the result of merging the blocks)
                                        #We can create the inverted index
                                        #Note - the index file has, per line, term - docs in which the term occurs
                                        #Ex : abaecin 11904 11904 11904 11904 11904 11904 11904 11904
                                        #It means that term "abaecin" has a term frequency of 8 in document 11904
    
    def get_inverted_index(self):

        """
        Creates the inverted index by reading the index file previously created to a dictionary
        """

        index_file = open(self.index_file)
        index_file.readline()
       
        for line in index_file:
            line=line.split()
            #inverted_index[line[0]] = sorted(map(int,line[1:]))
            #line[0] -> term
            #line[1:] -> documents (docs ids) where the term occurs 
            for doc_id in sorted(map(int,line[1:])):
                if line[0] not in self.inverted_index:
                    freq_posting=[] # [doc_freq,posting]  where doc_freq is the number total of documents where the term occurs
                                    # In python, the order of an array is mantained, so no problem!
                    posting={} # {"doc1":occurrences_of_term_in_doc1,"doc2":occurences_of_term_in_doc2,...}  only with documents where the term occurs
                    freq_posting.append(1)
                    posting[doc_id]=1
                    freq_posting.append(posting)
                    self.inverted_index[line[0]]=freq_posting # {"term1":freq_posting1,"term2":freq_posting2,...}
                else:
                    freq_posting=self.inverted_index[line[0]]
                    posting=freq_posting[1] # The second position of this arrays are always the posting dictionary!
                    if doc_id in posting:
                        posting[doc_id]=posting[doc_id]+1 # The document already exists in the posting dictionary, so we only need to increment the occurance of the term in it
                    else: # The document for this term don't exists in the posting dictionary
                        posting[doc_id]=1
                        freq_posting[0]=freq_posting[0]+1

        print(self.inverted_index)



        






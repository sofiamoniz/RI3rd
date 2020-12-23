"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys
import os
import collections
from collections import OrderedDict


## Class that will be used as Single-pass in-memory indexer
class InvertedSpimi:

    def __init__(self,tokenizer_path):
        self.tokenzier_path = tokenizer_path

        self.inverted_index = {}
        self.term_posting_lists = {} # dictionary with term-postings list
        self.block_number = 0 # each block is a directory
        self.segmentation = [('a','f'),('g','p'),('q','z')] # each block/directory has files segmented by this range
        self.block_paths = []
        self.final_index_file = tokenizer_path + "mergeWeighted/final_index.txt" # final Weighted Index with ALL blocks merged
        

    def spimi(self, document_tokens, document_id, block_size_limit = 1000000): #ir pelo block_size_limit ou outra cena mais eficiente, mas pareceu-me o melhor até agora
        """
        Applies the SPIMI invert algorithm (with term positions).
        First, we start by initializing a dictionary for term-postings list.
        Then, we read the terms of passed document and create the postings-lists for each term.
        When the dictionary of the term-postings lists is bigger than the passed size (in bytes), 
        this block has ended and we need to write it to memory, and then empty the dictionary in order to start another block.
        Each block corresponds to a directory and has files divided by an alphabetic range.
        """
        term_position = 0 # position of token(term) in the array of tokens for this document
        for token in document_tokens: 
            if token not in self.term_posting_lists:
                postings_list = self.add_to_dict(self.term_posting_lists, token) # when a term occurs for the first time, it is added to the dictionary and a new postings list is created
            else:
                postings_list = self.get_postings_list(self.term_posting_lists, token) # returns this postings list for subsequent occurrences of the term
            self.add_to_postings_list(postings_list, document_id, term_position) # add to postings list
            term_position += 1
            
        if sys.getsizeof(self.term_posting_lists) > block_size_limit:
            self.block_number += 1 
            self.term_posting_lists = self.sort_terms(self.term_posting_lists) # sort dictionary by terms, alphabetic order
            block_path = self.tokenzier_path + "spimiInverted/block_" + str(self.block_number)
            self.block_paths.append(block_path)
            if not os.path.exists(block_path):
                os.makedirs(block_path)
            for segment in self.segmentation: # each partition is for a range of terms first letters/segment
                partition = {k:v for k,v in self.term_posting_lists.items() if (k[0] in self.char_range(segment[0],segment[1]))}
                self.write_block_to_disk(partition, block_path, segment[0], segment[1]) # write the partitions of block to disk
                                                                                                                   
            self.term_posting_lists = {} # empty the dictionary so that another block can be started
           
        

    def merge_blocks(self):  
        """
        Agora tem se de ir a cada bloco/pasta, e juntar num só ficheiro todas as partições a-f, g-p e q-z e passar do inverted index
        pro weighted index. 
        E depois escrever um ficheiro também com TUDO junto, porque o stor pede no exercicio
        """
        block_files = [open(block_file) for block_file in self.block_files] #List with all block files to be readen in sequencial order
        lines = [block_file.readline()[:-1] for block_file in block_files] #List with the first line of each block file (-1 deletes the last line that is "")
        last_term = "" #String created to save the last readen term

        index = 0
        for block_file in block_files: #Read each block file from all the files
            if lines[index] == "": #Check if the file is empty - if so, it is deleted (pop)
                block_files.pop(index)
                lines.pop(index)
            else:
                index += 1 #Otherwise, we increase the index value in one
        
        with open(self.final_index_file , "w") as index_file:
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
                    
        #Now, once we have the index file (the result of merging the blocks)
        #We can create the inverted index
        #Note - the index file has, per line, (term - docs) in which the term occurs
        #Ex : abaecin 11904 11904 11904 11904 11904 11904 11904 11904
        #It means that term "abaecin" has a term frequency of 8 in document 11904


    def final_inverted_index(self):
        """
        Creates the inverted index by reading the index file previously created to a dictionary
        """
        index_file = open(self.final_index_file)
        index_file.readline()
       
        for line in index_file:
            line=line.split()
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

        return self.inverted_index



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

    def add_to_postings_list(self, postings_list, document_id, term_position):
        """
        Adds document ID and term position to the postings list
        """
        postings_list.append((document_id,term_position))

    def sort_terms(self,dictionary):
        """
        Sort the dictionary in alphabetic order
        """
        return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[0])}

    def char_range(self,first_char,last_char): 
        """
        Generates the characters from first_char to last_char, inclusive.
        """
        for c in range(ord(first_char), ord(last_char)+1):
            yield chr(c)

    def write_block_to_disk(self, dictionary, block_path, first_char, last_char):
        """
        Writes each partition of the block in disk
        """
        partition_file = block_path + '/' + str(first_char) + '-' + str(last_char) + '.txt'
        with open(partition_file , "w") as file:
            for term in dictionary:
                line = "%s %s\n" % (term, ' '.join([str(document_id) for document_id in dictionary[term]]))
                file.write(line)
           
    def show_inverted_index(self):
        """
        Prints the Inverted Index
        """
        print(self.inverted_index) 

    def get_term_positions_dictionary(self):
        """
        Returns the dictionary for term-position in each document
        """
        #return self.term_position_dict
        pass

    
  
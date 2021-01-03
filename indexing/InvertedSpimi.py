"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import os, json
from collections import defaultdict
from indexing.WeightedIndexer import WeightedIndexer

## Class that will be used as Single-pass in-memory indexer
class InvertedSpimi:

    def __init__(self, weighted_indexer_type):
        self.weighted_indexer_type = weighted_indexer_type

        self.models_path = "models/"
        self.term_postings_list = {}
        self.block_size = 0 # N documents
        self.block_number = 0 # each block is a directory
        self.processed_documents = 0 # to know if we reached the end of a block
        self.partitions = [('a','f'),('g','p'),('q','z')] # each block/directory has segment files, partitioned by this range
        self.block_paths = [] 
        
    def spimi(self, document, document_id):
        """
        Applies the SPIMI invert algorithm (with term positions) for this block of N documents.
        First, we start by initializing a dictionary for term-postings list.
        Then, we read the terms of each passed document and create the postings list for each term. 
        After processing each document of this block, this block has ended and we need to write it to memory and empty the dictionary in order to start another block.
        Each block corresponds to a directory and has files divided by an alphabetic range / partitions.
        """

        # Create the dictionary, for this block, with terms and their posting list:
        term_position = 0 # position of token/term in this document
        self.processed_documents += 1
        for token in document: 
            if token not in self.term_postings_list:
                postings_list = self.add_to_dict(self.term_postings_list, token) 
            else:
                postings_list = self.get_postings_list(self.term_postings_list, token) 
            self.add_to_postings_list(postings_list, document_id, term_position) 
            term_position += 1
            
        # Sort terms and write block (partitioned in segments) to disk:
        if self.processed_documents == self.block_size: # we processed all documents for this block
            self.block_number += 1 
            self.term_posting_list = self.sort_terms(self.term_postings_list) # sort dictionary by terms, in alphabetic order
            block_path = self.models_path + "spimiInverted/block_" + str(self.block_number) + '/'
            self.block_paths.append(block_path)
            if not os.path.exists(block_path): # create the directory for block if not exists
                os.makedirs(block_path)
            for partition in self.partitions: # each partition is for a range of terms first char/segment
                segment = {k:v for k,v in self.term_posting_list.items() if (k[0] in self.char_range(partition[0],partition[1]))}
                self.write_block_to_disk(segment, block_path, partition[0], partition[1]) # write the segment to disk
            
            # Empty the dictionary in memory, so that another block can be started:
            self.term_postings_list = {} 
            self.processed_documents = 0

    def merge_blocks(self, total_docs, documents_len, total_tokens):
        """
        For each partition, merge all segments with that partition, from all existing blocks, to one and write to disk.
        Each segment file have a part of the Inverted Index, for that partition.
        After the merge, we have a merged Inverted Index and we construct the Weighted Index.
        """  
        for partition in self.partitions: 

            merged_inverted_index = defaultdict(list)
            merged_weighted_index = {}

            # Merge all parts of the Inverted Indexes from SPIMI, for this partition:
            all_segments = [open(file + partition[0] + '-' + partition[1] + ".txt") for file in self.block_paths] # all segments in all blocks, with this partition
            lines = [file.readline()[:-1] for file in all_segments] # first lines of each segment
            last_term = "" # last readen term
    
            while(len(all_segments) > 0): 
                first_index = lines.index(min(lines)) # first word in alphabetic order
                line = lines[first_index]
                current_term = line.split(';')[0]
                current_postings = line.split(';')[1:]
                if (last_term != current_term): 
                    merged_inverted_index[current_term].append(int(current_postings[0]))
                    merged_inverted_index[current_term].append(json.loads(current_postings[1]))
                    last_term = current_term
                else: 
                    merged_inverted_index[current_term][0] += int(current_postings[0])
                    merged_inverted_index[current_term][1].update(json.loads(current_postings[1]))

                lines[first_index] = all_segments[first_index].readline()[:]
                line = lines[first_index]

                if lines[first_index] == "": # no more lines
                    all_segments[first_index].close()
                    all_segments.pop(first_index)
                    lines.pop(first_index)
            
            # Construct the Weighted Index from the merged Inverted Index, for this partition:
            weighted_indexer = WeightedIndexer(total_docs, merged_inverted_index, documents_len, total_tokens)
            if self.weighted_indexer_type == "bm25": merged_weighted_index = weighted_indexer.bm25()
            else: merged_weighted_index = weighted_indexer.lnc_ltc()
            merged_weighted_index = weighted_indexer.get_weighted_index()
            
            # Write the Weighted Index, for this partition, to a file:
            self.write_merged_block_to_disk(partition, merged_weighted_index)
            weighted_indexer.empty_weighted_index() # empty in memory
                

## AUXILIAR FUNCTIONS:

    def set_block_size(self, block_size):
        """
        Sets the size (number of documents to be processed) for a block
        """
        self.block_size = block_size

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
        Writes segment of the block in disk
        """
        segment_file = block_path + '/' + str(first_char) + '-' + str(last_char) + '.txt'
        with open(segment_file , "w") as file:
            for term, posting_list in dictionary.items():
                inverted_index = []
                docs_freq = defaultdict(list)
                for posting in posting_list:
                    docs_freq[posting[0]].append(posting[1])
                inverted_index.append(len(docs_freq))
                inverted_index.append(docs_freq)
                line = "%s;%s;%s\n" % (term, inverted_index[0], json.dumps(inverted_index[1]))
                file.write(line)
        file.close()

    def write_merged_block_to_disk(self, partition, weighted_index):
        """
        Writes merged segment of all blocks in disk
        """
        merged_path = self.models_path + "mergedWeighted/"
        if not os.path.exists(merged_path): # create the directory for block if not exists
                os.makedirs(merged_path)
        with open(merged_path + partition[0] + '-' + partition[1] + ".txt", "w") as file:
            for term,index in weighted_index.items():
                line = "%s;%s;%s\n" % (term, index[0], json.dumps(index[1]))
                file.write(line)
        file.close()
        


    
  
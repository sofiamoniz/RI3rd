"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys, getopt, time, json
from indexing.InvertedSpimi import InvertedSpimi
from indexing.Corpus import CorpusReader

def main():
    """ 
    Gets the arguments and runs the indexing program 
    """
    if len(sys.argv) > 5 or len(sys.argv) < 4 or (sys.argv[1] != "i" and sys.argv[1] != "s") or (sys.argv[3] != "bm25" and sys.argv[3] != "lnc_ltc"): 
        print ("\nUsage:\n\n   Index.py <tokenizer> <csv_file> <ranking_type> <consider_proximity>\n\n Example: python3 Index.py i metadata.csv bm25 consider_proximity\n       or python3 Index.py s metadata.csv lnc_ltc\n")
        sys.exit()
    else:
        if len(sys.argv) == 4: proximity = False
        else: proximity = True
        
    indexer(sys.argv[1], sys.argv[2], sys.argv[3], proximity)
    
def indexer(tokenizer_type, input_file, weighted_indexer_type, proximity):
    """
    Index the documents with SPIMI and writes/prints results
        
    Follows this pipeline, for each chunk/block of N readed documents of Corpus:

        Tokenize and index each document of block
            |           
        Writes segments of block to disk, by partitions (parts of Inverted Index)

    After process all blocks:

        Merge all segments of all blocks, by partitions, and writes to disk (parts of Weighted Index)
            |             
        Show results
    """

    # Some imports, variables and initializations:
    if tokenizer_type == "s":
        from indexing.SimpleTokenizer import SimpleTokenizer
        tokenizer = SimpleTokenizer()
    else:
        from indexing.ImprovedTokenizer import ImprovedTokenizer
        tokenizer = ImprovedTokenizer()
    inverted_spimi = InvertedSpimi(weighted_indexer_type, proximity)
    corpus_reader = CorpusReader(input_file)
    total_docs = 0 # total number of documents
    total_tokens = 0 # total number of tokens
    indexing_time = 0  
    doc_ids = {} # will store the mapping between the real IDs of documents and the generated ones
    documents_len = {} # will store the number of tokens in each document
        
    # Tokenization and SPIMI for each Corpus chunk (chunk = N documents = block):
    start_time = time.time()
    while True:
        chunk = corpus_reader.nextChunk()
        if chunk is None:
            break
        inverted_spimi.set_block_size(len(chunk)) # block size will be the size of the chunk (= N documents)
        for document in chunk:  
            real_id, title, abstract = document[0], document[1], document[2]
            title_abstract = title + abstract
            tokens = tokenizer.tokenize(title_abstract) # tokenize
            total_docs += 1 # will also be used as generated ID for this document 
            total_tokens += len(tokens) 
            documents_len[total_docs] = len(tokens)
            doc_ids[total_docs] = real_id # Generated ID: real ID

            inverted_spimi.spimi(tokens,total_docs) # Inverted Spimi for this chunk / block
        
    # Merge of all blocks:
    inverted_spimi.merge_blocks(total_docs, documents_len, total_tokens) 
    with open("models/mergedWeighted/type.txt", "w") as file: # File stores the tokenizer and weighted indexer types used
        line = "%s %s %s" % (tokenizer_type, weighted_indexer_type, proximity)
        file.write(line)
    file.close()
    indexing_time = time.time() - start_time
        
    # Results:
    write_document_ids_to_file(doc_ids)
    print("Number of documents: " + str(total_docs))
    print("Indexation time:  %s seconds" % (round(indexing_time,3)))
    print("Blocks of Inverted Index in results/spimiInverted    and    Merged and Weighted Blocks in results/mergedWeighted")


## AUXILIAR FUNCTIONS:

def write_document_ids_to_file(docsIds):
    """
    Writes the mapping between real doc IDs and the generated ones to a file in the file "documentIds.txt", in the models folder.
    """
    with open("models/documentIDs.txt",'w') as file_ids:
        json.dump(docsIds, file_ids)
    file_ids.close()

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



if __name__ == '__main__':
    main()
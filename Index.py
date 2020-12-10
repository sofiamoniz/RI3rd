"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys, getopt
from indexing.DocumentIndexer import DocumentIndexer

## Main class that runs the indexing part of the program ( gets the arguments from command line and starts the program )
def main():

    """
    The program needs 3 arguments: type of tokenizer, file to read and type of weighted indexer/ranking.

    And PyStemmer instaled: pip install pystemmer
                            pip install psutil

    Examples of usage:

        python3 Index.py -s metadata_2020-03-27.csv -bm25
        python3 Index.py -i metadata_2020-03-27.csv -lnc.ltc

    After running, the results files are stored in the "results" folder.
    """

    if len(sys.argv)!=4: 
        print ('Usage:\n\n   Index.py -s <fileToRead> -bm25\nor Index.py -i <fileToRead> -bm25\nor Index.py -s <fileToRead> -lnc.ltc\nor Index.py -i <fileToRead> -lnc.ltc \n\n Example: python3 Index.py -s metadata_2020-03-27.csv -bm25')
        sys.exit()
    elif (sys.argv[1]!="-i" and sys.argv[1]!="-s") or (sys.argv[3]!="-bm25" and sys.argv[3]!="-lnc.ltc"):
        print ('Usage:\n\n   Index.py -s <fileToRead> -bm25\nor Index.py -i <fileToRead> -bm25\nor Index.py -s <fileToRead> -lnc.ltc\nor Index.py -i <fileToRead> -lnc.ltc \n\n Example: python3 Index.py -s metadata_2020-03-27.csv -bm25')
        sys.exit()

    indexer=DocumentIndexer(sys.argv[1],sys.argv[2],sys.argv[3])
    #indexer.document_indexer()
    indexer.test_spimi()



if __name__ == '__main__':
    main()
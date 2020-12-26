"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys, getopt
from searching.RetrievalEngine import RetrievalEngine

## Main class that runs the searching part of the program ( gets the arguments from command line and starts the program )
def main():

    """
    The program needs 4 arguments: file with the weighted index, file with the queries, file with the relevances and number of documents to retrieve for each query (TOP)
    For everything workd correcly do not change the name and Relative Path of the files generated automatically by the programs!
    Please, run this program exactly as described on the Examples of usage.

    And PyStemmer instaled: pip install pystemmer
                            pip install psutil
                            pip install ntlk

    Examples of usage:

        python3 Search.py models/simpleTokenizer/weightedIndex_bm25.txt queries.txt queries.relevance.filtered.txt 50
        python3 Search.py models/simpleTokenizer/weightedIndex_lnc_ltc.txt queries.txt queries.relevance.filtered.txt 10
    """

    if len(sys.argv) != 6: 
        print ("\nUsage:\n\n   Search.py <ranking_type> <tokenizer> <queryFile> <queryRelevancesFile> <numberOfDocsToReturn>  \n\n Example: Search.py -bm25 -i queries.txt queries.relevance.filtered.txt 50")
        print("isto tem q ser mudado mas escolhe o q usaste anteriormente xD")
        #isto por agora fica assim, mas temos q arranjar uma forma melhor para usar
        #o tokenizer e o ranking q foram usados no indexer anteriormente, por causa de 
        #ter q se correr o indexer e o search separados
        sys.exit()
    elif not float(sys.argv[5]).is_integer():
        print("Invalid number of document to return per query! Must be an integer.")
        sys.exit()



    chosen_ranking=sys.argv[1]
    tokenizer=sys.argv[2] # type of tokenizer used in the weighted index ('s' or 'i')
    query_file=sys.argv[3]
    relevances_file=sys.argv[4]
    number_of_docs_to_return=sys.argv[5]
    
    if "bm25" == chosen_ranking[1:]: ranking_type="bm25"   # type of ranking used in the weighted index ('bm25' or 'lnc.ltc')
    else: ranking_type="lnc.ltc"
 
    retrieval_engine = RetrievalEngine(tokenizer,ranking_type,query_file,relevances_file,number_of_docs_to_return)
    #print(retrieval_engine.construct_weighted_index())
    retrieval_engine.query_search()
    #retrieval_engine.evaluation()


if __name__ == '__main__':
    main()
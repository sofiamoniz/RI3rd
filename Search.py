"""
IR, December 2020
Assignment 3: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import sys, os, getopt, time, json
from statistics import mean, median
from searching.Ranking import Ranking
from searching.Evaluation import Evaluation

def main():
    """ 
    Gets the arguments and runs the searching (or indexing and searching) program 
    """
    if len(sys.argv) != 5 and len(sys.argv) != 6: 
        print ("\nUsage:\n\n   Search.py <tokenizer> <csv_file> <ranking_type> <numberOfDocsToReturn> <consider_proximity>\n\n Example: Search.py i metadata.csv bm25 50 consider_proximity\n       or Search.py s metadata.csv lnc_ltc 50\n")
        sys.exit()
    else:
        if sys.argv[1] != "s" and sys.argv[1] != "i" :
            print("Invalid tokenizer type! Must be 's' or 'i'.")
            sys.exit()
        elif sys.argv[3] != "bm25" and sys.argv[3] != "lnc_ltc" :
            print("Invalid ranking type! Must be 'bm25' or 'lnc_ltc'.")
            sys.exit()
        elif not float(sys.argv[4]).is_integer():
            print("Invalid number of documents to return per query! Must be an integer.")
            sys.exit()
        if len(sys.argv) == 6: 
            if sys.argv[5] != "consider_proximity":
                print("Invalid last argument! Must be None or 'consider_proximity'.")
                sys.exit()
            else: 
                consider_proximity = True
        else: consider_proximity = False
        if (not os.path.exists('models/mergedWeighted')) or ((os.path.exists('models/mergedWeighted') and check_index(sys.argv[1], sys.argv[3], consider_proximity) != True)) : 
        # if models/mergedWeighted don't exist 
        # or exist, but the Weighted Index was not constructed with the same tokenizer and ranking types choosen by the user in this program
        # then run indexing part
            print("Running indexing program...\n")
            from Index import indexer # indexing program
            indexer(sys.argv[1], sys.argv[2], sys.argv[3], consider_proximity)
        
        retrieval_engine(sys.argv[1], sys.argv[3], sys.argv[4], consider_proximity) 
       
def retrieval_engine(tokenizer, ranking_type, number_of_docs_to_return, consider_proximity):
    """
    Searches the query terms and returns the retrieved ordered documents, based on the ranking type choosen. Writes results to files.
    Calls the evaluation method.

    The ranking and retrieval process follows this pipeline:

                Weights the queries   (only if using lnc.ltc)
                    |         
                Computes the scores   (for each document that answers the query) 
                    |             
                Retrieves the ranked documents and writes them to a file
    """

    # Read from files to memory:
    queries = read_queries_file("searching/queries.txt") # queries = [ query1, query2, query3,...]
    real_doc_ids = read_doc_ids_file('models/documentIDs.txt') # real_doc_ids = { doc1_generated Id : doc1_real_Id, ... }
    relevances = read_relevances_file("searching/queries.relevance.filtered.txt") # { query1_id : { doc1_real_Id: relevance, doc2_real_Id: relevance,...},...}
    
    # Some variables and initializations:
    scores_for_evaluation = {} # { query1_id : { doc1_real_Id : score , doc2_real_Id: score,...},...}
    queries_latency = [] # [ latency_of_query1, ...]

    # Ranking and retrieval process:
    ranking = Ranking(tokenizer, queries, consider_proximity)
    start_queries_processing = time.time()  # time to process all the queries
    if ranking_type == "lnc_ltc":
        ranking.weight_queries_lnc_ltc() # this step is only for lnc.ltc
        ranking.score_lnc_ltc()
    else:
        ranking.score_bm25() # no need to weight the queries
    queries_processing = time.time() - start_queries_processing
    queries_latency = ranking.queries_latency # latency of each query
    
    # Write TOP N results (for each query) to file and create dictionary with N scores for evaluation:
    with open("results/ranking_" + ranking_type + ".txt", 'w') as file_ranking:
        file_ranking.write("***  TOP " + number_of_docs_to_return + " RETURNED DOCUMENTS *** ")
        file_ranking.write("\n\nRanking: " + ranking_type)
        file_ranking.write("\nTokenizer: " + ("Improved\n" if tokenizer=='i' else "Simple\n"))
        file_ranking.write("Consider proximity: " + str(consider_proximity))
        for i in range(0,len(queries)):
            file_ranking.write("\n\n -> Query: " + queries[i]+"\n")
            file_ranking.write("\nQuery latency: " + str(queries_latency[i+1]) + " seconds\n")
            number_of_docs_returned = 0 # TOP self.top
            docs_scores = {}
            for doc,score in ranking.scores[i].items():
                if number_of_docs_returned == int(number_of_docs_to_return): break
                else:
                    docs_scores[real_doc_ids[doc]] = score 
                    file_ranking.write("\nDocument: " + real_doc_ids[doc] + "                  Score: " + str(score))
                    number_of_docs_returned = number_of_docs_returned+1
            scores_for_evaluation[str(i+1)] = docs_scores
    
    # Evaluation:
    evaluate(number_of_docs_to_return, relevances, scores_for_evaluation, queries_processing, ranking_type, queries_latency)
    
def evaluate(top, relevances, scores_for_evaluation, queries_processing, ranking_type, queries_latency):
    """
    Evaluates the retrieval engine with some relevant metrics and shows the results
    """
    evaluation = Evaluation(relevances, scores_for_evaluation)

    for query_id in scores_for_evaluation:
        evaluation.precision_recall(query_id)
        evaluation.f1(query_id)
        evaluation.average_precision(query_id)
        evaluation.ndcg(query_id)

    print("\nEvaluation TOP " + top + " :\n")
    print("Mean Precision -> ", round(mean(list(evaluation.queries_precision.values())), 3))
    print("Mean Recall ->  ", round(mean(list(evaluation.queries_recall.values())), 3))
    print("Mean F-Measure -> ", round(mean(list(evaluation.queries_f1.values())), 3))
    print("MAP -> ", round(mean(list(evaluation.queries_average_precision.values())), 3))
    print("Mean NDGC -> ", round(mean(list(evaluation.queries_ndcg.values())), 3))
    print("Query throughput -> " + str(round(len(list(scores_for_evaluation.keys())) / queries_processing))+ " queries per second")
    print("Median of Queries Latency -> " + str(round(median(list(queries_latency.values())), 3)) + " seconds")

    print("\nRetrieved documents, for each query, in: " + "results/ranking_" + ranking_type + ".txt\n")

    
## AUXILIAR FUNCTIONS: 

def check_index(tokenizer, ranking, proximity):
    """
    Returns True if the tokenizer, ranking and proximity choosen by the user are the same as the ones used 
    to construct the Weighted Index in memory
    """
    file = open("models/mergedWeighted/type.txt", 'r')
    for line in file:
        line = line.split()
        if line[0] == tokenizer and line[1] == ranking and line[2] == str(proximity):
            file.close()
            return True
        file.close()
        return False

def read_queries_file(query_file):
    """
    Reads the file with the queries to an array
    """
    queries=[]
    file = open(query_file, 'r') 
    for line in file: 
        queries.append(line.rstrip())   # queries = [ query1, query2, query3,...]
    file.close()
        
    return queries

def read_doc_ids_file(ids_file):
    """
    Reads the file with the document id's mapping to a dictionary
    """
    real_doc_ids={}
    with open(ids_file) as file_ids:
        real_doc_ids = json.load(file_ids)   # real_doc_ids = { doc1_generated Id : doc1_real_Id, ... }
    file_ids.close()

    return real_doc_ids

def read_relevances_file(relevances_file):
    """
    Reads the file with the document relevances for each query, to a dictionary
    """
    relevances={}
    with open (relevances_file, mode='r') as file_to_read:
        for row in file_to_read:
            query_id = row.split()[0]
            cord_ui = row.split()[1]
            content = float(row.split()[2])
            if query_id not in relevances.keys():
                doc_scores = {}
                doc_scores[cord_ui] = content
                relevances[query_id] = doc_scores
            else:
                doc_scores=relevances[query_id]
                doc_scores[cord_ui] = content
                relevances[query_id] = doc_scores   # { query1_id : { doc_1: relevance, doc_2: relevance,...},...} 
    file_to_read.close()

    return relevances



if __name__ == '__main__':
    main()
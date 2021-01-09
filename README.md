 IR, January 2020
Assignment 3: Indexing and Retrieval
Authors: Alina Yanchuk, 89093; Ana Sofia Fernandes, 88739


The searching program produces a file with the Weighted Index (produced by using SPIMI), based on the Tokenizer and Ranking function chosen, and a file with the documents IDs mapping, that will be used in the searching process. It also produces a file with the Ranking results and shows the Evaluation metrics calculated (it can have query term proximity if passed through argument).

In order to everything work correctly, all the generated files by the indexing program must not have their defined names and Relative Paths changed!


## To run the script:

    1. Run the command pip install nltk
    2. Run the command pip install psutil
    3. Run the command pip install pystemmer
    
    4. Execute the command:    

        python3 Search.py <tokenizer> <csv_file> <ranking_type> <numberOfDocsToReturn> <consider_proximity>

            Examples: 
              Search.py i metadata.csv bm25 50 consider_proximity
              Search.py s metadata.csv lnc_ltc 50


##### All the results (Weighted Index, document IDs mapping and Ranking) are stored in the "results" folder             

##### The table with the Evaluation metrics can be found in the "results" folder, in the file table_evaluation.xlsx

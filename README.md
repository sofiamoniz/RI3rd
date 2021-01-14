     IR, January 2021
     Assignment 3: Indexing and Retrieval
     Authors: Alina Yanchuk, 89093; Ana Sofia Fernandes, 88739


The searching program produces the Ranking results and shows the Evaluation metrics calculated (it can have query term proximity if passed through argument). If the arguments (only the tokenizer, ranking_type and consider_proximity) passed by the user match the Weighted Index in disk, it is executed only the searching part. If not, it is executed the indexing program first. 

CSV file: from 12/01/2021 (if the .csv file is changed, please delete all in "models" folder, in order to re-run the indexing program with the new file)

Please do not change the folders and files names / paths.


## To run the script:

    1. Run the command pip install nltk
    2. Run the command pip install psutil
    3. Run the command pip install pystemmer
    4. Run the command pip install pandas
    
    5. Execute the command:    

        python3 Search.py <tokenizer> <csv_file> <ranking_type> <numberOfDocsToReturn> <consider_proximity>

            Examples: 
              python3 Search.py i metadata.csv bm25 50 consider_proximity
              python3 Search.py s metadata.csv lnc_ltc 50    


##### All the models (partioned Inverted Indexes, partioned Weighted Indexes and document IDs mapping) are stored in the "models" folder             
##### All results from searching (returned documents and evaluation) are stored in "results" folder

##### The table with the Evaluation metrics can be found in the "results" folder, in the file table_evaluation.xlsx
produced

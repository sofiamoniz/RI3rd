"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import re

## Class that acts as the Simple Tokenizer
class SimpleTokenizer:

    def __init__(self):
        pass


    def simple_tokenizer(self, received_string):

        """
        Returns an array with lower cased terms only with alphabetic characters and len 3 or more
        """

        received_string=self.replace_non_alpha(received_string) # Replace non-alpha chars
        received_string=received_string.lower().split() # Put all chars to lower          
                  
        return [word for word in received_string if len(word) >=3 ] # Only admit strings with len >=3


   

    def replace_non_alpha(self,old_string): # Used to replace non-alpha chars
    
        """
        Replaces the non-alpha characters of the text by space
        """

        new_string = re.sub('[^a-zA-Z]+', ' ', old_string) 

        return new_string
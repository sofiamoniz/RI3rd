"""
IR, November 2020
Assignment 2: Ranked Retrieval
Autors: Alina Yanchuk, 89093
        Ana Sofia Fernandes, 88739
"""

import re
import Stemmer

## Class that acts as the Improved Tokenizer

class ImprovedTokenizer:

    def __init__(self):
        self.stemmer = Stemmer.Stemmer('english')



    def improved_tokenizer(self,received_string):

        """
        Returns an array with treated and tokenized terms (without numbers,repeated sequences of chars, treated URLs, len bigger than 3 (after PorterStemmer), and so on...)
        """

        stop_words=self.set_stop_words() # Save the stop words, to be used, in a set
        word_tokens= re.sub('[^a-zA-Z]+', ' ', received_string).lower().split() # Transform the received string in tokens, by using the function word_tokenize from library ntlk
        filtered_sentence = [] 
        
        for w in word_tokens:
            if w not in stop_words and len(w)>=3:
                if self.is_website(w): #If the string is a website, it will be treated in order to give only the important part
                    parse_object = urlparse(w)
                    if (parse_object.netloc != ''): filtered_sentence.append(parse_object.netloc.split('.')[1]) # This condition is made to transfrom a website and give the user only the 
                                                                                                                # Relevant part. Eg: www.google.com -> google
                    else:
                        if w.startswith('www'): filtered_sentence.append(w.split('.')[1])   # This refers to the objects that can't be treated by the library urlparse     
                else:
                    if not self.contains_digit(w): filtered_sentence.append(w)  #If the treated string doesn't contain numbers, it will be appended.
                                                                                #This is made in order to avoid strange words like a23df or xcxft3, for example

        #Do the stem to each word from filtered_sentence, using the PyStemmer
        # Words with at least 3 chars (after the stem), and not having all the same chars or more than 3 sequentially (eg. zzz) will not be appended to the final tokenized array
        
        final_tokenized=[]
        temp=[]
        temp=self.stemmer.stemWords(filtered_sentence)   #Stem the array of terms in order to remove certain sufixes, using the PyStemmer
        for w in temp:
            if len(w)>=3 and not self.characs_same(w):
                final_tokenized.append(w)
        
        return final_tokenized



    def set_stop_words(self): 

        """
        Reads and saves the stop words from the file required
        """

        with open ("indexing/snowball_stopwords_EN.txt", mode='r') as stop_words:
            stop_words_set = set([word.strip() for word in stop_words])
            
        return stop_words_set



    def characs_same(self,s) :

        """
        Verifies if a string has all the same chars (Eg. "aaaaa" )
        or 3 same sequential chars (Eg. "aaab")
        or 2 same sequential and len equal to 3 (Eg. "aab")
        
        After a research, we found that
        "In English the most common repeated letters are ss, ee, tt, ff, ll, mm and oo" from https://www3.nd.edu/~busiforc/handouts/cryptography/cryptography%20hints.html
        
        So, we also exclude all the terms with repeated chars that are not present in this list.
        """

        n = len(s)
        sameChars=0
        repeatedChars=""

        if(len(s)>=3):
            for i in range(0, n-1) :
                j=i+1
                if s[i] == s[j] :
                    sameChars=sameChars+1
                    repeatedChars=s[i]+s[j]   

        if (sameChars>=2) or (sameChars==1 and len(s)==3) or (sameChars==1 and repeatedChars not in ["ss","tt","ff","ll","mm","oo","ee"]): return True
        else: return False



    def contains_digit(self, w): 

        """
        Check if a given string contains digits
        """

        if any(char.isdigit() for char in w): return True



    def is_website(self, w):

        """
        Check if a given string is a website
        """

        if ('www' in w or 'http' in w or 'https' in w) and w.count('.') > 1: return True





import youtubedataextraction
import pandas as pd
import regex as re
import string
import glob

# *****Running Sentiment analysis using stanford CoreNLP******
# After downloading the stanford CoreNLP full version zip file 
# it is needed to download the related dump and the language files needed.
# this can be downloaded here https://stanfordnlp.github.io/CoreNLP/download.html
# in a command prompt at the directory of the unzipped stanford CoreNLP 
# run the below command to start the stanford server on port 9000. 
# This server which is running on port 9000 is accessed by our python program  
# 
#java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -annotators "tokenize,ssplit,pos,lemma,parse,sentiment" -port 9000 -timeout 100000
#
# Here we read the tweets extracted from twitter for each race and get the sentiments of the comments for each race.
# we use the stanford_sentiment method from the youtubedataextraction.py.
# A .csv file with the details of the race, year, name, total positive comments, total negative comments, 
# number of useful comments and the normalized value excitement index is created and used for analysis.
def main():
    maindata=[]
    race = pd.read_csv(r"C:\\personal data\\New folder\\f1db_csv\\races.csv")
    for file in glob.glob("./twitter_data-2/*.csv"):
        arr=[]
        sample_tweets = pd.read_csv(file,header=None,sep=';')
        print(len(sample_tweets.index))
        print(file)
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        totalpos=0;totalneg=0;numberofusefulcomments=0;otherlanguage=0
        for comment in sample_tweets.iloc[:,1]:
            #print(comment)
            comment= regex.sub('.', comment)
            comment=comment.replace("\n",".")
   
            try:
                numSentence, numWords, poscount,negcount  = youtubedataextraction.stanford_sentiment(comment)
            except:
                continue
            """ print(comment)
            print("-----------------------------------")
            print(numSentence,sep=" ")
            print(numWords,sep=" ")
            print(poscount,sep=" " )
            print(negcount,sep=" ") """
            if poscount!=0 or negcount!=0:
                numberofusefulcomments= numberofusefulcomments+1
            totalpos=totalpos+poscount
            totalneg=totalneg+negcount
        print("total pos occurences:"+str(totalpos))
        print("total neg occcurences:" +str(totalneg))
        # we get positive and negative sentiment occurences per sentence in a comment.
        # i.e poscount = (positive sentences/ total number of sentences)
        # i.e negcount = (negative sentences/ total number of sentences) 
        # So each comment has a fraction response. we add up all the positive and negative
        # sentiments together for all the comments (totalpos, totalneg).
        # we now divide this with the number of comments which resulted in a positive or 
        # negative sentiment. (numberofusefulcomments)
        # excitement index can be calculated as the ratio between the sum of positive and 
        # negative sentiments and number of useful comments for all comments.
        # 
        # useful comments = the comments from which either a positive or negative sentiment can be obtained.
        # not useful comments = the comments which are neutral, noisy comments, uninterpretable languages. 
        print("excitement index:",(totalpos+totalneg)/numberofusefulcomments)
        print(numberofusefulcomments)
        arr=(race.loc[race["raceId"]==int(file.split(".")[1].split("\\")[1])].values[0])
        maindata.append([arr[0],arr[1],arr[4],arr[5],len(sample_tweets.index),numberofusefulcomments,
        totalpos,totalneg,(totalpos+totalneg)/numberofusefulcomments])
        pd.DataFrame(maindata).to_csv("C:\\personal data\\New folder\\twitter_sentiment.csv")

if __name__ == "__main__":
    main()
#
import os
import numpy as np
import pandas as pd
import re
import string
import itertools
from textblob import TextBlob
#import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from pycorenlp import StanfordCoreNLP
#
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
#
# ****Using youtube data api to extract youtube data******
# you need to create an account in the google cloud platform and include an api to use
#  youtube data api v3 and create credentials to be able to use this api. 
# once your credentials are ready you will have a key which you have to provide in your api calls.
# the usage of youtube data api v3 help can be found in this link. https://developers.google.com/youtube/v3/docs/
#


#scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
#In this main function we read a manually gathered list of youtube video links(URL) and collect the statistics and comments
# of that particular video using the videoID which is part of the video URL. we extract the videoIDs from URL using regex
def main():
    main_data=[]
    # this csv contains the youtube video links for some races.
    #you can create such a list for the videos you want to extract the comments for.
    linkscsv=pd.read_csv('Formel1_youtube.csv')
    links=linkscsv.link
    videoIDS=[]
    for link in links:
        videoIDS.append(re.match('^[^v]+v=(.{11}).*',str(link)).group(1))
    videoid_df=pd.DataFrame(videoIDS)
    videoid_df.to_csv('videoid_df.csv')
    for video_id in videoIDS:
        statistics = extract_statisticsofvideo(video_id)
        #print(statistics)
        viewcount=int(extract_from_json(statistics,'viewCount')[0])
        likecount=int(extract_from_json(statistics,'likeCount')[0])
        dislikecount=int(extract_from_json(statistics,'dislikeCount')[0])
        commentcount=int(extract_from_json(statistics,'commentCount')[0])
        commentslist=[]
        if os.path.exists(video_id+'.csv'):
            commentslist = list(pd.read_csv(video_id+'.csv').iloc[:,1])
        else:
            commentslist = extract_commentsofvideo(video_id)
            pd.DataFrame(commentslist).to_csv(video_id+'.csv')
        #print(response)
        print(len(commentslist)-commentcount)
    
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        
        print("--------------------------------------------------------------")
        print(len(commentslist))
        print("--------------------------------------------------------------")
        #piprint(commentslist)
        totalpos=0;totalneg=0;numberofusefulcomments=0;otherlanguage=0
        for comment in commentslist:
            """ if len(comment)>2:
                a=TextBlob(comment).detect_language()
                if a!='en':
                    otherlanguage=otherlanguage+1
                    continue """
            comment= regex.sub('.', comment)
            comment=comment.replace("\n",".")
            try:
                numSentence, numWords, poscount,negcount  = stanford_sentiment(comment)
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
        main_data.append([viewcount,likecount,dislikecount,likecount/viewcount,dislikecount/viewcount,likecount+dislikecount,
        (likecount+dislikecount)/viewcount,commentcount,len(commentslist),numberofusefulcomments,totalpos,totalneg,
        (totalpos+totalneg)/numberofusefulcomments])
    main_data=pd.DataFrame(main_data)
    main_data.insert(0,'Grand_Prix',list(linkscsv['Grand Prix']),True)
    main_data.to_csv('youtube_data_formula1.csv')
    # the results are saved into a .csv file and later used for the analysis.

# This method sends an api request to get the 
# statistics (json containing likecount, dislike count, comment count etc) of a youtube video given the video ID.
# you have pass in your key to be able to use the api.        
def extract_statisticsofvideo(video_id):
    api_service_name = "youtube"
    api_version = "v3"
    key = "Your-api-key-generated-in-the-googleapis-webpage"
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=key )
    request = youtube.videos().list(
        part="snippet,id,statistics",
        id= video_id
    )
    response = request.execute()
    return response

# This method calls an api to receive the comments of video given ID of the video.
# The returns a json for comments contained in one page and a token to go to the next page
# we have to use to token to go to the next page and extract the comments till all the comments are extracted.
# refer to the youtube api v3 docs about comments using the link mentioned above 
def extract_commentsofvideo(video_id): 
    api_service_name = "youtube"
    api_version = "v3"
    key = "Your-api-key-generated-in-the-googleapis-webpage"
    commentslist=[]
    # Get credentials and create an API client
    #flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
     #   client_secrets_file, scopes)
    #credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=key )

    #request = youtube.videos().list(
     #   part="snippet,id,statistics",
      #  id="suZHkUxPzjE,th5_9woFJmk"
    #)
    #response = request.execute()
    #cleprint(response)
    request = youtube.commentThreads().list(
        part="id,replies,snippet",
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()
    print(response)
    commentslist.append(extract_from_json(response,'textOriginal'))
    count=0
    while 'nextPageToken' in response.keys():
        request = youtube.commentThreads().list(
        part="id,replies,snippet",
        videoId=video_id,
        pageToken=response['nextPageToken'],
        maxResults=100
        )
        response = request.execute()
        commentslist.append(extract_from_json(response,'textOriginal'))
        count+=1
        print(count)
    print('nextPageToken' in response.keys())
    print(type(response.keys()))
    commentslist= list(itertools.chain.from_iterable(commentslist))
    return commentslist

# this method is written to extract the required raw data from the json which is received as a response 
# to the youtube api calls.
def extract_from_json(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


# this method is used to connect to the standford CoreNLP server which is already running on port 9000.
# For a give comment text, we extract number of sentences the comment has and the count of sentences 
# with positive sentiment and count of sentences with negative sentiment.
def stanford_sentiment(text_str):
    nlp = StanfordCoreNLP('http://localhost:9000')
    res = nlp.annotate(text_str,
                       properties={
                           'annotators': 'sentiment',
                           'outputFormat': 'json',
                           'timeout': 100000
                       })
    numSentence = len(res["sentences"])
    if numSentence==0: return(0,0,0,0)
    numWords = len(text_str.split())

    # data arrangement
    arraySentVal = np.zeros(numSentence)

    for i, s in enumerate(res["sentences"]):
        arraySentVal[i] = int(s["sentimentValue"])

    # sum of sentiment values
    totSentiment = sum(arraySentVal)
    poscount= np.count_nonzero(arraySentVal==3)/numSentence
    negcount= np.count_nonzero(arraySentVal==1)/numSentence
    # avg. of sentiment values
    avgSentiment = np.mean(arraySentVal)
    # frequency of sentimentValue
    #bins = [0, 1, 2, 3, 4, 5, 6]
    #freq = np.histogram(arraySentVal, bins)[0]  # getting freq. only w/o bins

    return (numSentence, numWords, poscount, negcount)


if __name__ == "__main__":
    main()
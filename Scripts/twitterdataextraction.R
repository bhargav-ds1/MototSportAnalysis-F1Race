#'-----------------------------------
#' Twitter data webscraping script
#' -----------------------------------
#' This script is for downloading and cleansing the Tweets for each of the races.
#' Output are n csv-files, one for each of the race.

library(httr) # Tool for working with URLs and HTTP
library(jsonlite) # JSON parser and generator, as API-output is JSON
library(dplyr) # Tool for data manipulation
#library(lubridate)
library(Hmisc)

# The code for the authentication on the Twitter API
# Create and enter your api token to use the twitter api
Sys.setenv(BEARER_TOKEN = "")

# Setting the necessary variables for the authentication 
bearer_token <- Sys.getenv("BEARER_TOKEN")
headers <- c(`Authorization` = sprintf('Bearer %s', bearer_token))

#' A list of all the races is needed, which the script can iterate over.
#' The file simply contains each race with its name, the date and the race time.
#' With this dataframe, we are able to use all the races from 2009 to 2021.
race_information <- read.csv2("races.csv", sep=",")
race_information_2013 <- race_information[race_information$year>2013,]
race_date <- cbind(race_information_2013$name, race_information_2013$date, 
                   race_information_2013$time)
race_date <- data.frame(race_date)
race_date <- race_date[order(race_date$X2),]

#' As the hashtag for searching Twitter is created from the race name, some
#' names need to be adjusted, as they are not explicit enough to be used as a
#' hashtag, e.g. UnitedStates Grand Prix is not used by any Twitter user, rather
#' USA Grand Prix.
race_date[race_date == "Emilia Romagna Grand Prix"] <- "EmiliaRomagna Grand Prix"
race_date[race_date == "UnitedStates Grand Prix"] <- "USA Grand Prix"
race_date[race_date == "Abu Dhabi Grand Prix"] <- "AbuDhabi Grand Prix"
race_date[race_date == "70th Anniversary Grand Prix"] <- "Silverstone Grand Prix"


#' Unfortunately, the data does not have a nice form, as there are e.g. line
#' breaks included. Furthermore, as the API also returns retweets, duplicates
#' are removed.
#' Inputs: data (as dataframe or json)
#' Outputs: data (as dataframe)
clean_tweets <- function(data){
  # Maybe we should take it out? Emojis could also be an important reaction for the race
  data <- data.frame(data$data.text[!duplicated(data$data.text)])
  data <- apply(data, 1, function(y) gsub("[\r\n]", "", y))
  data <- data.frame(data)
  return(data)
}


# This loop iterates over all races.
for(i in 1:nrow(race_date)){
  # Create hashtag from race name
  hashtag <- paste(first.word(race_date[i,][1]), "GP", sep="")
  # The filename for saving the file is created from the date and the hashtag
  filename <- paste(paste(race_date[i,][2],hashtag, sep="_"), ".csv", sep="")

  # This determines the time at which the script should stop scraping data.
  # It is necessary, as you can only download 500 rows with one transaction.
  end_hour <- as.numeric(first.word(race_date[i,][3]))+7
  end_hour
  
  #' This if-clause makes sure that all end_hours >= 24, i.e., on the next day,
  #' are set to the next day, so the proper date can be handed to the API.
  if(end_hour >= 24){
    end_hour <- end_hour - 24 # this is done to get the actual end-hour
    # This checks whether the new date is 1 digit or 2 digit long.
    if(nchar(as.numeric(substring(race_date[i,][2], 9,10))+1) == 1){
      date <- paste(substring(race_date[i,][2], 1,8), "0",as.numeric(substring(race_date[i,][2], 9,10))+1,sep="")
    }else{
      date <- paste(substring(race_date[i,][2], 1,8),as.numeric(substring(race_date[i,][2], 9,10))+1,sep="")
    }
    curr_time <- paste(date, "T0", end_hour, ":00:00Z",sep="")
    
  }else{
    curr_time <- paste(race_date[i,][2], "T", end_hour ,":00:00Z", sep="")
  }
  # start_time is set to the time at which the current race starts.
  start_time <- paste(race_date[i,][2], paste("T",race_date[i,][3], sep=""), sep="")
  
  n <- 1 # necessary for the iteration
  # Control-output to see the current status of the webscraping.
  print(paste("Grand Prix:", hashtag, race_date[i,][2]))
  #' This while-loop iterates backwards over all the timepoints, until it 
  #' reaches the start_time of the current race.
  #' This is done because of the API-restriction to just 500 Tweets in one 
  #' transaction. 
  while(as.numeric(substring(start_time, 12, 13)) <= as.numeric(substring(curr_time, 12, 13)) || as.numeric(substring(start_time, 9,10)) < as.numeric(substring(curr_time, 9,10))){
    # The URL is created for each time-point individually
    url_handle_hashtag <- 
      sprintf("https://api.twitter.com/2/tweets/search/all?query=%%23%s&tweet.fields=lang,text,created_at&max_results=500&end_time=%s", hashtag, curr_time)
    #' This sends the request to the API and saves the returned JSON-data in the
    #' variable "response_hashtag".
    url_handle_hashtag
      response_hashtag <- 
      httr::GET(url = url_handle_hashtag,
                httr::add_headers(.headers = headers))
    # The data is converted into text-format
    obj <- httr::content(response_hashtag, as = "text")
    # The JSON-format is converted into a dataframe.
    json_data <- fromJSON(obj, flatten = TRUE) %>% as.data.frame
    
    #' The else-case is only executed the first time this script runs, so a 
    #' new dataframe "result_data" can be created.
    if(n > 1){
      result_data <- rbind(result_data, json_data[,1:4])
    }else{
      result_data <- json_data[,1:4]
    }
    
    # Control-output for checking current timepoint and iteration.
    print(curr_time)
    print(n)
    
    #' A sleep time, so the API does not prohibit the connection because of
    #' too many requests at a time.
    Sys.sleep(3)
    
    # Set the new current time to the last time point of the data downloaded.
    curr_time <- tail(result_data$data.created_at, n=1)
    n <- n + 1
  }
  # Clean the tweets and save them in a csv-file using the filename. 
  result_data <- clean_tweets(result_data)
  write.csv2(result_data, filename)
  
}
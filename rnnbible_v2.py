#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API 
import re
import json
import sys
import string
import pprint
import subprocess
import random
import threading


#Variables that contains the user credentials to access Twitter API 
consumer_key = 'eOK9XGaXJ7OdEXFyO4GudE3ny'
consumer_secret = 'ON8prPM5hdlG8LnOlPRKyHZEKFRikWl8GLQ7Hf6NMHwYWHhFWn'
access_token = '3225927684-yCTXeh1iWcacJGcT66ytPOxwRbcvM00B7ZbpmCz'
access_token_secret = '0OHHnOzfuuXiFLR6dKj7TydPyAFh5RyCeZww9IJFaG336'

books = ["Gen", "Exo", "Lev", "Num", "Deu", "Jos", "Jdg", "Rut", "1Sa", "2Sa", "1Ki", "2Ki", "1Ch", "2Ch", "Ezr", "Neh", "Est", "Job", "Psa", "Pro", "Ecc", "Son", "Isa", "Jer", "Lam", "Eze", "Dan", "Hos", "Joe", "Amo", "Oba", "Jon", "Mic", "Nah", "Hab", "Zep", "Hag", "Zec", "Mal", "Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal", "Eph", "Phi", "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jam", "1Pe", "2Pe", "1Jo", "2Jo", "3Jo", "Jud", "Rev"]
        
def GenerateBibleVerseTweet(user_handle, primetext):
  for attempt in range(1,5): 
    # Sanitize for safety
    primetext = " ".join(re.findall("[a-zA-Z,.]+", primetext)) + random.choice(string.ascii_lowercase)  
    primetext = re.sub("X","x", primetext)
    temperature = random.random()/2.0 + 0.49
    print "Try", attempt, " ", primetext
    try:
      cmdline = " ".join([
          "/usr/local/bin/th",
          "/home/mtyka/src/rnnbible/sample.lua",
          "/home/mtyka/src/rnnbible/bible.t7",
          "-gpuid",
          "0",
          "-primetext", 
          "'%s ='"%( primetext),
          "-temperature",
          "%f"%temperature,
          "-length",
          "2048" ])
      print cmdline
      proc = subprocess.Popen(cmdline,
#          cwd="/home/mtyka/src/char-rnn/",
          stdout=subprocess.PIPE, shell=True)
      (out, err) = proc.communicate()
    except:
      print sys.exc_info()[0]
      print sys.exc_info()
      continue 
    out_lines = out.split("=")
    if not out_lines: 
      print "NO VERSES!"
      continue 
    
    tweets = [] 
    if user_handle: user_handle = "@" + user_handle + " "
    for out_line in out_lines[1:]:
      reply = " ".join(out_line.strip().splitlines())
      reply = re.sub("\\[[0-9a-zA-Z]*","",reply); ## get rid of ansi sequences
      reply = " ".join(re.findall("[a-zA-Z,.:;'?!]+", reply))
      ## Clean reply 
      verse = "%s %d:%d"%(random.choice(books), random.randint(1,15), random.randint(1,15))  
      tweets.append("%s%s"%(user_handle, reply))
   
    tweet_rank = []
    for tweet in tweets:
      raw_tweet = tweet[0:129]
      for i in ".,;:?!":
        pos = raw_tweet.rfind(i)
        if pos > 0:
          truncation = raw_tweet[0:pos]
          tweet_rank.append(truncation)
         
    tweet_rank.sort(key = len)
    for t in tweet_rank:
      print t
    return tweet_rank[-1]  + " - " + verse  
    #return tweets[0][0:126] + "..."  + " - " + verse  
  print "Borked - lets restart."
  sys.exit(1)

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, api):
        self.api = api

    def on_data(self, data):
        json_data = json.loads(data)
        #pp = pprint.PrettyPrinter(depth=6)
        #pp.pprint(json_data)

        user_handle = json_data["user"]["screen_name"]
        #print user_handle
        input_tweet = json_data["text"]
        clean_tweet = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', input_tweet)
        clean_tweet = " ".join(re.findall("[a-zA-Z,.]+", clean_tweet))
        
        the_chosen_tweet = GenerateBibleVerseTweet(user_handle, clean_tweet)
        print the_chosen_tweet, "REPLY_TO: ", json_data["id"]
        if the_chosen_tweet:
          self.api.update_status(status=the_chosen_tweet, in_reply_to_status_id = json_data["id"])
        return True

    def on_error(self, status):
        print "Error: ", status


if __name__ == '__main__':

    #This handles Twitter authetification and the connection to Twitter Streaming API
    if len(sys.argv)>1 and sys.argv[1] == "live":
      auth = OAuthHandler(consumer_key, consumer_secret)
      auth.set_access_token(access_token, access_token_secret)
      api = API(auth)
      
      # Start random tweess
      def set_interval(sec):
        def func_wrapper():
          random_primer = ''.join(random.choice(
            string.ascii_uppercase + string.ascii_lowercase) for _ in range(10))
          print "Primer: ", random_primer
          the_chosen_tweet = GenerateBibleVerseTweet("", random_primer)
          print "RANDOM:", the_chosen_tweet
          if the_chosen_tweet:
            api.update_status(status=the_chosen_tweet)
          set_interval(sec)
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t
      
      set_interval(1600)

      l = StdOutListener(api)
      stream = Stream(auth, l)
      stream.filter(track=['@rnnbible'])
    else:
      print "Test mode. Example tweets: "
      for i in range(0,1000):
        random_primer = ''.join(random.choice(
          string.ascii_uppercase + string.ascii_lowercase + ' ') for _ in range(10))
        print "Primer: ", random_primer
        the_chosen_tweet = GenerateBibleVerseTweet("user", random_primer)
      

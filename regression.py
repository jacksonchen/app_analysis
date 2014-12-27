from __future__ import division
import pandas as pd
import re
from pylab import *
import glob
import string
import sys
from datetime import datetime

def compile_comments(path, app_comments):
  for fname in glob.glob(path):
    app_comments = pd.concat([app_comments, pd.read_json(fname)], ignore_index=True)
  return app_comments

def words_table(app_comments):
  words_per_comment = pd.DataFrame(columns = ['comments', 'words'])
  words_per_comment.set_index(['comments'], inplace = True)
  contraction_match = re.compile("[^']+'[a-zA-Z]{1,2}$")
  total_words = []
  for index, row in app_comments.iterrows():
    if row[3]['st'] is not None and row[3]['cmt'] is not None:
      contractions = [x.encode('ascii','ignore').lower().translate(string.maketrans('', ''), '\\') for x in filter(None, re.split("\s|,|:|-|\.|\(|\)|\/|\[|\]|!|\*|;|\"|\\|\\\\|\+", row[3]['cmt'])) if contraction_match.match(x.encode('ascii','ignore'))]
      cleaned_words = [x.encode('ascii','ignore').lower().translate(string.maketrans('', ''), '\\!?\.') for x in filter(None, re.split("\s|,|:|-|\.|\(|\)|\/|\[|\]|!|\*|;|\"|'|\\|\\\\|\+", row[3]['cmt']))]
      cleaned_words = filter(None, cleaned_words)
      words_per_comment.loc[index, 'words'] = cleaned_words + contractions
      total_words.extend(cleaned_words)
      if contractions is not None:
        total_words.extend(contractions)

  return list(set(total_words)), words_per_comment

def words_comments_table(total_words, comments_table, words_per_comment):
  words_comments = pd.DataFrame(columns = ['comments'])
  words_comments.set_index(['comments'], inplace = True)

  comments_ratings = pd.DataFrame(columns = ['comments', 'rating'])
  comments_ratings.set_index(['comments'], inplace = True)

  progress_counter = 0
  for index, row in comments_table.iterrows():
    if row[3]['st'] is not None and row[3]['cmt'] is not None:
      for word in total_words:
        words_comments.loc[index, word] = words_per_comment.loc[index, 'words'].count(word)
      comments_ratings.loc[index, 'rating'] = row[3]['st']
    progress = int(round(progress_counter*190/len(comments_table.index)))
    sys.stdout.write('\r')
    sys.stdout.write("[%-190s] %d%%" % ('='*progress, (progress_counter/len(comments_table.index)*100)))
    sys.stdout.flush()
    progress_counter += 1

  return words_comments, comments_ratings

## Generates word_comments and comments_ratings tables
def generate_words_comments():
  app_comments = pd.DataFrame(columns = ['date_published', 'downloads', 'package', 'reviews', 'version_code', 'version_name'])
  app_comments = compile_comments("/Users/Jackson/dev/science/health-apps/comments/*.json", app_comments)

  total_words, words_per_comment = words_table(app_comments)
  print "Total word count: " + str(len(total_words))

  words_comments, comments_ratings = words_comments_table(total_words, app_comments, words_per_comment)

  ## Writes the dataframes into csv files
  f = open('words_comments.csv', 'wb')
  f.write(words_comments.to_csv(index = False))
  f.close()
  f = open('comments_ratings.csv', 'wb')
  f.write(comments_ratings.to_csv(index = False))
  f.close()

### Main ###
beginning_time = datetime.now()



end_time = datetime.now()
elapsed_seconds = (end_time - beginning_time).seconds
print ""
print "Finished after " + '{:02}:{:02}:{:02}'.format(elapsed_seconds // 3600, elapsed_seconds % 3600 // 60, elapsed_seconds % 60)

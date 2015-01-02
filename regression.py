import pandas as pd
import matplotlib
import re
import glob
from pylab import *
import numpy as np
from sklearn import linear_model
from ast import literal_eval
from sklearn.linear_model import MultiTaskElasticNetCV
from sklearn.linear_model import RidgeCV
import sys
from datetime import datetime

def load_data(x_path, y_path, words_comments_path, app_comments_path):
  x = pd.read_csv(x_path, index_col = False)
  x.set_index(['comments'], inplace = True)
  y = pd.read_csv(y_path)
  y.set_index(['comments'], inplace = True)
  words_comments = pd.read_csv(words_comments_path)
  words_comments.words = words_comments.words.apply(literal_eval)
  words_comments.set_index(['comments'], inplace = True)

  app_comments = pd.DataFrame(columns = ['date_published', 'downloads', 'package', 'reviews', 'version_code', 'version_name'])
  for fname in glob.glob(app_comments_path):
    app_comments = pd.concat([app_comments, pd.read_json(fname)], ignore_index=True)

  return x, y, words_comments, app_comments

def regression(x, y):
  #enet = MultiTaskElasticNetCV(l1_ratio=0.2)
  enet = RidgeCV()
  y_pred_enet = enet.fit(x, y)

  word_vals = pd.DataFrame(columns = ['coeff'])
  counter = 0
  for i in y_pred_enet.coef_[0]:
    word_vals.loc[x.columns.values[counter]] = i
    counter += 1

  predicted_vals = y_pred_enet.predict(x)
  predicted_df = pd.DataFrame(columns = ['comment','predicted'])
  predicted_df.set_index(['comment'], inplace = True)
  counter = 0
  for i in y.index.values:
    predicted_df.loc[i, 'predicted'] = predicted_vals[counter][0]
    counter += 1

  return word_vals, predicted_df

def predict_true_table(y, predicted_df):
  predict_true_vals = pd.DataFrame(columns = ['predicted', 'true'])
  for i in y.index.values:
    predict_true_vals.loc[i] = [predicted_df.loc[i, 'predicted'], y.loc[i, "rating"]]

  return predict_true_vals

def consistency(predict_true_vals, words_comments, word_vals):
  consistent_neg_comments = pd.DataFrame(columns = ['words'])
  inconsistent_comments = pd.DataFrame(columns = ['predicted', 'true'])
  for i in predict_true_vals.index.values:
    if (predict_true_vals.loc[i, 'true'] < 3) and (abs(predict_true_vals.loc[i, 'predicted'] - predict_true_vals.loc[i, 'true']) < 0.5):
      neg_words = []
      for word in words_comments.loc[i, 'words']:
        if word_vals.loc[word, 'coeff'] < 0:
          neg_words.append(word)
      consistent_neg_comments.loc[i, 'words'] = neg_words
    elif (abs(predict_true_vals.loc[i, 'predicted'] - predict_true_vals.loc[i, 'true']) >= 3):
      inconsistent_comments.loc[i] = [predict_true_vals.loc[i, 'predicted'], predict_true_vals.loc[i, 'true']]

  return consistent_neg_comments, inconsistent_comments

def pre_lda(consistent_neg_comments, app_comments):
  combined = pd.DataFrame(columns = ['package', 'verc', 'blank', 'words'])
  combined.set_index(['package', 'verc'], inplace = True)
  for i in consistent_neg_comments.index.values:
    inIndex = False
    if len(combined.index.values) > 0:
      for s in combined.index.values:
        if (str(app_comments.loc[i, 'package']), str(int(app_comments.loc[i, 'version_code']))) == s:
          inIndex = True
          break

    if inIndex == True:
      prev = combined.loc[(str(app_comments.loc[i, 'package']), str(int(app_comments.loc[i, 'version_code']))), "words"]
      combined.loc[(str(app_comments.loc[i, 'package']), str(int(app_comments.loc[i, 'version_code']))), "words"] = prev + ' ' + ' '.join(consistent_neg_comments.loc[i, 'words'])
    else:
      combined.loc[(str(app_comments.loc[i, 'package']), str(int(app_comments.loc[i, 'version_code']))), 'words'] = ' '.join(consistent_neg_comments.loc[i, 'words'])

  to_print = pd.DataFrame(columns = ['package', 'verc', 'words'])
  for i in range(len(combined.index.get_values())):
    to_print.loc[i, 'package'] = str(combined.index.get_values()[i][0])
    to_print.loc[i, 'verc'] = str(combined.index.get_values()[i][1])
    to_print.loc[i, 'words'] = str(combined.loc[(combined.index.get_values()[i][0], combined.index.get_values()[i][1]), 'words'])

  f = open('health-apps/lda/lda.csv', 'wb')
  f.write(to_print.to_csv(header = False))
  f.close()

### Main ###
beginning_time = datetime.now()

  # Configurations
f = open('config.py', 'r').readlines()
x_path = re.match("x_path = '([^']+)'", f[0]).group(1)
y_path = re.match("y_path = '([^']+)'", f[1]).group(1)
words_comments_path = re.match("words_comments_path = '([^']+)'", f[2]).group(1)
app_comments_path = re.match("app_comments_path = '([^']+)'", f[3]).group(1)

# x_path = 'health-apps/regression_matrices/words_comments.csv'
# y_path = 'health-apps/regression_matrices/comments_ratings.csv'
# words_comments_path = 'health-apps/regression_matrices/words_per_comment.csv'
# app_comments_path = 'health-apps/comments/*.json'

x, y, words_per_comment, app_comments = load_data(x_path, y_path, words_comments_path, app_comments_path)
word_vals, comments_prediction = regression(x, y)
predict_true_vals = predict_true_table(y, comments_prediction)
consistent_neg_comments, inconsistent_comments = consistency(predict_true_vals, words_per_comment, word_vals)
pre_lda(consistent_neg_comments, app_comments)

end_time = datetime.now()
elapsed_seconds = (end_time - beginning_time).seconds
print ""
print "Finished after " + '{:02}:{:02}:{:02}'.format(elapsed_seconds // 3600, elapsed_seconds % 3600 // 60, elapsed_seconds % 60)

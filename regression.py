from __future__ import division
import pandas as pd
import re
from pylab import *
import glob
import string

app_comments = pd.DataFrame(columns=['date_published', 'downloads', 'package', 'reviews', 'version_code', 'version_name'])

path = "/Users/Jackson/dev/science/health-apps/comments/*.json"
for fname in glob.glob(path):
  app_comments = pd.concat([app_comments, pd.read_json(fname)], ignore_index=True)

regex = re.compile(r'[^()!?]')
ellipse = re.compile(r'([^.]+)\.+([^.]+)')
total_words = []
for index, row in app_comments.iterrows():
  if row[3]['st'] is not None and row[3]['cmt'] is not None:
    cleaned_words = [str(x).translate(string.maketrans('', ''), '()?!\"\'\\/').lower() for x in row[3]['cmt'].split()]
    cleaned_words = list(set(cleaned_words))
    for x in cleaned_words:
      if ellipse.match(x):
        results = ellipse.match(x)
        cleaned_words = [y for y in cleaned_words if y != x]
        cleaned_words.extend([results.group(1), results.group(2)])
      cleaned_words = [z.translate(string.maketrans('', ''), '.') for z in cleaned_words]

    total_words.extend(cleaned_words)

total_words = list(set(total_words))
print total_words

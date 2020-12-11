import pymongo
import pandas as pd
client = pymongo.MongoClient('mongodb://3.35.46.109:27017/')
db = client.news
collection = db.articles
items = collection.find()
df = pd.DataFrame(items)

from datetime import date, timedelta

yesterday = date.today() - timedelta(1)
date = yesterday.strftime('%Y.%m.%d')
df = df[df['p_date'] == date ]
df = df.drop(df.loc[df['content']==''].index)
df = df.drop(['_id'], axis=1)
df.dropna(inplace=True)
df.isnull().sum()
df['removal'] = date
df.reset_index(drop=True, inplace=True)


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

tfidf = TfidfVectorizer()
tfidf_matrix = tfidf.fit_transform(df['content'])
n = len(df['content'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

num = []
i = 0
j = 0
l = []
cosine_sim[i][j]
for i in range(n - 1):

    for j in range(1, n - 1):

        if cosine_sim[i][j] >= 0.8:

            if i < j:
                num.append(j)
                l.append([i, j])
                #print(i, j)
                #print(cosine_sim[i][j])

new_ = []
for v in num:
    if v not in new_:
        new_.append(v)

article = df.drop(index=new_)

#print(article)


my_articles = article.to_dict('records')
client = pymongo.MongoClient('mongodb://3.35.46.109:27017/')
articles = client.news.articles
articles.insert(my_articles)











import discord
import asyncio
import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from wordcloud import WordCloud
from PIL import Image
import pandas as pd
import nltk
from konlpy.tag import Mecab
from discord.ext import commands
import re
import pymongo

token = "Bot_token"
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('Ready!!')
    
@bot.command()
async def news(ctx,p_date):
    # 이미지 파일 불러오기 위한 엠베드 추가
    embed = discord.Embed(
        title='wordcloud',
        color=discord.Color.blue()
    )
    datas = tdk(p_date)
    # 단어 총 갯수
    number = 0
    for data in datas:
        number += data[1]
    # % & count구하기
    words = []
    counts = []
    for data in datas[:10]:
        words.append(data[0] + " " + str(round(data[1]/number * 100,2)) + "%")
        counts.append(data[0] + " " + str(data[1]) + "개")
    
    wordstr = " ".join(words)
    countstr = " ".join(counts)
    file = discord.File("1.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    # %정보 엠베드에 붙이기
    embed.add_field(name="word %", value=wordstr, inline=False)
    # 정보 카운트
    embed.add_field(name="word_count",value=countstr, inline=False)
    # 엠베드 보내기
    await ctx.send(file=file, embed=embed)

#오늘의 키워드를 이용한 추천 기사  
@bot.command()
async def t_pick(ctx,p_date):
    df = database(p_date)
    datas = tdk(p_date)
    t_key = []
    for keyword in datas[:10]:
        t_key.append(keyword[0])
    articles = []
    for data in df.iterrows():
        judge = True
        for idx in range(len(t_key)):
            if t_key[idx] not in data[1].content:
                judge = False
        if judge == True:
            articles.append(data[1].link)
    for idx in range(len(articles)):
        await ctx.send(articles[idx])

    
    
@bot.command()
async def title(ctx,p_date,search,max_num=3):
    df = database(p_date)
    #기사 모음
    articles = []
    for data in df.iterrows():
        if search in data[1].title:
            articles.append(data[1].title + " " + data[1].link)
    try:
        for idx in range(max_num):
            await ctx.send(articles[idx])
    except:
        await ctx.send(str(len(articles)) + '개의 기사 모두 불러왔습니다.')

@bot.command()        
async def content(ctx,p_date,*search):
    df = database(p_date)
    articles = []
    for data in df.iterrows():
        judge = True
        for idx in range(len(search)):
            if search[idx] not in data[1].content:
                judge = False
        if judge == True:
            articles.append(data[1].link)
    for idx in range(len(articles)):
        await ctx.send(articles[idx])


        
# 데이터 베이스에서 추출하여 데이터프레임 만드는 함수    
def database(p_date):
    client = pymongo.MongoClient('mongodb://3.35.46.109:27017/')
    db = client.news
    ls = list(db.articles.find({'p_date':p_date}))
    df = pd.DataFrame(ls)
    #중복 기사 제거
    df = df[df.removal.notnull()].reset_index().drop(columns=['index'])
    return df

# 오늘의 키워드 
def tdk(p_date):
    # 자연어처리 툴
    mecab = Mecab()
    # 데이터프레임 불러오기
    df = database(p_date)
    # 기사 데이터 추출
    contents = []
    for data in df.content:
        if type(data) == str:
            contents.append(data.strip())
    # 단어만 추출
    nouns = []
    for idx in range(len(contents)):
        nouns.extend(mecab.nouns(contents[idx]))
    # 불용어
    with open('ko_stopwords.txt', 'rt') as txt_file:
        stop_words = txt_file.readlines()
    stop_word = []
    for idx in range(len(stop_words)):
        stop_word.append(stop_words[idx].replace("\n", ""))
    # 불용어 걸러내기
    new_nouns = [each_word for each_word in nouns if each_word not in stop_word]
    # 단어 중복 체크
    words = nltk.Text(new_nouns, name='words')
    # 상위100개 추출
    data = words.vocab().most_common(100)
    #워드크라우드 만들기
    wordcloud = WordCloud(font_path='/usr/share/fonts/truetype/nanum/NanumMyeongjoExtraBold.ttf',
                          relative_scaling=0.05,
                          background_color='white',
                          ).generate_from_frequencies(dict(data))
    wordcloud.to_file('1.png')
    return data

bot.run(token)
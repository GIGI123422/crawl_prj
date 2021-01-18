import discord   # discord 실행을 위한 import
import asyncio
import datetime   # 자연어처리를 위한 패키지
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from wordcloud import WordCloud
from PIL import Image
import pandas as pd
import nltk
from konlpy.tag import Mecab
from discord.ext import commands
import pymongo

token = "BOT_KEY"   # https://discord.com/developers/applications에서 제공하는 Bot Token 입력
bot = commands.Bot(command_prefix='!')   # 봇에게 명령하기 위해 맨 처음 넣어야 하는 표시기호 설정
bot.remove_command('help')   # 기존 내장되어 있는 help 함수 제거


@bot.event
async def on_ready():   # 봇이 정상적으로 작동할 준비가 되어 있다는 표시
    """
    bot 실행시 제대로 작동되는지 인지하게 해주는 함수
    """
    print('Ready!!')


@bot.command()
async def summary(ctx, p_date):   # 해당 날짜의 뉴스 기사들 중 빈도수가 높은 단어를 워드클라우드 이미지로 전송
    """
    Embed 형태로 wordcloud 및 중복 top10 단어 데이터를 표출 해주는 함수
    """

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
        words.append(data[0] + " " + str(round(data[1] / number * 100, 2)) + "%")
        counts.append(data[0] + " " + str(data[1]) + "개")

    wordstr = " ".join(words)
    countstr = " ".join(counts)
    file = discord.File("1.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    # %정보 엠베드에 붙이기
    embed.add_field(name="word %", value=wordstr, inline=False)
    # 정보 카운트
    embed.add_field(name="word_count", value=countstr, inline=False)
    # 엠베드 보내기
    await ctx.send(file=file, embed=embed)


@bot.command()
async def t_pick(ctx, p_date):   # 해당 날짜의 뉴스 기사 내용 중 빈도수가 가장 높은 단어들이 포함된 뉴스 기사 상위 5개 전송
    """
    특정 날짜의 추천 기사를 보내주는 함수
    """

    df = database(p_date)
    datas = tdk(p_date)
    t_key = []
    for keyword in datas[:5]:
        t_key.append(keyword[0])
    mecab = Mecab()
    articles = {}
    for data in df.iterrows():
        # 기사 하나씩 대조
        news = data[1].content
        # 단어
        words = nltk.Text(mecab.nouns(news))
        count = 0
        for idx in range(len(t_key)):
            count += words.vocab()[t_key[idx]]
        # 딕셔너리에 저장
        if count != 0:
            articles[data[1].link] = count
            # count 갯수로 정렬
    sorted_articles = dict(sorted(articles.items(), key=lambda item: item[1], reverse=True))
    limit = 0
    # 추천 기사
    rcd = []
    for link in sorted_articles.keys():
        rcd.append(link)
        limit += 1
        # 추천 갯수 제한
        if limit == 5:
            break
    try:
        for idx in range(len(rcd)):
            await ctx.send(rcd[idx])
    except:
        ctx.send('추천 기사를 모두 불러왔습니다!')


@bot.command()
async def content(ctx, p_date, *search):   # 해당 날짜의 누스 기사들 중 기사 내용에 해당 키워드가 가장 많이 들어있는 순으로 뉴스 기사 링크 전송
    """
    단어를 입력하여, 이와 연관된 기사를 특정 날짜에 찾아주는 함수
    """

    df = database(p_date)
    mecab = Mecab()
    articles = {}
    for data in df.iterrows():
        # 기사 하나씩 대조
        news = data[1].content
        # 단어
        words = nltk.Text(mecab.nouns(news))
        count = 0
        for idx in range(len(search)):
            count += words.vocab()[search[idx]]
        # 딕셔너리에 저장
        if count != 0:
            articles[data[1].link] = count
            # count 갯수로 정렬
    sorted_articles = dict(sorted(articles.items(), key=lambda item: item[1], reverse=True))
    limit = 0
    # 추천 기사
    rcd = []
    for link in sorted_articles.keys():
        rcd.append(link)
        limit += 1
        # 추천 갯수 제한
        if limit == 5:
            break
    try:
        for idx in range(len(rcd)):
            await ctx.send(rcd[idx])
    except:
        ctx.send('추천 기사를 모두 불러왔습니다!')


@bot.command()
async def help(ctx):   # 명령어 리스트 정보 
    """
    Embed 형태로 bot의 명령어를 설명해주는 함수
    """

    embed = discord.Embed(
        title='명령 리스트!!(command list)',
        color=discord.Color.blue()
    )

    embed.set_thumbnail(
        url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLByFMbwV_iorbq0iETHCYcuSjXbp7G4BMsA&usqp=CAU')
    embed.add_field(name="summary (date)", value='입력 날짜의 워드크라우드와 워드카운트를 보여줍니다.', inline=False)
    embed.add_field(name="content (date, *keywords)", value='입력한 키워드들을 바탕으로 입력된 키워드가 많이 들어간 기사를 찾아줍니다.', inline=False)
    embed.add_field(name="t_pick (date)", value='입력한 날짜에 가장 많이 쓰여진 키워드를 바탕으로 기사를 추천 해줍니다.', inline=False)

    await ctx.send(embed=embed)


def database(p_date):
    """
    몽고DB에서 데이터를 추출하여 데이터프레임 만드는 함수
    """

    client = pymongo.MongoClient('database')
    db = client.news
    ls = list(db.articles.find({'p_date': p_date}))
    df = pd.DataFrame(ls)
    # 중복 기사 제거
    df = df[df.removal.notnull()].reset_index().drop(columns=['index'])
    return df


# 오늘의 키워드
def tdk(p_date):
    """
    데이터 베이스에 있는 특정 날짜의 모든 기사 데이터를 가지고 자연어처리를 해주는 함수
    """

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
    # 워드크라우드 만들기
    wordcloud = WordCloud(font_path='/usr/share/fonts/truetype/nanum/NanumMyeongjoExtraBold.ttf',
                          relative_scaling=0.05,
                          background_color='white',
                          ).generate_from_frequencies(dict(data))
    wordcloud.to_file('1.png')
    return data


bot.run(token)

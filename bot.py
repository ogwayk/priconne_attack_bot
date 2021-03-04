import discord
import sys
import re
import datetime
import os
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials


scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

intents = discord.Intents.all()
intents.typing = False
client = discord.Client(intents = intents)
#client = discord.Client()

@client.event
# 起動通知
async def on_ready():
    print('リンクスタート！')

@client.event
async def on_message(message):
    # botだったら無視
    if message.author.bot:
         return
    if client.user in message.mentions:
        # 切断
        if '/bye' in message.content:
            await client.logout()
            return
        await get_uma_data(message)

async def get_uma_data(message):
    credentials = ServiceAccountCredentials.from_json(os.environ['gcp-umaumabot-json'], scope)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(os.environ['MATCH_SPREADSHEET_KEY']).sheet1
    import_value = worksheet.acell('A2').value
    await reply(message, message.author.mention, import_value)

async def pricone(message):
    # 凸完了チャンネルの取得
    guild = client.get_guild(int(os.environ['GUILD_ID']))
    channel = get_channel(guild)
    print(guild.name)
    # 凸完了チャンネルからメッセージを拾ってくる
    # print(channel.name)
    histories = await channel.history(limit = None).flatten()
    reactions = await get_today_reactions(histories, channel)
    # print(reactions)
    # 数字のスタンプのリアクションのメンバーを取得
    text = ''
    member_dict = {}

    channel_users = channel.members
    print(channel_users)
    if len(reactions) > 0:
        for reaction in reactions:
            users = await reaction.users().flatten()
            # print(users)
            match = re.search(r'\d', reaction.emoji)
            if match is not None:
                member_dict[match.group()] = get_reaction_member(users, channel_users)
    else:
            text = '私、相手のスリーサイズはわかるんですが今日の残り凸はわかりません…。'
            await reply(message, message.author.mention, text)
    
    # print(member_dict)
    # n+1凸にスタンプ押している人をn凸のリストから削除する
    if "1" in member_dict and "2" in member_dict:
        member_dict['1'] = list(set(member_dict['1']) - set(member_dict['2']))
    if "2" in member_dict and "3" in member_dict:
        member_dict['2'] = list(set(member_dict['2']) - set(member_dict['3']))
    
    # リプライを作成
    attack_count = 0
    for num in [3, 2, 1]:
        dict_value = []
        if str(num) in member_dict:
            dict_value = member_dict[str(num)]
            attack_count += len(dict_value) * num
        text += '残り{0}凸の人\n{1}\n\n'.format(num, ', '.join(dict_value), len(dict_value) * num)
    text += '全体残り凸数：{0}'.format(attack_count)
    await reply(message, message.author.mention, text)

# 凸完了チャンネルを取得する
def get_channel(guild):
    text_channels = guild.text_channels
    for channel in text_channels:
        # 月と凸完了が入っていて、作成年が今年のチャンネル
        if str(get_today().month) in channel.name and '凸完了' in channel.name:
            if get_today().year == channel.created_at.year:
                return channel

# 今日の凸完了メッセージに対するリアクションを取得
async def get_today_reactions(histories, channel):
    today = get_today()
    for history in histories:
        message = await channel.fetch_message(history.id)
        # 今日の報告用メッセージを取ってくる
        if '{0}/{1}'.format(today.month, today.day) in message.content:
            return message.reactions
    return []

# リアクションしているメンバーを取得
def get_reaction_member(users, channel_users):
    remain_members = []
    for user in users:
        # 今サーバーにいない人のリアクションは抜く
        if user in channel_users:
            remain_members.append(get_user_name(user))
    return remain_members

# ユーザーの名前を取得
def get_user_name(user):
    user_name = user.name

    if user.nick is not None:
        user_name = user.nick
    return user_name

# 今日の日付を取得(5時切り替え)
def get_today():
    today = datetime.datetime.now()
    if today.hour < 5:
        today = today + datetime.timedelta(days=-1)

    return today

# 返信
async def reply(message, mention, text):
    reply = '{0} \n {1}'.format(mention, text)
    await message.channel.send(reply) 

# Botの起動とDiscordサーバーへの接続
client.run(os.environ['TOKEN'])

import asyncio
from discord.ext import commands
from discord import Embed
import cleaner
from cleanerbot_token import get_token
import threading

prefix = "clb "
bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix))
token = get_token()

auths = dict()

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    mention = f"<@!{bot.user.id}>"
    if mention in message.content:
        await help(message)
        return
    if not message.content.startswith(prefix):
        return
    if message.guild:
        await message.channel.send("개인정보 유출을 방지하기 위해 DM으로 해주세요!")
        await message.channel.send(f"헬프는 {mention} 멘션")
    await bot.process_commands(message)

async def help(message):
    embed = Embed(title="CLEANERBOT 사용 설명서", color=0x95e4fe)

    embed.add_field(name=f"{prefix}login [id] [pw]", value="id와 pw를 통해 로그인합니다.", inline=False)
    embed.add_field(name="제한 사항", value="이후 커맨드는 로그인된 사용자만 사용 가능합니다.", inline=True)
    embed.add_field(name=f"{prefix}stat", value="글과 댓글 갯수를 보여줍니다.", inline=False)
    embed.add_field(name=f"{prefix}clean", value="글과 댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}post", value="글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}comment", value="댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"Github", value="https://github.com/DPS0340/CleanerBot", inline=False)

    await message.channel.send(embed=embed)

@bot.command()
async def login(ctx, id, pw):
    message = ctx.message
    if not (id and pw):
        await message.channel.send("잘못된 인자입니다!")
        return
    auths[ctx.author.id] = {'id': id, 'pw': pw}
    await message.channel.send("로그인이 완료되었습니다!")

async def invokeClean(ctx, posting=True, comment=True):
    message = ctx.message
    uid = ctx.author.id
    if not uid in auths:
        await message.channel.send("로그인 해주세요!")
        return
    await message.channel.send("삭제중..")
    auth = auths[uid]
    await cleanMatchArg(ctx, auth, posting, comment)

async def cleanMatchArg(ctx, auth, posting=True, comment=True):
    await cleaner.loginAndClean(bot, ctx, auth, posting, comment)

@bot.command()
async def clean(ctx):
    await invokeClean(ctx, True, True)

@bot.command()
async def post(ctx):
    await invokeClean(ctx, True, False)

@bot.command()
async def comment(ctx):
    await invokeClean(ctx, False, True)

@bot.command()
async def stat(ctx):
    message = ctx.message
    uid = ctx.author.id
    if not uid in auths:
        await message.channel.send("로그인 해주세요!")
        return
    auth = auths[uid]
    nickname = await cleaner.get_nickname(auth)
    postNum = await cleaner.get_num(auth, _type='posting')
    commentNum = await cleaner.get_num(auth, _type='comment')
    await message.channel.send(f"사용자 {nickname}: 글 {postNum}개 댓글 {commentNum}개")

def matchPrefix(message):
    return message.content.startswith(prefix)

def isDM(message):
    return not message.guild


bot.run(token)
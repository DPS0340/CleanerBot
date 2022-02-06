import asyncio
import logging
from discord.ext import commands
from discord import Embed
import discord
from server import ArcaProxyServer, GallogProxyServer, LoginProxyServer
import cleaner
from cleanerbot_token import get_token
from log import logger
from constants import ip_address


prefix = "clb "
bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix))
token = get_token()

auths = dict()


@bot.event
async def on_ready():
    logging.info(f"bot ip address: {ip_address}")
    logger.info('Logged on as {0}!'.format(bot.user))


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

    embed.add_field(
        name=f"{prefix}login id pw", value="id와 pw를 통해 로그인합니다.", inline=False)
    embed.add_field(
        name="제한 사항", value="이후 커맨드는 로그인된 사용자만 사용 가능합니다.", inline=True)
    embed.add_field(name=f"{prefix}stat",
                    value="글과 댓글 갯수를 보여줍니다.", inline=False)
    embed.add_field(name=f"{prefix}clean", value="글과 댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}post", value="글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}comment", value="댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}arca id pw nickname",
                    value="id와 pw, 닉네임을 통해 아카라이브에 있는 글과 댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}arca post id pw nickname",
                    value="id와 pw, 닉네임을 통해 아카라이브에 있는 글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}arca comment id pw nickname",
                    value="id와 pw, 닉네임을 통해 아카라이브에 있는 댓글을 지웁니다.", inline=False)
    embed.add_field(
        name=f"Github", value="https://github.com/DPS0340/CleanerBot", inline=False)

    await message.channel.send(embed=embed)


@bot.command()
async def login(ctx: commands.Context, id, pw):
    message = ctx.message
    if not (id and pw):
        await message.channel.send("잘못된 인자입니다!")
        return
    auths[ctx.author.id] = {'id': id, 'pw': pw}
    await message.channel.send("로그인이 완료되었습니다!")


async def invokeClean(ctx: commands.Context, posting=True, comment=True):
    message = ctx.message
    uid = ctx.author.id
    if not uid in auths:
        await message.channel.send("로그인 해주세요!")
        return
    await message.channel.send("삭제중..")
    auth = auths[uid]
    await cleanMatchArg(ctx, auth, posting, comment)


async def cleanMatchArg(ctx: commands.Context, auth, posting=True, comment=True):
    await cleaner.loginAndClean(bot, ctx, auth, posting, comment)


@bot.command()
async def clean(ctx: commands.Context):
    await invokeClean(ctx, True, True)


@bot.command()
async def post(ctx: commands.Context):
    await invokeClean(ctx, True, False)


@bot.command()
async def comment(ctx: commands.Context):
    await invokeClean(ctx, False, True)


@bot.command()
async def arca(ctx: commands.Context, *args):
    message = ctx.message
    if len(args) == 3:
        id, pw, nickname = args
        flag = ''
    elif len(args) == 4:
        flag, id, pw, nickname = args
    else:
        await message.channel.send("잘못된 인자입니다!")
        return
    posting = True
    comment = True
    if flag == 'post':
        comment = False
    elif flag == 'comment':
        posting = False
    elif flag != '':
        await message.channel.send("잘못된 인자입니다!")
        return
    await cleaner.cleanArcaLive(bot, ctx, id, pw, nickname, posting, comment)


@bot.command()
async def stat(ctx: commands.Context):
    message = ctx.message
    uid = ctx.author.id
    if not uid in auths:
        await message.channel.send("로그인 해주세요!")
        return
    auth = auths[uid]
    nickname, post_num, comment_num = await asyncio.gather(cleaner.get_nickname(auth), cleaner.get_num(auth, _type='posting'), cleaner.get_num(auth, _type='comment'))
    await message.channel.send(f"{nickname}님은 글 {post_num}개와 댓글 {comment_num}개를 작성하셨습니다.")


def matchPrefix(message):
    return message.content.startswith(prefix)


def isDM(message):
    return not message.guild


if __name__ == '__main__':
    bot.add_cog(ArcaProxyServer(bot))
    bot.add_cog(GallogProxyServer(bot))
    bot.add_cog(LoginProxyServer(bot))
    bot.run(token)

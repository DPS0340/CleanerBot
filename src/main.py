import asyncio
import logging
from discord.ext import commands
from discord import Embed, Interaction
from discord import app_commands
import discord
from server import ArcaProxyServer, GallogProxyServer, LoginProxyServer
import cleaner
from cleanerbot_token import get_token
from log import logger
from constants import ip_address


intents = discord.Intents.default()
intents.message_content = True

prefix = "/"
bot = commands.Bot(command_prefix=prefix, intents=intents)
token = get_token()

auths = dict()


# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return
#     mention = f"<@!{bot.user.id}>"
#     if mention in message.content:
#         await help(message)
#         return
#     if not message.content.startswith(prefix):
#         return
#     if message.guild:
#         await message.channel.send("개인정보 유출을 방지하기 위해 DM으로 해주세요!")
#         await message.channel.send(f"헬프는 {mention} 멘션")
#     await bot.process_commands(message)


@bot.tree.command(name="help", description="help")
async def help_(ctx: Interaction):
    embed = Embed(title="CLEANERBOT 사용 설명서", color=0x95E4FE)

    embed.add_field(
        name=f"{prefix}login id pw", value="id와 pw를 통해 로그인합니다.", inline=False
    )
    embed.add_field(
        name="제한 사항",
        value="이후 커맨드는 로그인된 사용자만 사용 가능합니다.",
        inline=True,
    )
    embed.add_field(
        name=f"{prefix}stat", value="글과 댓글 갯수를 보여줍니다.", inline=False
    )
    embed.add_field(name=f"{prefix}clean", value="글과 댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}post", value="글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}comment", value="댓글을 지웁니다.", inline=False)
    embed.add_field(
        name=f"{prefix}arca id pw nickname",
        value="id와 pw, 닉네임을 통해 아카라이브에 있는 글과 댓글을 지웁니다.",
        inline=False,
    )
    embed.add_field(
        name=f"{prefix}arca post id pw nickname",
        value="id와 pw, 닉네임을 통해 아카라이브에 있는 글을 지웁니다.",
        inline=False,
    )
    embed.add_field(
        name=f"{prefix}arca comment id pw nickname",
        value="id와 pw, 닉네임을 통해 아카라이브에 있는 댓글을 지웁니다.",
        inline=False,
    )
    embed.add_field(
        name=f"Github", value="https://github.com/DPS0340/CleanerBot", inline=False
    )

    await ctx.response.send_message(embed=embed)


@bot.tree.command(name="login", description="login")
async def login(ctx: Interaction, id: str, pw: str):
    if not (id and pw):
        await ctx.response.send_message("잘못된 인자입니다!")
        return
    auths[ctx.user.id] = {"id": id, "pw": pw}
    await ctx.response.send_message("로그인이 완료되었습니다!")


async def invokeClean(ctx: Interaction, posting=True, comment=True):
    uid = ctx.user.id
    if not uid in auths:
        await ctx.response.send_message("로그인 해주세요!")
        return
    await ctx.response.send_message("삭제중..")
    auth = auths[uid]
    await cleanMatchArg(ctx, auth, posting, comment)


async def cleanMatchArg(ctx: Interaction, auth, posting=True, comment=True):
    await cleaner.loginAndClean(bot, ctx, auth, posting, comment)


@bot.tree.command(name="clean", description="clean")
async def clean(ctx: Interaction):
    await invokeClean(ctx, True, True)


@bot.tree.command(name="post", description="post")
async def post(ctx: Interaction):
    await invokeClean(ctx, True, False)


@bot.tree.command(name="comment", description="comment")
async def comment(ctx: Interaction):
    await invokeClean(ctx, False, True)


@bot.tree.command(name="arca", description="arca")
async def arca(
    ctx: Interaction,
    flag: str,
    id: str,
    pw: str,
    nickname: str,
):
    posting = True
    comment = True
    if flag == "post":
        comment = False
    elif flag == "comment":
        posting = False
    elif flag != "all":
        await ctx.response.send_message("잘못된 인자입니다!")
        return
    await cleaner.cleanArcaLive(bot, ctx, id, pw, nickname, posting, comment)


@bot.tree.command(name="stat", description="stat")
async def stat(ctx: Interaction):
    uid = ctx.user.id
    if not uid in auths:
        await ctx.response.send_message("로그인 해주세요!")
        return
    auth = auths[uid]
    nickname, post_num, comment_num = await asyncio.gather(
        cleaner.get_nickname(auth),
        cleaner.get_num(auth, _type="posting"),
        cleaner.get_num(auth, _type="comment"),
    )
    await ctx.response.send_message(
        f"{nickname}님은 글 {post_num}개와 댓글 {comment_num}개를 작성하셨습니다."
    )


def matchPrefix(message):
    return message.content.startswith(prefix)


def isDM(message):
    return not message.guild


@bot.event
async def setup_hook():
    await bot.add_cog(ArcaProxyServer(bot))
    await bot.add_cog(GallogProxyServer(bot))
    await bot.add_cog(LoginProxyServer(bot))


@bot.event
async def on_ready():
    logger.info(f"bot ip address: {ip_address}")
    logger.info("Logged on as {0}!".format(bot.user))
    logger.info(await bot.tree.sync())
    for server in bot.guilds:
        logger.info(server)
        logger.info(server.id)
        logger.info(await bot.tree.sync(guild=discord.Object(id=server.id)))


if __name__ == "__main__":
    bot.run(token)

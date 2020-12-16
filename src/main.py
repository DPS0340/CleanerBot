from discord.ext import commands
from discord import Embed
import cleaner
import db
from cleanerbot_token import get_token

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
    if message.guild:
        await message.channel.send("개인정보 유출을 방지하기 위해 DM으로 해주세요!")
        await message.channel.send(f"헬프는 {mention} 멘션")
    await bot.process_commands(message)

async def help(message):
    embed = Embed(title="CLEANERBOT 사용 설명서", color=0x95e4fe)

    embed.add_field(name=f"{prefix}login", value="id와 pw를 통해 로그인합니다.", inline=False)
    embed.add_field(name="제한 사항", value="이후 커맨드는 로그인된 사용자만 사용 가능합니다.", inline=True)
    embed.add_field(name=f"{prefix}stat", value="글과 댓글 갯수를 보여줍니다.", inline=False)
    embed.add_field(name=f"{prefix}clean", value="글과 댓글을 지웁니다.", inline=False)
    embed.add_field(name=f"{prefix}commen", value="댓글을 지웁니다.", inline=False)

    await message.channel.send(embed=embed)

@bot.command
async def clean(message):
    await message.channel.send("id를 입력해 주세요:")
    id = await bot.wait_for('message', timeout=120)
    await message.channel.send("패스워드를 입력해 주세요:")
    pw = await bot.wait_for('message', timeout=120)
    auths[message.user.id] = {'id': id, 'pw': pw}
    await message.channel.send("로그인이 완료되었습니다!")

@bot.command
async def clean(message):
    uid = message.user.id
    auths.has_key(uid)
    auth = auths[message.user.id]
    cleaner.loginAndClean(message, {'id': id.content, 'pw': pw.content})

def matchPrefix(message):
    return message.content.startswith(prefix)

def isDM(message):
    return not message.guild


bot.run(token)
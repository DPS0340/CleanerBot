from discord.ext import commands
import cleaner
import db
from cleanerbot_token import get_token

prefix = "clb "
bot = commands.Bot(command_prefix='$')
token = get_token()

auths = dict()

@bot.event()
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

@client.event
async def on_message(message):
    if message.guild:
        await message.author.send(f"")
    await bot.process_commands(message)


@bot.command()
async def clean(message):
    await message.channel.send("id를 입력해 주세요:")
    id = await bot.wait_for('message', timeout=120)
    await message.channel.send("패스워드를 입력해 주세요:")
    pw = await bot.wait_for('message', timeout=120)
    auths[message.user.id] = {'id': id, 'pw': pw}
    await message.channel.send("")

@bot.command()
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
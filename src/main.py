import discord
import cleaner
import db
from cleanerbot_token import get_token

prefix = "clb "

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == self.user or not self.matchPrefix(message):
            return
        if not self.isDM(message):
            await message.channel.send('개인정보 유출을 방지하기 위해 DM으로 해주세요!')
            return
        if message.content.startswith(f'{prefix}clean'):
            await self.clean(message)
            return
        
    async def clean(self, message):
        await message.channel.send("id를 입력해 주세요:")
        id = await client.wait_for('message', timeout=120)
        await message.channel.send("패스워드를 입력해 주세요:")
        pw = await client.wait_for('message', timeout=120)
        cleaner.loginAndClean({'id': id.content, 'pw': pw.content})

    def matchPrefix(self, message):
        return message.content.startswith(prefix)
    
    def isDM(self, message):
        return not message.guild

token = get_token()

client = MyClient()
client.run(token)
from aiohttp import web
from constants import webserver_port
from discord.ext import commands, tasks
import aiohttp
from log import logger
from cleaner import header

app = web.Application()
routes = web.RouteTableDef()
class Webserver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webserver_port = webserver_port
        self.sessions = {}
        app.router.add_routes([
            web.get('', self.arca_proxy),
            web.post('', self.arca_proxy),
            web.get('/{url:.*}', self.arca_proxy),
            web.post('/{url:.*}', self.arca_proxy)])
        self.web_server.start()

    async def arca_proxy(self, request: web.Request):
        url = request.path_qs
        headers = request.headers.copy()

        logger.info(f'Headers: {headers}')
        logger.info(f'URL: {url}')
        if url.startswith('favicon.ico'):
            url = f"/static{url}"
        remote_url = f"https://arca.live{url}"

        request_header = {**header, 'Referer': remote_url}
        
        if self.sessions.get(request.remote):
            session = self.sessions[request.remote]
        else:
            session = aiohttp.ClientSession(headers=request_header)
            self.sessions[request.remote] = session 

        http_method = session.post if request.method == 'POST' else session.get
        if request.method == 'POST':
            data = await request.post()
            req = await http_method(remote_url, data=data, ssl=False)
        else:
            req = await http_method(remote_url, ssl=False)
        body = await req.read()
        text = body.decode('utf-8')
        return web.Response(text=text, status=req.status, content_type=req.content_type)

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()
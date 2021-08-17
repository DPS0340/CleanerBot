from aiohttp import web
from discord.ext import commands, tasks
import constants
from constants import sessions
import aiohttp
from log import logger
from cleaner import header
from urllib import parse

class AbstractProxyServer(commands.Cog):
    def __init__(self, bot, webserver_port, base_url):
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.bot = bot
        self.webserver_port = webserver_port
        self.base_url = base_url
        self.app.router.add_routes([
            web.get('', self.proxy_method),
            web.post('', self.proxy_method),
            web.get('/favicon.ico', self.favicon),
            web.get('/{url:.*}', self.proxy_method),
            web.post('/{url:.*}', self.proxy_method)])
        self.web_server.start()
    
    async def favicon(self, request: web.Request):
        return web.FileResponse('./assets/favicon.ico')

    async def proxy_method(self, request: web.Request):
        url = request.path_qs
        headers = request.headers.copy()

        logger.info(f'Headers: {headers}')
        logger.info(f'URL: {url}')

        if 'join_new' in url:
            original_url = url.split('s_url=')[1]
            original_url = parse.unquote(original_url)
            return web.HTTPFound(original_url)

        remote_url = f"{self.base_url}{url}"

        request_header = {**header, 'Referer': remote_url, 'Origin': self.base_url}
        
        if sessions.get(request.remote):
            session = sessions[request.remote]
        else:
            session = aiohttp.ClientSession(headers=request_header)
            sessions[request.remote] = session

        http_method = session.post if request.method == 'POST' else session.get
        if request.method == 'POST':
            data = await request.post()
            # if 'join/member_check.php' in url:
            #     data.set('ssl', 'Y')
            #     data.set('checksaveid', 'on')
            req = await http_method(remote_url, data=data, ssl=False)
        else:
            req = await http_method(remote_url, ssl=False)
        body = await req.read()
        text = body.decode('utf-8')
        text = text.replace(constants.dcinside_login_url, f"{constants.dcinside_proxy_url}:{constants.dcinside_login_proxy_port}")
        text = text.replace(constants.dcinside_gallog_url, parse.quote(f"{constants.dcinside_proxy_url}:{constants.dcinside_gallog_proxy_port}"))

        return web.Response(text=text, status=req.status, content_type=req.content_type)
    
    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()

class ArcaProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.arca_proxy_port, constants.arca_url)

class GallogProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.dcinside_gallog_proxy_port, constants.dcinside_gallog_url)

class LoginProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.dcinside_login_proxy_port, constants.dcinside_login_url)
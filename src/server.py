from http.cookies import SimpleCookie
from aiohttp import web
from discord.ext import commands, tasks
from yarl import URL
import constants
from constants import sessions
import aiohttp
from log import logger
from urllib import parse


class AbstractProxyServer(commands.Cog):
    def __init__(self, bot, webserver_port, base_url):
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.bot = bot
        self.webserver_port = webserver_port
        self.base_url = base_url
        self.urls = {}
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
        if not self.urls.get(request.remote):
            self.urls[request.remote] = []
        self.urls[request.remote].append(str(request.url))

        url = request.path_qs
        headers = request.headers.copy()
        remote_url = f"{self.base_url}{url}"

        logger.info(f'Headers: {headers}')
        logger.info(f'URL: {url}')
        logger.info(f'Remote-URL: {remote_url}')

        request_header = {**headers, 'Referer': remote_url,
                          'Origin': self.base_url, 'Host': self.base_url.replace('https://', '')}

        if sessions.get(request.remote):
            session: aiohttp.ClientSession = sessions[request.remote]
        else:
            session = aiohttp.ClientSession()
            sessions[request.remote] = session

        cookies = SimpleCookie(request.cookies)
        session.cookie_jar.update_cookies(cookies, URL(self.base_url))

        http_method = session.post if request.method == 'POST' else session.get
        if request.method == 'POST':
            data = await request.post()
            req = await http_method(remote_url, headers=request_header, data=data, ssl=False)
        else:
            req = await http_method(remote_url, headers=request_header, ssl=False)

        body = await req.content.read()
        headers = req.headers.copy()

        params = {'status': req.status, 'headers': headers}

        text = body.decode('utf-8')

        text = text.replace(constants.dcinside_login_url,
                            f"{constants.dcinside_proxy_url}:{constants.dcinside_login_proxy_port}")
        text = text.replace(parse.quote(constants.dcinside_gallog_url).replace(
            "/", r'%2F'), f"{constants.dcinside_proxy_url}:{constants.dcinside_gallog_proxy_port}")

        params['text'] = text

        content_length = str(len(text.encode('utf-8')))
        headers['Content-Length'] = content_length

        if headers.get('Content-Encoding'):
            del headers['Content-Encoding']
        if headers.get('Transfer-Encoding'):
            del headers['Transfer-Encoding']

        # if headers.get('Set-Cookie'):
        #     for cookie in headers.popall('Set-Cookie'):
        #         cookie.replace('; secure', '')
        #         headers.add('Set-Cookie', cookie)

        return web.Response(**params)

    @ tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @ web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()


class ArcaProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.arca_proxy_port, constants.arca_url)


class GallogProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.dcinside_gallog_proxy_port,
                         constants.dcinside_gallog_url)


class LoginProxyServer(AbstractProxyServer):
    def __init__(self, bot):
        super().__init__(bot, constants.dcinside_login_proxy_port, constants.dcinside_login_url)

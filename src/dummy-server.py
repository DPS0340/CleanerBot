from aiohttp import web
import asyncio


class Server():
    def __init__(self):
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.app.router.add_routes([
            web.get('', self.acme),
            web.post('', self.acme)
        ])

    async def acme(self, request: web.Request):
        return web.Response(text="A6QGIcHfOy3-XIoixYXiZDjbGC9g2yVUfRydfGunPxU")

    async def web_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=80)
        await site.start()
        while True:
            await asyncio.sleep(0.5)


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.web_server())

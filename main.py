import json
from aiohttp import web


class WSChat:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.conns = {}
        self.notify_users = {}

    async def main_page(self, request):
        return web.FileResponse('./index.html')

    async def handle(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        id = None
        self.conns[ws] = None
        async for msg in ws:
            if msg.data == 'ping':
                await ws.send_str('pong')
            else:
                data = json.loads(msg.data)
                if data['mtype'] == "INIT":
                    id = data['id']
                    self.conns[ws] = id
                    self.notify_users[id] = ws
                    await self.notify_all("USER_ENTER", {'id': id}, id)

                elif data['mtype'] == 'TEXT':
                    if not data['to']:
                        await self.notify_all('MSG', {'id': data['id'], 'text': data['text']}, data['id'])
                    else:
                        await self.notify_user(data['to'], 'DM', {'id': data['id'], 'text': data['text']})
        del self.conns[ws]
        del self.notify_users[id]
        await self.notify_all('USER_LEAVE', {'id': id}, None)

    async def notify_user(self, user_id, mtype, data):
        ws = self.notify_users.get(user_id, None)
        if ws != None:
            await ws.send_json({'mtype': mtype, **data})

    async def notify_all(self, mtype, data, except_id):
        for ws in self.notify_users.values():
            if self.conns[ws] != except_id:
                await ws.send_json({'mtype': mtype, **data})

    def run(self):
        app = web.Application()

        app.router.add_get('/', self.main_page)

        app.router.add_get('/chat', self.handle)

        web.run_app(app, host=self.host, port=self.port)


if __name__ == '__main__':
    WSChat().run()
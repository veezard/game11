from aiohttp import web
import asyncio
import json
import logging
exec(open("gameplay.py").read())
exec(open("server_side.py").read())


logging.basicConfig(filename='log.log', level=logging.DEBUG)

# app['websockets'] is a dictionary of [name: websocket].


async def index(request):

    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:

        #		with open('static/index.html', 'r') as myfile:
        #			data = myfile.read()
        #			return web.Response(text=data, content_type='text/html')
        raise web.HTTPFound("index.html")

    await ws_current.prepare(request)

    try:

        introduction = await ws_current.receive()
        name = json.loads(introduction.data)["name"]
        await register(ws_current, name, request.app)

    except Exception as exception:
        await ws_current.send_json({"type": "error", "msg": exception.__str__()})
        return

    try:
        async for message in ws_current:
            await responde_to_msg(json.loads(message.data), name, request.app)

    except Exception as exception:
        await ws_current.send_json({"type": "error", "msg": exception.__str__()})

    finally:
        await unregister(ws_current, name, request.app)


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


async def init_app():

    app = web.Application()
    app['websockets'] = {}
    app.on_shutdown.append(shutdown)
    app.router.add_get('/', index)
    app.router.add_static('/', 'static/', follow_symlinks=True)

    return app

players_dict = {}


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = init_app()
    web.run_app(app, port=6789)


if __name__ == '__main__':
    main()

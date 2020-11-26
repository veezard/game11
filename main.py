from aiohttp import web
import asyncio
import json
import logging
import src.gameplay as gm
import src.server_side as ss


logging.basicConfig(filename='log.log', level=logging.DEBUG)

# app['websockets'] is a dictionary of [name: websocket].

active_games = {}

active_games['abc'] = gm.Gameplay()


async def index(request):
    with open('static/index.html', 'r') as myfile:
        data = myfile.read()
        return web.Response(text=data, content_type='text/html')


async def enter_game(request):
    game_id = request.match_info['game_id']
    if game_id not in active_games:
        raise web.HTTPFound('/')

    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)

    if not ws_ready.ok:

        with open('static/game.html', 'r') as myfile:
            data = myfile.read()
            return web.Response(text=data, content_type='text/html')

    await ws_current.prepare(request)
    try:
        introduction = await ws_current.receive()
        name = json.loads(introduction.data)["name"]
        await ss.register(ws_current, name, active_games[game_id])

    except Exception as exception:
        await ws_current.send_json({"type": "error", "msg": exception.__str__()})
        return

    try:
        async for message in ws_current:
            await ss.responde_to_msg(json.loads(message.data), name, active_games[game_id])

    except Exception as exception:
        await ws_current.send_json({"type": "error", "msg": exception.__str__()})

    finally:
        await ss.unregister(ws_current, name, active_games[game_id])


async def init_app():
    app = web.Application()
    app['websockets'] = {}
    app.on_shutdown.append(shutdown)
    app.router.add_get('/', index)
    app.router.add_get('/game={game_id}', enter_game)
    app.router.add_static('/', 'static/', follow_symlinks=True)

    return app


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = init_app()
    web.run_app(app, port=6789)


if __name__ == '__main__':
    main()

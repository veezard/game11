from aiohttp import web
import asyncio
import json
import logging
import src.gameplay as gm
import src.server_side as ss
import time


logging.basicConfig(filename='log.log', level=logging.DEBUG)

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
            current_game = active_games[game_id]
            response = web.Response(text=data, content_type='text/html')
            response.set_cookie(
                "room_full",
                current_game.players.game_full(),
                max_age=5)
            response.set_cookie(
                "names_logged_in",
                current_game.players.names_logged_in, max_age=5)
            response.set_cookie(
                "number_of_orphaned_names",
                current_game.players.number_of_orphaned_names(), max_age=5)
            for i in range(current_game.players.number_of_orphaned_names()):
                response.set_cookie(
                    str(i) + "_orphan",
                    current_game.players.orphaned_names()[i],
                    max_age=5)
            return response

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
        if len(active_games[game_id].players.websockets) == 0:
            await delete_game_maybe(game_id)


async def delete_game_maybe(game_id):  # Can't get asyncio.sleep to no stall
    await asyncio.sleep(5)  # set to wait 5 seconds
    if game_id in active_games and len(
            active_games[game_id].players.websockets) == 0:
        del active_games[game_id]


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

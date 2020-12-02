from aiohttp import web
import argparse
import asyncio
import json
import logging
import src.gameplay as gm
import src.server_side as ss
import time
import random
import string

logging.basicConfig(filename='log.log', level=logging.DEBUG)

active_games = {}
games_to_delete = []

letters = string.ascii_lowercase


async def index(request):
    with open('static/index.html', 'r') as myfile:
        data = myfile.read()
        response = web.Response(text=data, content_type='text/html')
        response.set_cookie("games_open", len(active_games), max_age=30)
        return response


async def create_new_game(request):
    new_game = ''.join(random.choice(letters) for i in range(20))
    while new_game in active_games:
        new_game = ''.join(random.choice(letters) for i in range(20))
    active_games[new_game] = gm.Gameplay()
    raise web.HTTPFound('/game=' + new_game)


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


def init_app():
    app = web.Application()
    app['websockets'] = {}
    app.on_shutdown.append(shutdown)
    app.router.add_get('/', index)
    app.router.add_post('/', create_new_game)
    app.router.add_get('/game={game_id}', enter_game)
    app.router.add_static('/', 'static/', follow_symlinks=True)
    return app


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


async def games_cleanup_routine():
    while True:
        await asyncio.sleep(600)
        games_cleanup()


def games_cleanup():
    for game in games_to_delete:
        if game in active_games and (
                len(active_games[game].players.websockets) == 0):
            del active_games[game]
    games_to_delete.clear()
    for game in active_games:
        if len(active_games[game].players.websockets) == 0:
            games_to_delete.append(game)


async def main(is_port: bool, destination):

    logging.basicConfig(level=logging.WARNING)
    app = init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    if is_port:
        site = web.TCPSite(runner, port=destination)
    else:
        site = web.UnixSite(runner, path=destination)
    await site.start()
    await games_cleanup_routine()

    while True:
        await asyncio.sleep(5)  # sleep forever

parser = argparse.ArgumentParser(description="Game 11")
parser.add_argument('--path')
parser.add_argument('--port')

if __name__ == '__main__':
    args = parser.parse_args()
    if args.port:
        asyncio.run(main(True, args.port))
    elif args.path:
        asyncio.run(main(False, args.path))
    else:
        print("Please provide a port or a path for unix socket")

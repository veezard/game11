from aiohttp import web
import asyncio
import json
import logging
from . import gameplay as gm


async def register(ws, name, game: gm.Gameplay):  # response to a new user entering

    if game.players.game_full():
        raise Exception("The game is full")
    tmp = game.players.register(ws, name)

    if tmp == -1:
        raise Exception("User already logged in")
    elif tmp == -2:
        raise Exception(
            "The room is full. If you are returning to the game, use the same name.")
    elif tmp == 0 and len(game.players.names) == 3:
        await send_users(name, game)
        await send_refresh(name, game)
    elif tmp == 1 and len(game.players.names) == 3:
        await start_game(game)


async def start_game(game: gm.Gameplay):

    await send_users_to_all(game)
    game.initialize()
    game.deal()
    game.initial_four()
    await refresh_all(game)


async def send_users_to_all(game: gm.Gameplay):
    for name in game.players.websockets:
        await send_users(name, game)


async def send_users(name, game: gm.Gameplay):
    await game.players.websockets[name].send_json({"type": 'users', "l_user": game.players.next_name(name), "r_user": game.players.previous_name(name)})


async def unregister(ws, name, game: gm.Gameplay):  # response to a user leaving

    del game.players.websockets[name]


# respond to a message coming from user.
async def responde_to_msg(message, name, game: gm.Gameplay):

    # cards coming from the server are encoded as (-1,1) if there is no card
    # and (-2,-2) if it is flipped over

    if (message['type'] == "__ping__"):
        await game.players.websockets[name].send_json({"type": "__pong__"})

    elif (message['type'] == "refresh"):
        await send_refresh(name, game)

    elif (message['type'] == "turn_data" and game.players.number_from_name(name) == game.turn_counter.turn):

        game.turn_data['player_card_selected'] = (
            message['data']['c_card_selected'])
        if game.turn_data['player_card_selected'] != -1:
            game.can_undo = False
        game.turn_data['t_cards_selected'] = message['data'][
            't_cards_selected'][:]
        for nm in game.players.websockets:
            if nm != name:
                await send_refresh(nm, game)

    elif (message['type'] == "undo"):
        if not game.can_undo:
            return
        else:
            game.undo()
            game.can_undo = False
            await refresh_all(game)

    elif (message['type'] == "play_hand"):
        if name != game.players.names[game.turn_counter.turn]:
            await game.players.websockets[name].send_json({"type": "alert", "msg": "Something went wrong. Please reload the page."})
            game.restart_turn()
            await refresh_all(game)
            return

        response = game.play_hand()
        if response == 1:
            await game.players.websockets[name].send_json({"type": "alert", "msg": "The move is invalid"})
            await refresh_all(game)

        elif response == 2:  # regular end of turn
            game.can_undo = True
            await refresh_all(game)
        elif response == 3:  # cards need to be redealt
            game.can_undo = True
            await refresh_all(game)

    elif (message['type'] == "deal"):
        if not game.dealer_neeeds_to_advance:
            return
        else:
            if not game.deal():
                game.move_table_to_dealer()
                round_scores = game.scores()
                game.update_score(round_scores)
                game.update_last_round_hands()
                game.dealer_counter.advance()
                game.can_undo = False
                game.dealer_neeeds_to_advance = False
                await start_game(game)
                await open_score_all(game)
            else:
                game.dealer_neeeds_to_advance = False
                game.can_undo = False
                await refresh_all(game)


async def send_refresh(name, game: gm.Gameplay):
    player_number = game.players.number_from_name(name)
    next_player = (player_number + 1) % 3
    previous_player = (player_number - 1) % 3
    c_player_cards = [None] * 4
    l_player_cards = [None] * 4
    r_player_cards = [None] * 4
    t_cards = [None] * 52

    # fill player card objects with pairs (i,j) corresponding to cards or lack
    # themof.
    for i in range(4):
        card = game.players_hands[player_number][i]
        if (card is not None):
            c_player_cards[i] = (card.suit, card.number)
        else:
            c_player_cards[i] = (-1, -1)

        card = game.players_hands[next_player][i]
        if (card is not None):
            l_player_cards[i] = (-2, -2)
        else:
            l_player_cards[i] = (-1, -1)

        card = game.players_hands[previous_player][i]
        if (card is not None):
            r_player_cards[i] = (-2, -2)
        else:
            r_player_cards[i] = (-1, -1)

    for i in range(52):
        card = game.table[i]
        if (card is not None):
            t_cards[i] = (card.suit, card.number)
        else:
            t_cards[i] = (-1, -1)


# Display the card the current player chose

    if (game.turn_data['player_card_selected'] != -1):

        if (next_player == game.turn_counter.turn):

            card = game.players_hands[game.turn_counter.turn][
                game.turn_data['player_card_selected']]
            if (card is not None):
                l_player_cards[game.turn_data['player_card_selected']] = (
                    card.suit, card.number)
            else:
                l_player_cards[game.turn_data['player_card_selected']
                               ] = (-1, -1)

        if previous_player == game.turn_counter.turn:
            card = game.players_hands[game.turn_counter.turn][
                game.turn_data['player_card_selected']]
            if (card is not None):
                r_player_cards[game.turn_data['player_card_selected']] = (
                    card.suit, card.number)
            else:
                r_player_cards[game.turn_data['player_card_selected']
                               ] = (-1, -1)

    # computing pile_ends. Recall that the first element of
    # game.players_piles[player] holds the number of the last taken hand
    pile_ends = [None] * 3
    for i in range(3):

        number_of_last_hand = game.players_piles[i][0]
        pile_ends[i] = game.players_piles[i][-number_of_last_hand:]
        for j in range(number_of_last_hand):
            card = pile_ends[i][j]
            pile_ends[i][j] = (card.suit, card.number)

    await game.players.websockets[name].send_json({"type": "refresh",
                                                   "c_player": c_player_cards,
                                                   "l_player": l_player_cards,
                                                   "r_player": r_player_cards,
                                                   "table_cards": t_cards,
                                                   "turn": (game.turn_counter.turn - player_number) % 3,
                                                   "dealer": (game.dealer_counter.turn - player_number) % 3,
                                                   "turn_data": game.turn_data,
                                                   "deck_size": len(game.deck),
                                                   "pile_sizes": rotate_list([len(game.players_piles[i]) - 1 for i in range(3)], player_number),
                                                   "pile_ends": rotate_list(pile_ends, player_number),
                                                   "score": rotate_list(game.score, player_number),
                                                   "last_round_score": rotate_list(game.last_round_score, player_number),
                                                   "last_round_hands": rotate_list(game.last_round_hands, player_number),
                                                   "can_undo": game.can_undo and next_player == game.turn_counter.turn
                                                   })


async def refresh_all(game: gm.Gameplay):
    for name in game.players.websockets:
        await send_refresh(name, game)


async def open_score_all(game: gm.Gameplay):
    for name in game.players.websockets:
        await game.players.websockets[name].send_json({"type": "show_score"})


def rotate_list(l: list, rotate_by):
    if rotate_by >= len(l):
        return None
    else:
        return l[rotate_by:] + l[:rotate_by]

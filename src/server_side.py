async def register(ws, name, app):  # response to a new user entering

    if name != "D" and name != "M" and name != "N":
        raise Exception("Wrong name")

    elif name in app['websockets']:
        raise Exception("User already logged in")
    else:
        app['websockets'][name] = ws

        if (not (name in players_dict)):
            player_number = int(len(players_dict) / 2)
            players_dict[name] = player_number
            players_dict[player_number] = name

            if (len(players_dict) == 6):
                for name in app['websockets']:
                    await send_users(name, app)
                await start_game(app)
        else:
            if (len(players_dict) == 6):
                await send_refresh(name, app)
                for name in app['websockets']:
                    await send_users(name, app)


async def start_game(app):

    Gameplay.initialize()
    Gameplay.deal()
    Gameplay.initial_four()
    await refresh_all(app)


async def send_users(name, app):

    await app['websockets'][name].send_json({"type": 'users', "l_user": players_dict[(players_dict[name] + 1) % 3], "r_user": players_dict[(players_dict[name] + 2) % 3]})


async def unregister(ws, name, app):  # response to a user leaving

    del app['websockets'][name]


# respond to a message coming from user.
async def responde_to_msg(message, name, app):

    global can_undo
# cards coming from the server are encoded as (-1,1) if there is no card
# and (-2,-2) if it is flipped over

    if (message['type'] == "__ping__"):
        await app['websockets'][name].send_json({"type": "__pong__"})

    elif (message['type'] == "refresh"):
        await send_refresh(name, app)

    elif (message['type'] == "turn_data" and players_dict[name] == Gameplay.turn_counter.turn):

        Gameplay.turn_data['player_card_selected'] = (
            message['data']['c_card_selected'])
        if Gameplay.turn_data['player_card_selected'] != -1:
            can_undo = False
        Gameplay.turn_data['t_cards_selected'] = message['data'][
            't_cards_selected'][:]
        for nm in app['websockets']:
            if nm != name:
                await send_refresh(nm, app)

    elif (message['type'] == "undo"):
        if not can_undo:
            return
        else:
            Gameplay.undo()
            can_undo = False
            await refresh_all(app)

    elif (message['type'] == "play_hand"):
        if name != players_dict[Gameplay.turn_counter.turn]:
            await app['websockets'][name].send_json({"type": "alert", "msg": "Something went wrong. Please reload the page."})
            Gameplay.restart_turn()
            await refresh_all(app)
            return

        response = Gameplay.play_hand()
        if response == 1:
            await app['websockets'][name].send_json({"type": "alert", "msg": "The move is invalid"})
            await refresh_all(app)

        elif response == 2:  # regular end of turn
            can_undo = True
            await refresh_all(app)
        elif response == 3:  # cards need to be redealt
            can_undo = True
            await refresh_all(app)

    elif (message['type'] == "deal"):
        if not Gameplay.dealer_neeeds_to_advance:
            return
        else:
            if not Gameplay.deal():
                Gameplay.move_table_to_dealer()

                round_scores = Gameplay.scores()
                update_score(round_scores)
                update_last_round_hands()
                rotate_players()
                can_undo = False
                Gameplay.dealer_neeeds_to_advance = False
                await start_game(app)
                await open_score_all(app)
            else:
                Gameplay.dealer_neeeds_to_advance = False
                can_undo = False
                await refresh_all(app)


async def send_refresh(name, app):
    c_player_cards = [None] * 4
    l_player_cards = [None] * 4
    r_player_cards = [None] * 4
    t_cards = [None] * 52

    # fill player card objects with pairs (i,j) corresponding to cards or lack
    # themof.
    for i in range(4):
        card = Gameplay.players_hands[players_dict[name]][i]
        if (card is not None):
            c_player_cards[i] = (card.suit, card.number)
        else:
            c_player_cards[i] = (-1, -1)

        card = Gameplay.players_hands[((players_dict[name] + 1) % 3)][i]
        if (card is not None):
            l_player_cards[i] = (-2, -2)
        else:
            l_player_cards[i] = (-1, -1)

        card = Gameplay.players_hands[((players_dict[name] + 2) % 3)][i]
        if (card is not None):
            r_player_cards[i] = (-2, -2)
        else:
            r_player_cards[i] = (-1, -1)

    for i in range(52):
        card = Gameplay.table[i]
        if (card is not None):
            t_cards[i] = (card.suit, card.number)
        else:
            t_cards[i] = (-1, -1)


# Display the card the current player chose

    if (Gameplay.turn_data['player_card_selected'] != -1):

        if ((players_dict[name] + 1) % 3 == Gameplay.turn_counter.turn):

            card = Gameplay.players_hands[Gameplay.turn_counter.turn][
                Gameplay.turn_data['player_card_selected']]
            if (card is not None):
                l_player_cards[Gameplay.turn_data['player_card_selected']] = (
                    card.suit, card.number)
            else:
                l_player_cards[Gameplay.turn_data['player_card_selected']
                               ] = (-1, -1)

        if ((players_dict[name] + 2) % 3 == Gameplay.turn_counter.turn):
            card = Gameplay.players_hands[Gameplay.turn_counter.turn][
                Gameplay.turn_data['player_card_selected']]
            if (card is not None):
                r_player_cards[Gameplay.turn_data['player_card_selected']] = (
                    card.suit, card.number)
            else:
                r_player_cards[Gameplay.turn_data['player_card_selected']
                               ] = (-1, -1)

    # computing pile_ends. Recall that the first element of
    # Gameplay.players_piles[player] holds the number of the last taken hand
    pile_ends = [None] * 3
    for i in range(3):

        number_of_last_hand = Gameplay.players_piles[i][0]
        pile_ends[i] = Gameplay.players_piles[i][-number_of_last_hand:]
        for j in range(number_of_last_hand):
            card = pile_ends[i][j]
            pile_ends[i][j] = (card.suit, card.number)

    pile_ends = pile_ends[players_dict[name]:] + pile_ends[:players_dict[name]]

    await app['websockets'][name].send_json({"type": "refresh",
                                             "c_player": c_player_cards,
                                             "l_player": l_player_cards,
                                             "r_player": r_player_cards,
                                             "table_cards": t_cards,
                                             "turn": (Gameplay.turn_counter.turn - players_dict[name]) % 3,
                                             "dealer": (Gameplay.dealer_counter.turn - players_dict[name]) % 3,
                                             "turn_data": Gameplay.turn_data,
                                             "deck_size": len(Gameplay.deck),
                                             "pile_sizes": [len(Gameplay.players_piles[(i + players_dict[name]) % 3]) - 1 for i in range(3)],
                                             "pile_ends": pile_ends,
                                             "score": score,
                                             "last_round_score": last_round_score,
                                             "last_round_hands": last_round_hands,
                                             "can_undo": can_undo and (players_dict[name] + 1) % 3 == Gameplay.turn_counter.turn
                                             })


async def refresh_all(app):
    for name in app['websockets']:
        await send_refresh(name, app)


async def open_score_all(app):
    for name in app['websockets']:
        await app['websockets'][name].send_json({"type": "show_score"})

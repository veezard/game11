import random
random.seed()


class Players:
    def __init__(self):
        self.names_logged_in = 0
        self.names = []
        self.websockets = {}  # dictionary {name: websocket}

    def register(self, ws, name):
        if name in self.websockets:  # Someone is already logged in with the name
            return -1
        if name in self.names:  # Someone already logged in with the name but then left. Registering new websocket to that name
            self.websockets[name] = ws
            return 0
        else:
            self.names.append(name)
            self.websockets[name] = ws
            self.names_logged_in += 1
            return 1

    def get_websocket_by_number(self, player_number):
        if player_number >= len(
                self.names) - 1:  # This shouldn't really ever happen
            return -1
        if self.names[player_number] not in self.websockets:
            return 0
        else:
            return self.websockets[self.names[player_number]]

    def orphaned_names(self):
        return [name for name in self.names if not self.websockets[name]]

    def number_from_name(self, name):
        if name in self.names:
            return self.names.index(name)
        else:
            return -1

    def next_name(self, name):
        if name not in self.names:
            return None
        else:
            return self.names[(self.names.index(name) + 1) % 3]

    def previous_name(self, name):
        if name not in self.names:
            return None
        else:
            return self.names[(self.names.index(name) - 1) % 3]

    def next_player_number(self, name):
        if name not in self.names:
            return None
        else:
            return (self.names.index(name) + 1) % 3

    def previous_player_number(self, name):
        if name not in self.names:
            return None
        else:
            return (self.names.index(name) - 1) % 3


class Gameplay:
    def __init__(self):
        # Internally to the game, the three players are 0,1,2. This is the list
        # of pairs consisting of their names and websocket
        self.players = Players()
        # Game progress keeps track of total number of turns elapsed for the
        # purpose of dealing/starting next round.
        self.game_progress = 0
        self.turn_counter = Player_counter()
        self.dealer_counter = Player_counter()
        self.deck = set()
        self.table = [None for i in range(52)]
        self.players_hands = [[None for i in range(4)] for j in range(3)]
        self.players_piles = []  # First element holds the size of previous hand
        self.cards = [[Card(j, i) for i in range(13)] for j in range(4)]
        self.turn_data = {
            "player_card_selected": -1,
            "t_cards_selected": [
                0 for i in range(52)]}
        self.last_move_card_on_table = None
        self.last_move_pile_end_size = 0
        self.dealer_neeeds_to_advance = False

        self.score = [0, 0, 0]
        self.last_round_score = [0, 0, 0]
        self.last_round_hands = [[]] * 3
        self.can_undo = False
        self.dealer_counter.turn = 0

    def initialize(self):
# Only deal 16 cards
        for i in range(1):
            self.cards[0][i].move_to(self.deck)
        # self.cards[1][1].move_to(self.deck)
        for i in range(3):
            self.cards[1][i].move_to(self.deck)
        for i in range(4):
            self.cards[2][i].move_to(self.deck)
        for i in range(4):
            self.cards[i][10].move_to(self.deck)
        for i in range(4):
            self.cards[i][9].move_to(self.deck)
        # move all cards to the deck
        # for suit in self.cards:
            # for card in suit:
            # card.move_to(self.deck)
        self.players_piles = [[0] for i in range(3)]
        self.turn_counter.turn = self.dealer_counter.turn+1

    def deal(self):
        if self.deck:  # a set evaluates to False if empty
            for player in range(3):
                for card in random.sample(self.deck, 4):
                    card.move_to(self.players_hands[player])
            return True
        else:
            return False

    def initial_four(self):
        for card in random.sample(self.deck, 4):
            card.move_to(self.table)

    def valid_move(self):
        if self.turn_data['player_card_selected'] == -1:
            return False

        card_played = self.players_hands[self.turn_counter.turn][
            self.turn_data['player_card_selected']].pair()
        cards_selected = []
        for i in range(52):
            if self.turn_data['t_cards_selected'][i] == 1:
                cards_selected.append(self.table[i].pair())

        if len(cards_selected) == 0:
            return True

        if card_played[1] == 10:  # jack takes everything below jack
            if False not in [crd[1] <= 10 for crd in cards_selected]:
                return True

        # a card below jack can only take cards if the sum of everything is 11
        if card_played[1] < 10:
            if sum([crd[1] + 1 for crd in cards_selected]
                   ) + card_played[1] + 1 == 11:
                return True

        if card_played[1] == 11 and len(
                cards_selected) == 1 and cards_selected[0][1] == 11:
            return True

        if card_played[1] == 12 and len(
                cards_selected) == 1 and cards_selected[0][1] == 12:
            return True

        return False

    def collect_cards_to_pile(self):

        cards_selected = [self.table[i] for i in range(
            52) if self.turn_data['t_cards_selected'][i] == 1]
        turn = self.turn_counter.turn
        c_card_selected_number = self.turn_data['player_card_selected']
        c_card_selected = self.players_hands[turn][c_card_selected_number]
        if len(cards_selected) == 0:
            if c_card_selected.number == 10:
                c_card_selected.move_to(self.players_piles[turn])
                self.last_move_pile_end_size = self.players_piles[turn][0]
                self.players_piles[turn][0] = 1
                self.last_move_card_on_table = None
            else:
                c_card_selected.move_to(self.table)
                self.last_move_card_on_table = c_card_selected
            return
        else:
            self.last_move_pile_end_size = self.players_piles[turn][0]
            self.players_piles[turn][0] = len(cards_selected) + 1
            c_card_selected.move_to(self.players_piles[turn])
            for card in cards_selected:
                card.move_to(self.players_piles[turn])

            self.last_move_card_on_table = None

    def restart_turn(self):
        self.turn_data["player_card_selected"] = -1
        for i in range(52):
            self.turn_data["t_cards_selected"][i] = 0

    def play_hand(self):
        if not self.valid_move():
            self.restart_turn()
            return 1  # 1: Move not valid

        self.collect_cards_to_pile()
        self.turn_counter.advance()
        self.game_progress = self.game_progress + 1
        self.restart_turn()
        if self.game_progress % 12 != 0:
            return 2  # 2: regular end of turn

        else:
            self.dealer_neeeds_to_advance = True
            return 3  # dealers input is necessary

    def move_table_to_dealer(self):
        """ Move all the cards on the table to the dealers pile. This happens at the end of the game."""
        for card in self.table:
            if card is not None:
                card.move_to(self.players_piles
                             [self.dealer_counter.turn])

    def scores(self):

        number_of_cards_collected = [len(cards) - 1
                                     for cards in self.players_piles]
        number_of_clubs_collected = [len([card for card in cards if not isinstance(
            card, int) and card.suit == 1]) for cards in self.players_piles]

        player_w_2_of_clubs = [
            i for i in range(3)
            if self.cards[1][1].location == self.players_piles[i]][0]
        player_w_10_of_diamonds = [
            i for i in range(3)
            if self.cards[3][9].location == self.players_piles[i]][0]

        point_for_2_of_clubs = [0] * 3
        point_for_2_of_clubs[player_w_2_of_clubs] = 1
        point_for_10_of_diamonds = [0] * 3
        point_for_10_of_diamonds[player_w_10_of_diamonds] = 1

        points_for_max_cards = [(1 if (number_of_cards_collected[i] == max(
            number_of_cards_collected)) else 0) for i in range(3)]
        points_for_max_clubs = [(1 if (number_of_clubs_collected[i] == max(
            number_of_clubs_collected)) else 0) for i in range(3)]

        return [
            a + b + c + d for a,
            b,
            c,
            d in zip(
                point_for_2_of_clubs,
                point_for_10_of_diamonds,
                points_for_max_cards,
                points_for_max_clubs)]

    def undo(self):

        self.turn_counter.turn = (self.turn_counter.turn - 1) % 3
        self.game_progress = self.game_progress - 1
        if self.last_move_card_on_table is not None:
            self.last_move_card_on_table.move_to(
                self.players_hands[self.turn_counter.turn])
            self.last_move_card_on_table = None

        else:
            # of cards to move back from the pile to the table
            cards_to_move_back = self.players_piles[self.turn_counter.turn][0] - 1
            for i in range(cards_to_move_back):
                self.players_piles[self.turn_counter.turn][-i - 1].move_to(
                    self.table)

            self.players_piles[self.turn_counter.turn][-cards_to_move_back - 1].move_to(
                self.players_hands[self.turn_counter.turn])
            self.players_piles[self.turn_counter.turn][:] = self.players_piles[self.turn_counter.turn][:(
                -cards_to_move_back - 1)]
            self.players_piles[self.turn_counter.turn][0] = self.last_move_pile_end_size

        self.restart_turn()

    def update_score(self, scores):
        for i in range(3):
            self.last_round_score[i] = scores[i]
            self.score[i] += scores[i]

    def update_last_round_hands(self):

        for i in range(3):
            self.last_round_hands[i] = []
        for i in range(3):
            for j in range(len(self.players_piles[i]) - 1):
                self.last_round_hands[i].append(
                    self.players_piles[i][j + 1].pair())


class Player_counter:
    def __init__(self):
        self.turn = 0

    def advance(self):
        self.turn = (self.turn + 1) % 3


class Card:
    def __init__(self, i, j):
        self.suit = i
        self.number = j
        self.location = None

    def move_to(self, location):
        if self.location is not None:
            if (isinstance(self.location, list)):
                self.location[self.location.index(self)] = None
            if (isinstance(self.location, set)):
                self.location.discard(self)

        if (isinstance(location, list)):
            try:
                location[location.index(None)] = self
            except BaseException:
                location.append(self)
        if (isinstance(location, set)):
            location.add(self)

        self.location = location

    def pair(self):
        return [self.suit, self.number]

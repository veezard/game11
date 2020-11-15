import random
random.seed()


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


class Gameplay:
    game_progress = 0
    turn_counter = Player_counter()
    dealer_counter = Player_counter()
    deck = set()
    table = [None for i in range(52)]
    players_hands = [[None for i in range(4)] for j in range(3)]
    players_piles = []  # First element holds the size of previous hand
    cards = [[Card(j, i) for i in range(13)] for j in range(4)]
    turn_data = {
        "player_card_selected": -1,
        "t_cards_selected": [
            0 for i in range(52)]}
    last_move_card_on_table = None
    last_move_pile_end_size = 0
    dealer_neeeds_to_advance = False

    def initialize(self):

        # move all cards to the deck
        for suit in Gameplay.cards:
            for card in suit:
                card.move_to(Gameplay.deck)


# Only deal 16 cards
#		for i in range(1):
#			Gameplay.cards[0][i].move_to(Gameplay.deck)
#		#Gameplay.cards[1][1].move_to(Gameplay.deck)
#		for i in range(3):
#			Gameplay.cards[1][i].move_to(Gameplay.deck)
#		for i in range(4):
#			Gameplay.cards[2][i].move_to(Gameplay.deck)
#		for i in range(4):
#			Gameplay.cards[i][10].move_to(Gameplay.deck)
#		for i in range(4):
#			Gameplay.cards[i][9].move_to(Gameplay.deck)

        Gameplay.players_piles = [[0] for i in range(3)]
        Gameplay.turn_counter.turn = 1
        Gameplay.dealer_counter.turn = 0
        Gameplay.game_progress = 0
        Gameplay.restart_turn()

    def deal(self):
        if Gameplay.deck:
            for player in range(3):
                for card in random.sample(Gameplay.deck, 4):
                    card.move_to(Gameplay.players_hands[player])
            return True
        else:
            return False

    def is_valid_move(card_played, cards_selected, player):
        if (player != Gameplay.turn_counter.turn):
            return False
        if (card_played.number == 12):
            card_played.move_to(Gameplay.players_piles[player])
            for card in cards_selected:
                card.move_to(Gameplay.players_piles[player])
            return True
        elif(cards_selected.length == 0):
            card_played.move_to(Gameplay.table)
            return True

        else:
            return False

    def initial_four():
        for card in random.sample(Gameplay.deck, 4):
            card.move_to(Gameplay.table)

    def valid_move():
        if Gameplay.turn_data['player_card_selected'] == -1:
            return False

        card_played = Gameplay.players_hands[Gameplay.turn_counter.turn][
            Gameplay.turn_data['player_card_selected']].pair()
        cards_selected = []
        for i in range(52):
            if Gameplay.turn_data['t_cards_selected'][i] == 1:
                cards_selected.append(Gameplay.table[i].pair())

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

    def collect_cards_to_pile():

        cards_selected = [Gameplay.table[i] for i in range(
            52) if Gameplay.turn_data['t_cards_selected'][i] == 1]
        turn = Gameplay.turn_counter.turn
        c_card_selected_number = Gameplay.turn_data['player_card_selected']
        c_card_selected = Gameplay.players_hands[turn][c_card_selected_number]
        if len(cards_selected) == 0:
            if c_card_selected.number == 10:
                c_card_selected.move_to(Gameplay.players_piles[turn])
                Gameplay.last_move_pile_end_size = Gameplay.players_piles[turn][0]
                Gameplay.players_piles[turn][0] = 1
                Gameplay.last_move_card_on_table = None
            else:
                c_card_selected.move_to(Gameplay.table)
                Gameplay.last_move_card_on_table = c_card_selected
            return
        else:
            Gameplay.last_move_pile_end_size = Gameplay.players_piles[turn][0]
            Gameplay.players_piles[turn][0] = len(cards_selected) + 1
            c_card_selected.move_to(Gameplay.players_piles[turn])
            for card in cards_selected:
                card.move_to(Gameplay.players_piles[turn])

            Gameplay.last_move_card_on_table = None

    def restart_turn():
        Gameplay.turn_data["player_card_selected"] = -1
        for i in range(52):
            Gameplay.turn_data["t_cards_selected"][i] = 0

    def play_hand():
        if not Gameplay.valid_move():
            Gameplay.restart_turn()
            return 1  # 1: Move not valid

        Gameplay.collect_cards_to_pile()
        Gameplay.turn_counter.advance()
        Gameplay.game_progress = Gameplay.game_progress + 1
        Gameplay.restart_turn()
        if Gameplay.game_progress % 12 != 0:
            return 2  # 2: regular end of turn

        else:
            Gameplay.dealer_neeeds_to_advance = True
            return 3  # dealers input is necessary

    def move_table_to_dealer():
        for card in Gameplay.table:
            if card is not None:
                card.move_to(Gameplay.players_piles
                             [Gameplay.dealer_counter.turn])

    def scores():

        points = []
        number_of_cards_collected = [len(cards) - 1
                                     for cards in Gameplay.players_piles]
        number_of_clubs_collected = [len([card for card in cards if not isinstance(
            card, int) and card.suit == 1]) for cards in Gameplay.players_piles]

        player_w_2_of_clubs = [
            i for i in range(3)
            if Gameplay.cards[1][1].location == Gameplay.players_piles[i]][0]
        player_w_10_of_diamonds = [
            i for i in range(3)
            if Gameplay.cards[3][9].location == Gameplay.players_piles[i]][0]

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

    def undo():

        Gameplay.turn_counter.turn = (Gameplay.turn_counter.turn - 1) % 3
        Gameplay.game_progress = Gameplay.game_progress - 1
        if Gameplay.last_move_card_on_table is not None:
            Gameplay.last_move_card_on_table.move_to(
                Gameplay.players_hands[Gameplay.turn_counter.turn])
            Gameplay.last_move_card_on_table = None

        else:
            # of cards to move back from the pile to the table
            cards_to_move_back = Gameplay.players_piles[Gameplay.turn_counter.turn][0] - 1
            for i in range(cards_to_move_back):
                Gameplay.players_piles[Gameplay.turn_counter.turn][-i - 1].move_to(
                    Gameplay.table)

            Gameplay.players_piles[Gameplay.turn_counter.turn][-cards_to_move_back - 1].move_to(
                Gameplay.players_hands[Gameplay.turn_counter.turn])
            Gameplay.players_piles[Gameplay.turn_counter.turn][:
                                                               ] = Gameplay.players_piles[Gameplay.turn_counter.turn][:(-cards_to_move_back - 1)]
            Gameplay.players_piles[Gameplay.turn_counter.turn][0] = Gameplay.last_move_pile_end_size

        Gameplay.restart_turn()


score = {"D": 0, "M": 0, "N": 0}
last_round_score = {"D": 0, "M": 0, "N": 0}
last_round_hands = {"D": [], "M": [], "N": []}
can_undo = False


def update_score(scores):

    for i in range(3):
        last_round_score[players_dict[i]] = scores[i]
        score[players_dict[i]] += scores[i]


def rotate_players():

    for nm in ["D", "M", "N"]:
        players_dict[nm] = (players_dict[nm] - 1) % 3

    for nm in ["D", "M", "N"]:
        players_dict[players_dict[nm]] = nm


def update_last_round_hands():

    for nm in {"D", "M", "N"}:
        last_round_hands[nm] = []
    for i in range(3):
        for j in range(len(Gameplay.players_piles[i]) - 1):

            last_round_hands[players_dict[i]].append(
                Gameplay.players_piles[i][j + 1].pair())

import logging

from card import PURPLE_CARD, YELLOW_CARD


HEADER = "－－－《{text}》－－－\n"


def display_name(user):
    """ Get the current players name including their username, if possible """
    user_name = user.first_name
    if user.username:
        user_name += "（@" + user.username + "）"
    return user_name


def make_other_players_notif(game) -> str:
    """Make the notification message without current player"""
    players = game.players
    players.remove(game.current_player)
    text = HEADER.format(text="黃牌")
    for p in players:
        text += display_name(p.user) + "\n"
    text += f"請依序打出 {game.board.purple.space} 張 {YELLOW_CARD}！"
    return text


def make_current_settlement(game) -> str:
    text = HEADER.format(text="分數")
    for p in game.players:
        text += display_name(p.user) + f"（{-p.score} 張 {YELLOW_CARD}）\n"
    return text.rstrip()


def make_settlement(game) -> str:
    text = HEADER.format(text="結束")
    players = game.players
    highest, lowest = float("-inf"), 0
    for p in players:
        if p.score > highest:
            highest = p.score
        if p.score < lowest:
            lowest = p.score

    for p in players:
        # prepend emoji to player
        if p.score == highest:
            text += "🏆 "
        elif p.score == lowest:
            text += "👎 "
        else:
            text += "👍 "
        text += f"{display_name(p.user)}（{-p.score} 張 {YELLOW_CARD}）\n"
    return text.rstrip()


def make_card_players(game, num: int) -> str:
    text = HEADER.format(text="裁決")
    text += f"{display_name(game.current_player.user)}選的是 {num}\n"
    for idx, p in game.board.get_players():
        text += f"{idx}：{display_name(p.user)}\n"
    return text.rstrip()


def make_game_start(game) -> str:
    text = HEADER.format(text="開始")
    text += display_name(game.current_player.user) + f"請打一張 {PURPLE_CARD}"
    return text


def make_loser_discard(game) -> str:
    text = HEADER.format(text="換牌")
    text += display_name(game.board.loser.user) + "你剛剛輸了\n"
    text += "你可以選擇換 1 至 2 張牌，或不換牌\n"
    return text


def make_room_info(game) -> str:
    text = HEADER.format("房間")
    others = [p.user for p in game.players]
    others.remove(game.starter)
    text = f"房主：{game.starter}\n"
    for u in others:
        text += display_name(u) + "\n"
    return text.rstrip()

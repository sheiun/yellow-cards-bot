from telegram import InlineQueryResultArticle
from telegram import InlineQueryResultCachedSticker as Sticker
from telegram import InputTextMessageContent

from card import YELLOW_CARD


def add_purple_cards(results, game: "Game"):
    """Add purple cards"""
    for card in game.purple_deck.cards[-2:]:
        results.append(
            Sticker("purple" + str(card), sticker_file_id=card.sticker["file_id"])
        )


def add_cards(results, player, can_play):
    """Add player's cards"""
    if can_play:
        content = "打出了一張 " + YELLOW_CARD
        prefix = "yellow"
    else:
        content = f"我想打出一張 {YELLOW_CARD} 但被阻止ㄌ"
        prefix = ""
    for card in player.cards:
        results.append(
            Sticker(
                prefix + str(card),
                sticker_file_id=card.sticker["file_id"],
                input_message_content=InputTextMessageContent(content),
            )
        )


def add_no_game(results):
    """Add text result if user is not playing"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title="你沒在玩ㄡ",
            input_message_content=InputTextMessageContent("趕快加入遊戲好ㄇ"),
        )
    )


def add_not_started(results):
    """Add text result if the game has not yet started"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title="還沒開始ㄡ",
            input_message_content=InputTextMessageContent("趕快按開始ㄅ"),
        )
    )


def add_gameinfo(game, results):
    """Add option to show game info"""

    # TODO: show 每個人獲得幾張黃牌
    pass


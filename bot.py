import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    Filters,
    InlineQueryHandler,
    MessageHandler,
    Updater,
)
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from card import PURPLE, PURPLE_CARD, YELLOW, YELLOW_CARD, Card
from config import MIN_PLAYERS, TOKEN, WORKERS
from errors import (
    AlreadyJoinedError,
    DeckEmptyError,
    LobbyClosedError,
    NoGameInChatError,
    NotEnoughPlayersError,
)
from game_manager import GameManager
from results import (
    add_cards,
    add_gameinfo,
    add_no_game,
    add_not_started,
    add_purple_cards,
)
from utils import (
    display_name,
    make_card_players,
    make_current_settlement,
    make_other_players_notif,
    make_settlement,
)

logging.basicConfig(
    format="%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Room:
    def __init__(self, updater: Updater):
        self.updater = updater
        self.handlers = [
            InlineQueryHandler(self.reply_query, run_async=True),
            ChosenInlineResultHandler(self.process_result, run_async=True),
            CallbackQueryHandler(self.select_loser, run_async=True),
            CommandHandler("new", self.new, run_async=True),
            CommandHandler("kill", self.kill, run_async=True),
            CommandHandler("join", self.join, run_async=True),
            CommandHandler("leave", self.leave, run_async=True),
            CommandHandler("start", self.start, run_async=True),
            MessageHandler(Filters.status_update, self.leave_group),
        ]
        self.register()

    def register(self):
        for handler in self.handlers:
            self.updater.dispatcher.add_handler(handler)
        self.updater.dispatcher.add_error_handler(self.error)

    def new(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if games:
            game = games[-1]
            if game.started and len(game.players) >= MIN_PLAYERS:
                return context.bot.send_message(
                    chat.id,
                    text="已經開始ㄌ",
                    reply_to_message_id=update.message.message_id,
                )

        game = gm.new_game(update.message.chat)
        game.starter = update.message.from_user
        context.bot.send_message(
            chat.id, text="幫你開ㄌ", reply_to_message_id=update.message.message_id,
        )

    def kill(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if not games:
            return

        user = update.message.from_user
        if user.username == "sheiun":
            try:
                gm.end_game(chat, user)
                text = "遊戲終了！"
            except NoGameInChatError:
                return
        else:
            text = "你沒有權限"
        context.bot.send_message(
            chat.id, text=text, reply_to_message_id=update.message.message_id
        )

    def join(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        try:
            gm.join_game(update.message.from_user, chat)
        except LobbyClosedError:
            text = "關房了"
        except NoGameInChatError:
            text = "沒房ㄌ"
        except AlreadyJoinedError:
            text = "已經加入ㄌ拉"
        except DeckEmptyError:
            text = "牌不夠ㄌ"
        else:
            text = "加入成功ㄌ"
        context.bot.send_message(
            chat.id, text=text, reply_to_message_id=update.message.message_id,
        )

    def leave(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        user = update.message.from_user

        player = gm.player_for_user_in_chat(user, chat)
        if player is None:
            text = "你不在遊戲內ㄡ"
        else:
            game = player.game
            try:
                gm.leave_game(user, chat)
            except NoGameInChatError:
                text = "你不在遊戲內ㄡ"
            except NotEnoughPlayersError:
                text = "遊戲結束ㄌ"
            else:
                if game.started:
                    text = f"好ㄉ。下位玩家 {display_name(game.current_player.user)}"
                else:
                    text = f"{display_name(user)} 離開ㄌ"
        context.bot.send_message(
            chat.id, text=text, reply_to_message_id=update.message.message_id,
        )

    def start(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return
        text = ""
        try:
            game = gm.chatid_games[chat.id][-1]
        except (KeyError, IndexError):
            text = "還沒開房ㄡ"
        else:
            if game.started:
                text = "已經開始ㄌㄡ"
            elif len(game.players) < MIN_PLAYERS:
                text = f"至少要 {MIN_PLAYERS} 人才能開ㄡ"
            else:
                game.start()
                context.bot.send_message(
                    chat.id, text=make_game_start(game), reply_markup=choice
                )
                return

        context.bot.send_message(
            chat.id, text=text, reply_to_message_id=update.message.message_id
        )

    def leave_group(self, update: Update, context: CallbackContext):
        chat = update.message.chat

        if update.message.left_chat_member:
            user = update.message.left_chat_member

            try:
                gm.leave_game(user, chat)
            except NoGameInChatError:
                return
            except NotEnoughPlayersError:
                gm.end_game(chat, user)
                text = "遊戲終了！"
            else:
                text = display_name(user) + " 被踢出遊戲ㄌ"
            context.bot.send_message(chat.id, text=text)

    def reply_query(self, update: Update, context: CallbackContext):
        results = []

        user = update.inline_query.from_user
        try:
            player = gm.userid_current[user.id]
        except KeyError:
            add_no_game(results)
        else:
            game = player.game
            if not game.started:
                add_not_started(results)

            elif user.id == game.current_player.user.id:
                if game.board.purple is not None:
                    add_cards(results, player, can_play=player.can_play)
                else:
                    add_purple_cards(results, game)
            else:
                add_cards(results, player, can_play=player.can_play)
        context.bot.answer_inline_query(update.inline_query.id, results, cache_time=0)

    def process_result(self, update: Update, context: CallbackContext):
        user = update.chosen_inline_result.from_user
        result_id = update.chosen_inline_result.result_id
        try:
            player = gm.userid_current[user.id]
            game = player.game
            chat = game.chat
        except (KeyError, AttributeError):
            return
        if result_id in ("hand", "gameinfo", "nogame"):
            return
        if result_id.isdigit() and len(result_id) == 19:
            return
        elif result_id.startswith(PURPLE):
            card = Card.from_id(result_id.replace(PURPLE, ""))
            player.play(card)
            # NOTE: notify other players to play yellow cards
            context.bot.send_message(
                chat.id, text=make_other_players_notif(game), reply_markup=choice
            )
        elif result_id.startswith(YELLOW):
            # NOTE: play card
            card = Card.from_id(result_id.replace(YELLOW, ""))
            player.play(card)

            if game.board.is_others_played:
                logger.info(game.board.get_cards())
                for idx, cards in game.board.get_cards():
                    context.bot.send_message(chat.id, text=f"第 {idx} 組")
                    # TODO: 可以把這個跟下面的整在一起
                    for card in cards:
                        context.bot.send_sticker(
                            chat.id, sticker=card.sticker["file_id"]
                        )

                # TODO: 可以直接把這個改到 send_sticker 的 replay_markup 取代 callback
                context.bot.send_message(
                    chat.id,
                    text=display_name(game.current_player.user) + "\n" + "請挑最爛ㄉ",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text=str(num), callback_data=str(num)
                                )
                                for num in range(1, len(game.players))
                            ]
                        ]
                    ),
                )

                context.bot.send_message(chat.id, text=f"這張 {PURPLE_CARD} 是剛剛的題目")
                context.bot.send_sticker(
                    chat.id, sticker=game.board.purple.sticker["file_id"]
                )
            else:
                # TODO: 這邊可以 show 所有人打牌的進度
                # context.bot.send_message(chat.id, text="")
                pass
        else:
            logger.info(f"Result: {result_id} is run into else clause!")
            # The card cannot be played

    def select_loser(self, update: Update, context: CallbackContext):
        chat = update.callback_query.message.chat
        user = update.callback_query.from_user
        try:
            player = gm.userid_current[user.id]
            game = player.game
        except (KeyError, AttributeError):
            return
        if player != game.current_player:
            context.bot.send_message(
                chat.id, text=display_name(user) + " 你又不是出題者湊什麼熱鬧！"
            )
            return
        num = int(update.callback_query.data)

        # NOTE: resolve join midway problem
        try:
            loser = game.board.get_loser(num)
        except IndexError:
            return

        context.bot.send_message(chat.id, text=make_card_players(game, num))
        loser.score -= game.board.purple.space

        # NOTE: Game end check
        final_loser = game.get_loser()
        if final_loser is not None:
            gm.end_game(chat, user)
            context.bot.send_message(chat.id, text=make_settlement(game))
        else:
            game.turn()
            context.bot.send_message(chat.id, text=make_current_settlement(game))
            context.bot.send_message(
                chat.id,
                text="換下一位玩家 " + display_name(game.current_player.user),
                reply_markup=choice,
            )

    def error(self, update: Update, context: CallbackContext):
        """Simple error handler"""
        logger.exception(context.error)

    def launch(self):
        self.updater.start_polling()
        self.updater.idle()


choice = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="選牌！", switch_inline_query_current_chat="")]]
)

gm = GameManager()

Room(Updater(token=TOKEN, workers=WORKERS)).launch()

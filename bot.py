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
    TooManyCardsError,
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
    make_game_start,
    make_loser_discard,
    make_other_players_notif,
    make_room_info,
    make_settlement,
)

logging.basicConfig(
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Room:
    def __init__(self, updater: Updater):
        self.updater = updater
        self.handlers = [
            InlineQueryHandler(self.reply_query, run_async=True),
            ChosenInlineResultHandler(self.process_result, run_async=True),
            CallbackQueryHandler(self.reply_callback, run_async=True),
            CommandHandler("new", self.new, run_async=True),
            CommandHandler("kill", self.kill, run_async=True),
            CommandHandler("join", self.join, run_async=True),
            CommandHandler("leave", self.leave, run_async=True),
            CommandHandler("start", self.start, run_async=True),
            CommandHandler("info", self.info, run_async=True),
            MessageHandler(Filters.status_update, self.leave_group, run_async=True),
        ]
        self.register()

    def register(self):
        for handler in self.handlers:
            self.updater.dispatcher.add_handler(handler)
        self.updater.dispatcher.add_error_handler(self.error)

    def info(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if games:
            game = games[-1]
            if game.ended:
                update.message.reply_text("遊戲已結束！")
            else:
                update.message.reply_text(make_room_info(game))
        else:
            update.message.reply_text("目前沒有房間！請用 /new 開房！")

    def new(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return

        games = gm.chatid_games.get(chat.id)
        if games:
            game = games[-1]
            if game.started and len(game.players) >= MIN_PLAYERS:
                text = "已經開始ㄌ用 /join 中途插入ㄅ"
            else:
                text = "房間早就開ㄌ，用 /info 查看資訊，用 /join 加入"
            update.message.reply_text(text)
            return

        game = gm.new_game(update.message.chat)
        game.starter = update.message.from_user
        update.message.reply_text("幫你開ㄌ，其他人可以用 /join 加入")
        # NOTE: auto join
        self.join(update, context)

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
        update.message.reply_text(text)

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
        update.message.reply_text(text)

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
        update.message.reply_text(text)

    def start(self, update: Update, context: CallbackContext):
        chat = update.message.chat
        if chat.type == "private":
            return
        text = ""
        markup = None
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
                text = make_game_start(game)
                markup = choice
                context.bot.send_message(chat.id, text=make_room_info(game))
        update.message.reply_text(text, reply_markup=markup)

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
                    add_cards(results, player)
                else:
                    add_purple_cards(results, game)
            else:
                add_cards(results, player)
        update.inline_query.answer(results, cache_time=0)

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
            # NOTE: play a yellow card
            card = Card.from_id(result_id)
            if game.state == game.State.PURPLE:
                if player != game.current_player:
                    context.bot.send_message(
                        chat.id,
                        text=display_name(user) + "你現在不能出黃牌",
                        reply_to_message_id=update.chosen_inline_result.inline_message_id,
                    )
            elif game.state == game.State.YELLOW:
                if player != game.current_player:
                    try:
                        player.play(card)
                    except TooManyCardsError:
                        context.bot.send_message(
                            chat.id,
                            text=display_name(user) + "你出太多張了！",
                            reply_to_message_id=update.chosen_inline_result.inline_message_id,
                        )
                        return
                    # TODO: 需要提醒打牌成功？
                    # TODO: 如果 game.state 沒跳 show 打牌進度?

                    if game.state == game.State.LOSE:
                        context.bot.send_message(
                            chat.id, text=f"這張 {PURPLE_CARD} 是剛剛的題目"
                        )
                        context.bot.send_sticker(
                            chat.id, sticker=game.board.purple.sticker["file_id"]
                        )

                        for idx, cards in game.board.get_cards():
                            button = InlineKeyboardButton(
                                text=f"🔼 第 {idx} 組 🔼", callback_data=str(idx)
                            )
                            last_card = cards.pop()
                            for card in cards:
                                context.bot.send_sticker(
                                    chat.id, sticker=card.sticker["file_id"]
                                )
                            context.bot.send_sticker(
                                chat.id,
                                sticker=last_card.sticker["file_id"],
                                reply_markup=InlineKeyboardMarkup([[button]]),
                            )
                        context.bot.send_message(
                            chat.id,
                            text=display_name(game.current_player.user)
                            + "\n"
                            + "請挑最爛ㄉ",
                        )

                else:
                    context.bot.send_message(
                        chat.id,
                        text=display_name(user) + "你現在不能出黃牌",
                        reply_to_message_id=update.chosen_inline_result.inline_message_id,
                    )

            elif game.state == game.State.DISCARD:
                if player == game.board.loser:
                    player.discard(card)
                    if player.discarded:
                        game.turn()
                        context.bot.send_message(
                            chat.id,
                            text="換下一位玩家 " + display_name(game.current_player.user),
                            reply_markup=choice,
                        )
                else:
                    context.bot.send_message(
                        chat.id,
                        text=display_name(user) + "你現在不能出黃牌",
                        reply_to_message_id=update.chosen_inline_result.inline_message_id,
                    )

        elif result_id.startswith(PURPLE):
            card = Card.from_id(result_id.replace(PURPLE, ""))
            player.play(card)
            # NOTE: notify other players to play yellow cards
            context.bot.send_message(
                chat.id, text=make_other_players_notif(game), reply_markup=choice
            )
        else:
            logger.info(f"Result: {result_id} is run into else clause!")
            # The card cannot be played

    def reply_callback(self, update: Update, context: CallbackContext):
        chat = update.callback_query.message.chat
        user = update.callback_query.from_user
        try:
            player = gm.userid_current[user.id]
            game = player.game
        except (KeyError, AttributeError):
            return

        data = update.callback_query.data

        if data.isdigit():
            if player != game.current_player:
                update.callback_query.answer("不要亂按啦！")
                return
            num = int(data)

            # NOTE: resolve join midway problem
            try:
                loser = game.board.get_loser(num)
            except IndexError:
                return

            if game.board.loser:
                update.callback_query.answer("你已經選過了！")
                return

            loser.score -= game.board.purple.space
            game.board.loser = loser
            context.bot.send_message(chat.id, text=make_card_players(game, num))

            # NOTE: Game end check
            if game.get_loser():
                gm.end_game(chat, user)
                context.bot.send_message(chat.id, text=make_settlement(game))
                return
            context.bot.send_message(chat.id, text=make_current_settlement(game))
            # NOTE: let loser to discard cards
            game.state += 1
            logger.info(f"{game.state} == {game.State.DISCARD}")

            actions = [1, 2, "不換"]
            buttons = []
            for act in actions:
                if isinstance(act, int):
                    data = f"discard{act}"
                else:
                    data = "skip_discard"
                buttons.append(InlineKeyboardButton(str(act), callback_data=data))
            context.bot.send_message(
                chat.id,
                text=make_loser_discard(game),
                reply_markup=InlineKeyboardMarkup([buttons]),
            )

        elif data.startswith("discard"):
            if player != game.board.loser:
                update.callback_query.answer("不要亂按啦！")
                return

            amount = int(data.replace("discard", ""))
            if player.discard_amount > 0:
                update.callback_query.answer(f"你已經選擇棄掉 {amount} 張 {YELLOW_CARD} 無法反悔")
                return
            player.discard_amount = amount
            context.bot.send_message(
                chat.id,
                text=display_name(user) + f"選擇了棄掉 {amount} 張牌",
                reply_markup=choice,
            )
            update.callback_query.answer(f"接下來請你選擇 {amount} 張 {YELLOW_CARD} 棄牌")
        elif data == "skip_discard":
            if player == game.board.loser and player.discard_amount == 0:
                game.turn()
                context.bot.send_message(
                    chat.id,
                    text="換下一位玩家 " + display_name(game.current_player.user),
                    reply_markup=choice,
                )
                text = "你選擇了不換牌！"
            else:
                text = "不要亂按啦！"
            update.callback_query.answer(text)
        else:
            logger.info(f"{data} run into else clause")

    def error(self, update: Update, context: CallbackContext):
        """Simple error handler"""
        logger.exception(context.error)

    def launch(self):
        self.updater.start_polling()
        self.updater.idle()


choice = InlineKeyboardMarkup(
    [[InlineKeyboardButton("選牌！", switch_inline_query_current_chat="")]]
)

gm = GameManager()

Room(Updater(token=TOKEN, workers=WORKERS)).launch()

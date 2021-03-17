# Yellow Cards Bot

> A yellow cards game bot inspired by mau_mau_bot

## Telegram Bot 設置

1. 找 BotFather (@BotFather) 建 Bot
2. 將 token 填入 `config.json`
3. 將 Bot 的 inlinemode 設為 Enable 並將 placeholder 設成 `🔼 選牌 🔼`
4. 將 inlinefeedback 設為 Enable
5. 設定 command list 從 `commandlist.txt` 複製

## 流程

1. 初始化

   - 系統分配給每人 13 張黃牌
   - 決定當前玩家並建一個循環鏈結串列
   - 系統自動分配 2 張紫牌給首位玩家

2. 當前玩家選擇 1 張紫牌

   - 系統自動將選中的紫牌在公開區打出 並將 不要的紫牌刪除

3. 其他玩家選擇 [1, N] 張黃牌（根據打出紫牌的空格數）

   - 系統等待所有玩家出牌，後將牌打亂並記錄大家出的牌，再由系統統一展示

4. 當前玩家選擇 "最爛" 的牌

   - 藉由 InlineQueryChosen 來選擇牌 (應該是編號的形式)
   - 系統自動展示誰出什麼牌 並把選中的玩家扣分
   - 系統判斷是否結束
     - 是 列出得分並結束遊戲
     - 否 則將所有人的黃牌補至 13 張
     - 將當前玩家設為 當前玩家.next
     - 系統自動分配 2 張紫牌給首位玩家
   - 被選中的玩家可以選擇棄牌
   - 跳至 2

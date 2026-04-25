# ⚔ Quest Board Bot

Quest Boardの**Discord配信ボット**。GitHub Actionsで毎朝のタスクを自動配信します。

これは [Quest Board本体（PWAアプリ）](https://github.com/YOUR-USERNAME/Shopee-Quest) の配信機能です。

---

## 🚀 セットアップ（5ステップ・10分）

### 1. このリポジトリをFork

このページの右上「**Fork**」ボタンを押して、自分のアカウントにコピーします。

### 2. Discord Webhook URLを取得

1. Discordで配信先のチャンネルを開く
2. ⚙️ **チャンネル設定** → **連携サービス**
3. **ウェブフックを作成** → 名前は「Quest Board」など
4. **ウェブフックURLをコピー**

> **Webhook URLとは**: チャンネルに直接メッセージを投稿できる特別なURL。
> 普通のチャンネルURL（`discord.com/channels/...`）とは別物です。
> このURLは外部に漏らさないでください。

### 3. Webhook URLをSecretsに登録

Forkしたリポジトリで:

1. **Settings** タブ → **Secrets and variables** → **Actions**
2. **New repository secret** をクリック
3. Name: `DISCORD_WEBHOOK_URL`
4. Secret: コピーしたWebhook URL
5. **Add secret**

### 4. プロフィールを登録（任意）

同じ画面の **Variables** タブ:

1. **New repository variable**
2. Name: `PLAYER_NAME` / Value: 自分の名前（例: `トルネコ`）
3. （オプション）`TIMEZONE` / `Asia/Tokyo`

### 5. 月間目標を登録

**Secrets** タブで:

1. **New repository secret**
2. Name: `USER_CONFIG_JSON`
3. Secret: 以下のJSONを貼る（自分用に編集）

```json
{
  "goals": [
    {"icon": "📦", "name": "出品", "target": 100, "done": 47},
    {"icon": "✏️", "name": "商品編集", "target": 50, "done": 32},
    {"icon": "🔍", "name": "リサーチ", "target": 30, "done": 18}
  ],
  "off_days": ["2026-04-26", "2026-04-30"],
  "half_days": ["2026-04-27"],
  "trip_days": ["2026-05-01"]
}
```

| キー | 内容 |
|---|---|
| `goals` | 月間目標。`target`が月の合計、`done`が現在の達成数 |
| `off_days` | 休日リスト（"YYYY-MM-DD"形式） |
| `half_days` | 半日勤務（目標が0.5日分） |
| `trip_days` | 出張日（休日と同じ扱い） |

**ヒント**: Quest Boardアプリの「設定」タブで「📋 JSONをコピー」を押せば、現在の状態が自動でJSON生成されるので、それを貼り付けるのが楽です。

---

## 🧪 動作テスト

1. リポジトリの **Actions** タブを開く
2. 左メニューの **🌅 Morning Delivery**
3. 右上の **Run workflow** → **Run workflow**
4. 数十秒後、Discordチャンネルに配信が届く

うまくいかない場合は、Actionsの実行ログを見ればエラー内容が分かります。

---

## ⏰ 配信時刻のカスタマイズ

`.github/workflows/morning.yml` の `cron` を編集します。

```yaml
# 例: 朝7:30配信 → JST 07:30 = UTC 22:30 (前日)
- cron: '30 22 * * *'

# 例: 朝6:00配信 → JST 06:00 = UTC 21:00 (前日)
- cron: '0 21 * * *'
```

**注意**: GitHub Actionsの時刻はUTCです。JSTから-9時間してください。

---

## 📊 進捗の更新方法

毎日の進捗は、現状**手動更新**です。

### 方法A: アプリで更新してJSONをコピー

1. Quest Boardアプリの「設定」タブを開く
2. 「📋 JSONをコピー」ボタンを押す
3. GitHubの `USER_CONFIG_JSON` Secret を **Update** で開く
4. 貼り付けて保存

### 方法B: GitHubで直接編集

`USER_CONFIG_JSON` Secretを開いて、`done`の数値だけ更新でもOK。

---

## 🔧 仕組み

```
GitHub Actions (cron)
       ↓
   毎朝7:30に発火
       ↓
   deliver.py 実行
       ↓
  Secrets から設定読み込み
       ↓
  今日のタスク量を計算
  （月間目標 ÷ 残稼働日）
       ↓
  Discord Webhook に POST
       ↓
   Discordチャンネルに通知
```

**動作環境**:
- 完全無料（GitHub Actionsの無料枠で月数十分しか使わない）
- サーバー不要
- 設定はGitHub Secretsで暗号化保存

---

## ⚠️ 制約事項

- **GitHub Actions の cron は厳密ではない**（数分〜十数分遅れることがある）
- **進捗の自動同期は未対応**（アプリで進捗を進めても、JSONを再コピーして更新する必要あり）

---

## 📁 ファイル構成

```
quest-board-bot/
├── deliver.py              # メイン配信スクリプト
├── requirements.txt        # Python依存関係
├── README.md               # このファイル
└── .github/workflows/
    └── morning.yml         # 朝の配信
```

---

## 🧰 ローカルで試す

PCで動作確認したい場合:

```bash
pip install -r requirements.txt

export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export PLAYER_NAME="トルネコ"
export USER_CONFIG_JSON='{"goals":[...]}'

python deliver.py morning
```

---

## ライセンス

MIT License

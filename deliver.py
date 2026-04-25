#!/usr/bin/env python3
"""
Quest Board - Discord配信ボット

毎朝のタスク配信を Discord Webhook に送信する。

使い方:
  python deliver.py morning

環境変数:
  DISCORD_WEBHOOK_URL  : 配信先のDiscord Webhook URL（必須）
  PLAYER_NAME          : プレイヤー名（デフォルト: "あなた"）
  USER_CONFIG_JSON     : 目標・休日設定のJSON文字列（任意）
  TIMEZONE             : タイムゾーン（デフォルト: Asia/Tokyo）
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def load_config():
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        print("ERROR: DISCORD_WEBHOOK_URL が設定されていません", file=sys.stderr)
        sys.exit(1)

    player_name = os.environ.get("PLAYER_NAME", "あなた").strip()
    timezone = os.environ.get("TIMEZONE", "Asia/Tokyo").strip()
    user_config_raw = os.environ.get("USER_CONFIG_JSON", "").strip()

    user_config = {}
    if user_config_raw:
        try:
            user_config = json.loads(user_config_raw)
        except json.JSONDecodeError as e:
            print(f"WARNING: USER_CONFIG_JSON のパースに失敗: {e}", file=sys.stderr)

    return {
        "webhook": webhook,
        "player_name": player_name,
        "timezone": timezone,
        "goals": user_config.get("goals", _default_goals()),
        "off_days": user_config.get("off_days", []),
        "half_days": user_config.get("half_days", []),
        "trip_days": user_config.get("trip_days", []),
    }


def _default_goals():
    return [
        {"icon": "📦", "name": "出品",     "target": 100, "done": 0},
        {"icon": "✏️", "name": "商品編集", "target": 50,  "done": 0},
        {"icon": "🔍", "name": "リサーチ", "target": 30,  "done": 0},
    ]


def calc_remaining_days(today, off_days, half_days, trip_days):
    last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    weighted = 0.0
    raw = 0
    off_set = set(off_days) | set(trip_days)
    half_set = set(half_days)
    cursor = today
    while cursor <= last_day:
        key = cursor.strftime("%Y-%m-%d")
        if key in off_set:
            cursor += timedelta(days=1)
            continue
        if key in half_set:
            weighted += 0.5
        else:
            weighted += 1
        raw += 1
        cursor += timedelta(days=1)
    return weighted, raw


def is_off_day(date, off_days, trip_days):
    key = date.strftime("%Y-%m-%d")
    return key in off_days or key in trip_days


def get_pep_talk(total_done, total_target):
    ratio = total_done / total_target if total_target > 0 else 0
    if ratio >= 1.0:
        return "月間目標、達成しちゃってるやん。月末までゆっくりしたらええ"
    if ratio >= 0.8:
        return "残り少し！もう一息で月間達成や"
    if ratio >= 0.6:
        return "今月、ええペースやで。このまま行けば月末ニンマリや"
    if ratio >= 0.4:
        return "ぼちぼちペース。焦らず一個ずつ片付けていこ"
    if ratio >= 0.2:
        return "ちょっとペース上げよか。今日3個でも前進や"
    return "月の前半やから、まだ全然挽回できる。深呼吸"


def make_progress_bar(ratio, width=10):
    filled = int(ratio / 100 * width)
    return "█" * filled + "░" * (width - filled)


def deliver_morning(config):
    tz = ZoneInfo(config["timezone"])
    today = datetime.now(tz).date()

    if is_off_day(today, set(config["off_days"]), set(config["trip_days"])):
        print(f"今日（{today}）は休日設定のため配信スキップします")
        return

    weighted, raw = calc_remaining_days(today, config["off_days"], config["half_days"], config["trip_days"])
    today_key = today.strftime("%Y-%m-%d")
    today_factor = 0.5 if today_key in config["half_days"] else 1.0

    fields = []
    progress_lines = []
    total_done = 0
    total_target = 0

    for g in config["goals"]:
        target = g.get("target", 0)
        done = g.get("done", 0)
        left = max(0, target - done)
        today_quota = max(0, int((left / weighted) * today_factor + 0.5)) if weighted > 0 else 0
        total_done += done
        total_target += target

        if today_quota > 0 and done < target:
            fields.append({
                "name": f"{g['icon']} {g['name']}",
                "value": f"**{today_quota}** 件",
                "inline": True
            })

        ratio = (done / target * 100) if target > 0 else 0
        bar = make_progress_bar(ratio)
        progress_lines.append(f"{g['icon']} {g['name']}: {bar} `{done}/{target}` ({ratio:.0f}%)")

    pep = get_pep_talk(total_done, total_target)
    weekday_ja = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]
    all_done = all(g.get("done", 0) >= g.get("target", 0) for g in config["goals"])

    if all_done:
        embed = {
            "title": "🏆 月間目標 全達成済み",
            "description": f"**{config['player_name']}** さん、おはようございます。\n今月の目標、すべて達成済みです。\n\n今日は心置きなく休んでも、新しいことを始めてもOKです。",
            "color": 0xb8893f,
            "footer": {"text": f"{today.strftime('%Y年%m月%d日')}（{weekday_ja}）"},
        }
    else:
        embed = {
            "title": "⚔ 本日のクエスト",
            "description": f"**{config['player_name']}** さん、おはようございます。\n\n_{pep}_",
            "color": 0xb8893f,
            "fields": fields if fields else [{"name": "📋", "value": "今日のタスクはありません（達成済み or 軽い日）", "inline": False}],
            "footer": {"text": f"{today.strftime('%Y年%m月%d日')}（{weekday_ja}）・残り稼働 {raw}日"},
        }

    progress_embed = {
        "title": "📊 今月の進捗",
        "description": "\n".join(progress_lines),
        "color": 0x7a5a25,
    }

    payload = {
        "username": "Quest Board ⚔",
        "embeds": [embed, progress_embed],
    }

    send_discord(config["webhook"], payload)
    print(f"朝の配信を送信しました: {today}")


def send_discord(webhook_url, payload):
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Discord送信失敗: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("使い方: python deliver.py morning", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    config = load_config()

    if mode == "morning":
        deliver_morning(config)
    else:
        print(f"不明なモード: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

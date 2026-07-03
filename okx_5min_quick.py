"""
OKX U本位合约 5分钟涨跌幅快检 - 并发版
用法: python okx_5min_quick.py
配置: 设置环境变量 TG_BOT_TOKEN / TG_CHAT_ID 
      或创建 config.toml (见 config.example.toml)
"""

import os, configparser, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ====== 配置加载 ======
# 优先级: 环境变量 > config.toml > 默认值
def load_config():
    cfg = {"TG_BOT_TOKEN": "", "TG_CHAT_ID": "", "CHANGE_THRESHOLD": 5.0}

    if os.environ.get("TG_BOT_TOKEN"):
        cfg["TG_BOT_TOKEN"] = os.environ["TG_BOT_TOKEN"]
    if os.environ.get("TG_CHAT_ID"):
        cfg["TG_CHAT_ID"] = os.environ["TG_CHAT_ID"]
    if os.environ.get("CHANGE_THRESHOLD"):
        cfg["CHANGE_THRESHOLD"] = float(os.environ["CHANGE_THRESHOLD"])

    if os.path.exists("config.toml"):
        cp = configparser.ConfigParser()
        cp.read("config.toml", encoding="utf-8")
        if "telegram" in cp:
            cfg["TG_BOT_TOKEN"] = cp["telegram"].get("token", cfg["TG_BOT_TOKEN"])
            cfg["TG_CHAT_ID"] = cp["telegram"].get("chat_id", cfg["TG_CHAT_ID"])
        if "monitor" in cp:
            cfg["CHANGE_THRESHOLD"] = cp["monitor"].getfloat("threshold", cfg["CHANGE_THRESHOLD"])

    return cfg

config = load_config()
TG_BOT_TOKEN = config["TG_BOT_TOKEN"]
TG_CHAT_ID = config["TG_CHAT_ID"]
CHANGE_THRESHOLD = config["CHANGE_THRESHOLD"]

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def tg_send(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print(f"[TG未配置] {text}")
        return False
    try:
        r = session.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except:
        return False

def get_swap_list():
    try:
        r = session.get("https://www.okx.com/api/v5/market/tickers?instType=SWAP", timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get('code') == '0':
                return [t['instId'] for t in data['data'] if t['instId'].endswith('-USDT-SWAP')]
        return []
    except:
        return []

def check_one(instId):
    try:
        r = session.get(f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar=5m&limit=1", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('code') == '0' and data.get('data'):
                c = data['data'][0]
                o, cl = float(c[1]), float(c[4])
                if o == 0:
                    return None
                chg = ((cl - o) / o) * 100
                if abs(chg) >= CHANGE_THRESHOLD:
                    return {'symbol': instId.replace('-USDT-SWAP', ''), 'change_pct': round(chg, 2), 'is_up': chg >= 0}
    except:
        pass
    return None

def run():
    t0 = datetime.now()
    print(f"Scan start: {t0.strftime('%H:%M:%S')}")

    swaps = get_swap_list()
    if not swaps:
        print("ERROR: failed to get contract list")
        return

    print(f"Contracts: {len(swaps)}, scanning...")

    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(check_one, i): i for i in swaps}
        done = 0
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
            done += 1
            if done % 100 == 0:
                print(f"  Progress: {done}/{len(swaps)}")

    surge = sorted([r for r in results if r['is_up']], key=lambda x: x['change_pct'], reverse=True)
    drop = sorted([r for r in results if not r['is_up']], key=lambda x: x['change_pct'])

    total = len(surge) + len(drop)
    elapsed = (datetime.now() - t0).total_seconds()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if total > 0:
        lines = [f"<b>OKX Contract Alert</b>", f"{now_str}", f"5min change >= {CHANGE_THRESHOLD}%", f"{elapsed:.0f}s scanned {len(swaps)} contracts", ""]
        if surge:
            lines.append(f"Up({len(surge)}):")
            for x in surge[:10]:
                lines.append(f"  {x['symbol']:12} | {x['change_pct']:+6.2f}%")
            if len(surge) > 10:
                lines.append(f"  ... total {len(surge)}")
        if drop:
            lines.append(f"Down({len(drop)}):")
            for x in drop[:10]:
                lines.append(f"  {x['symbol']:12} | {x['change_pct']:+6.2f}%")
            if len(drop) > 10:
                lines.append(f"  ... total {len(drop)}")
        msg = "\n".join(lines)
    else:
        msg = f"No alert | {now_str} | {elapsed:.0f}s scanned {len(swaps)} contracts"

    print(f"\n{msg}")
    tg_send(msg)
    print(f"\nDone: {(datetime.now()-t0).total_seconds():.0f}s")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Error: {e}")
        tg_send(f"Script error: {e}")

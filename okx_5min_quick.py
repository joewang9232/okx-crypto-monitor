"""
OKX U本位合约 5分钟涨跌幅快检 - 并发版
扫描394个合约约15秒，不依赖定时器
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TG_BOT_TOKEN = "8919890713:AAFgylqmVbXVCjgsu5gaCR105OqAWptRlXA"
TG_CHAT_ID = "7191094692"
CHANGE_THRESHOLD = 5.0

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def tg_send(text):
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
    print(f"🔍 开始快检: {t0.strftime('%H:%M:%S')}")

    swaps = get_swap_list()
    if not swaps:
        print("ERROR: 获取列表失败")
        return

    print(f"合约: {len(swaps)}，开始并发查…")

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
                print(f"  进度: {done}/{len(swaps)}")

    surge = sorted([r for r in results if r['is_up']], key=lambda x: x['change_pct'], reverse=True)
    drop = sorted([r for r in results if not r['is_up']], key=lambda x: x['change_pct'])

    total = len(surge) + len(drop)
    elapsed = (datetime.now() - t0).total_seconds()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if total > 0:
        lines = [f"🚨 <b>OKX合约异动</b>", f"⏰ {now_str}", f"📊 5分钟涨跌幅≥{CHANGE_THRESHOLD}%", f"⚡ {elapsed:.0f}s扫描{len(swaps)}合约", ""]
        if surge:
            lines.append(f"📈 急涨({len(surge)}):")
            for x in surge[:10]:
                lines.append(f"  {x['symbol']:12} | {x['change_pct']:+6.2f}%")
            if len(surge) > 10:
                lines.append(f"  … 共{len(surge)}个")
        if drop:
            lines.append(f"\n📉 急跌({len(drop)}):")
            for x in drop[:10]:
                lines.append(f"  {x['symbol']:12} | {x['change_pct']:+6.2f}%")
            if len(drop) > 10:
                lines.append(f"  … 共{len(drop)}个")
        msg = "\n".join(lines)
    else:
        msg = f"✅ 本轮无异动 | {now_str} | {elapsed:.0f}s扫描{len(swaps)}合约"

    print(f"\n{msg}")
    tg_send(msg)
    print(f"\n✅ 完成: {(datetime.now()-t0).total_seconds():.0f}s")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"异常: {e}")
        try:
            tg_send(f"❌ 脚本异常: {e}")
        except:
            pass

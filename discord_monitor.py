"""
Dual Discord Self-Bot Join Monitor → Telegram Alerts
Runs two user accounts concurrently, each monitoring a different set of servers.
Sends all alerts to the same Telegram chat.
"""

import asyncio
import os
import discord
import requests
import time
from datetime import datetime, timezone
from flask import Flask
from threading import Thread

# ------------------ TELEGRAM CONFIG (same for both bots) ------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
if not TELEGRAM_TOKEN or not CHAT_ID:
    raise Exception("Missing TELEGRAM_TOKEN or CHAT_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ------------------ CONFIGURATION FOR TWO ACCOUNTS ------------------
# Account A (replace with actual token and server list)
TOKEN_A = os.getenv("DISCORD_TOKEN_A")    # first user token
SERVERS_A = {
    "1196857788220067943": "Variational",
    "667044843901681675": "Optimism",
    "1364669301751283793": "Solflare",
    "925207817923743794": "SOL Decoder",
    "402910780124561410": "Compound",
    "978714252934258779": "Zcash",
    "1240797310196125857": "Lombard",
    "1255553987206447194": "OP_NET",
    "1296015181985349715": "STBL",
    "1381686363233194004": "Bullpen",
    "710897173927297116": "Polymarket",
    "1024239646357594122": "THENA",
    "1230430080514396161": "Yei Finance",
    "1209575590362095676": "Avalon Labs",
    "943473409541685319": "Camelot DEX",
    "1139242134495559801": "SPARK DotFi",
    "551050633898360852": "Fluid",
    "841556000632078378": "Bullet",
    "491256308461207573": "Algorand",
    "1329085279411245088": "Falcon Finance",
    "895116209958297631": "LoopScale",
    "793925570739044362": "Goldfinch",
    "885256081289379850": "Ledger OP3N",
    "1385014051272265868": "Shelby",
}

# Account B (replace with actual token and server list)
TOKEN_B = os.getenv("DISCORD_TOKEN_B")    # second user token
SERVERS_B = {
    "1219739501673451551": "MegaETH",
    "1443079201996410987": "Alien",
    "334085157441110017": "Horizen",
    "1165826384975908924": "Midnight Network",
    "473781666251538452": "Build on Circle",
    "933846070344167464": "Moonwell Fi",
    "839766295808311306": "Telcoin",
    "1270276651636232282": "Pharos",
    "1211893851489304576": "ORANGE WEB3",
    "1268289052264632434": "SKY",
    "1334957028334112922": "40 Acres",
    "943486047625572392": "Peaq Network",
    "900389466781401098": "MapMetrics",
    "1139239009772642416": "AERODROME",
    "842045244035301406": "Limitless",
    "765195245016449027": "Bluefin",
    "1456786812382085459": "Flying Tulip",
    "1303532852003995689": "Vanish Trade",
}

IGNORED_SERVERS = {"703994580499955784", "1067165013397213286"}

# ------------------ DISCORD CLIENT FACTORY ------------------
class MonitorClient(discord.Client):
    def __init__(self, token, server_map, account_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.server_map = server_map
        self.account_name = account_name
        self.verified = {}

    async def on_ready(self):
        # Determine which of the assigned servers this account is actually in
        connected = 0
        for guild in self.guilds:
            if str(guild.id) in self.server_map and str(guild.id) not in IGNORED_SERVERS:
                self.verified[str(guild.id)] = self.server_map[str(guild.id)]
                connected += 1
        msg = f"✅ {self.account_name} online | Monitoring {connected}/{len(self.server_map)} servers"
        send_telegram(msg)
        print(msg)

    async def on_member_join(self, member):
        gid = str(member.guild.id)
        if gid not in self.verified:
            return
        server_name = self.verified[gid]
        alert = (f"🚨 NEW MEMBER JOINED\n"
                 f"Account: {self.account_name}\n"
                 f"🏠 Server: {server_name}\n"
                 f"👤 Username: {member.name}\n"
                 f"🆔 ID: {member.id}")
        send_telegram(alert)
        print(f"🔔 [{self.account_name}] [{server_name}] {member.name} joined")

    async def start_bot(self):
        await self.start(self.token)

# ------------------ RUN BOTH CLIENTS CONCURRENTLY ------------------
async def main():
    client_a = MonitorClient(TOKEN_A, SERVERS_A, "AccountA")
    client_b = MonitorClient(TOKEN_B, SERVERS_B, "AccountB")
    await asyncio.gather(
        client_a.start_bot(),
        client_b.start_bot(),
        return_exceptions=True
    )

# ------------------ FLASK KEEP-ALIVE (for Render) ------------------
app = Flask(__name__)
@app.route('/')
def home():
    return "Dual bot monitor is alive."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start Flask in a background thread
    Thread(target=run_flask, daemon=True).start()
    # Run the two bots
    asyncio.run(main())

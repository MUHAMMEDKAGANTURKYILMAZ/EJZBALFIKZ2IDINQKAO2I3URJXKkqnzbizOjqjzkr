#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, random, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SAYAC_DOSYASI = "gonderi_sayaci.txt"
if not os.path.exists(SAYAC_DOSYASI):
    with open(SAYAC_DOSYASI, "w") as f: f.write("0")

RENK = {
    'baslik': '\033[1;36m', 'bilgi': '\033[0;37m', 'basari': '\033[0;32m',
    'hata': '\033[0;31m', 'uyari': '\033[0;33m', 'zaman': '\033[0;35m', 'reset': '\033[0m'
}

def log(mesaj, renk='bilgi'):
    print(f"{RENK[renk]}{mesaj}{RENK['reset']}")

class APIYonetici:
    def __init__(self):
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.bluesky_handle = os.getenv('BLUESKY_HANDLE')
        self.bluesky_pass = os.getenv('BLUESKY_APP_PASSWORD')
        self.bluesky_did = os.getenv('BLUESKY_DID')
        self.prompt_file = os.getenv('GROQ_PROMPT_FILE', 'groq_prompt.txt')
        self.konular_file = os.getenv('KONULAR_FILE', 'konular.txt')
        self.bluesky_token = None

    def groq_metin_uret(self, konu, prompt):
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": f"{prompt}\n\nKONU: {konu}\n\nMax 250 karakter, emoji yok."}]}, timeout=30)
            return resp.json()['choices'][0]['message']['content'].strip() if resp.status_code == 200 else None
        except: return None

    def bluesky_auth(self):
        try:
            resp = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                json={"identifier": self.bluesky_handle, "password": self.bluesky_pass}, timeout=30)
            if resp.status_code == 200: self.bluesky_token = resp.json()['accessJwt']; return True
            return False
        except: return False

    def bluesky_gonder(self, metin, gorsel_url=None, baslik=None):
        if not self.bluesky_token and not self.bluesky_auth(): return False
        tam_metin = (f"{baslik}\n\n{metin}" if baslik else metin)[:295]
        embed = None
        if gorsel_url:
            try:
                img_resp = requests.get(gorsel_url, timeout=30)
                upload = requests.post("https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
                    headers={"Authorization": f"Bearer {self.bluesky_token}", "Content-Type": "image/jpeg"},
                    data=img_resp.content, timeout=30)
                if upload.status_code == 200:
                    embed = {"$type": "app.bsky.embed.images", "images": [{"alt": "Post", "image": upload.json()["blob"]}]}
            except: pass
        record = {"text": tam_metin, "createdAt": datetime.now().isoformat() + "Z", "$type": "app.bsky.feed.post"}
        if embed: record["embed"] = embed
        try:
            resp = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {self.bluesky_token}"},
                json={"repo": self.bluesky_did, "collection": "app.bsky.feed.post", "record": record}, timeout=30)
            return resp.status_code == 200
        except: return False

class BlueskyBot:
    def __init__(self):
        self.api = APIYonetici()
        self.konular = [s.strip() for s in open(self.api.konular_file).readlines() if s.strip()]
        self.prompt = open(self.api.prompt_file).read().strip()

    def gonderi_yap(self):
        log("\n" + "="*50, "baslik")
        try:
            with open(SAYAC_DOSYASI, "r") as f: s = int(f.read().strip())
        except: s = 0

        gorsel = f"https://loremflickr.com/800/600/technology,hacker,coding?random={random.randint(1, 99999)}" if s % 2 == 0 else None

        konu = random.choice(self.konular)
        metin = self.api.groq_metin_uret(konu, self.prompt)

        # Takılmayı önlemek için sayacı hemen artırıyoruz
        with open(SAYAC_DOSYASI, "w") as f: f.write(str(s + 1))

        if not metin:
            log("HATA: Groq metin uretemedi!", "hata")
            return False

        # --- Detaylı Loglar ---
        # Basit emoji sayacı (ASCII dışı karakterleri sayar)
        emoji_count = len([c for c in metin if ord(c) > 127])
        ai_len = len(metin)
        bsky_len = len(f"{konu.title()}\n\n{metin}")

        log(f"SECILEN KONU: {konu.title()}", "basari")
        log(f"AI CEVAP UZUNLUGU: {ai_len} karakter", "bilgi")
        log(f"EMOJI SAYISI: {emoji_count}", "bilgi")
        log(f"BLUESKY TOPLAM: {bsky_len}/300 karakter", "bilgi")
        # ---------------------

        if self.api.bluesky_gonder(metin, gorsel, konu.title()):
            log("DURUM: Bluesky Paylasimi Basarili!", "basari")
            return True
        else:
            log("DURUM: Bluesky Hatasi! (Sira degisti, devam ediliyor)", "hata")
            return False

if __name__ == "__main__":
    bot = BlueskyBot()
    log("BOT BASLATILDI - DETAYLI LOG MODU AKTIF", "zaman")
    while True:
        bot.gonderi_yap()
        # 10 dakika modu için 8-12 dk arası rastgele
        bekleme = random.randint(50, 80)
        log(f"ZAMAN: {datetime.now().strftime('%H:%M:%S')}", "zaman")
        log(f"{bekleme} dk bekleniyor...", "uyari")
        time.sleep(bekleme * 60)

"""
Seiten-Watcher
Ueberwacht eine oder mehrere Webseiten (z. B. TaskCards-Boards) mit einem
Headless-Browser, vergleicht den Stand mit dem letzten Lauf und sendet bei
Aenderungen eine Push-Benachrichtigung ueber ntfy.sh auf das Handy.

Benoetigte Umgebungsvariablen:
  URLS        Eine oder mehrere URLs, jeweils eine pro Zeile.
              Optional mit Namen davor, getrennt durch " | ", z. B.:
                Baerenklasse | https://essen.taskcards.app/#/board/...
                Schul-Homepage | https://www.beispielschule.de/aktuelles
  NTFY_TOPIC  Name des ntfy-Themas (in der ntfy-App abonniert)

TaskCards-Boards werden Karte fuer Karte verglichen (Meldung pro neuer
Karte). Alle anderen Seiten werden ueber ihren Textinhalt verglichen
(Meldung "Seite hat sich geaendert").
"""

import asyncio
import hashlib
import json
import os
import re
import sys
import urllib.request

from playwright.async_api import async_playwright

STATE_FILE = "state.json"
CARD_SELECTOR = ".board-card-content"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_urls(raw: str) -> list[tuple[str, str]]:
    """Zeilen im Format 'Name | URL' oder nur 'URL' einlesen."""
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            name, url = line.split("|", 1)
            entries.append((name.strip(), url.strip()))
        else:
            entries.append((line[:40], line))
    return entries


async def fetch_taskcards(page) -> list[str]:
    """Kartentexte eines TaskCards-Boards auslesen (wartet bis stabil)."""
    last_count, stable = -1, 0
    for _ in range(20):
        await page.wait_for_timeout(2000)
        count = await page.eval_on_selector_all(CARD_SELECTOR, "els => els.length")
        if count == last_count and count > 0:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last_count = count
    texts = await page.eval_on_selector_all(
        CARD_SELECTOR, "els => els.map(e => e.innerText)"
    )
    return [normalize(t) for t in texts if normalize(t)]


async def fetch_generic(page) -> str:
    """Gesamten sichtbaren Text einer normalen Webseite auslesen."""
    await page.wait_for_timeout(5000)
    return normalize(await page.inner_text("body"))


def send_ntfy(topic: str, title: str, message: str) -> None:
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": title.encode("utf-8").decode("latin-1", "replace"),
            "Priority": "high",
            "Tags": "bell",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


async def check_all(entries, state, topic) -> dict:
    new_state = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for name, url in entries:
            key = h(url)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=90000)
                if "taskcards" in url:
                    cards = await fetch_taskcards(page)
                    if not cards:
                        print(f"[{name}] WARNUNG: keine Karten, uebersprungen.")
                        if key in state:
                            new_state[key] = state[key]
                        continue
                    old = state.get(key, {}).get("cards", {})
                    fresh = {h(c): c for c in cards}
                    new_cards = [c for cid, c in fresh.items() if cid not in old]
                    print(f"[{name}] Karten: {len(cards)}, neu: {len(new_cards)}")
                    if old:
                        for c in new_cards:
                            preview = c[:400] + ("…" if len(c) > 400 else "")
                            send_ntfy(topic, f"Neue Karte: {name}", preview)
                    else:
                        print(f"[{name}] Erster Lauf, Ausgangszustand gespeichert.")
                    new_state[key] = {"name": name, "cards": fresh}
                else:
                    text = await fetch_generic(page)
                    if not text:
                        print(f"[{name}] WARNUNG: leere Seite, uebersprungen.")
                        if key in state:
                            new_state[key] = state[key]
                        continue
                    old_hash = state.get(key, {}).get("hash")
                    text_hash = h(text)
                    print(f"[{name}] Hash: {text_hash} (vorher: {old_hash})")
                    if old_hash and old_hash != text_hash:
                        send_ntfy(
                            topic,
                            f"Seite geaendert: {name}",
                            f"Der Inhalt von {url} hat sich geaendert.",
                        )
                    elif not old_hash:
                        print(f"[{name}] Erster Lauf, Ausgangszustand gespeichert.")
                    new_state[key] = {"name": name, "hash": text_hash}
            except Exception as e:
                print(f"[{name}] FEHLER: {e}")
                if key in state:
                    new_state[key] = state[key]
            finally:
                await page.close()
        await browser.close()
    return new_state


def main() -> None:
    raw_urls = os.environ.get("URLS") or os.environ.get("BOARD_URL", "")
    topic = os.environ.get("NTFY_TOPIC")
    entries = parse_urls(raw_urls)
    if not entries or not topic:
        print("FEHLER: URLS und NTFY_TOPIC muessen gesetzt sein.")
        sys.exit(1)

    state = load_state()
    # Altes Zustandsformat (nur ein Board) verwerfen, falls vorhanden
    if state and not all(isinstance(v, dict) and ("cards" in v or "hash" in v)
                         for v in state.values()):
        state = {}

    new_state = asyncio.run(check_all(entries, state, topic))
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

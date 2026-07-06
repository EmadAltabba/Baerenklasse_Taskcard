# TaskCards-Watcher: Einrichtung in 4 Schritten

Dieses Tool prüft alle 30 Minuten automatisch das TaskCards-Board der Klasse
und schickt dir eine Push-Benachrichtigung aufs Handy, sobald eine neue Karte
gepostet wird. Alles läuft kostenlos über GitHub Actions und ntfy.sh, du
brauchst keinen eigenen Server.

## Schritt 1: ntfy-App auf dem Handy einrichten (ca. 2 Minuten)

1. Installiere die App **ntfy** aus dem Google Play Store (Herausgeber:
   Philipp Heckel, kostenlos, ohne Registrierung).
2. Öffne die App und tippe auf das **Plus-Symbol** („Subscribe to topic").
3. Gib einen **frei erfundenen, schwer erratbaren Themennamen** ein,
   zum Beispiel: `baerenklasse-emad-7k3x9p`
   Wichtig: Der Name ist wie ein Passwort. Jeder, der ihn kennt, könnte die
   Benachrichtigungen ebenfalls empfangen. Also keinen einfachen Namen wählen.
4. Fertig. Merke dir den Themennamen für Schritt 3.

## Schritt 2: GitHub-Repository anlegen (ca. 5 Minuten)

1. Erstelle ein kostenloses Konto auf https://github.com (falls noch nicht
   vorhanden).
2. Klicke oben rechts auf **+** → **New repository**.
3. Name z. B. `taskcards-watcher`, Sichtbarkeit unbedingt **Private**
   (der Board-Link mit Token soll nicht öffentlich sein).
4. Klicke **Create repository**.
5. Lade die drei Dateien aus diesem Paket hoch:
   - Auf der Repository-Seite: **uploading an existing file** anklicken
     (oder **Add file → Upload files**).
   - Ziehe `check_board.py` und `ANLEITUNG.md` hinein und klicke
     **Commit changes**.
   - Die Datei `check.yml` muss in den Ordner `.github/workflows/`. Dazu:
     **Add file → Create new file**, als Dateinamen exakt
     `.github/workflows/check.yml` eingeben (die Schrägstriche erzeugen die
     Ordner automatisch), den Inhalt der Datei hineinkopieren und
     **Commit changes** klicken.

## Schritt 3: Geheime Einstellungen (Secrets) hinterlegen

1. Im Repository: **Settings → Secrets and variables → Actions →
   New repository secret**.
2. Lege zwei Secrets an:

   | Name | Wert |
   |---|---|
   | `URLS` | Alle zu ueberwachenden Seiten, eine pro Zeile, im Format `Name \| Link` (siehe Beispiel unten) |
   | `NTFY_TOPIC` | Dein Themenname aus Schritt 1, z. B. `baerenklasse-emad-7k3x9p` |

   Beispielwert fuer `URLS` (beide Boards, einfach so einfuegen):

   ```
   Baerenklasse | https://essen.taskcards.app/#/board/9a9eac33-863d-4089-abcf-3866782812da/view?token=d5dc0b85-72fd-4456-aa27-91cd8986e3fc
   Elterninfo | https://essen.taskcards.app/#/board/62f2e2b6-82a2-496c-8ce5-8d12648ea231/view
   ```

   Weitere Seiten kannst du jederzeit als zusaetzliche Zeile ergaenzen.
   TaskCards-Boards werden Karte fuer Karte verglichen; jede andere
   Webseite wird ebenfalls unterstuetzt und als Ganzes ueberwacht
   (Meldung "Seite geaendert").

## Schritt 4: Ersten Lauf starten und testen

1. Gehe im Repository auf den Tab **Actions**.
2. Falls eine Meldung erscheint, bestätige mit
   **I understand my workflows, go ahead and enable them**.
3. Wähle links den Workflow **TaskCards Board pruefen** und klicke
   **Run workflow → Run workflow**.
4. Der erste Lauf speichert nur den Ausgangszustand (keine Benachrichtigung,
   das ist Absicht). Ab dann prüft GitHub alle 30 Minuten automatisch und
   du bekommst bei jeder **neuen Karte** einen Push mit einer Textvorschau.

## Gut zu wissen

- **Kosten:** GitHub Actions ist für private Repositories bis 2.000 Minuten
  pro Monat kostenlos. Dieses Tool verbraucht etwa 1.500 bis 2.000 Minuten
  bei 30-Minuten-Takt. Falls das knapp wird, stelle im `check.yml` den
  Zeitplan auf `"0 * * * *"` (stündlich) um, das reicht für ein Klassenboard
  in der Regel völlig aus.
- **Zeitplan:** GitHub führt geplante Läufe manchmal mit einigen Minuten
  Verspätung aus. Für Schul-Ankündigungen ist das unkritisch.
- **Geänderte Karten:** Wenn eine bestehende Karte inhaltlich geändert wird,
  meldet das Tool sie ebenfalls als „neue Karte", weil sich der Text
  geändert hat. Gelöschte Karten werden nicht gemeldet.
- **Pause im Repository:** GitHub deaktiviert geplante Workflows in privaten
  Repositories nach 60 Tagen ohne Aktivität. Da das Tool bei jeder Änderung
  selbst einen Commit erzeugt, passiert das praktisch nur in langen Ferien.
  Dann einfach im Actions-Tab auf **Enable workflow** klicken.
- **Links ändern sich oder kommen hinzu:** Einfach das Secret `URLS`
  anpassen. Neue Seiten werden beim ersten Lauf ohne Meldung erfasst und
  danach normal überwacht.

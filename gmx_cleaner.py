#!/usr/bin/env python3
"""
GMX Cleaner — Interaktives Tool zum Aufräumen deines GMX-Postfachs
Verbindung via IMAP (imap.gmx.net:993)

Setup:
  1. Erstelle eine .env Datei im selben Ordner:
       GMX_EMAIL=deine@gmx.de
       GMX_PASSWORD=dein_passwort
  2. pip install python-dotenv
  3. python gmx_cleaner.py
"""

import imaplib
import email
from email.header import decode_header
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# python-dotenv für sichere Passwort-Verwaltung
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Hinweis: 'python-dotenv' nicht installiert. Führe aus: pip install python-dotenv")
    print("Du kannst Zugangsdaten auch direkt eingeben.\n")

IMAP_SERVER = "imap.gmx.net"
IMAP_PORT = 993

# Archiv-Ordner, die bei Lösch-Funktionen immer ausgeschlossen werden
ARCHIVE_FOLDERS = {"Archiv", "Archive", "ARCHIV", "All Mail", "Alle Nachrichten"}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def decode_str(value):
    """Dekodiert Email-Header-Strings sauber."""
    if not value:
        return ""
    parts = decode_header(value)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("latin-1", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)


def connect(email_addr, password):
    """Verbindet mit GMX IMAP."""
    print(f"\n🔌 Verbinde mit {IMAP_SERVER}...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_addr, password)
        print("✅ Login erfolgreich!\n")
        return mail
    except imaplib.IMAP4.error as e:
        print(f"❌ Login fehlgeschlagen: {e}")
        print("Tipp: Stelle sicher, dass IMAP in deinen GMX-Einstellungen aktiviert ist.")
        sys.exit(1)


def get_folders(mail):
    """Listet alle verfügbaren Ordner."""
    _, folders = mail.list()
    result = []
    for f in folders:
        if isinstance(f, bytes):
            parts = f.decode().split('"')
            name = parts[-1].strip().strip('"')
            result.append(name)
    return result


def select_folder(mail, folder="INBOX"):
    """Wählt einen Ordner aus."""
    status, data = mail.select(f'"{folder}"', readonly=False)
    if status != "OK":
        status, data = mail.select(folder, readonly=False)
    return status == "OK"


def fetch_message_ids(mail, search_criteria):
    """Gibt Nachrichten-IDs für ein Suchkriterium zurück."""
    _, data = mail.search(None, search_criteria)
    ids = data[0].split() if data[0] else []
    return ids


def fetch_envelope(mail, msg_id):
    """Holt Betreff, Absender, Datum einer Email."""
    try:
        _, data = mail.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
        raw = data[0][1] if data and data[0] else b""
        msg = email.message_from_bytes(raw)
        subject = decode_str(msg.get("Subject", "(kein Betreff)"))
        sender = decode_str(msg.get("From", ""))
        date_str = msg.get("Date", "")
        return sender, subject, date_str
    except Exception:
        return "?", "?", "?"


def delete_messages(mail, msg_ids, trash=True):
    """Löscht Nachrichten (verschiebt in Trash oder direkt)."""
    if not msg_ids:
        return 0
    for msg_id in msg_ids:
        if trash:
            mail.store(msg_id, "+FLAGS", "\\Deleted")
        else:
            mail.store(msg_id, "+FLAGS", "\\Deleted")
    mail.expunge()
    return len(msg_ids)


def is_archive_folder(folder_name):
    """Prüft ob ein Ordner ein geschützter Archiv-Ordner ist."""
    return folder_name in ARCHIVE_FOLDERS


def confirm(prompt, count):
    """Bestätigung vor dem Löschen."""
    print(f"\n⚠️  {prompt} ({count} Email(s))")
    answer = input("   Wirklich löschen? [j/N]: ").strip().lower()
    return answer == "j"


# ── Menü-Funktionen ──────────────────────────────────────────────────────────

def show_stats(mail):
    """Zeigt Postfach-Statistiken."""
    print("\n📊 Postfach-Statistiken")
    print("─" * 40)
    folders = get_folders(mail)
    total = 0
    for folder in folders:
        try:
            status, data = mail.select(f'"{folder}"', readonly=True)
            if status == "OK":
                count = int(data[0])
                if count > 0:
                    print(f"  {folder:<30} {count:>6} Emails")
                    total += count
        except Exception:
            continue
    print(f"  {'GESAMT':<30} {total:>6} Emails")
    print()


def search_and_delete(mail):
    """Suche nach Absender oder Suchbegriff und löschen."""
    print("\n🔍 Suche & Löschen")
    print("─" * 40)
    print("Suchoptionen:")
    print("  1. Nach Absender (z.B. 'newsletter@otto.de' oder 'otto.de')")
    print("  2. Nach Betreff-Keyword (z.B. 'Angebot', 'Gutschein')")
    print("  3. Kombination (Absender UND Betreff)")
    print("  0. Zurück")

    choice = input("\nAuswahl: ").strip()
    if choice == "0":
        return

    sender_query = ""
    subject_query = ""

    if choice in ("1", "3"):
        sender_query = input("Absender (oder Teil davon): ").strip()
    if choice in ("2", "3"):
        subject_query = input("Betreff-Keyword: ").strip()

    if not sender_query and not subject_query:
        print("❌ Keine Suchbegriffe eingegeben.")
        return

    # Ordner-Auswahl
    print("\nIn welchem Ordner suchen?")
    print("  1. INBOX")
    print("  2. Alle Ordner")
    print("  3. Bestimmten Ordner eingeben")
    folder_choice = input("Auswahl [1]: ").strip() or "1"

    if folder_choice == "1":
        search_folders = ["INBOX"]
    elif folder_choice == "2":
        search_folders = [f for f in get_folders(mail)
                          if "noselect" not in f.lower() and not is_archive_folder(f)]
        print(f"   ℹ️  Archiv-Ordner werden übersprungen (geschützt).")
    else:
        custom = input("Ordner-Name: ").strip()
        search_folders = [custom] if custom else ["INBOX"]

    # Suche ausführen
    all_found = []  # Liste von (folder, msg_id, sender, subject, date)

    for folder in search_folders:
        if not select_folder(mail, folder):
            continue

        # IMAP Suchkriterien aufbauen
        criteria_parts = []
        if sender_query:
            criteria_parts.append(f'FROM "{sender_query}"')
        if subject_query:
            criteria_parts.append(f'SUBJECT "{subject_query}"')

        if len(criteria_parts) == 1:
            criteria = criteria_parts[0]
        else:
            criteria = f'({" ".join(criteria_parts)})'

        msg_ids = fetch_message_ids(mail, criteria)

        for msg_id in msg_ids:
            sender, subject, date_str = fetch_envelope(mail, msg_id)
            all_found.append((folder, msg_id, sender, subject, date_str))

    if not all_found:
        print("\n✅ Keine Emails gefunden.")
        return

    # Vorschau anzeigen
    print(f"\n📧 {len(all_found)} Email(s) gefunden:\n")
    for i, (folder, _, sender, subject, date_str) in enumerate(all_found[:20], 1):
        print(f"  [{i:2}] [{folder}] Von: {sender[:40]:<40} | {subject[:45]}")
    if len(all_found) > 20:
        print(f"  ... und {len(all_found) - 20} weitere")

    # Löschen bestätigen
    if confirm(f"Alle {len(all_found)} gefundenen Emails löschen", len(all_found)):
        # Gruppiert nach Ordner löschen
        by_folder = defaultdict(list)
        for folder, msg_id, _, _, _ in all_found:
            by_folder[folder].append(msg_id)

        deleted = 0
        for folder, ids in by_folder.items():
            select_folder(mail, folder)
            deleted += delete_messages(mail, ids)

        print(f"🗑️  {deleted} Email(s) gelöscht.")
    else:
        print("Abgebrochen.")


def delete_by_newsletter(mail):
    """Erkennt und löscht Newsletter automatisch."""
    print("\n📰 Newsletter erkennen & löschen")
    print("─" * 40)

    if not select_folder(mail, "INBOX"):
        print("❌ INBOX nicht erreichbar.")
        return

    print("🔎 Suche nach Newsletters (via List-Unsubscribe Header)...")

    # Alle Emails holen
    msg_ids = fetch_message_ids(mail, "ALL")
    if not msg_ids:
        print("Postfach ist leer.")
        return

    print(f"   Analysiere {len(msg_ids)} Emails...")

    newsletter_senders = defaultdict(list)  # sender -> [msg_id, ...]

    for i, msg_id in enumerate(msg_ids):
        if i % 50 == 0 and i > 0:
            print(f"   ... {i}/{len(msg_ids)}")
        try:
            _, data = mail.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE)])")
            raw = data[0][1] if data and data[0] else b""
            msg = email.message_from_bytes(raw)
            if msg.get("List-Unsubscribe"):
                sender = decode_str(msg.get("From", "unbekannt"))
                newsletter_senders[sender].append(msg_id)
        except Exception:
            continue

    if not newsletter_senders:
        print("✅ Keine Newsletter gefunden.")
        return

    # Sortiert nach Anzahl anzeigen
    sorted_senders = sorted(newsletter_senders.items(), key=lambda x: -len(x[1]))
    print(f"\n📨 {len(sorted_senders)} Newsletter-Absender gefunden:\n")
    for i, (sender, ids) in enumerate(sorted_senders, 1):
        print(f"  [{i:2}] {len(ids):4}x  {sender[:60]}")

    print("\nOptionen:")
    print("  'alle'     → Alle Newsletter löschen")
    print("  '1,3,5'    → Bestimmte Nummern löschen")
    print("  '0'        → Zurück")

    choice = input("\nAuswahl: ").strip().lower()
    if choice == "0":
        return

    if choice == "alle":
        selected = sorted_senders
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = [sorted_senders[i] for i in indices if 0 <= i < len(sorted_senders)]
        except ValueError:
            print("❌ Ungültige Eingabe.")
            return

    total_ids = [msg_id for _, ids in selected for msg_id in ids]
    if confirm(f"Newsletter von {len(selected)} Absendern löschen", len(total_ids)):
        deleted = delete_messages(mail, total_ids)
        print(f"🗑️  {deleted} Newsletter gelöscht.")
    else:
        print("Abgebrochen.")


def delete_old_emails(mail):
    """Löscht alte Emails nach Datum."""
    print("\n📅 Alte Emails löschen")
    print("─" * 40)

    months = input("Emails älter als X Monate löschen (z.B. 6): ").strip()
    try:
        months = int(months)
    except ValueError:
        print("❌ Ungültige Eingabe.")
        return

    cutoff = datetime.now() - timedelta(days=months * 30)
    date_str = cutoff.strftime("%d-%b-%Y")

    folder_input = input("Ordner [INBOX]: ").strip() or "INBOX"
    if is_archive_folder(folder_input):
        print(f"⛔ Der Ordner '{folder_input}' ist geschützt und wird nicht gelöscht.")
        return
    if not select_folder(mail, folder_input):
        print("❌ Ordner nicht gefunden.")
        return

    msg_ids = fetch_message_ids(mail, f'BEFORE {date_str}')

    if not msg_ids:
        print(f"✅ Keine Emails vor dem {cutoff.strftime('%d.%m.%Y')} gefunden.")
        return

    print(f"\n📧 {len(msg_ids)} Email(s) älter als {months} Monate gefunden.")
    if confirm(f"Alle Emails vor {cutoff.strftime('%d.%m.%Y')} löschen", len(msg_ids)):
        deleted = delete_messages(mail, msg_ids)
        print(f"🗑️  {deleted} Email(s) gelöscht.")
    else:
        print("Abgebrochen.")


def find_large_emails(mail):
    """Findet die größten Emails."""
    print("\n📦 Große Emails finden")
    print("─" * 40)

    folder_input = input("Ordner [INBOX]: ").strip() or "INBOX"
    if is_archive_folder(folder_input):
        print(f"⛔ Der Ordner '{folder_input}' ist geschützt und wird nicht durchsucht.")
        return
    if not select_folder(mail, folder_input):
        print("❌ Ordner nicht gefunden.")
        return

    min_kb = input("Mindestgröße in KB [500]: ").strip() or "500"
    try:
        min_bytes = int(min_kb) * 1024
    except ValueError:
        min_bytes = 512000

    print("🔎 Suche nach großen Emails...")
    _, data = mail.search(None, f"LARGER {min_bytes}")
    msg_ids = data[0].split() if data[0] else []

    if not msg_ids:
        print(f"✅ Keine Emails größer als {min_kb} KB gefunden.")
        return

    # Größe und Info holen
    emails_info = []
    for msg_id in msg_ids:
        try:
            _, size_data = mail.fetch(msg_id, "(RFC822.SIZE)")
            size_str = size_data[0].decode() if size_data and size_data[0] else ""
            import re
            size_match = re.search(r'RFC822\.SIZE (\d+)', size_str)
            size = int(size_match.group(1)) if size_match else 0
            sender, subject, date_str = fetch_envelope(mail, msg_id)
            emails_info.append((msg_id, size, sender, subject))
        except Exception:
            continue

    emails_info.sort(key=lambda x: -x[1])

    print(f"\n📧 {len(emails_info)} Email(s) gefunden:\n")
    for i, (msg_id, size, sender, subject) in enumerate(emails_info[:20], 1):
        size_mb = size / (1024 * 1024)
        print(f"  [{i:2}] {size_mb:6.1f} MB  {sender[:35]:<35} | {subject[:40]}")

    print("\nOptionen:")
    print("  'alle'     → Alle löschen")
    print("  '1,3,5'    → Bestimmte Nummern löschen")
    print("  '0'        → Zurück")

    choice = input("\nAuswahl: ").strip().lower()
    if choice == "0":
        return

    if choice == "alle":
        to_delete = [x[0] for x in emails_info]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            to_delete = [emails_info[i][0] for i in indices if 0 <= i < len(emails_info)]
        except ValueError:
            print("❌ Ungültige Eingabe.")
            return

    if confirm("Ausgewählte Emails löschen", len(to_delete)):
        deleted = delete_messages(mail, to_delete)
        print(f"🗑️  {deleted} Email(s) gelöscht.")
    else:
        print("Abgebrochen.")


def empty_spam(mail):
    """Leert den Spam/Junk-Ordner."""
    print("\n🚫 Spam-Ordner leeren")
    print("─" * 40)

    # GMX nutzt verschiedene mögliche Ordnernamen für Spam
    spam_candidates = ["Spam", "Junk", "SPAM", "JUNK", "Junk E-Mail", "Bulk Mail"]
    spam_folder = None

    available = get_folders(mail)
    for candidate in spam_candidates:
        if candidate in available:
            spam_folder = candidate
            break

    if not spam_folder:
        # Manuell eingeben falls nicht gefunden
        print("⚠️  Kein Spam-Ordner automatisch erkannt.")
        print(f"   Verfügbare Ordner: {', '.join(available[:10])}")
        spam_folder = input("Ordner-Name eingeben: ").strip()
        if not spam_folder:
            return

    if not select_folder(mail, spam_folder):
        print(f"❌ Ordner '{spam_folder}' nicht erreichbar.")
        return

    msg_ids = fetch_message_ids(mail, "ALL")
    if not msg_ids:
        print(f"✅ Spam-Ordner '{spam_folder}' ist bereits leer.")
        return

    print(f"📧 {len(msg_ids)} Email(s) im Ordner '{spam_folder}' gefunden.")

    if confirm(f"Gesamten Spam-Ordner '{spam_folder}' leeren", len(msg_ids)):
        deleted = delete_messages(mail, msg_ids)
        print(f"🗑️  {deleted} Spam-Email(s) gelöscht.")
    else:
        print("Abgebrochen.")


def empty_trash(mail):
    """Leert den Papierkorb."""
    print("\n🗑️  Papierkorb leeren")
    print("─" * 40)

    trash_candidates = ["Trash", "Gelöschte Elemente", "Papierkorb", "Deleted", "Deleted Items", "TRASH"]
    trash_folder = None

    available = get_folders(mail)
    for candidate in trash_candidates:
        if candidate in available:
            trash_folder = candidate
            break

    if not trash_folder:
        print("⚠️  Kein Papierkorb automatisch erkannt.")
        print(f"   Verfügbare Ordner: {', '.join(available[:10])}")
        trash_folder = input("Ordner-Name eingeben: ").strip()
        if not trash_folder:
            return

    if not select_folder(mail, trash_folder):
        print(f"❌ Ordner '{trash_folder}' nicht erreichbar.")
        return

    msg_ids = fetch_message_ids(mail, "ALL")
    if not msg_ids:
        print(f"✅ Papierkorb '{trash_folder}' ist bereits leer.")
        return

    print(f"📧 {len(msg_ids)} Email(s) im Papierkorb '{trash_folder}' gefunden.")

    if confirm(f"Papierkorb '{trash_folder}' endgültig leeren", len(msg_ids)):
        deleted = delete_messages(mail, msg_ids)
        print(f"🗑️  {deleted} Email(s) endgültig gelöscht.")
    else:
        print("Abgebrochen.")


def empty_archive(mail):
    """Leert den Archiv-Ordner."""
    print("\n📦 Archiv-Ordner leeren")
    print("─" * 40)

    archive_candidates = ["Archiv", "Archive", "ARCHIV", "All Mail", "Alle Nachrichten"]
    archive_folder = None

    available = get_folders(mail)
    for candidate in archive_candidates:
        if candidate in available:
            archive_folder = candidate
            break

    if not archive_folder:
        print("⚠️  Kein Archiv-Ordner automatisch erkannt.")
        print(f"   Verfügbare Ordner: {', '.join(available[:10])}")
        archive_folder = input("Ordner-Name eingeben: ").strip()
        if not archive_folder:
            return

    if not select_folder(mail, archive_folder):
        print(f"❌ Ordner '{archive_folder}' nicht erreichbar.")
        return

    msg_ids = fetch_message_ids(mail, "ALL")
    if not msg_ids:
        print(f"✅ Archiv-Ordner '{archive_folder}' ist bereits leer.")
        return

    print(f"\n📧 {len(msg_ids)} Email(s) im Archiv '{archive_folder}':\n")
    for i, msg_id in enumerate(msg_ids, 1):
        sender, subject, date_str = fetch_envelope(mail, msg_id)
        print(f"  [{i:3}] {date_str[:16]:<16} | {sender[:35]:<35} | {subject[:45]}")
    if len(msg_ids) > 0:
        print()

    if confirm(f"Archiv-Ordner '{archive_folder}' endgültig leeren", len(msg_ids)):
        deleted = delete_messages(mail, msg_ids)
        print(f"🗑️  {deleted} Email(s) aus dem Archiv gelöscht.")
    else:
        print("Abgebrochen.")


# ── Hauptprogramm ────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("       GMX Cleaner — Postfach aufräumen")
    print("=" * 50)

    # Zugangsdaten
    email_addr = os.getenv("GMX_EMAIL") or input("GMX E-Mail: ").strip()
    password = os.getenv("GMX_PASSWORD")
    if not password:
        import getpass
        password = getpass.getpass("Passwort: ")

    mail = connect(email_addr, password)

    while True:
        print("\n── Hauptmenü " + "─" * 36)
        print("  1. 📊 Postfach-Statistiken")
        print("  2. 🔍 Suche & Löschen (Absender / Betreff)")
        print("  3. 📰 Newsletter erkennen & löschen")
        print("  4. 📅 Alte Emails löschen")
        print("  5. 📦 Große Emails finden & löschen")
        print("  6. 🚫 Spam-Ordner leeren")
        print("  7. 🗑️  Papierkorb leeren")
        print("  8. 📦 Archiv-Ordner leeren")
        print("  0. 🚪 Beenden")
        print("─" * 49)

        choice = input("Auswahl: ").strip()

        if choice == "1":
            show_stats(mail)
        elif choice == "2":
            search_and_delete(mail)
        elif choice == "3":
            delete_by_newsletter(mail)
        elif choice == "4":
            delete_old_emails(mail)
        elif choice == "5":
            find_large_emails(mail)
        elif choice == "6":
            empty_spam(mail)
        elif choice == "7":
            empty_trash(mail)
        elif choice == "8":
            empty_archive(mail)
        elif choice == "0":
            print("\n👋 Bis zum nächsten Aufräumen!\n")
            mail.logout()
            break
        else:
            print("❌ Ungültige Auswahl.")


if __name__ == "__main__":
    main()

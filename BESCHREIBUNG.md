# GMX Cleaner – Tool-Beschreibung

## Was ist der GMX Cleaner?

GMX Cleaner ist ein interaktives Kommandozeilen-Tool für Python 3, das dabei hilft, ein GMX-E-Mail-Postfach effizient zu bereinigen und zu verwalten. Es verbindet sich über das verschlüsselte IMAP-Protokoll (imap.gmx.net, Port 993) mit dem GMX-Server und bietet verschiedene Funktionen zum Suchen, Filtern und Löschen von E-Mails – immer mit Nutzerbestätigung vor jedem Löschvorgang.

Das Tool ist vollständig auf Deutsch und für den persönlichen Einsatz am Mac konzipiert.

---

## Funktionen im Überblick

### 1. Postfach-Statistik
Zeigt eine Übersicht aller Ordner im Postfach mit der jeweiligen Anzahl an E-Mails. Ideal als erster Schritt, um einen Überblick zu bekommen.

### 2. Suchen und Löschen
Ermöglicht eine gezielte Suche nach E-Mails anhand von:
- **Absender** (vollständige E-Mail-Adresse oder Domain, z. B. `@newsletter.de`)
- **Betreff** (Stichwort-Suche)
- **Kombination** aus Absender und Betreff

Die Suche kann auf den Posteingang, alle Ordner oder einen selbst gewählten Ordner beschränkt werden. Gefundene E-Mails werden mit Vorschau (Absender, Betreff, Datum) angezeigt, bevor eine Löschbestätigung angefordert wird.

### 3. Newsletter erkennen und löschen
Erkennt automatisch Newsletter anhand des RFC-2369-Headers `List-Unsubscribe`. Die gefundenen Newsletter werden nach Absender gruppiert dargestellt. Es kann gezielt nach Absendernummer oder alle auf einmal gelöscht werden.

### 4. Alte E-Mails löschen
Löscht E-Mails, die älter als eine angegebene Anzahl von Monaten sind. Der Zielordner ist frei wählbar oder kann auf alle Ordner ausgeweitet werden.

### 5. Große E-Mails finden
Sucht nach E-Mails, die eine bestimmte Dateigröße (in KB) überschreiten, und listet sie zur Auswahl auf. So lässt sich Speicher freigeben.

### 6. Spam-Ordner leeren
Leert den Spam-/Junk-Ordner vollständig nach Bestätigung. Unterstützt verschiedene Ordnerbezeichnungen (deutsch und englisch).

### 7. Papierkorb leeren
Leert den Papierkorb (Gelöschte Elemente) vollständig nach Bestätigung.

### 8. Archiv leeren
Leert den Archivordner mit einer detaillierten Vorschau der enthaltenen E-Mails. Archivordner sind standardmäßig vor versehentlichem Löschen in anderen Funktionen geschützt.

---

## Sicherheitsmerkmale

- **Bestätigungspflicht**: Vor jedem Löschvorgang wird eine explizite Bestätigung (`j/n`) eingeholt.
- **Archivschutz**: Archivordner (`Archiv`, `Archive`, `All Mail` etc.) sind in Bulk-Operationen gesperrt und können nur über die dedizierte Archiv-Funktion geleert werden.
- **Vorschau vor Löschung**: Die ersten 20 gefundenen E-Mails werden angezeigt, bevor gelöscht wird.
- **Verschlüsselte Verbindung**: Kommunikation ausschließlich über SSL/TLS (Port 993).
- **Sichere Passworteingabe**: Passwort wird über `getpass` eingegeben (nicht im Terminal sichtbar).

---

## Konfiguration

**Empfohlen**: Eine `.env`-Datei im Projektordner mit den Zugangsdaten:

```env
GMX_EMAIL=deine@gmx.de
GMX_PASSWORD=deinpasswort
```

**Alternativ**: Bei fehlendem `.env` werden Zugangsdaten beim Start interaktiv abgefragt.

---

## Technische Details

| Eigenschaft       | Details                        |
|-------------------|-------------------------------|
| Sprache           | Python 3                      |
| Protokoll         | IMAP4_SSL                     |
| Server            | imap.gmx.net:993              |
| Oberfläche        | Interaktives CLI-Menü          |
| Betriebssystem    | macOS (Launcher) / plattformunabhängig (Script) |

**Abhängigkeiten:**
- `python-dotenv` (für `.env`-Unterstützung, wird automatisch installiert)
- Alle weiteren Bibliotheken (`imaplib`, `email`, `getpass` etc.) sind Teil der Python-Standardbibliothek.

---

## Projektstruktur

```
GMX Cleaner/
├── gmx_cleaner.py                 # Hauptprogramm
├── .env                           # Zugangsdaten (nicht ins Git einchecken!)
├── GMX Cleaner starten.command    # macOS-Startskript (Doppelklick zum Starten)
└── BESCHREIBUNG.md                # Diese Datei
```

---

## Start des Tools

**Per Doppelklick (macOS):** `GMX Cleaner starten.command` im Finder doppelklicken.

**Per Terminal:**
```bash
cd /pfad/zum/GMX-Cleaner
python3 gmx_cleaner.py
```

Das Startskript installiert fehlende Abhängigkeiten automatisch und öffnet das Programmfenster im Terminal.

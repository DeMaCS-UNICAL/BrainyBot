# Backend iOS Simulator (Appium)

BrainyBot può inviare tap/swipe e catturare screenshot su un **iPhone Simulator**
invece che su un dispositivo Android (`adb`) o sul robot fisico (`tappy`).
Questo backend si chiama `ios_sim` e usa [Appium](https://appium.io/) con il
driver **XCUITest** per parlare con il Simulatore.

Questa guida spiega come installare e avviare tutto da zero su macOS.

## Requisiti

- **macOS** con **Xcode** installato (serve per il Simulatore iOS e XCUITest).
- **Node.js** + **npm** (per installare Appium).
- **Python 3.10** + **pipenv** (ambiente già usato dal resto del progetto in `Brain/`).

## 1. Installare Appium e il driver XCUITest

```bash
npm install -g appium
appium driver install xcuitest
```

Verifica che il driver sia installato:

```bash
appium driver list --installed
# deve comparire: xcuitest@... [installed (npm)]
```

## 2. Installare le dipendenze Python

Dalla cartella `Brain/`:

```bash
cd Brain
pipenv install
pipenv run pip install Appium-Python-Client
```

> `Appium-Python-Client` non è ancora nel `Pipfile`: va installato a mano nel venv
> finché non viene aggiunto ufficialmente alle dipendenze del progetto.

## 3. Avviare un Simulatore iOS

Apri l'app Simulator e avvia un device (oppure da terminale):

```bash
xcrun simctl list devices          # elenca i device disponibili e i loro UDID
xcrun simctl boot "<nome device>"  # es: "iPhone 17"
open -a Simulator
```

## 4. Configurare `constants.py`

In `Brain/AI/src/constants.py`:

```python
INPUT_BACKEND = 'ios_sim'
APPIUM_SERVER_URL = 'http://127.0.0.1:4723'
IOS_SIMULATOR_UDID = '<UDID del simulatore avviato al punto 3>'
```

Copia l'UDID esatto dall'output di `xcrun simctl list devices` (il device deve
risultare `(Booted)`).

## 5. Avviare il server Appium

```bash
appium
```

Il server resta in ascolto su `http://127.0.0.1:4723`, in linea con
`APPIUM_SERVER_URL`. Lascialo attivo in un terminale dedicato mentre esegui
BrainyBot in un altro (oppure lancialo in background con `appium &`).

## 6. Eseguire BrainyBot

Con Simulatore booted e Appium in esecuzione, in un altro terminale:

```bash
cd Brain
pipenv run play
```

## Troubleshooting

- **`Is the iOS Simulator booted and is the Appium server running?`**
  Controlla che entrambi i passi 3 e 5 siano stati fatti, in quell'ordine.
- **Connection refused su `127.0.0.1:4723`**
  Il server Appium non è avviato, oppure è su una porta diversa: verifica con
  `curl http://127.0.0.1:4723/status`.
- **UDID mismatch / device non trovato**
  L'UDID in `constants.py` non corrisponde a nessun simulatore booted: rilancia
  `xcrun simctl list devices` e aggiorna il valore.
- **Driver xcuitest mancante**
  `appium driver install xcuitest` (vedi punto 1).

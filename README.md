# 🔊 NoiseShield

**Generator szumu maskującego rozmowy przed podsłuchem i nagrywaniem.**

NoiseShield generuje wielowarstwowy szum akustyczny pokrywający pasmo mowy ludzkiej (300–3400 Hz), co sprawia, że rozmowy prowadzone w jego zasięgu są niezrozumiałe dla urządzeń nagrywających, a nagrania praktycznie niemożliwe do odfiltrowania.

---

## Zrzut ekranu

```
╔══════════════════════════════════════╗
║  🔊  NoiseShield                     ║
║  Maskowanie rozmów przed podsłuchem  ║
╠══════════════════════════════════════╣
║  ▶  AKTYWNY – maskowanie włączone    ║
║                                      ║
║  Tryb:    ● Ultra (zalecany)         ║
║  Głośność:     ████████░░  75%       ║
║  Modulacja:    ██░░░░░░░░  0.5 Hz    ║
║                                      ║
║          [  STOP  ]                  ║
╚══════════════════════════════════════╝
```

> Aplikacja posiada graficzny interfejs (GUI) jeśli dostępny jest `tkinter`, w przeciwnym razie uruchamia się w trybie terminalowym (TUI).

---

## Funkcje

- **5 trybów szumu** – od białego po złożony tryb Ultra
- **Modulacja amplitudy** – wieloczęstotliwościowa, nieregularna, trudna do analizy
- **Losowe składowe tonalne** w paśmie mowy (250–3800 Hz) zmieniające się w czasie
- **Automatyczna instalacja** brakujących zależności (`numpy`, `sounddevice`)
- **GUI** (tkinter) lub **TUI** (terminal) – działa bez środowiska graficznego
- Działa na **Linux**, **macOS** i **Windows**

---

## Wymagania

- Python 3.8+
- PortAudio (wymagane przez `sounddevice`)

### Instalacja PortAudio

```bash
# Ubuntu / Debian
sudo apt install portaudio19-dev

# Fedora / RHEL
sudo dnf install portaudio-devel

# macOS
brew install portaudio

# Windows
# PortAudio jest dołączone do binarek sounddevice – zazwyczaj nie wymaga osobnej instalacji
```

### Instalacja zależności Python

```bash
pip install numpy sounddevice
```

> Przy pierwszym uruchomieniu brakujące biblioteki zostaną zainstalowane automatycznie.

---

## Uruchomienie

```bash
python3 noise_shield.py
```

---

## Tryby szumu

| Tryb | Opis | Skuteczność |
|------|------|-------------|
| **Ultra** | Kombinacja wszystkich trybów + 8 losowych składowych tonalnych + nieregularna modulacja wieloma częstotliwościami jednocześnie | ⭐⭐⭐⭐⭐ |
| **Babble** | Symulacja gwaru wielu osób – 12 składowych w paśmie mowy modulowanych niezależnie | ⭐⭐⭐⭐ |
| **Różowy** | Szum o nachyleniu −3 dB/oktawę, dominujący w paśmie mowy, brzmiący naturalnie | ⭐⭐⭐ |
| **Biały** | Równa energia we wszystkim częstotliwościach | ⭐⭐ |
| **Brązowy** | Wzmocnione niskie częstotliwości, trudne do wytłumienia fizycznie | ⭐⭐ |

---

## Dlaczego tryb Ultra jest trudny do odfiltrowania?

Klasyczne filtry audio zakładają stacjonarność szumu (stałe widmo w czasie). NoiseShield w trybie Ultra celowo to łamie:

1. **Niestacjonarne widmo** – losowe składowe tonalne zmieniają się każdy blok audio (~23 ms)
2. **Wielowarstwowość** – biały + różowy + brązowy + babble zsumowane w zmiennych proporcjach
3. **Nieregularna modulacja głośności** – cztery niezależne częstotliwości LFO (1.3, 3.7, 7.1, 13.3 Hz) nakładają się, tworząc aperiodyczny rytm
4. **Pokrycie pasma mowy** – szum koncentruje się dokładnie w 300–3400 Hz, więc żaden filtr nie może go usunąć bez jednoczesnego usunięcia głosu ludzkiego

---

## Sterowanie

### GUI (graficzny)

| Element | Działanie |
|---------|-----------|
| Przyciski trybów | Wybór rodzaju szumu |
| Suwak Głośność | Regulacja poziomu wyjściowego (0–100%) |
| Suwak Modulacja | Szybkość modulacji LFO (0.1–5.0 Hz) |
| Przycisk START/STOP | Włączenie/wyłączenie generowania szumu |

### TUI (terminal)

| Klawisz | Działanie |
|---------|-----------|
| `1` | Tryb Ultra |
| `2` | Tryb Babble |
| `3` | Tryb Różowy |
| `4` | Tryb Biały |
| `5` | Tryb Brązowy |
| `+` / `-` | Głośność +5% / −5% |
| `Enter` | Start / Stop |
| `Q` | Wyjście |

---

## Praktyczne użycie

1. Ustaw głośnik **jak najbliżej** mikrofonu urządzenia nagrywającego (np. telefon leżący na stole)
2. Wybierz tryb **Ultra**
3. Ustaw głośność na **70–80%**
4. Naciśnij **START**

Skuteczny zasięg maskowania wynosi **1–3 metry** w zależności od głośności głośnika i otoczenia.

---

## Struktura projektu

```
noise_shield.py   # Główny plik aplikacji
README.md         # Dokumentacja
LICENSE           # Licencja MIT
```

---

## Licencja

Projekt udostępniony na licencji **MIT**. Szczegóły w pliku [LICENSE](LICENSE).

---

## Zastrzeżenie prawne

Aplikacja przeznaczona wyłącznie do ochrony prywatności własnych rozmów. Użytkownik ponosi pełną odpowiedzialność za zgodność korzystania z aplikacji z lokalnym prawem. Autor nie ponosi odpowiedzialności za niewłaściwe użycie.

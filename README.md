# Pico Hello

The example Pico W product on [App Base](https://github.com/EarthstormSoftware/app-base), the code the Earthstorm
devices share, and the starting point for new ones. App Base does what every one of them has: the web page and JSON
API, settings, MQTT and Home Assistant, Wi-Fi with a setup hotspot, changing Wi-Fi from the page, the Wi-Fi
fallback, updates over Wi-Fi that go back by themselves, the clock and the watchdog. Pico Hello's own part is small:
one setting, a greeting, shown on its page with the board's health, and changed from the page, the API, MQTT or Home
Assistant.

Its sister for a Raspberry Pi running [Juggle OS](https://github.com/EarthstormSoftware/juggle-os) is
[Juggle Hello](https://github.com/EarthstormSoftware/juggle-hello), on the same base.

## What it needs

- A Raspberry Pi Pico W running MicroPython 1.29 or later (the `RPI_PICO_W` build from
  [micropython.org](https://micropython.org/download/RPI_PICO_W/)). To flash it, hold BOOTSEL while plugging the
  board in (or run `py -m mpremote bootloader`), then copy the `.uf2` file to the `RPI-RP2` drive that appears.
- On the PC: Python 3 and the tools in `requirements-dev.txt`:

```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
```

- Optional, for editor type hints: the MicroPython stubs in `typings/` (gitignored), where Pylance finds them:
  `py -m pip install --target typings micropython-rp2-rpi_pico_w-stubs`.

## Deploying it

Connect the Pico over USB and run:

```powershell
.\scripts\deploy.ps1
```

The script compiles everything except the small `main.py` to bytecode (`.mpy`, which saves the board compiling it in
RAM), gzips the web files, copies it all to the board, checks it arrived, and resets the board. Keep `mpy-cross`'s
bytecode version in line with the board's MicroPython (1.29 loads `.mpy` v6.3).

| Option | Effect |
|---|---|
| `-Port COM4` | Use a specific serial port instead of auto-detecting |
| `-ResetConfig` | Overwrite the board's `config.json` (it's otherwise only copied when the board has none) |
| `-PreserveProvisioning:$false` | Wipe the stored Wi-Fi details and name, so the board starts setup mode again |
| `-Wipe` | Delete everything on the board first, then deploy. It starts in setup mode |
| `-SkipReset` | Don't reset the board after copying |
| `-WiFi <host>[,<host>...]` | Update over Wi-Fi instead of USB (below) |
| `-Rebuild` | Compile every module again, not just those whose source changed |

On its first start the board opens a `PicoHello-SETUP` Wi-Fi hotspot: join it and open **`http://192.168.4.1`** to
choose its network and name. Holding BOOTSEL for 5 seconds while it runs starts setup mode again.

### Updating over Wi-Fi

Once the board runs it, with a web password set (Device tab):

```powershell
$env:PICOHELLO_WEB_PASSWORD = '...'   # or leave it unset to be asked
.\scripts\deploy.ps1 -WiFi <name>.local
```

It sends only the files that changed, and the board restarts onto them on trial: if the new version doesn't start
its web server within 3 minutes, twice, the board puts the old files back by itself. `main.py` and `otaboot.py`,
which apply updates and roll them back, only go over USB.

## Starting a new product from it

1. Copy the repository under a new name.
2. In `src/product.py`, change `NAME`, `SETUP_SSID` (its setup hotspot) and `NAME_PREFIX` (the start of a name made
   from the board's id), and replace the greeting with the product's own settings and hooks. App Base's
   `base/device.py` lists them all; for a light, see PlasmaStick Controller.
3. Start `src/version.py` at its first version, and put the product's settings in `config.example.json`.
4. In `src/www/index.html`, replace the Hello tab with the product's own; the Device, Network and MQTT tabs can stay.
5. Rename `PICOHELLO_WEB_PASSWORD` in `scripts/`, change the tests in `tests/` to match, and the README.

Keep an eye on memory: the smallest Pico has about 190 KB of heap, and App Base with a small product leaves plenty,
but each module and buffer counts. `/api/info` shows `mem_free`.

## How it's laid out

| Path | Is |
|---|---|
| `src/main.py` | What MicroPython starts: it applies a waiting update (or rolls one back), then imports `app.py`. Only updated over USB. |
| `src/app.py` | `run(product)` |
| `src/product.py`, `src/version.py` | What's this product's own: its name, settings and hooks (here `info`, `state`, `set`, `applied`, `HA_ENTITIES` and `ha_entity`), and its version |
| `src/base/` | A copy of App Base, which the tests check is unchanged: a fix goes into App Base, then `..\app-base\update-base.ps1 -Product src` copies it in (`-Tag vX.Y.Z` for a release of App Base). The deploy leaves out what's only for a Pi. |
| `src/lib/mqtt_as/` | The MQTT client, [mqtt_as](https://github.com/peterhinch/micropython-mqtt) |
| `src/www/index.html` | Its page, using App Base's `/base.css` and `/base.js` |
| `config.example.json` | The settings a first deploy puts on the board (a local `config.json`, gitignored, wins) |

## The page

| Tab | Has |
|---|---|
| Hello | The greeting and a box to change it, the firmware version, up time, time, free memory, Wi-Fi, IP address and MQTT |
| Device | The clock (time zone, summer time, time server), the web password, the log level, the watchdog, the name, restart and reset |
| Network | Changing Wi-Fi, setup mode, the Wi-Fi fallback, and how it connects |
| MQTT | The broker, the topic base and Home Assistant discovery |

## The API

From App Base, as every Earthstorm device's: `GET /api/info`, `GET` and `POST /api/config` (`{"hello":
{"greeting": "..."}}` changes the greeting), `POST /api/restart`, `/api/reset` and `/api/factory-reset` (with
`{"confirm": true}`), `POST /api/name`, `GET` and `POST /api/wifi` and `GET /api/wifi/networks`, `POST
/api/setup-mode`, and `/api/update` for updates over Wi-Fi. POSTs from other sites' pages are refused, and with a web
password set every request needs it (HTTP Basic, any username).

## MQTT

Under the topic base (`/home/device/{name}` unless changed):

| Topic | Is |
|---|---|
| `<base>/state` | The greeting, retained: `{"greeting": "..."}` |
| `<base>/set` | Changes it: `{"greeting": "..."}` |
| `<base>/status`, `<base>/info` | `online` or `offline`, and the board's health every minute, retained |
| `<base>/log` | Its warnings and errors (the last 8 kept while it's offline) |

With discovery on, Home Assistant finds the greeting as a text box, and the board's Wi-Fi signal, up time, free
memory and IP address.

## Tests

`py -m pytest` runs host-side tests of Pico Hello's own code, the PC's side of Wi-Fi updates, and that `src/base` is
App Base's copy unchanged, with stand-ins for the MicroPython-only modules. Anything that touches hardware or the
network needs the board.

To release: copy in a tagged App Base, put the version in `src/version.py`, check it on a board, and tag `vX.Y.Z`.

## Licence

MIT. See [LICENSE](LICENSE). Microdot (in App Base) and mqtt_as have their own licences: see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

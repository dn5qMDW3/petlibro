# PETLIBRO Integration for Home Assistant

[![hacs_badge][hacsbadge]][hacs] [![version][versionbadge]][versionlink]

Custom Home Assistant integration for PETLIBRO pet devices (feeders, fountains, litter boxes). Cloud-polling hub-based integration using the PETLIBRO API.

> **Based on** [jjjonesjr33/petlibro](https://github.com/jjjonesjr33/petlibro) — this is a maintained fork with additional features, bug fixes, and audit improvements. Original credit goes to [@jjjonesjr33](https://github.com/jjjonesjr33), [@C4-Dimitri](https://github.com/C4-Dimitri), and [@FeliGoblin](https://github.com/FeliGoblin) for the foundational work.

---

## Supported Devices

### Feeders
- Granary Smart Feeder (PLAF103) — V1 & V2
- Space Smart Feeder (PLAF107)
- Air Smart Feeder (PLAF108)
- Polar Wet Food Feeder (PLAF109)
- Granary Smart Camera Feeder (PLAF203)
- One RFID Smart Feeder (PLAF301)

### Fountains
- Dockstream Smart Fountain (PLWF105)
- Dockstream RFID Smart Fountain (PLWF305)
- Dockstream 2 Smart Fountain — Plug-In (PLWF106)
- Dockstream 2 Smart Fountain — Cordless (PLWF116)

### Litter Boxes
- Luma Smart Litter Box (PLLB001)

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu → **Custom repositories**
4. Add `https://github.com/dn5qMDW3/petlibro` as an **Integration**
5. Install **PETLIBRO** from HACS
6. Restart Home Assistant
7. Go to **Settings → Devices & Services → Add Integration** and search for **PETLIBRO**

### Manual

1. Download the latest [release](https://github.com/dn5qMDW3/petlibro/releases) `.zip`
2. Extract `custom_components/petlibro/` into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via **Settings → Devices & Services**

---

## Configuration

When adding the integration, enter:

- **Region** — `US` or `CN` (server region for your account)
- **Email** — your PETLIBRO account email
- **Password** — your PETLIBRO account password

> **Note:** PETLIBRO only allows one active session per account. If you keep the mobile app logged in, create a separate account for Home Assistant and share your devices to it.

---

## Features

- Real-time device data (60-second polling interval)
- Sensor entities for battery, water level, food level, weights, drinking statistics, etc.
- Switches for sound, light, child lock, deodorization, and other device toggles
- Buttons for manual feed, manual clean, lid open, timer resets, etc.
- Number inputs for volume, schedules, thresholds
- Selects for modes (clean mode, water dispensing mode, etc.)
- Firmware update notifications
- Multi-language support (13 languages)
- Account-level unit preferences (feed, water, weight)

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for the full PETLIBRO Cloud API reference.

---

## Pending / Experimental

- **Live camera feed** — Granary Smart Camera Feeder (PLAF203) and Luma Smart Litter Box (PLLB001) use TUTK/Kalay P2P video which isn't currently feasible to integrate directly into HA. Help welcome.
- **Real-time MQTT push** — PETLIBRO devices support MQTT for instant state updates. Currently blocked on certificate generation. See [docs/MQTT_RESEARCH.md](docs/MQTT_RESEARCH.md).

---

## Troubleshooting

### Enable debug logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.petlibro: debug
```

### First-time setup

After adding the integration, allow 1–5 minutes for all entities to populate. If entities are missing, restart Home Assistant.

### Common issues

- **Login fails** — Verify credentials and region. Code `1009` means the token expired (auto-handled). Code `1025` means a force logout (someone else logged in to the same account).
- **Devices missing** — Check your account on the PETLIBRO mobile app to confirm devices are bound. Shared devices appear with limited control.
- **Empty values** — Some devices return empty strings/null for unused fields. The integration filters these where possible.

---

## Companion Project

For a richer dashboard experience, check out [dn5qMDW3/petlibro-cards](https://github.com/dn5qMDW3/petlibro-cards) — custom Lovelace cards designed for this integration.

---

## License

GPL-3.0 — same as upstream.

---

## Acknowledgments

This integration is built on the work of:
- [@jjjonesjr33](https://github.com/jjjonesjr33) — original integration
- [@C4-Dimitri](https://github.com/C4-Dimitri) — co-developer
- [@FeliGoblin](https://github.com/FeliGoblin) — co-developer

Original repo: https://github.com/jjjonesjr33/petlibro

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-black.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[versionlink]: https://github.com/dn5qMDW3/petlibro/releases
[versionbadge]: https://img.shields.io/github/manifest-json/v/dn5qMDW3/petlibro?filename=custom_components%2Fpetlibro%2Fmanifest.json&color=slateblue&style=for-the-badge

# PETLIBRO MQTT / Real-Time Push — Research Notes

> Status: **Blocked** — certificate generation fails for shared accounts
> Last updated: 2026-04-15
> Source: APK v1.7.90 reverse engineering + live API testing

## Overview

PETLIBRO devices support MQTT for real-time event push. The app uses MQTT to receive instant notifications when devices change state (online/offline, cleaning complete, feeding done, etc.) instead of polling.

Currently the HA integration uses **cloud polling at 60s intervals**. MQTT would enable near-instant updates with minimal API calls.

## Infrastructure

| Component | Value | Verified |
|-----------|-------|----------|
| Broker (plain) | `mqtt.us.petlibro.com:1883` | Port open, requires auth |
| Broker (TLS) | `mqtt.us.petlibro.com:8883` | Port open, TLS works with CA cert |
| CA Certificate | `/member/certificate/ca` (GET) | Downloaded and validated |
| CA Issuer | `DesignLibroCA` (EJBCA-based PKI) | Confirmed from cert |
| CA Expiry | 2035-05-29 | From API response |
| Auth method | **Mutual TLS (client certificate)** | Confirmed — username/password rejected |
| App MQTT config | `/member/app/config` (POST, authenticated) | Returns broker hosts |

## MQTT Configuration (from `/member/app/config`)

```json
{
  "mqttTlsEnable": true,
  "appMqttHosts": [{ "host": "mqtt.us.petlibro.com", "port": 1883 }],
  "deviceMqttHosts": [{ "host": "mqtt.us.petlibro.com", "port": 1883 }],
  "appMqttsHosts": [{ "host": "mqtt.us.petlibro.com", "port": 8883 }],
  "deviceMqttsHosts": [{ "host": "mqtt.us.petlibro.com", "port": 8883 }]
}
```

## Topic Structure

From APK string extraction:

```
dl/{productId}/{deviceSn}/app/+/sub
```

Example: `dl/PLLB001/LB0102030312CEF4AE4D/app/+/sub`

The `+` wildcard matches different event types. The app subscribes to all events for each device using the wildcard.

### `getDeviceSnFromTopic` — the app extracts the device serial from the topic path.

## MQTT Event Types (Strategy Handlers)

Found in APK under `package:petlibro/app/component/dl_mqtt/mqtt_strategy/`:

### Device Events (`MqttDeviceStrategyHandler`)
| Handler | File | Purpose |
|---------|------|---------|
| `StrategyOnlineOffline` | `strategy_online_offline.dart` | Device online/offline status change |
| `StrategyRefreshEvent` | `strategy_refresh_event.dart` | Device data changed — triggers data refresh |
| `StrategyUnbind` | `strategy_unbind.dart` | Device was unbound/removed |

### User Events (`MqttUserStrategyHandler`)
| Handler | File | Purpose |
|---------|------|---------|
| `StrategyDeviceShareInvitation` | `strategy_device_share_invitation.dart` | Incoming device share invite |
| `StrategyDeviceShareCancel` | `strategy_device_share_cancel.dart` | Share cancelled |
| `StrategyMemberLogin` | `strategy_member_login.dart` | Account logged in elsewhere |
| `StrategyMemberRejectLogin` | `strategy_member_reject_login.dart` | Session kicked (forced logout) |
| `StrategyMemberActivated` | `strategy_member_activated.dart` | Account activated |
| `StrategyIAPServiceChange` | `strategy_iap_service_change.dart` | Subscription/IAP change |
| `StrategyAppLogService` | `strategy_app_log_service.dart` | App logging event |

## Certificate Auth Flow (from APK)

The app uses mutual TLS with client certificates. The flow is:

### Key Files
- `package:hi_mqtt/hi_mqtt.dart` — Main MQTT client wrapper
- `package:hi_mqtt/mqtt_certificate_util.dart` — Certificate management
- `package:petlibro/app/component/dl_mqtt/mqtt_strategy/mqtt_certificate_helper.dart` — Certificate helper
- `package:petlibro/app/component/dl_mqtt/mqtt.controller.dart` — MQTT controller
- `package:petlibro/app/component/dl_user/auth/login/controllers/login_mqtt.controller.dart` — Login→MQTT flow

### Certificate Generation Flow
1. App calls `generateKeyPair()` — generates RSA key pair (using `pointycastle` Dart package)
2. App calls `generateRsaCsrPem(commonName)` — creates PKCS#10 CSR with CN
3. App sends CSR to `POST /member/certificate/generate` with `{"csrPem": "<pem>"}`
4. Server signs CSR with EJBCA and returns signed client certificate
5. App stores cert locally and calls `POST /member/certificate/confirm` to acknowledge
6. App connects to MQTT broker using CA cert + client cert + private key

### Certificate Lifecycle
- `checkCertValid` / `checkCaCertValid` — checks expiry before each connection
- `deleteCertificate` / `deleteCertificateDir` — cleanup on logout
- `certificateReport` / `certificateReportSuccess` — report cert status to server
- `POST /member/certificate/error` — report certificate errors

## What We Tested

### Connection Tests
| Test | Port | Auth | Result |
|------|------|------|--------|
| No auth | 1883 | None | CONNACK rc=5 (Not authorized) |
| clientId/token | 1883 | Username/password | CONNACK rc=5 (Not authorized) |
| email/token | 1883 | Username/password | CONNACK rc=5 (Not authorized) |
| TLS + CA cert only | 8883 | None | CONNACK rc=5 (Not authorized) |
| TLS + CA + clientId/token | 8883 | Username/password | CONNACK rc=5 (Not authorized) |

**Conclusion:** Broker strictly requires mutual TLS with client certificate. No username/password fallback.

### Certificate Generation Tests
| CSR CN | Body Fields | Result |
|--------|-------------|--------|
| `APP_190201021` (clientId) | `{"csrPem": "<pem>"}` | Error 5995 |
| `190201021` (memberId) | `{"csrPem": "<pem>"}` | Error 5995 |
| `petlibro@erandom.xyz` | `{"csrPem": "<pem>"}` | Error 5995 |
| Various with commonName field | `{"csrPem": "<pem>", "commonName": "..."}` | Error 5995 |
| Empty body | `{}` | Error 5995 |
| Base64 only (no PEM armor) | `{"csrPem": "<b64>"}` | Error 5995 |
| 3072-bit key | `{"csrPem": "<pem>"}` | Error 5995 |
| Various subject formats | `/CN=.../O=DesignLibro` etc. | Error 5995 |

**Error 5995 = "Certificate generate failed"** — consistent regardless of request format.

### Likely Cause
**Verified server-side block.** Tested with multiple accounts:

| Account | Status | Active | Device Owner | Result |
|---------|--------|--------|--------------|--------|
| `petlibro@erandom.xyz` | 1 (active) | ✅ | No (shared) | 5995 |
| `pet@etandom.xyz` | 0 (inactive) | ❌ | Yes (owned) | 5995 |
| `pet@erandom.xyz` | 1 (active) | ✅ | Yes (owned) | 5995 |

The endpoint returns `5995 "Certificate generate failed"` regardless of:
- CSR format (PEM, DER base64, with/without commonName)
- Key size (2048, 3072)
- Account type (active/inactive, owner/shared)
- Request headers (including `appId`, `appSn`, `User-Agent`)
- CN value (`APP_xxxxxxxxx`, memberId, email)
- Body structure (flat, nested, empty)

Related endpoints tested:
- `GET /member/certificate/ca` — works (returns CA cert)
- `POST /member/certificate/confirm` — returns `5999 "TLS certificate does not exist"` (waiting on generate)
- `POST /member/certificate/error` — works (silent acknowledgment)
- `POST /device/certificate/generate` — returns `5994 "Device token invalid"` (different code path, for devices not apps)
- V2/V3/alternate endpoint variations — all 404

### Hypothesis
The `/member/certificate/generate` endpoint may be **disabled for third-party clients**. The official app likely sends a signature or uses certificate pinning that includes a secret only bundled in the real APK at runtime. The compiled Dart AOT code obscures the exact mechanism.

## CA Certificate (for reference)

Retrieved from `GET /member/certificate/ca`:

```
Issuer: CN=DesignLibroCA
Subject: CN=PetlibroCA
Valid: 2025-05-31 to 2035-05-29
Key: RSA 3072-bit
Downloads:
  PEM: https://dl-oss-prod.s3-accelerate.amazonaws.com/ejbca/PetlibroCA-Prod.pem
  CRT: https://dl-oss-prod.s3-accelerate.amazonaws.com/ejbca/PetlibroCA-Prod.crt
```

## PetKit Comparison

PetKit (a competing pet device brand) also uses MQTT but with a simpler auth model:

| | PetKit | PETLIBRO |
|---|--------|---------|
| MQTT auth | Device secret (username/password from API) | Client certificate (mutual TLS) |
| Cert generation | Not needed | Requires CSR signed by server |
| API endpoint | `user/iotDeviceInfo` returns MQTT creds directly | `/member/certificate/generate` |
| Difficulty to implement | Easy | Hard — blocked on cert generation |
| HA integration | [petkit](https://github.com/Jezza34000/py-petkit-api) has MQTT support | Not yet |

## Next Steps to Unblock

### Option 1: Test with device owner account
Try `/member/certificate/generate` with the account that originally set up the devices. If it works, the blocker is just account permissions.

### Option 2: MITM the real app
1. Install PETLIBRO app on a physical Android device
2. Set up mitmproxy with the CA cert installed as system cert
3. Log in and let the app connect to MQTT
4. Capture the exact `/member/certificate/generate` request payload
5. Note: The XAPK only has `armeabi_v7a` native libs, so emulator needs 32-bit ARM support or use a real device

### Option 3: Dart AOT decompilation
1. Use [blutter](https://github.com/aspect-dev/blutter) to decompile `libapp.so`
2. Find the `hi_mqtt` package's `generateRsaCsrPem` function
3. Extract exact CSR parameters (CN format, extensions, key usage, etc.)

### Option 4: Frida instrumentation
1. Root a real Android device or use an emulator with matching ABI
2. Use Frida to hook `generateRsaCsrPem` and `generateCertificate`
3. Capture the CSR before it's sent and the cert after it's received

## Proposed Integration Architecture (when unblocked)

```
┌─────────────────────────────────────────────┐
│              PetLibroHub                     │
│                                              │
│  ┌──────────────┐    ┌───────────────────┐  │
│  │  HTTP Poller  │    │  MQTT Subscriber  │  │
│  │  (60s backup) │    │  (real-time push) │  │
│  └──────┬───────┘    └────────┬──────────┘  │
│         │                     │              │
│         └─────────┬───────────┘              │
│                   │                          │
│         ┌─────────▼─────────┐               │
│         │  Device._data     │               │
│         │  (unified state)  │               │
│         └─────────┬─────────┘               │
│                   │                          │
│         ┌─────────▼─────────┐               │
│         │  Coordinator      │               │
│         │  emit(UPDATE)     │               │
│         └───────────────────┘               │
└─────────────────────────────────────────────┘
```

1. **Initial load** — HTTP API for full device state (same as now)
2. **MQTT subscribe** — connect to broker, subscribe to device topics
3. **On MQTT event** — `StrategyRefreshEvent` triggers targeted HTTP refresh of affected device
4. **On MQTT `StrategyOnlineOffline`** — update device availability immediately
5. **Fallback** — if MQTT disconnects, continue with 60s HTTP polling
6. **Certificate management** — generate cert on first setup, store in HA config, auto-renew before expiry

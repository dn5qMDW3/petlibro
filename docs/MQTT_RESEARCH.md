# PETLIBRO MQTT / Real-Time Push — Research Notes

> Status: **Cert generation UNBLOCKED** as of 2026-04-22.
> One MQTT-level detail (CONNECT rc=5) still open — see "Remaining".
> Source: APK v1.8.10 reverse engineering via MITM + Frida on an Android emulator.
>
> Supporting artifacts under `docs/research/`:
> - `frida-scripts/` — the script bundle that captured Flutter HTTP traffic (config.js
>   sanitized; replace `CERT_PEM` with your local mitmproxy CA before re-using).
> - `captured-requests.json` — sanitized request/response examples for each endpoint
>   touched during the investigation (tokens, CSRs, PEMs redacted; structure preserved).

## TL;DR

The "Error 5995" that blocked us for weeks was caused by a **single wrong field name**. Our Python
code sent `{"csrPem": "..."}`. The official app sends `{"csr": "..."}`. The server rejected the
former with a generic "Certificate generate failed" code regardless of any other tweak we tried.

With the correct field name (and the correct CSR subject format, captured from the live app), the
`/member/certificate/generate` + `/member/certificate/confirm` flow works end-to-end from Python,
with no HMAC, no appSecret, and no request signing.

Working cert + private key captured at `/tmp/petlibro_csr_and_cert/OUR_{cert,key}.pem` during the
investigation (ephemeral — regenerate via the working recipe below on demand).

## The Working Recipe

```python
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID

def generate_mqtt_cert(auth_token: str, member_id: str, timezone: str = "UTC"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "DesignLibro"),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, str(member_id)),
        ]))
        .sign(key, hashes.SHA256())
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

    headers = {
        "source": "ANDROID",
        "language": "EN",
        "timezone": timezone,
        "version": "1.8.10",
        "token": auth_token,
        "Content-Type": "application/json; charset=utf-8",
    }
    gen = requests.post(
        "https://api.us.petlibro.com/member/certificate/generate",
        headers=headers, json={"csr": csr_pem}, timeout=15,
    ).json()
    assert gen["code"] == 0, gen
    cert_pem = gen["data"]["certificate"]
    serial   = gen["data"]["serialNumber"]
    expires  = gen["data"]["expireTime"]  # epoch ms; ~3 years out

    cfm = requests.post(
        "https://api.us.petlibro.com/member/certificate/confirm",
        headers=headers, json={"serialNumber": serial}, timeout=15,
    ).json()
    assert cfm["code"] == 0, cfm

    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return key_pem, cert_pem, serial, expires
```

### CSR subject matters

The CSR subject is `CN=DesignLibro, serialNumber=<memberId>` — literally the CN string
`"DesignLibro"` plus the memberId stored under the `serialNumber` (OID 2.5.4.5) attribute. Other
formats we had previously guessed (`CN=APP_<memberId>`, `CN=<memberId>`, email) produce the same
error 5995 even with the correct field name.

### Cert attributes (from a server response)

- Issuer: `CN=PetlibroCA`
- Validity: 3 years
- Key usage: Digital Signature, Key Encipherment, Key Agreement
- Extended key usage: TLS Web Server + Client Authentication
- Signature: sha256WithRSA

### Broker CA trust chain

MQTT client needs to trust the broker cert, which is signed by `PetlibroCA` → `DesignLibroCA`
(root). Obtain both from `GET /member/certificate/ca` on the API, or extract from the APK's
`app_flutter/ca.crt` (the CA file is stored unencrypted; only the client cert + key are
encrypted at rest).

## Infrastructure

| Component | Value | Verified |
|-----------|-------|----------|
| Broker TLS | `mqtt.us.petlibro.com:8883` | Mutual-TLS accepts our generated cert |
| Broker plain | `mqtt.us.petlibro.com:1883` | Not used by app (requires mTLS) |
| CA issuer | `DesignLibroCA` (EJBCA-based) | |
| Cert lifetime | 3 years per issuance | From live response |
| App clientId | `APP_<memberId>` | From `user.hive` offset 0xd0 |

### App MQTT config (`/member/app/config`, with auth token)

```json
{
  "mqttTlsEnable": true,
  "appMqttHosts":    [{"host": "mqtt.us.petlibro.com", "port": 1883}],
  "appMqttsHosts":   [{"host": "mqtt.us.petlibro.com", "port": 8883}],
  "deviceMqttHosts": [{"host": "mqtt.us.petlibro.com", "port": 1883}],
  "deviceMqttsHosts":[{"host": "mqtt.us.petlibro.com", "port": 8883}]
}
```

## Captured request/response

### `POST /member/certificate/generate`

```
headers:
  source: ANDROID
  language: EN
  timezone: Europe/Berlin
  version: 1.8.10
  token: <session token from /member/auth/login>
  content-type: application/json; charset=utf-8

body:
  {"csr":"-----BEGIN CERTIFICATE REQUEST-----\n...\n-----END CERTIFICATE REQUEST-----"}

response:
  {"code":0,"msg":null,"data":{
    "certificate":"-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n",
    "serialNumber":"118493010925196852368124744824991405451",
    "responseFormat":"PEM",
    "expireTime":1871573685378
  }}
```

### `POST /member/certificate/confirm`

```
body:     {"serialNumber":"<value from generate response>"}
response: {"code":0,"msg":null,"data":null}
```

## Remaining: MQTT CONNECT rc=5

With a freshly generated cert, TLS mutual auth to `mqtt.us.petlibro.com:8883` **succeeds** —
the broker accepts our client cert at the TLS layer. The subsequent MQTT CONNECT packet is
rejected with rc=5 ("Not authorized"), regardless of:
- clientId format (`APP_<memberId>`, `<memberId>`, `app_<memberId>`, etc.)
- username/password permutations (email, memberId, clientId, token, stored password)
- whether the intermediate `PetlibroCA` is included in the client's presented chain
- whether the emulator app is still holding a session

This is a CONNECT-packet-content issue, not a cert issue. Two approaches to unblock:
1. Capture the exact CONNECT bytes from the live app via Frida (hook `SSL_write` inside
   `libflutter.so` — requires pattern-matching because symbols are stripped).
2. Write a tiny MQTT passthrough proxy on the host that TLS-terminates with mitmproxy CA,
   logs MQTT control packets in plaintext, then re-connects to the real broker with a
   *different* cert of our own.

## Topic structure (from APK strings)

```
dl/{productId}/{deviceSn}/app/+/sub
```

Example: `dl/PLLB001/LB0102030312CEF4AE4D/app/+/sub`

### Event strategy handlers (`package:petlibro/app/component/dl_mqtt/mqtt_strategy/`)

| Handler | Purpose |
|---------|---------|
| `StrategyOnlineOffline` | Device online/offline status change |
| `StrategyRefreshEvent` | Device data changed — app re-fetches via HTTP |
| `StrategyUnbind` | Device was unbound/removed |
| `StrategyDeviceShareInvitation` | Incoming device share invite |
| `StrategyDeviceShareCancel` | Share cancelled |
| `StrategyMemberLogin` | Account logged in elsewhere |
| `StrategyMemberRejectLogin` | Session kicked (forced logout) |
| `StrategyMemberActivated` | Account activated |
| `StrategyIAPServiceChange` | Subscription/IAP change |
| `StrategyAppLogService` | App logging event |

## MITM methodology that worked

Documented separately in `docs/mobile.md` (emulator + mitmproxy + Frida). The piece specific
to Flutter apps that the generic `mobile.md` recipe lacks:

- **Android system proxy isn't enough.** Flutter/Dart's `HttpClient` ignores `settings global http_proxy`.
  Redirecting via iptables DNAT also fails because mitmproxy's transparent mode doesn't recover
  the original destination on macOS.
- **The fix: httptoolkit's `native-connect-hook.js`** (from
  `github.com/httptoolkit/frida-interception-and-unpinning`). It intercepts `connect(2)` at the
  libc layer and redirects to the proxy, capturing both Java/WebView *and* Flutter/Dart traffic.
- **For MQTT traffic specifically**: set `IGNORED_NON_HTTP_PORTS = [1883, 8883]` in `config.js`,
  otherwise the native-connect-hook redirects MQTT to mitmproxy (which doesn't speak MQTT) and
  the app enters a `/member/certificate/error` retry loop.
- **Cert pinning**: the official PETLIBRO Flutter app does *not* pin against bundled CAs — once
  the mitmproxy CA is installed as a system certificate, TLS to `api.us.petlibro.com` works
  without further hooks. This simplifies things considerably vs many Flutter apps.

Full script bundle used:
```
config.js                  (PROXY_HOST=10.0.2.2 PROXY_PORT=8080, mitmproxy CA_PEM inlined)
native-connect-hook.js
android-system-certificate-injection.js
android-certificate-unpinning.js
android-proxy-override.js
android-disable-root-detection.js
```

## Encrypted local storage (for reference)

The app caches its client cert + key under `/data/data/com.designlibro.petlibro/app_flutter/certificate/<memberId>_client.{crt,key}` in AES-encrypted form (key wrapped by Android Keystore, stored in `shared_prefs/FlutterKeychain.xml`). We don't need to decrypt these — regenerating via `/certificate/generate` is simpler and gives us a key pair we can actually use (the app's private key never leaves its keystore-wrapped envelope).

## New API endpoints discovered (from live traffic)

Captured from the app but not currently used by this integration. Useful for future entities:

| Endpoint | Likely payload |
|---|---|
| `GET /device/msg/unreadQuantity` | Unread message count |
| `POST /member/pet/list` | Pet profiles (name, species, weight targets, activity goals) |
| `POST /device/deviceShare/sharePopList` | Pending device-share invitations |
| `POST /member/app/ota` | Alternative OTA feed (vs `/device/ota/getUpgrade`) |
| `GET /mall/pet/care/state` | PetCare subscription tier/state |
| `POST /member/app/commonConfig` | Keyed runtime config values |
| `GET /mall/device/cloud/saas/v2/state` | Cloud-storage SaaS state |
| `POST /notification/notification/push/config/report` | Push-token registration |

## Historical context (pre-unblock, kept for reference)

The original hypothesis was that the cert-generate endpoint required a request signature
bundled in the APK. It does not. The research doc previously tried many CSR formats, key
sizes, and CN values — all while sending `{"csrPem": ...}` instead of `{"csr": ...}`, so the
server's rejection was consistent regardless of content.

Tested accounts — all returned 5995 with `csrPem`, all work with `csr`:
- `petlibro@erandom.xyz` (active, shared device)
- `pet@etandom.xyz` (inactive, owner)
- `pet@erandom.xyz` (active, owner)

## Proposed integration architecture (for when CONNECT is solved)

```
┌─────────────────────────────────────────────┐
│              PetLibroHub                     │
│                                              │
│  ┌──────────────┐    ┌───────────────────┐  │
│  │  HTTP Poller  │    │  MQTT Subscriber  │  │
│  │  (fallback)   │    │  (real-time push) │  │
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
│         │  DataUpdateCoord. │               │
│         └───────────────────┘               │
└─────────────────────────────────────────────┘
```

1. On first config-entry setup: `generate_mqtt_cert(token, member_id)` → store PEM cert + key in
   `entry.data` (these are already-per-account credentials, same sensitivity as the stored password).
2. Connect paho-mqtt to `mqtt.us.petlibro.com:8883` with the cert + key + PetlibroCA chain.
3. Subscribe to `dl/+/<deviceSn>/app/+/sub` per device.
4. On inbound MQTT event:
   - `StrategyOnlineOffline` → flip device availability immediately.
   - `StrategyRefreshEvent` → trigger targeted HTTP refresh of that device's data.
5. Fall back to the current 60s HTTP poll if MQTT disconnects, until reconnection.
6. Renew the client cert before expiry (~3 years, but re-check at each startup via
   `/member/certificate/ca` for CA rotation).

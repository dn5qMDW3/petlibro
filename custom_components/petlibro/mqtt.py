"""Real-time push support for PETLIBRO via the vendor's MQTT broker.

The PETLIBRO app does not poll. It holds a mutual-TLS MQTT session and reacts to
``APP_REFRESH_EVENT`` pushes. This module gives the integration the same channel,
which turns a 60-second worst-case lag into roughly 200 milliseconds.

Protocol, recovered from the 1.8.95 Flutter client and verified against the live
broker:

* Broker — ``mqtt.us.petlibro.com:8883``, mutual TLS. Host and port come from
  ``/member/app/config`` (``appMqttsHosts``); the constants here are fallbacks.
* Client certificate — minted per account through ``/member/certificate/generate``
  with a ``CN=DesignLibro, serialNumber=<memberId>`` CSR, then acknowledged via
  ``/member/certificate/confirm``. Valid ~3 years.
* Identity — the CONNECT packet's client identifier, username **and** password
  are all the same string: ``clientId`` from the login response ("APP_<memberId>").
  Getting this wrong is what produced the long-standing CONNECT rc=5.
* Topics
    - ``dl/member/<memberId>/sub`` — account scope: share invitations, forced
      logout, subscription changes.
    - ``dl/<productIdentifier>/<deviceSn>/app/+/sub`` — per device. The broker's
      ACL rejects wildcards in the first two levels, so each device is
      subscribed explicitly.
* Payload — ``{"cmd": "APP_REFRESH_EVENT", "ts": <ms>, "msgId": <uuid>,
  "eventKeys": ["DEVICE_ATTR_CHANGE", ...]}``. This is a *signal to re-fetch*,
  not a state delta; the app reloads over HTTP when it arrives, and so do we.

paho-mqtt runs its network loop on its own thread, so every callback hops back
onto the Home Assistant event loop with ``call_soon_threadsafe``.
"""

from __future__ import annotations

import asyncio
import json
import ssl
import time
from collections.abc import Callable, Iterable
from logging import getLogger
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = getLogger(__name__)

DEFAULT_MQTT_HOST = "mqtt.us.petlibro.com"
DEFAULT_MQTT_PORT = 8883
KEEPALIVE = 60

# Config-entry keys for the cached client certificate.
CONF_MQTT_CERT = "mqtt_cert_pem"
CONF_MQTT_KEY = "mqtt_key_pem"
CONF_MQTT_CA = "mqtt_ca_pem"
CONF_MQTT_CERT_EXPIRY = "mqtt_cert_expire_ms"

# Re-mint the client certificate this long before it actually expires.
CERT_RENEW_MARGIN_MS = 30 * 24 * 60 * 60 * 1000  # 30 days

RC_MEANING = {
    0: "accepted",
    1: "refused: unacceptable protocol version",
    2: "refused: identifier rejected",
    3: "refused: server unavailable",
    4: "refused: bad username or password",
    5: "refused: not authorized",
}


class PetLibroMQTT:
    """Maintains the account's MQTT session and reports refresh events."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: Any,
        on_device_event: Callable[[str, list[str]], None],
        on_member_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.hass = hass
        self.api = api
        self._on_device_event = on_device_event
        self._on_member_event = on_member_event

        self._client: Any = None
        self._ssl_ctx: ssl.SSLContext | None = None
        self._host = DEFAULT_MQTT_HOST
        self._port = DEFAULT_MQTT_PORT
        self._member_id: str | None = None
        self._client_id: str | None = None

        # deviceSn -> topic, so we can diff on device list changes
        self._device_topics: dict[str, str] = {}
        self._member_topic: str | None = None

        self.connected = False
        self.last_event_at: float | None = None
        self.last_error: str | None = None
        self._started = False
        self._stopping = False

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    async def async_start(self, devices: Iterable[tuple[str, str]]) -> bool:
        """Connect and subscribe. `devices` yields (productIdentifier, deviceSn).

        Returns True when the broker accepted the connection. Never raises —
        MQTT is an optimisation, and polling remains the fallback.
        """
        if self._started:
            return self.connected
        try:
            await self._async_start(devices)
        except Exception as exc:  # noqa: BLE001 - must not break setup
            self.last_error = f"{type(exc).__name__}: {exc}"
            _LOGGER.warning(
                "MQTT push unavailable, falling back to polling only: %s", self.last_error
            )
            await self.async_stop()
            return False
        return self.connected

    async def _async_start(self, devices: Iterable[tuple[str, str]]) -> None:
        import paho.mqtt.client as mqtt  # deferred: declared in manifest requirements

        # `clientId` is only ever returned by the login endpoint, and a normal
        # restart reuses the stored token without logging in — so ask the API
        # for it, which falls back to a single login when it isn't cached yet.
        client_id, member_id = await self.api.async_ensure_identity()
        if not client_id:
            raise RuntimeError(
                "could not obtain clientId from the API; cannot authenticate to the broker"
            )
        self._client_id = str(client_id)
        self._member_id = str(member_id) if member_id else None

        await self._async_resolve_broker()
        certs = await self._async_ensure_certificates()
        self._ssl_ctx = await self.hass.async_add_executor_job(self._build_ssl_context, certs)

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self._client_id,
            protocol=mqtt.MQTTv311,
            clean_session=True,
        )
        client.tls_set_context(self._ssl_ctx)
        # The broker wants the same value in all three slots.
        client.username_pw_set(self._client_id, self._client_id)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=1, max_delay=120)
        self._client = client

        self._build_topics(devices)

        await self.hass.async_add_executor_job(
            lambda: client.connect(self._host, self._port, keepalive=KEEPALIVE)
        )
        client.loop_start()
        self._started = True

        # Give the broker a moment to answer so setup can report honestly.
        for _ in range(50):
            if self.connected:
                break
            await asyncio.sleep(0.1)

    async def async_stop(self) -> None:
        """Tear the session down."""
        self._stopping = True
        client, self._client = self._client, None
        self._started = False
        self.connected = False
        if client is None:
            return
        try:
            await self.hass.async_add_executor_job(client.loop_stop)
            await self.hass.async_add_executor_job(client.disconnect)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Error while closing MQTT session", exc_info=True)

    # ------------------------------------------------------------------
    # setup helpers
    # ------------------------------------------------------------------

    async def _async_resolve_broker(self) -> None:
        """Ask the API where the broker lives, falling back to known defaults."""
        try:
            cfg = await self.api.session.post("/member/app/config", json={})
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not read /member/app/config; using default broker", exc_info=True)
            return
        hosts = (cfg or {}).get("appMqttsHosts") or []
        if hosts and isinstance(hosts[0], dict):
            self._host = hosts[0].get("host") or DEFAULT_MQTT_HOST
            try:
                self._port = int(hosts[0].get("port") or DEFAULT_MQTT_PORT)
            except (TypeError, ValueError):
                self._port = DEFAULT_MQTT_PORT
        _LOGGER.debug("PETLIBRO MQTT broker resolved to %s:%s", self._host, self._port)

    async def _async_ensure_certificates(self) -> dict[str, str]:
        """Return a usable client cert/key/CA trio, minting a new one if needed."""
        entry = getattr(self.api, "config_entry", None)
        data = dict(entry.data) if entry else {}

        cert = data.get(CONF_MQTT_CERT)
        key = data.get(CONF_MQTT_KEY)
        ca = data.get(CONF_MQTT_CA)
        expiry = data.get(CONF_MQTT_CERT_EXPIRY)

        fresh_enough = (
            cert
            and key
            and isinstance(expiry, (int, float))
            and expiry - CERT_RENEW_MARGIN_MS > time.time() * 1000
        )

        if not fresh_enough:
            _LOGGER.debug("Minting a new PETLIBRO MQTT client certificate")
            member_id = self._member_id or getattr(self.api.session, "member_id", None)
            if not member_id:
                raise RuntimeError("no memberId available for the certificate CSR")
            minted = await self.api.generate_mqtt_cert(member_id)
            cert = minted["cert_pem"]
            key = minted["key_pem"]
            expiry = minted.get("expire_time_ms")

        if not ca:
            ca = await self.api.get_mqtt_ca_cert()

        if entry is not None and self.api.hass is not None:
            self.api.hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_MQTT_CERT: cert,
                    CONF_MQTT_KEY: key,
                    CONF_MQTT_CA: ca,
                    CONF_MQTT_CERT_EXPIRY: expiry,
                },
            )

        return {"cert": cert, "key": key, "ca": ca}

    @staticmethod
    def _build_ssl_context(certs: dict[str, str]) -> ssl.SSLContext:
        """Build a fully-verifying mutual-TLS context.

        The broker certificate chains to PetlibroCA / DesignLibroCA, which the
        API hands us at ``/member/certificate/ca`` — so the server is verified
        against that chain rather than the system trust store.
        """
        import tempfile
        from pathlib import Path

        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        with tempfile.TemporaryDirectory(prefix="petlibro_mqtt_") as tmp:
            base = Path(tmp)
            ca_path = base / "ca.pem"
            crt_path = base / "client.crt"
            key_path = base / "client.key"
            ca_path.write_text(certs["ca"])
            crt_path.write_text(certs["cert"])
            key_path.write_text(certs["key"])
            ctx.load_verify_locations(str(ca_path))
            ctx.load_cert_chain(str(crt_path), str(key_path))
        return ctx

    def _build_topics(self, devices: Iterable[tuple[str, str]]) -> None:
        self._device_topics = {
            serial: f"dl/{product}/{serial}/app/+/sub"
            for product, serial in devices
            if product and serial
        }
        self._member_topic = f"dl/member/{self._member_id}/sub" if self._member_id else None

    async def async_sync_devices(self, devices: Iterable[tuple[str, str]]) -> None:
        """Subscribe to any device that appeared since the last sync."""
        if not self._client or not self.connected:
            return
        previous = set(self._device_topics)
        self._build_topics(devices)
        for serial, topic in self._device_topics.items():
            if serial not in previous:
                _LOGGER.debug("Subscribing to newly seen device %s", serial)
                self._client.subscribe(topic, 0)

    # ------------------------------------------------------------------
    # paho callbacks (worker thread)
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        rc = int(getattr(reason_code, "value", reason_code) or 0)
        if rc != 0:
            self.connected = False
            self.last_error = RC_MEANING.get(rc, f"CONNACK rc={rc}")
            _LOGGER.error("PETLIBRO MQTT connection refused: %s", self.last_error)
            return

        self.connected = True
        self.last_error = None
        topics = [t for t in (self._member_topic, *self._device_topics.values()) if t]
        _LOGGER.info(
            "PETLIBRO MQTT connected to %s:%s as %s; subscribing to %d topic(s)",
            self._host,
            self._port,
            self._client_id,
            len(topics),
        )
        for topic in topics:
            client.subscribe(topic, 0)

    def _on_disconnect(self, client, userdata, *args) -> None:
        self.connected = False
        if not self._stopping:
            _LOGGER.info("PETLIBRO MQTT disconnected; paho will retry automatically")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8", "replace"))
        except (ValueError, AttributeError):
            _LOGGER.debug("Ignoring non-JSON MQTT payload on %s", msg.topic)
            return
        self.hass.loop.call_soon_threadsafe(self._handle_message, msg.topic, payload)

    # ------------------------------------------------------------------
    # event-loop side
    # ------------------------------------------------------------------

    def _handle_message(self, topic: str, payload: dict[str, Any]) -> None:
        self.last_event_at = time.time()
        cmd = payload.get("cmd") or ""
        _LOGGER.debug("MQTT push on %s: %s", topic, payload)

        parts = topic.split("/")
        # dl/<product>/<deviceSn>/app/<kind>/sub
        if len(parts) >= 4 and parts[0] == "dl" and parts[1] != "member":
            serial = parts[2]
            keys = payload.get("eventKeys") or []
            if not isinstance(keys, list):
                keys = [str(keys)]
            try:
                self._on_device_event(serial, [str(k) for k in keys])
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error dispatching MQTT device event for %s", serial)
            return

        if self._on_member_event is not None:
            try:
                self._on_member_event(cmd, payload)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error dispatching MQTT member event %s", cmd)

    @property
    def diagnostics(self) -> dict[str, Any]:
        """Status surface for the diagnostics download and the status sensor."""
        return {
            "connected": self.connected,
            "broker": f"{self._host}:{self._port}",
            "client_id": self._client_id,
            "subscribed_devices": sorted(self._device_topics),
            "member_topic": self._member_topic,
            "last_event_at": self.last_event_at,
            "last_error": self.last_error,
        }

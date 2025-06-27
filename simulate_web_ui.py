#!/usr/bin/env python
"""
Integration-style smoke test for the Z-Waif Web UI.

Usage:
 1. Make sure `python -m pip install gradio_client requests` is done once.
 2. Start Z-Waif so the Web UI is running at http://localhost:7864.
 3. Run `python simulate_web_ui.py` in another terminal.

The script fetches the UI's /config to discover every exposed API endpoint
and then attempts to call each one with a reasonable dummy payload.
It prints a concise pass/fail table so you can quickly verify that every
callback in utils/web_ui.py is still functional after refactors.

Note: This is *not* a comprehensive unit-test suite – it simply ensures
all endpoints respond without raising an HTTP or validation error.
You can extend the `EXAMPLE_INPUTS` map below if new component types are
added to the UI.
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, List

import requests
from gradio_client import Client, utils as gr_utils

# ---------------------- Configuration ---------------------- #
WEB_PORT = 7864
BASE_URL = f"http://localhost:{WEB_PORT}"
TIMEOUT = 10  # seconds to wait for UI to start responding

# Mapping of Gradio component types → dummy example value to send.
EXAMPLE_INPUTS: Dict[str, Any] = {
    "textbox": "test input",
    "multiline": "multiline test",
    "slider": 42,
    "checkbox": True,
    "checkboxgroup": [True],
    "number": 7,
    "radio": None,  # will be replaced by an option dynamically
    "dropdown": None,
    "button": None,  # buttons usually have no positional input
    "image": None,
    "chatbot": [],  # empty history
}

# Max seconds to wait for a single endpoint before marking as timeout
PER_EP_TIMEOUT = 6

# ---------------------- Helpers ---------------------- #

def wait_for_server() -> None:
    """Poll /config until the Web UI is up or TIMEOUT reached."""
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/config", timeout=2)
            if r.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    print(f"[ERROR] Could not reach Web UI at {BASE_URL} within {TIMEOUT}s", file=sys.stderr)
    sys.exit(1)


def fetch_api_info(client: Client) -> List[Dict[str, Any]]:
    """Return list of endpoint dicts (api_name, inputs, etc.)."""
    try:
        return client.view_api(return_format="dict")  # type: ignore[arg-type]
    except Exception as e:
        print(f"Failed to retrieve API metadata: {e}", file=sys.stderr)
        sys.exit(1)


def build_input_payload(endpoint: Dict[str, Any]) -> List[Any]:
    """Construct argument list matching the endpoint's input signature."""
    payload: List[Any] = []
    for component in endpoint.get("inputs", []):
        ctype = component.get("type", "textbox")
        val = EXAMPLE_INPUTS.get(ctype)

        # Provide first available choice for radios/dropdowns if not preset
        if val is None and ctype in {"radio", "dropdown"}:
            choices = component.get("choices", [])
            val = choices[0] if choices else None

        payload.append(val)
    return payload

# ---------------------- Main ---------------------- #

def main() -> None:
    print("Waiting for Web UI…", end=" ", flush=True)
    wait_for_server()
    print("OK")

    client = Client(BASE_URL, verbose=False, ssl_verify=False)
    raw_info = fetch_api_info(client)

    # The gradio client may return a dict keyed by endpoint name. Normalize to list of endpoint
    # metadata dictionaries so the rest of the script can treat each uniformly.
    if isinstance(raw_info, dict):
        endpoints = []

        # 1) Named endpoints come under key "named_endpoints" (dict of api_name -> meta)
        named = raw_info.get("named_endpoints", {})
        if isinstance(named, dict):
            for api_name, meta in named.items():
                meta = meta or {}
                if isinstance(meta, dict):
                    meta = {**meta}
                    meta["_api_name"] = api_name
                endpoints.append(meta)

        # 2) Un-named endpoints are a list under "unnamed_endpoints"
        unnamed = raw_info.get("unnamed_endpoints", [])
        if isinstance(unnamed, list):
            endpoints.extend(unnamed)

        # 3) Edge-case: older gradio may return api dict at top-level
        if not endpoints:
            for key, meta in raw_info.items():
                if key in {"named_endpoints", "unnamed_endpoints"}:
                    continue
                meta = meta or {}
                if isinstance(meta, dict):
                    meta = {**meta, "_api_name": key}
                endpoints.append(meta)
    elif isinstance(raw_info, list):
        endpoints = raw_info  # already list-like
    else:
        print(f"Unrecognised view_api payload: {type(raw_info)}", file=sys.stderr)
        sys.exit(1)

    if not endpoints:
        print("No API endpoints discovered – is the UI exposing any?", file=sys.stderr)
        sys.exit(1)

    print(f"Discovered {len(endpoints)} endpoints. Beginning simulation…\n")
    results = {}

    for ep in endpoints:
        name = ep.get("_api_name") or ep.get("api_name") or f"fn_index={ep.get('fn_index')}"

        # Skip known long-running watcher endpoints
        if "continuous_coro" in name:
            results[name] = ("SKIP", "skipped long-running endpoint")
            continue

        payload = build_input_payload(ep)
        status: str
        detail: str
        # Worker to invoke predict; result via queue
        import threading, queue
        q: "queue.Queue[tuple[str,str]]" = queue.Queue()

        def _worker():
            try:
                if payload and any(item is not None for item in payload):
                    client.predict(*payload, api_name=name)
                else:
                    client.predict(api_name=name)
                q.put(("PASS", "success"))
            except Exception as exc:
                q.put(("FAIL", str(exc).split("\n")[0]))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        try:
            res_status, res_detail = q.get(timeout=PER_EP_TIMEOUT)
        except queue.Empty:
            res_status, res_detail = "TIMEOUT", f">{PER_EP_TIMEOUT}s"
        results[name] = (res_status, res_detail)

    print("--- Simulation Results ---")
    for ep_name, (stat, msg) in results.items():
        print(f"{ep_name:<25} {stat:<5} {msg}")

    failures = [k for k, v in results.items() if v[0] in {"FAIL", "TIMEOUT"}]
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main() 
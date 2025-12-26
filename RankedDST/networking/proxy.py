"""
RankedDST/networking/proxy.py

This module establishes a proxy server that forwards requests from

http://localhost:3035 -> http://localhost:5000 or https://dontgetlosttogether.com/api
"""

from flask import Flask, request, Response
import requests
import json

import RankedDST.state as state


def _backend_url() -> str:
    if state.Developing:
        return "http://localhost:5000"
    return "https://dontgetlosttogether.com/api"


def _forward_to_backend(endpoint: str, payload: dict) -> Response:
    # Inject secret hash
    raw_secret = state.GetKleiSecret()
    payload["klei_secret_hash"] = state.HashString(raw_secret)

    try:
        resp = requests.post(
            _backend_url() + endpoint,
            json=payload,
            timeout=5,
        )
    except requests.RequestException:
        return Response(
            json.dumps({"error": "backend unreachable"}),
            status=502,
            mimetype="application/json",
        )

    return Response(
        resp.content,
        status=resp.status_code,
        mimetype=resp.headers.get("Content-Type", "application/json"),
    )


def create_proxy() -> Flask:
    """
    Creates a flask object to be used as a proxy

    Routes
    ------
    - day_reached
    - flare_used
    - boss_killed
    - player_revived
    - player_died

    Returns
    -------
    proxy_app: flask.Flask
        The flask object
    """

    proxy_app = Flask(__name__)

    @proxy_app.post("/day_reached")
    def day_reached():
        payload = request.get_json(silent=True)
        if not payload:
            return {"error": "invalid json"}, 400

        print(
            f"[day_reached] klei_id={payload.get('klei_id')} "
            f"day={payload.get('day')} "
            f"character={payload.get('character')} "
            f"seed={payload.get('seed')}"
        )

        if state.get_match_state() == state.MatchWorldReady:
            state.set_match_state(state.MatchInProgress)
            print("  Player has started their run!")

        return _forward_to_backend("/day_reached", payload)

    @proxy_app.post("/flare_used")
    def flare_used():
        payload = request.get_json(silent=True)
        if not payload:
            return {"error": "invalid json"}, 400

        print(
            f"[flare_used] klei_id={payload.get('klei_id')} "
            f"day={payload.get('day')} "
            f"character={payload.get('character')} "
            f"seed={payload.get('seed')}"
        )

        return _forward_to_backend("/flare_used", payload)

    @proxy_app.post("/boss_killed")
    def boss_killed():
        payload = request.get_json(silent=True)
        if not payload:
            return {"error": "invalid json"}, 400

        print(
            f"[boss_killed] klei_id={payload.get('klei_id')} "
            f"boss={payload.get('boss_name')} "
            f"day={payload.get('day')}"
        )

        return _forward_to_backend("/boss_killed", payload)

    @proxy_app.post("/player_died")
    def player_died():
        payload = request.get_json(silent=True)
        if not payload:
            return {"error": "invalid json"}, 400

        print(
            f"[player_died] klei_id={payload.get('klei_id')} "
            f"death_cause={payload.get('death_cause')} "
            f"day={payload.get('day')}"
        )

        return _forward_to_backend("/player_died", payload)

    @proxy_app.post("/player_revived")
    def player_revived():
        payload = request.get_json(silent=True)
        if not payload:
            return {"error": "invalid json"}, 400

        print(
            f"[player_revived] klei_id={payload.get('klei_id')} "
            f"revive_method={payload.get('revive_method')} "
            f"day={payload.get('day')}"
        )

        return _forward_to_backend("/player_revived", payload)

    return proxy_app


def start_proxy_server(host: str, port: int) -> None:
    """
    Creates and runs a flask proxy server at the host url with the specified port
    """
    proxy_app = create_proxy()

    print(f"🌐 Proxy listening on {host}:{port}")
    proxy_app.run(
        host=host, 
        port=port, 
        threaded=True, 
        use_reloader=False
    )

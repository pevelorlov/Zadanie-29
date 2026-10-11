"""Живая проверка Дня 27: Flask API -> LM Studio -> ответ модели."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import Agent, AgentSettings, RoutingProvider  # noqa: E402
from app import create_app  # noqa: E402


def main() -> int:
    settings = AgentSettings(
        model="ornith-1.5-9b",
        temperature=0.2,
        max_tokens=512,
        reasoning_enabled=False,
    )
    with tempfile.TemporaryDirectory(prefix="day27-live-") as temp_dir:
        app = create_app(Path(temp_dir), Agent(RoutingProvider()))
        app.config.update(TESTING=True)
        client = app.test_client()

        client.post("/api/task-control/disable", json={})
        client.post("/api/mcp-control/disable", json={})
        preset_response = client.post("/api/presets", json={
            "name": "Day 27 · LM Studio",
            "description": "Живая проверка маршрутизации локального пресета",
            "settings": settings.to_dict(),
        })
        if preset_response.status_code != 201:
            print(json.dumps(preset_response.get_json(), ensure_ascii=False, indent=2))
            return 1
        preset = preset_response.get_json()["preset"]
        created = client.post("/api/conversations", json={"title": "Day 27 smoke"})
        if created.status_code != 201:
            print(json.dumps(created.get_json(), ensure_ascii=False, indent=2))
            return 1
        conversation_id = created.get_json()["conversation"]["id"]

        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "content": "Ответь одним словом: столица Франции?",
                "preset_id": preset["id"],
                "settings": preset["settings"],
                "rag": {"enabled": False},
            },
        )
        payload = response.get_json()
        if response.status_code != 200:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1

        assistant = payload["conversation"]["visible_messages"][-1]
        result = {
            "ok": True,
            "http_status": response.status_code,
            "model": assistant["technical"].get("model"),
            "provider": assistant["technical"].get("provider"),
            "configuration_source": assistant["technical"].get("configuration_source"),
            "answer": assistant["content"],
            "usage": assistant["technical"].get("usage"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if assistant["content"].strip() else 2


if __name__ == "__main__":
    raise SystemExit(main())

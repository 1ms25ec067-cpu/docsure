import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


QUEUE_FILE = Path("offline_queue.json")


class OfflineQueue:

    def __init__(self):
        self.queue_file = QUEUE_FILE
        self.queue_file.touch(exist_ok=True)

        if self.queue_file.stat().st_size == 0:
            self._write([])

    def _read(self):
        try:
            return json.loads(self.queue_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, events):
        self.queue_file.write_text(
            json.dumps(events, indent=2),
            encoding="utf-8",
        )

    def add(self, event_type, application_id, result):
        events = self._read()

        event = {
            "event_id": f"OFF-{uuid4().hex[:8].upper()}",
            "event_type": event_type,
            "application_id": application_id,
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "synced": False,
        }

        events.append(event)
        self._write(events)

        return event

    def get_pending(self):
        return [
            event
            for event in self._read()
            if not event.get("synced", False)
        ]

    def mark_synced(self, event_ids):
        events = self._read()

        for event in events:
            if event["event_id"] in event_ids:
                event["synced"] = True
                event["synced_at"] = datetime.now(
                    timezone.utc
                ).isoformat()

        self._write(events)

    def get_all(self):
        return self._read()


offline_queue = OfflineQueue()
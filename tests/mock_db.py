"""In-memory mock Supabase client for deterministic API testing."""

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional


class MockBucket:
    def __init__(self, bucket_name: str) -> None:
        self.bucket = bucket_name
        self.files: dict[str, bytes] = {}

    def upload(
        self, filename: str, data: bytes, options: Optional[dict] = None
    ) -> None:
        self.files[filename] = data

    def get_public_url(self, filename: str) -> str:
        return f"https://mock.supabase.co/storage/v1/object/public/{self.bucket}/{filename}"

    def create_signed_url(self, path: str, expires_in: int = 900) -> dict[str, str]:
        return {
            "signedURL": f"https://mock.supabase.co/storage/v1/object/sign/{self.bucket}/{path}?token=signed-token"
        }

    def remove(self, paths: list[str]) -> None:
        for p in paths:
            self.files.pop(p, None)


class MockStorage:
    def __init__(self) -> None:
        self.buckets: dict[str, MockBucket] = {}

    def from_(self, bucket_name: str) -> MockBucket:
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = MockBucket(bucket_name)
        return self.buckets[bucket_name]


class MockTableQuery:
    def __init__(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        self.table_name = table_name
        self.all_rows = rows
        self._filters: list[tuple[str, str, Any]] = []  # (op, field, value)
        self._order_field: Optional[str] = None
        self._order_desc: bool = False
        self._limit: Optional[int] = None
        self._selected_columns: Optional[str] = None
        self._pending_update: Optional[dict[str, Any]] = None
        self._pending_insert: Optional[list[dict[str, Any]]] = None

    def select(self, columns: str = "*") -> "MockTableQuery":
        self._selected_columns = columns
        return self

    def eq(self, field: str, value: Any) -> "MockTableQuery":
        self._filters.append(("eq", field, value))
        return self

    def gte(self, field: str, value: Any) -> "MockTableQuery":
        self._filters.append(("gte", field, value))
        return self

    def order(self, field: str, desc: bool = False) -> "MockTableQuery":
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, count: int) -> "MockTableQuery":
        self._limit = count
        return self

    def insert(self, data: Any) -> "MockTableQuery":
        items = data if isinstance(data, list) else [data]
        self._pending_insert = deepcopy(items)
        return self

    def update(self, data: dict[str, Any]) -> "MockTableQuery":
        self._pending_update = deepcopy(data)
        return self

    def execute(self) -> Any:
        # Handle Insert
        if self._pending_insert is not None:
            inserted: list[dict[str, Any]] = []
            for item in self._pending_insert:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                if "created_at" not in item:
                    item["created_at"] = datetime.now(timezone.utc).isoformat()
                if "changed_at" not in item:
                    item["changed_at"] = datetime.now(timezone.utc).isoformat()
                self.all_rows.append(item)
                inserted.append(deepcopy(item))
            res = type("Result", (), {})()
            res.data = inserted
            return res

        # Filter rows
        matched = list(self.all_rows)
        for op, field, val in self._filters:
            if op == "eq":
                matched = [r for r in matched if str(r.get(field)) == str(val)]
            elif op == "gte":
                matched = [r for r in matched if str(r.get(field)) >= str(val)]

        # Handle Update
        if self._pending_update is not None:
            updated: list[dict[str, Any]] = []
            for r in matched:
                r.update(self._pending_update)
                updated.append(deepcopy(r))
            res = type("Result", (), {})()
            res.data = updated
            return res

        # Order
        if self._order_field:
            matched.sort(
                key=lambda x: str(x.get(self._order_field, "")),
                reverse=self._order_desc,
            )

        # Limit
        if self._limit is not None:
            matched = matched[: self._limit]

        res = type("Result", (), {})()
        res.data = [deepcopy(r) for r in matched]
        return res


class MockSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "complaints": [],
            "status_history": [],
            "departments": [],
        }
        self.storage = MockStorage()

    def table(self, table_name: str) -> MockTableQuery:
        if table_name not in self.tables:
            self.tables[table_name] = []
        return MockTableQuery(table_name, self.tables[table_name])

    def clear(self) -> None:
        for rows in self.tables.values():
            rows.clear()
        self.storage.buckets.clear()

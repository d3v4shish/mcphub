import ipaddress
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Protocol = Literal["TCP", "UDP", "ICMP"]
Action = Literal["ALLOW", "BLOCK"]
GroupBy = Literal["protocol", "action", "src_ip", "dst_ip"]


class FirewallFilters(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    protocol: Protocol | None = None
    action: Action | None = None
    dst_port: int | None = Field(default=None, ge=0, le=65535)

    @field_validator("src_ip", "dst_ip")
    @classmethod
    def valid_ip(cls, value: str | None) -> str | None:
        if value is not None:
            ipaddress.ip_address(value)
        return value

    def clauses(self) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        values: list[object] = []
        for column, value in (
            ("timestamp >=", self.start_at.isoformat() if self.start_at else None),
            ("timestamp <=", self.end_at.isoformat() if self.end_at else None),
            ("src_ip =", self.src_ip),
            ("dst_ip =", self.dst_ip),
            ("protocol =", self.protocol),
            ("action =", self.action),
            ("dst_port =", self.dst_port),
        ):
            if value is not None:
                clauses.append(f"{column} ?")
                values.append(value)
        return clauses, values


class FirewallRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path.resolve()

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.is_file():
            raise FileNotFoundError(f"Firewall database does not exist: {self.database_path}")
        return sqlite3.connect(f"file:{self.database_path}?mode=ro", uri=True)

    def search(self, filters: FirewallFilters, limit: int = 25, offset: int = 0) -> dict:
        limit = min(max(limit, 1), 100)
        offset = max(offset, 0)
        clauses, values = filters.clauses()
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT timestamp, src_ip, dst_ip, src_port, dst_port, protocol, action, bytes_transferred "
            f"FROM firewall_logs{where} ORDER BY timestamp LIMIT ? OFFSET ?"
        )
        with self._connect() as connection:
            cursor = connection.execute(sql, [*values, limit, offset])
            fields = [column[0] for column in cursor.description]
            events = [dict(zip(fields, row, strict=True)) for row in cursor.fetchall()]
        return {"events": events, "limit": limit, "offset": offset, "returned": len(events)}

    def summarize(self, filters: FirewallFilters, group_by: GroupBy = "action") -> dict:
        if group_by not in {"protocol", "action", "src_ip", "dst_ip"}:
            raise ValueError("Unsupported group_by field")
        clauses, values = filters.clauses()
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT {group_by} AS group_value, COUNT(*) AS event_count, "
            f"COALESCE(SUM(bytes_transferred), 0) AS bytes_transferred FROM firewall_logs{where} "
            f"GROUP BY {group_by} ORDER BY event_count DESC, group_value LIMIT 100"
        )
        with self._connect() as connection:
            cursor = connection.execute(sql, values)
            fields = [column[0] for column in cursor.description]
            groups = [dict(zip(fields, row, strict=True)) for row in cursor.fetchall()]
        return {
            "filters": filters.model_dump(mode="json", exclude_none=True),
            "group_by": group_by,
            "groups": groups,
        }

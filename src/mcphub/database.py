from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class MCPServerRecord(Base):
    __tablename__ = "mcp_servers"
    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    mcp_url: Mapped[str] = mapped_column(String(512), unique=True)
    manifest_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="online")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AgentRecord(Base):
    __tablename__ = "agents"
    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text)


class AgentServerRecord(Base):
    __tablename__ = "agent_servers"
    agent_name: Mapped[str] = mapped_column(ForeignKey("agents.name", ondelete="CASCADE"), primary_key=True)
    server_name: Mapped[str] = mapped_column(ForeignKey("mcp_servers.name"), primary_key=True)
    allowed_tools_json: Mapped[str] = mapped_column(Text)


def utcnow() -> datetime:
    return datetime.now(UTC)


def make_session_factory(database_path: Path) -> sessionmaker[Session]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{database_path.resolve()}", connect_args={"check_same_thread": False, "timeout": 5}
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)

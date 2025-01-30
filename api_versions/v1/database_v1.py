"""
YOAS-(Your-Own-Anti-Spam-System)-API
=================================
"""

# Other imports
import os
from datetime import datetime, UTC

# Main imports
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Config loading
load_dotenv()
db_file = os.path.join(
    os.getenv("DB_N_LOGS_FOLDER", "db_n_logs"),
    os.getenv("DB_FILE", "yoas.db")
)
if not db_file.endswith(".db"):
    db_file += ".db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer,
        autoincrement=False,
        index=True,
        nullable=False,
        primary_key=True
    )
    ban_reason = Column(String)
    additional_info = Column(String)
    utc_created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return (f"User ID: {self.user_id}\n"
                f"Ban reason: {self.ban_reason}\n"
                f"Additional info: {self.additional_info}\n"
                f"Added at (UTC): {self.utc_created_at}\n"
                f"Messages: {self.messages}")

    def __repr__(self):
        return (f"User(user_id={self.user_id}, "
                f"ban_reason={self.ban_reason}, "
                f"additional_info={self.additional_info}, "
                f"utc_created_at={self.utc_created_at}, "
                f"messages={self.messages})")


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        Integer,
        autoincrement=True,
        index=True,
        nullable=False,
        primary_key=True
    )
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    text = Column(String, nullable=False)
    user = relationship("User", back_populates="messages")

    def __str__(self):
        return (f"Message ID: {self.id}\n"
                f"User ID: {self.user_id}\n"
                f"Text: {self.text}")

    def __repr__(self):
        return (f"Message(id={self.id}, "
                f"user_id={self.user_id}, "
                f"text={self.text})")


Base.metadata.create_all(bind=engine)

# Other imports
import os
import csv
import json
import shutil
from enum import StrEnum
from typing import Any, Dict, List

# Main imports
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float  # noqa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .database_v1 import SessionLocal, User, Message

__all__ = [
    "Dumper",
    "TableName", "FileFormat",
    "UserInclude", "UserOrderBy",
    "MessageInclude", "MessageOrderBy"
]

# Config loading
load_dotenv()
original_db_file = os.path.join(
    os.getenv("DB_N_LOGS_FOLDER", "db_n_logs"),
    os.getenv("DB_FILE", "wall_of_text.db")
)
if not original_db_file.endswith(".db"):
    original_db_file += ".db"


class TableName(StrEnum):
    USERS = "users"
    MESSAGES = "messages"


class FileFormat(StrEnum):
    DB = "db"
    CSV = "csv"
    JSON = "json"


class UserInclude(StrEnum):
    USER_ID = "user_id"
    BAN_REASON = "ban_reason"
    ADDITIONAL_INFO = "additional_info"
    LAST_MESSAGE = "last_message"
    TIMESTAMP = "timestamp_utc_created_at"
    TIME = "string_utc_created_at"


class UserOrderBy(StrEnum):
    USER_ID = "user_id"
    BAN_REASON = "ban_reason"
    ADDITIONAL_INFO = "additional_info"
    TIME = "utc_created_at"


class MessageInclude(StrEnum):
    MESSAGE_ID = "id"
    USER_ID = "user_id"
    TEXT = "text"


class MessageOrderBy(StrEnum):
    MESSAGE_ID = "id"
    USER_ID = "user_id"
    TEXT = "text"


class Dumper:
    @staticmethod
    def dump(
        table: TableName | str,
        file_format: FileFormat | str,
        filename: str = "dump",
        include: List[UserInclude | MessageInclude | str] | None = None,
        order_by: List[UserOrderBy | MessageOrderBy | str] | None = None,
        original_db: bool = False,
        indent: int = None
    ) -> None:
        """
        Dump all data from database to file

        ``filename`` parameter is name of the file without file extension.
        Extension will be added based on the ``file_format`` parameter,
        regardless of whether there is format in the ``filename`` or not.

        ``original_db`` parameter is only used for DB format, otherwise it is
        ignored. If this parameter is set to True and ``file_format`` is DB -
        parameters ``table``, ``include`` and ``order_by`` will be ignored.
        This parameter used for creating a 1:1 copy of original database.

        ``indent`` is only used for JSON format, otherwise it is ignored.
        It is used for indentation in JSON file, if set to 0 or None -
        file will be in one line without any indentation.

        Parameters ``include`` and ``order_by`` must be without duplicates,
        because they follow the order of the list that is passed (if passed).

        Args:
            table: ``TableName`` or ``str``
            file_format: ``FileFormat`` or ``str``
            filename: Optional[str], default="dump"
            include: Optional[List[UserInclude | MessageInclude]], default=None
            order_by: Optional[List[UserOrderBy | MessageOrderBy]], default=None
            original_db: Optional[bool], default=False
            indent: Optional[int], default=None

        Returns:
            None
        """
        table_names = list(TableName.__dict__["_member_map_"].values())
        file_formats = list(FileFormat.__dict__["_member_map_"].values())

        if str(table) not in table_names:
            error = '"table" parameter must be: {}'.format(
                ", ".join(f'"{i}"' for i in table_names))
            raise ValueError(error)

        if str(file_format) not in file_formats:
            error = '"tile_format" parameter must be: {}'.format(
                ", ".join(f'"{i}"' for i in file_formats))
            raise ValueError(error)

        parameters = {
            "filename": filename,
            "include": include,
            "order_by": order_by
        }
        if file_format == str(FileFormat.DB):
            parameters["original_db"] = original_db
        elif file_format == str(FileFormat.JSON) and indent is not None:
            parameters["indent"] = indent
        functions = {
            f"{TableName.USERS}-{FileFormat.DB}": Dumper.users_to_db,
            f"{TableName.MESSAGES}-{FileFormat.DB}": Dumper.messages_to_db,
            f"{TableName.USERS}-{FileFormat.CSV}": Dumper.users_to_csv,
            f"{TableName.MESSAGES}-{FileFormat.CSV}": Dumper.messages_to_csv,
            f"{TableName.USERS}-{FileFormat.JSON}": Dumper.users_to_json,
            f"{TableName.MESSAGES}-{FileFormat.JSON}": Dumper.messages_to_json
        }

        functions[f"{str(table)}-{str(file_format)}"](**parameters)

    @staticmethod
    def _type_checker(var: Any, var_name: str, _type: type) -> None:
        if not isinstance(var, _type):
            error = f'"{var_name}" parameter must be a type {_type}'
            raise ValueError(error)

    @staticmethod
    def _init_users(
        include: List[MessageInclude | str] | None = None,
        order_by: List[MessageOrderBy | str] | None = None
    ) -> List[Dict[str, str | int | float | None]]:
        include_list = [str(i) for i in
                        UserInclude.__dict__["_member_map_"].values()]
        order_by_list = [str(i) for i in
                         UserOrderBy.__dict__["_member_map_"].values()]

        if include:
            Dumper._type_checker(include, "include", list)

            is_include_length_valid = len(set(include)) == len(include)
            if not is_include_length_valid:
                error = '"include" parameter has duplicate values'
                raise ValueError(error)

            is_include_valid = all((str(i) in include_list) for i in include)
            if not is_include_valid:
                error = '"include" parameter must be a list of: {}'.format(
                    ", ".join(f'"{i}"' for i in include_list))
                raise ValueError(error)
        else:
            include = include_list

        if order_by:
            Dumper._type_checker(order_by, "order_by", list)

            is_order_by_length_valid = len(set(order_by)) == len(order_by)
            if not is_order_by_length_valid:
                error = '"order_by" parameter has duplicate values'
                raise ValueError(error)

            is_order_by_valid = all((str(i) in order_by_list)
                                    for i in order_by)
            if not is_order_by_valid:
                error = '"order_by" parameter must be a list of: {}'.format(
                    ", ".join(f'"{i}"' for i in order_by_list))
                raise ValueError(error)
        else:
            order_by = [UserOrderBy.TIME]

        attributes = {
            str(UserInclude.USER_ID): lambda _user:
                _user.user_id,
            str(UserInclude.BAN_REASON): lambda _user:
                _user.ban_reason,
            str(UserInclude.ADDITIONAL_INFO): lambda _user:
                _user.additional_info,
            str(UserInclude.LAST_MESSAGE): lambda _user:
                _user.messages[-1].text,
            str(UserInclude.TIMESTAMP): lambda _user:
                _user.utc_created_at.timestamp(),
            str(UserInclude.TIME): lambda _user:
                _user.utc_created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

        info_dump = []
        db = SessionLocal()
        users = db.query(User).order_by(
            *[getattr(User, o) for o in order_by]
        ).all()

        for user in users:
            info_dump.append({})
            for i in include:
                info_dump[-1][str(i)] = attributes[str(i)](user)
        db.close()

        return info_dump

    @staticmethod
    def _init_messages(
        include: List[MessageInclude | str] | None = None,
        order_by: List[MessageOrderBy | str] | None = None
    ) -> List[Dict[str, str | int]]:
        include_list = [str(i) for i in
                        MessageInclude.__dict__["_member_map_"].values()]
        order_by_list = [str(i) for i in
                         MessageOrderBy.__dict__["_member_map_"].values()]

        if include:
            Dumper._type_checker(include, "include", list)

            is_include_length_valid = len(set(include)) == len(include)
            if not is_include_length_valid:
                error = '"include" parameter has duplicate values'
                raise ValueError(error)

            is_include_valid = all((str(i) in include_list) for i in include)
            if not is_include_valid:
                error = '"include" parameter must be a list of: {}'.format(
                    ", ".join(f'"{i}"' for i in include_list))
                raise ValueError(error)
        else:
            include = include_list

        if order_by:
            Dumper._type_checker(order_by, "order_by", list)

            is_order_by_length_valid = len(set(order_by)) == len(order_by)
            if not is_order_by_length_valid:
                error = '"order_by" parameter has duplicate values'
                raise ValueError(error)

            is_order_by_valid = all((str(i) in order_by_list)
                                    for i in order_by)
            if not is_order_by_valid:
                error = '"order_by" parameter must be a list of: {}'.format(
                    ", ".join(f'"{i}"' for i in order_by_list))
                raise ValueError(error)
        else:
            order_by = [MessageOrderBy.MESSAGE_ID]

        attributes = {
            str(MessageInclude.MESSAGE_ID): lambda _message: _message.id,
            str(MessageInclude.USER_ID): lambda _message: _message.user_id,
            str(MessageInclude.TEXT): lambda _message: _message.text
        }

        info_dump = []
        db = SessionLocal()
        messages = db.query(Message).distinct(Message.text).order_by(
            *[getattr(Message, o) for o in order_by]
        ).all()

        for message in messages:
            info_dump.append({})
            for i in include:
                info_dump[-1][str(i)] = attributes[str(i)](message)
        db.close()

        return info_dump

    @staticmethod
    def users_to_db(
        filename: str = "users_dump",
        include: List[UserInclude | str] | None = None,
        order_by: List[UserOrderBy | str] | None = None,
        original_db: bool = False
    ) -> None:
        Dumper._type_checker(filename, "filename", str)
        Dumper._type_checker(original_db, "original_db", bool)

        if original_db:
            shutil.copy(original_db_file, filename + ".db")
            return

        info_dump = Dumper._init_users(include, order_by)
        include = list(info_dump[0].keys())

        _engine = create_engine(f"sqlite:///{filename}.db")
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )
        _Base = declarative_base()

        _user_columns = {
            "user_id": "user_id = Column(Integer)",
            "ban_reason": "ban_reason = Column(String)",
            "additional_info": "additional_info = Column(String)",
            "last_message": "last_message = Column(String)",
            "timestamp_utc_created_at":
                "timestamp_utc_created_at = Column(Float)",
            "string_utc_created_at":
                "string_utc_created_at = Column(String(255))"
        }

        class _User(_Base):
            __tablename__ = "entries"

            id = Column(
                Integer,
                autoincrement=True,
                index=True,
                nullable=False,
                primary_key=True
            )
            for i in include:
                exec(_user_columns[i])

        _Base.metadata.create_all(bind=_engine)

        _db = _SessionLocal()

        for user in info_dump:
            _db.add(_User(**user))
        _db.commit()
        _db.close()

    @staticmethod
    def messages_to_db(
        filename: str = "messages_dump",
        include: List[MessageInclude | str] | None = None,
        order_by: List[MessageOrderBy | str] | None = None,
        original_db: bool = False
    ) -> None:
        Dumper._type_checker(filename, "filename", str)
        Dumper._type_checker(original_db, "original_db", bool)

        if original_db:
            shutil.copy(original_db_file, filename + ".db")
            return

        info_dump = Dumper._init_messages(include, order_by)
        include = list(info_dump[0].keys())
        if "id" in include:
            _ = include.index("id")
            include.insert(_, "message_id")
            include.remove("id")

        _engine = create_engine(f"sqlite:///{filename}.db")
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )
        _Base = declarative_base()

        _messages_columns = {
            "message_id": "message_id = Column(Integer)",
            "user_id": "user_id = Column(Integer)",
            "text": "text = Column(String)"
        }

        class _Message(_Base):
            __tablename__ = "entries"

            id = Column(
                Integer,
                autoincrement=True,
                index=True,
                nullable=False,
                primary_key=True
            )
            for i in include:
                exec(_messages_columns[i])

        _Base.metadata.create_all(bind=_engine)

        _db = _SessionLocal()

        for message in info_dump:
            if "id" in message:
                message["message_id"] = message.pop("id")
            _db.add(_Message(**message))
        _db.commit()
        _db.close()

    @staticmethod
    def users_to_csv(
        filename: str = "users_dump",
        include: List[UserInclude | str] | None = None,
        order_by: List[UserOrderBy | str] | None = None
    ) -> None:
        Dumper._type_checker(filename, "filename", str)

        info_dump = Dumper._init_users(include, order_by)
        include = list(info_dump[0].keys())

        with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=include)  # noqa
            writer.writeheader()
            writer.writerows(info_dump)

    @staticmethod
    def messages_to_csv(
        filename: str = "messages_dump",
        include: List[MessageInclude | str] | None = None,
        order_by: List[MessageOrderBy | str] | None = None
    ) -> None:
        Dumper._type_checker(filename, "filename", str)

        info_dump = Dumper._init_messages(include, order_by)
        include = list(info_dump[0].keys())

        with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=include)  # noqa
            writer.writeheader()
            writer.writerows(info_dump)

    @staticmethod
    def users_to_json(
        filename: str = "users_dump",
        include: List[UserInclude | str] = None,
        order_by: List[UserOrderBy | str] = None,
        indent: int = 0
    ) -> None:
        Dumper._type_checker(filename, "filename", str)
        Dumper._type_checker(indent, "indent", int)

        if indent == 0:
            indent = None

        info_dump = Dumper._init_users(include, order_by)

        with open(f"{filename}.json", "w") as f:
            json.dump(info_dump, f, indent=indent, ensure_ascii=False)  # noqa

    @staticmethod
    def messages_to_json(
        filename: str = "messages_dump",
        include: List[MessageInclude | str] | None = None,
        order_by: List[MessageOrderBy | str] | None = None,
        indent: int = 0
    ) -> None:
        Dumper._type_checker(filename, "filename", str)
        Dumper._type_checker(indent, "indent", int)

        if indent == 0:
            indent = None

        info_dump = Dumper._init_messages(include, order_by)

        with open(f"{filename}.json", "w") as f:
            json.dump(info_dump, f, indent=indent, ensure_ascii=False)  # noqa

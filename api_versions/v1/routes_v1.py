# Other imports
import os
from typing import Annotated, Dict
from datetime import datetime, UTC

# Main imports
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, status, Query
from fastapi.responses import RedirectResponse, FileResponse

# Imports from project
from .database_v1 import (
    SessionLocal,
    User as UserDB,
    Message as MessageDB
)
from .pydantic_models_v1 import (
    Error,
    UserCreate, UserResponse, UserResponseMessages, UserFound,
    MessageResponse, MessageFound,
    DumpQueryParams
)
from .database_dumper_v1 import Dumper

# Config loading
load_dotenv(".KEY")
key = os.getenv("KEY")
if not key:
    raise ValueError("KEY is not set.")
main_api_address = os.getenv("MAIN_API_ADDRESS", "/api")
main_address = os.getenv("MAIN_ADDRESS")
main_address = f" Main address: {main_address}." if main_address else ""

main_router_v1 = APIRouter()


def text_characters_fixer(text: str) -> str:
    characters = {
        "\n": " ",
        chr(65279): "",
    }
    return "".join(characters.get(c, c) for c in text).replace("  ", " ")


@main_router_v1.get("")
async def root(response: Response, request: Request) -> Dict[str, str]:
    response.status_code = status.HTTP_200_OK
    return {"welcome_text":
            "This is YOAS (Your Own Anti-Spam System) API. "
            f"You can check the docs at {request.url}/docs "
            f"and {request.url}/redoc{main_address} "
            "It is something like a copy of CAS API to have your own "
            "database of bans if you need it for some reason. "
            "More info about CAS and CAS API can be found here: "
            "https://cas.chat"}


@main_router_v1.get("/docs", status_code=301, include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    return RedirectResponse(f"{main_api_address}/docs", status_code=301)


@main_router_v1.get("/redoc", status_code=301, include_in_schema=False)
async def redoc_redirect() -> RedirectResponse:
    return RedirectResponse(f"{main_api_address}/redoc", status_code=301)


@main_router_v1.get("/openapi.json", status_code=301, include_in_schema=False)
async def openapi_json_redirect() -> RedirectResponse:
    return RedirectResponse(
        f"{main_api_address}/openapi.json", status_code=301
    )


@main_router_v1.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": UserResponse},
        400: {"model": Error},
        403: {"model": Error},
        500: {"model": Error}
    }
)
async def create_user(
        response: Response,
        access_key: Annotated[str, Query()],
        user_create: UserCreate
) -> UserResponse | Error:
    if access_key != key:
        response.status_code = status.HTTP_403_FORBIDDEN
        return Error(error="Forbidden: invalid access key.")

    user_id = user_create.user_id
    ban_reason = user_create.ban_reason
    additional_info = user_create.additional_info
    text = text_characters_fixer(user_create.message)

    db = SessionLocal()
    existing_user_id = db.get(UserDB, user_id)
    if existing_user_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Error(error="This User_ID is already in database.")
        
    try:
        db_message = MessageDB(
            user_id=user_id,
            text=text
        )
        db_user = UserDB(
            user_id=user_id,
            ban_reason=ban_reason,
            additional_info=additional_info,
            messages=[db_message]
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        db.refresh(db_message)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return Error(error=str(e))
    finally:
        db.close()

    response.status_code = status.HTTP_201_CREATED
    return UserResponse(
        user_id=user_id,
        ban_reason=ban_reason,
        additional_info=additional_info,
        message=MessageResponse(id=db_message.id, text=text),
        utc_created_at=db_user.utc_created_at,  # noqa
        utc_created_at_formatted=db_user.utc_created_at  # noqa
    )


@main_router_v1.delete(
    "/user",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": UserFound},
        404: {"model": Error},
        500: {"model": Error}
    }
)
async def delete_user(
        response: Response,
        user_id: Annotated[int, Query()],
        access_key: Annotated[str, Query()],
) -> UserFound | Error:
    if access_key != key:
        response.status_code = status.HTTP_403_FORBIDDEN
        return Error(error="Forbidden: invalid access key.")

    db = SessionLocal()
    try:
        user = db.get(UserDB, user_id)
        messages = user.messages
        db.delete(user)
        db.commit()
    except AttributeError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return Error(error="User not found.")
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return Error(error=str(e))
    finally:
        db.close()

    response.status_code = status.HTTP_200_OK
    return UserFound(
        found=True,
        user=UserResponseMessages(
            user_id=user.user_id,
            ban_reason=user.ban_reason,
            additional_info=user.additional_info,
            messages=[MessageResponse(id=m.id, text=m.text) for m in messages],
            utc_created_at=user.utc_created_at,  # noqa
            utc_created_at_formatted=user.utc_created_at  # noqa
        )
    )


@main_router_v1.get(
    "/user",
    responses={
        200: {"model": UserFound},
        404: {"model": UserFound},
    }
)
async def get_user(
        response: Response,
        user_id: Annotated[int, Query()]
) -> UserFound:
    db = SessionLocal()
    try:
        user = db.get(UserDB, user_id)
        messages = user.messages
    except AttributeError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserFound(found=False)
    finally:
        db.close()

    response.status_code = status.HTTP_200_OK
    return UserFound(
        found=True,
        user=UserResponseMessages(
            user_id=user.user_id,
            ban_reason=user.ban_reason,
            additional_info=user.additional_info,
            messages=[MessageResponse(id=m.id, text=m.text) for m in messages],
            utc_created_at=user.utc_created_at,  # noqa
            utc_created_at_formatted=user.utc_created_at  # noqa
        )
    )


@main_router_v1.get(
    "/message",
    responses={
        200: {"model": MessageFound},
        404: {"model": MessageFound},
    }
)
async def get_message(
    response: Response,
    message_text: Annotated[str, Query()]
) -> MessageFound:
    db = SessionLocal()
    message = db.query(MessageDB).filter(
        MessageDB.text == text_characters_fixer(message_text)).first()
    db.close()

    if not message:
        response.status_code = status.HTTP_404_NOT_FOUND
        return MessageFound(found=False)

    response.status_code = status.HTTP_200_OK
    return MessageFound(found=True)


@main_router_v1.get(
    "/dump", responses={500: {"model": Error}}
)
async def database_dump(
    response: Response,
    dump: Annotated[DumpQueryParams, Query()]
) -> FileResponse:
    """
    Returns the database dump as a file with the specified format.

     ``original_db`` parameter is only used for DB format, otherwise it is
     ignored. If this parameter is set to True and ``file_format`` is DB -
     parameters ``table``, ``include`` and ``order_by`` will be ignored.
     This parameter used for creating a 1:1 copy of original database.

     ``indent`` is only used for JSON format, otherwise it is ignored.
     It is used for indentation in JSON file, if set to 0 or None -
     file will be in one line without any indentation.

     Parameters ``include`` and ``order_by`` must be without duplicates,
     because they follow the order of the list that is passed (if passed).

     For the ``include`` parameter see the
     ``UserInclude`` and ``MessageInclude`` schemas.

     For the ``order_by`` parameter see the
     ``UserOrderBy`` and ``MessageOrderBy`` schemas.


      Examples:

      Include for table users:
      ``/dump?include=user_id&include=string_utc_created_at``

      Order by for table messages: ``/dump?order_by=user_id&order_by=text``
    """
    file_formats = ("db", "csv", "json")
    dont_remove_files = ("yoas.db", "yoas_test.db")
    for file in os.listdir():
        if file.endswith(file_formats):
            if file not in dont_remove_files:
                os.remove(file)

    now = datetime.now(UTC).strftime("%d.%m.%Y-%H.%M.%S")

    parameters = {
        "table": dump.table,
        "file_format": dump.file_format,
        "filename": f"{dump.table}-dump-{now}",
        "include": dump.include,
        "order_by": dump.order_by,
        "original_db": dump.original_db,
        "indent": dump.indent
    }
    output_file = parameters["filename"] + "." + parameters["file_format"]

    try:
        Dumper.dump(**parameters)
    except Exception as e:
        print(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return Error(error=str(e))

    return FileResponse(
        path=output_file,
        filename=output_file,
        media_type="application/octet-stream"
    )

# TODO: POST /user/{user_id}/message
# TODO: DELETE /user/{user_id}/message
#  (but need to check if it is the last message, if so - return error)

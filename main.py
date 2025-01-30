"""
Tested on Python 3.11.1

# noqa lines because of PyCharm bug, see here:
https://youtrack.jetbrains.com/issue/PY-63306/False-positive-for-unresolved-reference-of-state-instance-field-in-FastAPI-app
"""

# Other imports
import os

# Main imports
from dotenv import load_dotenv
from fastapi import FastAPI, Request

# Imports from project
from api_versions import main_router_v1

# Config loading
load_dotenv()
main_api_address = os.getenv("MAIN_API_ADDRESS", "/api")
if not main_api_address.startswith("/"):
    main_api_address = f"/{main_api_address}"
main_address = os.getenv("MAIN_ADDRESS")
main_address = f"\n\nMain address: {main_address}." if main_address else ""

DESCRIPTION = ("YOAS (Your Own Anti-Spam System) API\n\n"
               f"You can check the docs at {main_api_address}/docs "
               f"and {main_api_address}/redoc.{main_address}\n\n"
               "It is something like a copy of CAS API to have your own "
               "database of bans if you need it for some reason.\n\n"
               "More info about CAS and CAS API can be found here: "
               "https://cas.chat")


app = FastAPI(
    title="YOAS (Your Own Anti-Spam System) API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_url=f"{main_api_address}/openapi.json",
    docs_url=f"{main_api_address}/docs",
    redoc_url=f"{main_api_address}/redoc",
    swagger_ui_oauth2_redirect_url=f"{main_api_address}/docs/oauth2-redirect"
)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return {"welcome_text":
            "This is the YOAS (Your Own Anti-Spam System) API. "
            f"Check {request.url}{main_api_address[1:]} for more info."}

app.include_router(
    main_router_v1,
    prefix=main_api_address,
    tags=["default"],
    include_in_schema=False
)
app.include_router(
    main_router_v1,
    prefix=main_api_address + "/latest",
    tags=["latest"]
)

app.include_router(
    main_router_v1, prefix=main_api_address + "/v1", tags=["v1"]
)

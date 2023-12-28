import logging
import os
import re
import traceback
from argparse import ArgumentParser
from datetime import datetime
from logging import getLogger
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import httpx
import jwt
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from . import __VERSION__ as APP_VERSION

logger = getLogger(__name__)


class ApiRequestBody(BaseModel):
    log: str


def create_app(
    minecraft_server_timezone: ZoneInfo,
    notification_timezone: ZoneInfo,
    jwt_secret_key: str,
    discord_webhook_url: str,
) -> FastAPI:
    app = FastAPI(
        title="Minecraft Server Log Hook API",
        version=APP_VERSION,
    )
    security = HTTPBearer()

    def get_authenticated_user(
        authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    ) -> str:
        token = authorization.credentials
        credential_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        username: str | None = None
        try:
            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=jwt_secret_key,
                algorithms=["HS256"],
            )

            username = payload.get("sub")
        except jwt.PyJWTError:
            raise credential_exception

        if username is None:
            raise credential_exception

        if not isinstance(username, str):
            raise credential_exception

        return username

    @app.post("/api")
    async def post_api(
        body: ApiRequestBody,
        current_user: Annotated[str, Depends(get_authenticated_user)],
    ) -> str:
        """
        Fluentdのhttp outputからのログ出力を受け取る
        """
        log = body.log.strip()
        logger.info(f"Incoming log: {body.log}")

        m = re.search(r"\[(.+?) INFO\] Player disconnected: (.+?), ", log)
        if m:
            timestamp_string = m.group(1)  # %Y-%m-%d %H:%M:%S:%f without timezone info
            timestamp = (
                datetime.strptime(timestamp_string, "%Y-%m-%d %H:%M:%S:%f")
                .replace(tzinfo=minecraft_server_timezone)
                .astimezone(tz=notification_timezone)
            )

            minecraft_username = m.group(2)
            message = f"[{timestamp.isoformat()}] {minecraft_username} が退出しました"

            logger.info(message)
            try:
                httpx.post(
                    discord_webhook_url,
                    json={
                        "content": message,
                    },
                )
            except httpx.HTTPError:
                traceback.print_exc()

        m = re.search(r"\[(.+?) INFO\] Player connected: (.+?), ", log)
        if m:
            timestamp_string = m.group(1)  # %Y-%m-%d %H:%M:%S:%f without timezone info
            timestamp = (
                datetime.strptime(timestamp_string, "%Y-%m-%d %H:%M:%S:%f")
                .replace(tzinfo=minecraft_server_timezone)
                .astimezone(tz=notification_timezone)
            )

            minecraft_username = m.group(2)
            message = f"[{timestamp.isoformat()}] {minecraft_username} が入室しました"

            logger.info(message)
            try:
                httpx.post(
                    discord_webhook_url,
                    json={
                        "content": message,
                    },
                )
            except httpx.HTTPError:
                traceback.print_exc()

        return "Ok"

    return app


def main() -> None:
    load_dotenv()

    default_host: str | None = os.environ.get("APP_HOST") or "0.0.0.0"
    default_port: str | None = os.environ.get("APP_PORT") or "8000"
    default_minecraft_server_timezone: str | None = (
        os.environ.get("APP_MINECRAFT_SERVER_TIMEZONE") or "UTC"
    )
    default_notification_timezone: str | None = (
        os.environ.get("APP_NOTIFICATION_TIMEZONE") or "UTC"
    )
    default_jwt_secret_key: str | None = os.environ.get("APP_JWT_SECRET_KEY") or None
    default_discord_webhook_url: str | None = (
        os.environ.get("APP_DISCORD_WEBHOOK_URL") or None
    )

    parser = ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default=default_host,
        required=default_host is None,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        required=default_port is None,
    )
    parser.add_argument(
        "--minecraft_server_timezone",
        type=str,
        default=default_minecraft_server_timezone,
        required=default_minecraft_server_timezone is None,
    )
    parser.add_argument(
        "--notification_timezone",
        type=str,
        default=default_notification_timezone,
        required=default_notification_timezone is None,
    )
    parser.add_argument(
        "--jwt_secret_key",
        type=str,
        default=default_jwt_secret_key,
        required=default_jwt_secret_key is None,
    )
    parser.add_argument(
        "--discord_webhook_url",
        type=str,
        default=default_discord_webhook_url,
        required=default_discord_webhook_url is None,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=APP_VERSION,
    )
    args = parser.parse_args()

    host: str = args.host
    port: int = args.port
    minecraft_server_timezone_string: str = args.minecraft_server_timezone
    notification_timezone_string: str = args.notification_timezone
    jwt_secret_key: str = args.jwt_secret_key
    discord_webhook_url: str = args.discord_webhook_url

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s",
    )

    minecraft_server_timezone = ZoneInfo(key=minecraft_server_timezone_string)
    notification_timezone = ZoneInfo(key=notification_timezone_string)

    app = create_app(
        minecraft_server_timezone=minecraft_server_timezone,
        notification_timezone=notification_timezone,
        jwt_secret_key=jwt_secret_key,
        discord_webhook_url=discord_webhook_url,
    )

    uvicorn.run(
        app=app,
        host=host,
        port=port,
    )

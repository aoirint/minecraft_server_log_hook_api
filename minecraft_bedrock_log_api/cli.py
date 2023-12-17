import logging
import os
import re
from argparse import ArgumentParser
from logging import getLogger
from typing import Annotated, Any

import jwt
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = getLogger(__name__)


class ApiRequestBody(BaseModel):
    log: str


def create_app(
    jwt_secret_key: str,
) -> FastAPI:
    app = FastAPI()
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

        m = re.search(r"INFO\] Player disconnected: (.+?), ", log)
        if m:
            logger.info(f"Disconnected: {m.group(1)}")

        m = re.search(r"INFO\] Player connected: (.+?), ", log)
        if m:
            logger.info(f"Connected: {m.group(1)}")

        return "Ok"

    return app


def main() -> None:
    load_dotenv()

    default_jwt_secret_key: str | None = os.environ.get("APP_JWT_SECRET_KEY") or None

    parser = ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=24931,
    )
    parser.add_argument(
        "--jwt_secret_key",
        type=str,
        default=default_jwt_secret_key,
        required=default_jwt_secret_key is None,
    )
    args = parser.parse_args()

    host: str = args.host
    port: int = args.port
    jwt_secret_key: str = args.jwt_secret_key

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s",
    )

    app = create_app(
        jwt_secret_key=jwt_secret_key,
    )

    uvicorn.run(
        app=app,
        host=host,
        port=port,
    )

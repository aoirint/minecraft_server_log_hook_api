import time
from getpass import getpass

import jwt


def main() -> None:
    sub = input("sub: ")
    if len(sub) == 0:
        raise Exception("Please input the sub.")

    secret_key = getpass("HS256 secret key: ")
    if len(secret_key) == 0:
        raise Exception("Please input the secret key.")

    iat = int(time.time())
    exp = 2524608000  # 2050-01-01T00:00:00+00:00

    payload = {
        "sub": "fluentd",
        "iat": iat,
        "exp": exp,
    }

    print(
        jwt.encode(
            payload=payload,
            key=secret_key,
            algorithm="HS256",
        ),
    )


if __name__ == "__main__":
    main()

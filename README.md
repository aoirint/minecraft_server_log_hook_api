# minecraft_server_log_hook_api

## Usage

`template.env`を`.env`にコピーして、値を設定します。

### Development

```shell
poetry install

poetry run python scripts/create_jwt_token.py

poetry run python -m minecraft_server_log_hook_api
```

## Docker

```shell
sudo docker build -t docker.aoirint.com/aoirint/minecraft_server_log_hook_api .

sudo docker run --rm -p "127.0.0.1:8000:8000" --env-file "./.env" docker.aoirint.com/aoirint/minecraft_server_log_hook_api
```

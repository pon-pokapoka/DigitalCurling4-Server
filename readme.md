# DigitalCurling4

This is a new server for digital curling.

## Dependencies

- Python 3.11 (or later)
- Docker
- Docker Compose
- FastAPI
- Uvicorn
- Gunicorn
- Pydantic
- SQLAlchemy

## Setup and Development

### Register user data to use basic authentication

This server uses Basic authentication to identify clients. Users are stored in Postgres, with their passwords salted and hashed.

The server creates the users in `DC_USERS` when it starts. It's a JSON object of username to password, in your `.env` file:

```bash
DC_USERS='{"user0":"pass0","user1":"pass1"}'
```

An administrator can also add a user to a running server, or change a password:

```bash
docker compose exec app python src/authentication/basic_authentication.py --username user --password password
```

Then set the same credentials in your client-side .env file:

```
MATCH_USER_NAME="user0"
PASS_WORD="pass0"
```

### Start server

1. first you need to install docker and docker-compose, then pull this repository.

1. Please input this command at Linux or WSL.
    ```bash
    sudo sysctl -w vm.overcommit_memory=1
    ```

1. Create a `.env` file in the root of the project and add the following variables:

    ```bash
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=your_db
    POSTGRES_HOST=your_host
    POSTGRES_PORT=your_port
    ```
    For details, refer to the [.env.sample](./.env.sample) file.

1. Create docker network:

    ```bash
    docker network create dc_network
    ```

1. If you want to run dc-server in production env, run the following command

    ```bash
    docker compose -f docker-compose.yml up --build
    ```

1. If you want to run dc-server in development env, run the following command:

    ```bash
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up
    ```

    or

    ```bash
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
    ```

    In development mode, changes in the code will be reflected in the server automatically.

    If you don't want to see the logs, you can run the server in daemon mode with the `-d` flag.

### Database migration

`python -m src.migrate` applies each file in `postgres/init/` once, in name order, and records it in the table `schema_migrations`. The server runs it before it starts, under Docker Compose and on Kubernetes, so a new file there is all a schema change needs. Add a new file rather than editing an old one.

### Run on Kubernetes

See [k8s/README.md](./k8s/README.md).

## Communication through SSE

Board data is sent to the client by SSE.
When communication by SSE is disconnected, all board data within the end of the current match is sent to the client.
In this case, the old board data is divided into "**state_update**" in event.type and the latest board data into "**latest_state_update**" in event.type.

## For developpers

### Generate requirements.txt

```bash
uv pip compile pyproject.toml -o requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## TODOs

- [ ] Add tests
- [ ] Preparation for operation in a production environment
- [ ] Develop a mode for multiple simultaneous matches in Webhook
- [ ] Add REST API for GUI, and tumeshogi mode and so on...


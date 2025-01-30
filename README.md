# YOAS (Your Own Anti-Spam System) API
Little project for managing spam-related text and comments.

You can check this API at https://pashok11.tw1.su/apis/yoas/docs
## How to use
(For now tested only on Linux and Docker, Python 3.11.1, 3.12.4, 3.13.1)

**Note**: if Docker doesn't working, try this:
- `systemctl start docker.socket` - for desktop
- `systemctl start docker.service` - for server

Create `.KEY` file in main directory with `KEY=string` any string you want. This key would be used for adding and deleting users from the database. API doesn't run without it.

After this you have several ways to run an API:
- Docker Compose:
    - Copy `.env.example` to `.env` and edit it.
    - `docker compose up` - start Docker Compose. You can add `-d` for run start it in background.
    - `docker compose down` - stop Docker Compose. You can add `--rmi local` for delete related to compose images (only created by compose, not by pulling from docker hub), containers and networks.
- Docker:
    - **Optional**: Copy `.env.example` to `.env` and edit it.
    - `docker volume create yoas-api_yoas` - create a volume for the database (name it like this for simple migrate to Docker Compose).
    - `docker build -t yoas .` for building an image with secret `KEY` file.
    - `docker run -p 8000:8000 --mount type=volume,src=yoas-api_yoas,target=/app/db_n_logs --env-file .KEY --name yoas_container yoas` - run a container with name `yoas_container`, with publishing `8000` port, mounting a volume `yoas-api_yoas` to the `/app/db_n_logs` directory in a container and using `.KEY` environment file. You can add `-d` for run it in background, `--rm` for deleting container when it exits and `-e HOST=0.0.0.0 -e PORT=8000` for setting environment variables for a container (especially if you don't do anything with `.env` file).
    - Stop container with `docker stop <CONTAINER_NAME>` for just stop a container, `docker rm -f <CONTAINER_NAME>` for stop and delete a container or just press `Ctrl+C` if it in foreground to stop it.
- Bash scripts:
    - **Optional**: Copy `.env.example` to `.env` and edit it.
    - Set `HOST` and `PORT` environment variables to what you want (`HOST=0.0.0.0 && PORT=8000`) or edit `./start.sh` (or `./start_dev.sh`).
    - Run `./start.sh` (or `./start_dev.sh` for development). If you can't run it - make script executable (`chmod +x start.sh`).
- or any other common way to run FastAPI app, like `fastapi run main.py --host 0.0.0.0 --port 8000` or `uvicorn main:app --host 0.0.0.0 --port 8000`.
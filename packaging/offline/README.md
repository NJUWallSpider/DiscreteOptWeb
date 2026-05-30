# Offline Docker Deployment Bundle

Use this workflow when the target server can run Docker/Compose but cannot
access GitHub or Docker registries.

## Build The Bundle On A Networked Machine

Run from the repository root:

```bash
./packaging/offline/create_bundle.sh
```

The script creates a tarball under `dist/offline/` containing:

- the working tree source code,
- `.env` and compose configuration,
- all Docker images referenced by `docker compose config --images`,
- extra benchmark runtime images such as `codalab/codalab-legacy:py312`,
- a target-side `start-offline.sh` helper.

If the target server is `linux/amd64` and the build machine is Apple Silicon,
build for the target platform:

```bash
TARGET_PLATFORM=linux/amd64 ./packaging/offline/create_bundle.sh
```

The image archive is architecture-specific. A bundle made from `linux/arm64`
images will not run on an `amd64` server.

If your competitions need additional runtime images, include them:

```bash
EXTRA_IMAGES="codalab/codalab-legacy:py312 my-registry/my-image:tag" \
  ./packaging/offline/create_bundle.sh
```

## Start On The Offline Server

Copy the generated tarball to the server, then:

```bash
tar -xzf codabench-offline-*.tar.gz
cd codabench-offline-*
./start-offline.sh
```

The helper loads `images.tar`, fixes the Compose project name to `codabench`,
and starts the stack with `--no-build` and `--pull never`.

## Server-Specific `.env` Values

Before starting on a real server, edit `.env`.

For an intranet/server IP deployment, change these Mac-local defaults:

```dotenv
ALLOWED_HOSTS=localhost,SERVER_IP_OR_DOMAIN
DOMAIN_NAME=SERVER_IP_OR_DOMAIN:80
AWS_S3_ENDPOINT_URL=http://SERVER_IP_OR_DOMAIN:9000/
WORKER_BUNDLE_URL_REWRITE=http://SERVER_IP_OR_DOMAIN:9000|http://minio:9000
```

If Caddy cannot get a public TLS certificate because the server is offline,
use port `8000` directly or adjust `Caddyfile` for internal HTTP.

## Notes

- The target still needs Docker and the Docker Compose plugin.
- Do not run `docker compose build` on the offline target.
- If a benchmark references a Docker image that was not included in
  `images.tar`, scoring will fail when the worker tries to pull it.

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
- the DiscreteOpt benchmark runtime image `discreteopt/runtime:py312`,
- extra benchmark runtime images such as `codalab/codalab-legacy:py312`,
- a target-side `start-offline.sh` helper.

If the target server is `linux/amd64` and the build machine is Apple Silicon,
build for the target platform:

```bash
TARGET_PLATFORM=linux/amd64 ./packaging/offline/create_bundle.sh
```

The image archive is architecture-specific. A bundle made from `linux/arm64`
images will not run on an `amd64` server. For `linux/amd64` offline bundles,
the script defaults project service images to `almalinux:9-minimal` because
`almalinux:10-minimal` requires the `x86-64-v3` CPU baseline and can fail under
cross-platform Docker builds or on older servers. Override it only when you know
the builder and target CPU support it:

```bash
APP_BASE_IMAGE=almalinux:10-minimal TARGET_PLATFORM=linux/amd64 \
  ./packaging/offline/create_bundle.sh
```

If your competitions need additional runtime images, include them:

```bash
EXTRA_IMAGES="codalab/codalab-legacy:py312 my-registry/my-image:tag" \
  ./packaging/offline/create_bundle.sh
```

The bundled DiscreteOpt runtime is built from
`packaging/runtime/Containerfile.discreteopt`. It includes C/C++, Java,
Python, OpenMPI, OpenMP/TBB support, and common optimization packages:
`pyscipopt`, OR-Tools, Pyomo, PuLP, python-mip, HiGHS, CVXPY, NumPy, SciPy,
NetworkX, Numba, DEAP, Joblib, Dask, and mpi4py.

For optimization competitions, set the competition YAML/image field to:

```yaml
docker_image: discreteopt/runtime:py312
```

You can change the image tag or base image when building:

```bash
DISCRETEOPT_RUNTIME_IMAGE=your-org/discreteopt-runtime:2026-05 \
DISCRETEOPT_RUNTIME_BASE_IMAGE=codalab/codalab-legacy:py312 \
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

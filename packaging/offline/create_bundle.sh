#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="${DIST_DIR:-$REPO_ROOT/dist/offline}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BUNDLE_NAME="${BUNDLE_NAME:-codabench-offline-$STAMP}"
WORKDIR="$DIST_DIR/$BUNDLE_NAME"
TARGET_PLATFORM="${TARGET_PLATFORM:-}"
APP_BASE_IMAGE="${APP_BASE_IMAGE:-}"
DISCRETEOPT_RUNTIME_IMAGE="${DISCRETEOPT_RUNTIME_IMAGE:-discreteopt/runtime:py312}"
DISCRETEOPT_RUNTIME_BASE_IMAGE="${DISCRETEOPT_RUNTIME_BASE_IMAGE:-codalab/codalab-legacy:py312}"
DISCRETEOPT_RUNTIME_DOCKERFILE="${DISCRETEOPT_RUNTIME_DOCKERFILE:-packaging/runtime/Containerfile.discreteopt}"
BUILD_DISCRETEOPT_RUNTIME="${BUILD_DISCRETEOPT_RUNTIME:-1}"
EXTRA_IMAGES="${EXTRA_IMAGES:-codalab/codalab-legacy:py312}"
ALLOW_MISSING_EXTRA_IMAGES="${ALLOW_MISSING_EXTRA_IMAGES:-0}"

cd "$REPO_ROOT"

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required." >&2
  exit 1
fi

if [ -n "$TARGET_PLATFORM" ]; then
  export DOCKER_DEFAULT_PLATFORM="$TARGET_PLATFORM"
fi

if [ -z "$APP_BASE_IMAGE" ]; then
  if [ "$TARGET_PLATFORM" = "linux/amd64" ]; then
    APP_BASE_IMAGE="almalinux:9-minimal"
  else
    APP_BASE_IMAGE="almalinux:10-minimal"
  fi
fi
export APP_BASE_IMAGE

mkdir -p "$WORKDIR/app"

echo "Building local project images..."
echo "Using APP_BASE_IMAGE=$APP_BASE_IMAGE"
docker compose build --pull

echo "Pulling registry images used by docker-compose.yml..."
docker compose pull --ignore-buildable

IMAGES_FILE="$WORKDIR/images.txt"
docker compose config --images | sort -u > "$IMAGES_FILE"

if [ "$BUILD_DISCRETEOPT_RUNTIME" = "1" ]; then
  echo "Building DiscreteOpt benchmark runtime image: $DISCRETEOPT_RUNTIME_IMAGE"
  runtime_build_args=(
    --pull
    -f "$DISCRETEOPT_RUNTIME_DOCKERFILE"
    -t "$DISCRETEOPT_RUNTIME_IMAGE"
    --build-arg "BASE_IMAGE=$DISCRETEOPT_RUNTIME_BASE_IMAGE"
  )

  if [ -n "$TARGET_PLATFORM" ]; then
    runtime_build_args=(--platform "$TARGET_PLATFORM" "${runtime_build_args[@]}")
  fi

  docker build "${runtime_build_args[@]}" "$REPO_ROOT"
  echo "$DISCRETEOPT_RUNTIME_IMAGE" >> "$IMAGES_FILE"
fi

for image in $EXTRA_IMAGES; do
  if docker image inspect "$image" >/dev/null 2>&1; then
    echo "$image" >> "$IMAGES_FILE"
    continue
  fi

  echo "Pulling extra runtime image: $image"
  if docker pull "$image"; then
    echo "$image" >> "$IMAGES_FILE"
  elif [ "$ALLOW_MISSING_EXTRA_IMAGES" = "1" ]; then
    echo "WARNING: missing extra image $image; it will not be included." >&2
  else
    echo "ERROR: missing extra image $image." >&2
    echo "Set ALLOW_MISSING_EXTRA_IMAGES=1 to continue without it." >&2
    exit 1
  fi
done

sort -u "$IMAGES_FILE" -o "$IMAGES_FILE"

echo "Saving Docker images..."
docker save -o "$WORKDIR/images.tar" $(cat "$IMAGES_FILE")

echo "Writing image manifest..."
{
  echo "created_at=$STAMP"
  echo "target_platform=${TARGET_PLATFORM:-host-default}"
  echo
  while IFS= read -r image; do
    docker image inspect \
      --format '{{.RepoTags}} {{.Os}}/{{.Architecture}} {{.Id}}' \
      "$image" 2>/dev/null || true
  done < "$IMAGES_FILE"
} > "$WORKDIR/image-manifest.txt"

echo "Copying source tree..."
rsync -a --delete \
  --exclude ".git" \
  --exclude ".DS_Store" \
  --exclude "node_modules" \
  --exclude "dist" \
  --exclude "var/postgres" \
  --exclude "var/minio" \
  --exclude "var/rabbit" \
  --exclude "caddy_data" \
  --exclude "caddy_config" \
  --exclude "logs" \
  --exclude "var/logs" \
  --exclude "__pycache__" \
  "$REPO_ROOT/" "$WORKDIR/app/"

cat > "$WORKDIR/start-offline.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/app"

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required." >&2
  exit 1
fi

if [ ! -f .env ]; then
  if [ -f .env_sample ]; then
    cp .env_sample .env
    echo "Created .env from .env_sample. Review it before exposing the server."
  else
    echo "Missing .env and .env_sample." >&2
    exit 1
  fi
fi

mkdir -p var/postgres var/minio var/rabbit backups caddy_data caddy_config logs var/logs maintenance_mode

echo "Loading Docker images..."
docker load -i ../images.tar

export COMPOSE_PROJECT_NAME=codabench

if docker compose up --help | grep -q -- "--pull"; then
  docker compose up -d --no-build --pull never "$@"
else
  docker compose up -d --no-build "$@"
fi

echo
echo "Codabench is starting."
echo "Django: http://localhost:8000"
echo "Caddy:  http://localhost"
EOF

chmod +x "$WORKDIR/start-offline.sh"

cp "$REPO_ROOT/packaging/offline/README.md" "$WORKDIR/README-OFFLINE.md"

(
  cd "$DIST_DIR"
  tar -czf "$BUNDLE_NAME.tar.gz" "$BUNDLE_NAME"
)

echo "Offline bundle created:"
echo "$DIST_DIR/$BUNDLE_NAME.tar.gz"

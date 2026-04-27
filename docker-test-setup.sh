#!/bin/bash
# Run once to build the image and create per-client data directories.
# Then open 3 terminal windows and run the docker run commands printed at the end.

set -e

echo "==> Building image..."
docker build -t securedrop .

echo "==> Creating Docker network..."
docker network create securedrop-net 2>/dev/null || echo "    (network already exists)"

echo "==> Creating per-client data directories..."
mkdir -p test-ca/data/certs test-cb/data/certs test-cc/data/certs

echo ""
echo "==> Done. Now open 3 terminal windows and run one command in each:"
echo ""
echo "  Terminal 1 (Client CA):"
echo "    docker run -it --rm --network securedrop-net --name ca -v \"\$(pwd)/test-ca/data:/app/data\" securedrop"
echo ""
echo "  Terminal 2 (Client CB):"
echo "    docker run -it --rm --network securedrop-net --name cb -v \"\$(pwd)/test-cb/data:/app/data\" securedrop"
echo ""
echo "  Terminal 3 (Client CC):"
echo "    docker run -it --rm --network securedrop-net --name cc -v \"\$(pwd)/test-cc/data:/app/data\" securedrop"
echo ""
echo "  To get a shell inside a running container (e.g. to cat files):"
echo "    docker exec -it ca bash"

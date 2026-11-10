# Distribution — Shipping the Lab to Partners

> **Internet is required in all cases.** The lab talks to the hosted **RankEZ
> SaaS (grKey)** portal during the workshop, so every attendee needs outbound
> internet access regardless of how the images are delivered. The sections
> below only affect *how Docker images reach the partner* — none of them remove
> the grKey SaaS dependency.

Three ways to hand the lab over. **Source is the default** — the two custom
images are tiny, and the two large base images are already public.

## 1. Source repo / tarball (recommended)

Ship the whole directory (`git clone` / archive). The partner runs:

```bash
./init-lab.sh          # prompts for their partner ID (or: ./init-lab.sh 3)
docker compose up -d --build
```

- `--build` builds the two local images (`Dockerfile.proxy`, `Dockerfile.target-web`)
  — a few seconds each — and pulls `mysql:8.0` + `ubuntu:22.04` from Docker Hub.
- Partners can read/modify the app, credentials, and Dockerfiles — full transparency.
- Every partner enters their own **ID** → isolated subnet and SSH ports.

## 2. Prebuilt images (for partners who can't / shouldn't build)

If a partner must *pull* rather than build, build + push the **two custom images**
to a registry they can reach, then ship a `docker-compose.yml` that references
`image:` instead of `build:`:

```bash
# on your side, once:
docker build -f Dockerfile.proxy     -t yourregistry.example/rankez/proxy-client:v1 .
docker build -f Dockerfile.target-web -t yourregistry.example/rankez/target-web:v1 .
docker push yourregistry.example/rankez/proxy-client:v1
docker push yourregistry.example/rankez/target-web:v1
```

Then swap the two `build:` blocks for `image:` in `docker-compose.yml` (drop
`context`/`dockerfile`). They still pull `mysql:8.0` + `ubuntu:22.04` from Docker
Hub unless you mirror those too.

## 3. Offline image delivery (air-gapped *images only*)

If the partner has **no Docker Hub access**, hand over tarballs. Note this only
removes the Docker Hub dependency — the partner still needs internet to reach
the **grKey SaaS** portal during the lab.

```bash
# on your side:
docker pull mysql:8.0 ubuntu:22.04
docker build -f Dockerfile.proxy      -t partners-workshop-proxy-client .
docker build -f Dockerfile.target-web -t partners-workshop-target-web .
docker save mysql:8.0 ubuntu:22.04 \
            partners-workshop-proxy-client partners-workshop-target-web \
  | gzip > partners-workshop-images.tar.gz
```

```bash
# on the partner's side:
docker load < partners-workshop-images.tar.gz
./init-lab.sh && docker compose up -d   # no --build, images already present
```

> Note: `mysql:8.0` is ~600 MB, so this tarball is large (~700 MB+ gzipped). Prefer
> section 1 or 2 whenever the partner has normal Docker Hub access.

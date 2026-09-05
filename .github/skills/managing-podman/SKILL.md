---
name: managing-podman
description: |
  Use when working with Podman, the rootless container and pod manager. The
  skill covers the container lifecycle, the pod orchestration, the image build,
  the systemd integration, the rootless networking, and the container migration
  from Docker. Use it when you manage a Podman container, when you create a pod,
  when you generate a systemd unit, or when you build an image without a daemon.
connection_type: podman
preload: false
---

# Podman Management Skill

Manage the Podman rootless containers, the pods, the images, and the systemd
integration.

Source: https://github.com/cloudthinker-ai/CloudSkills/blob/main/skills/connections/managing-podman/SKILL.md

## Core helper functions

```bash
#!/bin/bash

# Podman command wrapper
podman_cmd() {
    podman "$@" 2>/dev/null
}

# Podman JSON output helper
podman_json() {
    podman "$@" --format json 2>/dev/null | jq '.'
}

# Podman API helper (for remote management)
podman_api() {
    local endpoint="$1"
    local socket="${PODMAN_SOCKET:-/run/user/$(id -u)/podman/podman.sock}"
    curl -s --unix-socket "$socket" "http://d/v4.0.0${endpoint}"
}
```

## MANDATORY: the discovery-first pattern

Always inspect the host capabilities and the running containers before you
perform an operation.

### Phase 1: discovery

```bash
#!/bin/bash

echo "=== Podman Host Info ==="
podman info --format json 2>/dev/null | jq '{
    version: .version.Version,
    api_version: .version.APIVersion,
    os: .host.os,
    arch: .host.arch,
    rootless: .host.security.rootless,
    cgroup_version: .host.cgroupVersion,
    oci_runtime: .host.ociRuntime.name,
    storage_driver: .store.graphDriverName,
    image_store: .store.imageStore.number,
    container_store: .store.containerStore.number
}'

echo ""
echo "=== Running Containers ==="
podman ps --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | column -t | head -20

echo ""
echo "=== Pods ==="
podman pod ps --format '{{.Id}}\t{{.Name}}\t{{.Status}}\t{{.NumberOfContainers}} containers\t{{.InfraId}}' 2>/dev/null | column -t | head -15

echo ""
echo "=== Disk Usage ==="
podman system df 2>/dev/null
```

## Output rules

- Token efficiency: keep each output at 50 lines or less.
- Use `--format json` with `jq`, or use `--format` with a Go template.
- Never print a full `podman inspect` output. Extract the key fields only.

## Common operations

### Container lifecycle dashboard

```bash
#!/bin/bash
echo "=== All Containers ==="
podman ps -a --format json 2>/dev/null | jq '{
    total: length,
    running: [.[] | select(.State == "running")] | length,
    exited: [.[] | select(.State == "exited")] | length,
    created: [.[] | select(.State == "created")] | length
}'

echo ""
echo "=== Resource Usage ==="
podman stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}' \
    | column -t | head -20

echo ""
echo "=== Container Health ==="
podman ps -a --format json 2>/dev/null | jq -r '
    .[] | "\(.Names[0] // .Id[0:12])\t\(.State)\t\(.StartedAt[0:19])\t\(.ExitCode // "N/A")"
' | column -t | head -15

echo ""
echo "=== Containers with Restart Issues ==="
podman ps -a --format json 2>/dev/null | jq -r '
    .[] | select(.RestartCount > 0) | "\(.Names[0])\t\(.RestartCount) restarts\t\(.State)"
' | column -t
```

### Pod management

```bash
#!/bin/bash
echo "=== Pod Overview ==="
podman pod ps --format json 2>/dev/null | jq -r '
    .[] | "\(.Name)\t\(.Status)\t\(.NumberOfContainers) containers\t\(.Id[0:12])"
' | column -t

echo ""
echo "=== Pod Detail ==="
POD="${1:-}"
if [ -n "$POD" ]; then
    podman pod inspect "$POD" 2>/dev/null | jq '{
        name: .Name,
        id: .Id[0:12],
        state: .State,
        created: .Created,
        infra_container: .InfraContainerId[0:12],
        shared_namespaces: .SharedNamespaces,
        containers: [.Containers[] | {id: .Id[0:12], name: .Name, state: .State}]
    }'

    echo ""
    echo "--- Pod Container Logs (last 10 lines each) ---"
    for cid in $(podman pod inspect "$POD" 2>/dev/null | jq -r '.Containers[].Id'); do
        CNAME=$(podman inspect "$cid" --format '{{.Name}}' 2>/dev/null)
        echo "=== $CNAME ==="
        podman logs "$cid" --tail 10 2>&1 | tail -5
    done
fi
```

### Image build and management

```bash
#!/bin/bash
echo "=== Local Images (sorted by size) ==="
podman images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.ID}}\t{{.Created}}' \
    | sort -k2 -h -r | column -t | head -20

echo ""
echo "=== Dangling Images ==="
podman images -f "dangling=true" --format '{{.ID}}\t{{.Size}}\t{{.Created}}' | column -t

echo ""
echo "=== Build History ==="
IMAGE="${1:-}"
if [ -n "$IMAGE" ]; then
    podman history "$IMAGE" --format '{{.CreatedBy}}\t{{.Size}}' --no-trunc | head -15
fi

echo ""
echo "=== Image Tree ==="
if [ -n "$IMAGE" ]; then
    podman image tree "$IMAGE" 2>/dev/null | head -20
fi
```

### Systemd integration

```bash
#!/bin/bash
echo "=== Generate Systemd Unit for Container ==="
CONTAINER="${1:-}"
if [ -n "$CONTAINER" ]; then
    echo "--- Unit file preview ---"
    podman generate systemd --name "$CONTAINER" --new 2>/dev/null | head -30

    echo ""
    echo "--- Quadlet support (Podman 4.4+) ---"
    echo "Place .container files in ~/.config/containers/systemd/ for rootless"
    echo "Place .container files in /etc/containers/systemd/ for rootful"
fi

echo ""
echo "=== Existing Podman Systemd Units ==="
systemctl --user list-units 'podman-*' --no-pager 2>/dev/null | head -15
systemctl list-units 'podman-*' --no-pager 2>/dev/null | head -15

echo ""
echo "=== Auto-Update Eligible Containers ==="
podman auto-update --dry-run 2>/dev/null | head -10
```

### Rootless networking and volumes

```bash
#!/bin/bash
echo "=== Networks ==="
podman network ls --format '{{.Name}}\t{{.Driver}}\t{{.ID}}' | column -t

echo ""
echo "=== Network Details ==="
for net in $(podman network ls --format '{{.Name}}' | grep -v "podman"); do
    podman network inspect "$net" 2>/dev/null | jq '.[0] | {
        name: .name,
        driver: .driver,
        subnets: [.subnets[]? | .subnet],
        dns_enabled: .dns_enabled
    }'
done

echo ""
echo "=== Volumes ==="
podman volume ls --format '{{.Name}}\t{{.Driver}}\t{{.Mountpoint}}' | column -t | head -15

echo ""
echo "=== Unused Volumes ==="
podman volume ls -f "dangling=true" --format '{{.Name}}\t{{.Driver}}' | column -t

echo ""
echo "=== Rootless Port Forwarding ==="
echo "Note: Rootless requires ports >= 1024 unless net.ipv4.ip_unprivileged_port_start is adjusted"
podman ps --format '{{.Names}}\t{{.Ports}}' | grep -v "^$" | column -t
```

## Safety rules

- Stay read-only by default. Use `podman inspect`, `podman ps`, `podman logs`,
  and `podman stats`.
- Warning: never remove a container or an image without explicit user
  confirmation. A removed container is not recoverable.
- Rootless mode limits the ports, the storage, and the networking. Keep those
  limits in mind.
- A generated systemd unit is safe. An installed systemd unit changes the state
  of the system.

## Output format

Present the result as a structured report.

```text
Managing Podman Report
======================
Resources discovered: [count]

Resource        Status     Key Metric    Issues
--------------------------------------------------
[name]          [ok/warn]  [value]       [findings]

Summary: [total] resources | [ok] healthy | [warn] warnings | [crit] critical
Action Items: [list of prioritized findings]
```

Keep the report at 50 lines or less. Use a table for a comparison of more than
one resource.

## Anti-hallucination rules

1. Never assume a resource name. Discover each name through the CLI or the API
   in Phase 1 before you reference it in Phase 2.
2. Never invent a metric name or a dimension. Verify each name against the
   service documentation or the `--help` output.
3. Never mix commands between two service versions. Confirm which version you
   target.
4. Always follow the chain discover, verify, analyze. Every resource that you
   reference must come from the discovery step.
5. Always handle an empty result as valid data. An empty response is not an
   error, so do not retry it.

## Counter-rationalizations

| Shortcut | Counter | Why |
| - | - | - |
| "I will skip the discovery and check the resources that I know." | Always run the Phase 1 discovery first. | A resource name changes, and a new resource appears. An assumed name causes an error. |
| "The user asked for a quick check only." | Follow the full discovery and analysis flow. | A quick check misses a critical problem. A structured analysis finds a silent failure. |
| "The default configuration is probably correct." | Audit the configuration explicitly. | A default often leaves the logging, the security, and the optimization features off. |
| "This task does not need the metrics." | Always read the relevant metrics when they exist. | A CLI response shows the current state only. A metric shows the trend and the intermittent problem. |
| "I do not have access to that." | Run the command, then report the actual error. | An assumed permission failure stops a useful investigation. An actual error carries information. |

## Common pitfalls

- Rootless mode and rootful mode behave differently. Read the `rootless` field
  of `podman info` before you act.
- Rootless networking uses `slirp4netns` or `pasta`. It differs from the Docker
  bridge network.
- Rootless mode stores an image in `~/.local/share/containers`. Rootful mode
  uses a different path.
- Most Docker commands work, but some flags differ. The `--privileged` flag is
  one example.
- Use `podman generate systemd --new` to create a unit that recreates the
  container at each start.

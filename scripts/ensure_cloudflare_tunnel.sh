#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-cloudflared}"
CLOUDFLARED_CONFIG="${CLOUDFLARED_CONFIG:-$HOME/.cloudflared/config.yml}"
CLOUDFLARED_TUNNEL_NAME="${CLOUDFLARED_TUNNEL_NAME:-wecom-dev}"
CLOUDFLARED_PROTOCOL="${CLOUDFLARED_PROTOCOL:-http2}"
CLOUDFLARED_LOG="${CLOUDFLARED_LOG:-$REPO_ROOT/.cloudflared-tunnel.log}"
CLOUDFLARED_PID_FILE="${CLOUDFLARED_PID_FILE:-$REPO_ROOT/.cloudflared-tunnel.pid}"
TUNNEL_START_TIMEOUT="${TUNNEL_START_TIMEOUT:-20}"

extract_hostname() {
  if [[ -f "$CLOUDFLARED_CONFIG" ]]; then
    awk '/^[[:space:]]*-[[:space:]]*hostname:/ {print $3; exit}' "$CLOUDFLARED_CONFIG"
  fi
}

TUNNEL_HOSTNAME="${TUNNEL_HOSTNAME:-$(extract_hostname)}"

print_info() {
  echo "[tunnel] $1"
}

is_process_running() {
  pgrep -af "cloudflared.*tunnel.*run ${CLOUDFLARED_TUNNEL_NAME}" >/dev/null 2>&1
}

is_hostname_reachable() {
  if [[ -z "$TUNNEL_HOSTNAME" ]]; then
    return 1
  fi

  curl -I -s --connect-timeout 3 --max-time 8 "https://${TUNNEL_HOSTNAME}" >/dev/null 2>&1
}

is_tunnel_ready() {
  is_hostname_reachable || is_process_running
}

start_tunnel() {
  print_info "Starting Cloudflare tunnel '${CLOUDFLARED_TUNNEL_NAME}' over ${CLOUDFLARED_PROTOCOL}..."
  nohup "$CLOUDFLARED_BIN" tunnel --protocol "$CLOUDFLARED_PROTOCOL" --config "$CLOUDFLARED_CONFIG" run "$CLOUDFLARED_TUNNEL_NAME" > "$CLOUDFLARED_LOG" 2>&1 &
  echo $! > "$CLOUDFLARED_PID_FILE"
}

wait_for_tunnel() {
  local elapsed=0
  while (( elapsed < TUNNEL_START_TIMEOUT )); do
    if is_tunnel_ready; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

show_status() {
  print_info "config=${CLOUDFLARED_CONFIG}"
  print_info "hostname=${TUNNEL_HOSTNAME:-<unknown>}"
  if is_hostname_reachable; then
    print_info "status=reachable"
    return 0
  fi
  if is_process_running; then
    print_info "status=process-running-but-host-unreachable"
    return 0
  fi
  print_info "status=stopped"
  return 1
}

ensure_tunnel() {
  if is_hostname_reachable; then
    print_info "Tunnel already reachable at https://${TUNNEL_HOSTNAME}"
    return 0
  fi

  if is_process_running; then
    print_info "Tunnel process already running; waiting for public hostname to become reachable..."
    if wait_for_tunnel; then
      print_info "Tunnel became reachable at https://${TUNNEL_HOSTNAME}"
      return 0
    fi
    print_info "Tunnel process is running, but hostname is still unreachable. Check ${CLOUDFLARED_LOG}"
    return 1
  fi

  start_tunnel
  if wait_for_tunnel; then
    print_info "Tunnel started successfully at https://${TUNNEL_HOSTNAME}"
    return 0
  fi

  print_info "Tunnel failed to become reachable within ${TUNNEL_START_TIMEOUT}s. Check ${CLOUDFLARED_LOG}"
  return 1
}

case "${1:---ensure}" in
  --status)
    show_status
    ;;
  --check)
    is_tunnel_ready
    ;;
  --ensure)
    ensure_tunnel
    ;;
  *)
    echo "Usage: $0 [--ensure|--status|--check]"
    exit 1
    ;;
esac

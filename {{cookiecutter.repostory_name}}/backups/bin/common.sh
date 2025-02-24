#!/bin/bash
set -euo pipefail

if [ -z "${_COMMON_SH_LOADED:-}" ]; then
  PATH=/usr/local/sbin:/usr/local/bin:$PATH

  check_env_vars() {
      local required_vars=("$@")
      local missing_vars=""
      for var in "${required_vars[@]}"; do
          if [ -z "${!var}" ]; then
              missing_vars+="$var "
          fi
      done

      if [ -n "$missing_vars" ]; then
          echo "Error: The following required environment variables are missing: $missing_vars" >&2
          exit 2
      fi
  }

  if [ -n "${SENTRY_DSN}" ]; then
    export SENTRY_DSN
    eval "$(sentry-cli bash-hook)"
  fi

  _COMMON_SH_LOADED=true
fi
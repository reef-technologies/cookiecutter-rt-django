#!/bin/sh
# A helper script to pretty-print json logs
# Usage (same as `docker compose logs`):
#   ./logs.sh --tail=100 -f app celery-worker

set -eu
docker compose logs --no-log-prefix "$@" | jq -Rr '
  # process each line as JSON, skip if not valid JSON
  fromjson? |
  select(. != null) |
  . as $orig |

  # 1. Using standard ANSI indices (30-37, 90-97)
  "\u001b[31m" as $red |      # Theme Red
  "\u001b[32m" as $green |    # Theme Green
  "\u001b[33m" as $yellow |   # Theme Yellow
  "\u001b[34m" as $blue |     # Theme Blue
  "\u001b[35m" as $purple |   # Theme Magenta/Purple
  "\u001b[36m" as $cyan |     # Theme Cyan
  "\u001b[90m" as $gray |     # Theme Bright Black / Gray
  "\u001b[0m" as $reset |

  # select color based on level
  (if $orig.level == "error" then $red
   elif $orig.level == "warning" then $yellow
   elif $orig.level == "info" then $green
   else $gray end) as $lvl_color |

  # form key=value pairs
  del(.timestamp, .level, .event) |
  to_entries | map("\($blue)\(.key)\($reset)=\($purple)\(.value)\($reset)") | join(" ") as $others |

  "\($gray)\($orig.timestamp)\($reset) [\($lvl_color)\($orig.level)\($reset)] \($orig.event) \($others)"
'
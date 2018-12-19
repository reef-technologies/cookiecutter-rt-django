#!/bin/bash

RELPATH="$(dirname "$0")"
ABSPATH="$(realpath "$RELPATH")"

(crontab -l ; echo -e "0 0 */3 * * \"$ABSPATH/letsencrypt_renew.sh\"\n@reboot sleep 60 && $ABSPATH/letsencrypt_renew.sh") 2>&1 |\
        grep -v "no crontab" |\
        sort |\
        uniq |\
        crontab -

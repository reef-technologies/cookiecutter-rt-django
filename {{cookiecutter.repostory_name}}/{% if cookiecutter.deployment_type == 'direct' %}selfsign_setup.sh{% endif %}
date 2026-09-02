#!/bin/bash
# Self-signed stand-in for letsencrypt_setup.sh, for deployments that cannot reach the ACME
# servers or have no public DNS name. It writes the same four files under letsencrypt/etc that
# nginx/templates/default.conf.template reads, so nothing in nginx/ or docker-compose.yml has to
# change. Clients must be told to trust the result; see "TLS certificates" in README.md.
set -euo pipefail
RELPATH="$(dirname "$0")"
ABSPATH="$(realpath "$RELPATH")"

cd "$ABSPATH"

source ./.env
: "${NGINX_HOST:?NGINX_HOST is empty in .env - set it to the hostname this deployment serves}"

LE_ETC="$ABSPATH/letsencrypt/etc"
LIVE_REL="live/$NGINX_HOST"
mkdir -p "$LE_ETC/dhparams" "$LE_ETC/$LIVE_REL"

# openssl runs in a container for the same reason the certbot flow does: the only tool the
# deployment host is required to have is docker. --user keeps the results owned by whoever ran
# the script, so the chmod below is not a root-only operation on a developer machine.
openssl_run() {
    docker run --rm \
        --user "$(id -u):$(id -g)" \
        -v "$LE_ETC:/etc/letsencrypt" \
        alpine/openssl \
        "$@"
}

# certbot's `certonly` keeps a certificate that is still valid instead of reissuing one. Do the
# same: rerunning the deployment steps must not silently invalidate the certificate that every
# client of this host was told to trust. Pass --force to reissue deliberately.
if [ "${1:-}" != "--force" ] && [ -f "$LE_ETC/$LIVE_REL/fullchain.pem" ] &&
    openssl_run x509 -in "/etc/letsencrypt/$LIVE_REL/fullchain.pem" -noout -checkend 2592000 >/dev/null; then
    echo "Certificate for $NGINX_HOST is present and not expiring within 30 days; keeping it."
    echo "Run '$0 --force' to reissue."
    exit 0
fi

# Same parameter the certbot flow generated. nginx loads it via ssl_dhparam whoever issued the
# certificate, and it is unrelated to the certificate itself, so it survives a reissue.
if [ ! -f "$LE_ETC/dhparams/dhparam.pem" ]; then
    openssl_run dhparam -out /etc/letsencrypt/dhparams/dhparam.pem 2048
fi

# Modern clients validate the SAN and ignore the CN entirely, and an address literal has to be
# typed as an IP SAN rather than a DNS one or the certificate is rejected on every connection.
if [[ "$NGINX_HOST" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ || "$NGINX_HOST" == *:* ]]; then
    SUBJECT_ALT_NAME="IP:$NGINX_HOST"
else
    SUBJECT_ALT_NAME="DNS:$NGINX_HOST"
fi

openssl_run req -x509 -nodes -newkey rsa:2048 -sha256 -days 3650 \
    -keyout "/etc/letsencrypt/$LIVE_REL/privkey.pem" \
    -out "/etc/letsencrypt/$LIVE_REL/fullchain.pem" \
    -subj "/CN=$NGINX_HOST" \
    -addext "subjectAltName=$SUBJECT_ALT_NAME" \
    -addext "basicConstraints=critical,CA:FALSE" \
    -addext "keyUsage=critical,digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

# ssl_trusted_certificate names the issuer, and a self-signed certificate is its own issuer.
cp "$LE_ETC/$LIVE_REL/fullchain.pem" "$LE_ETC/$LIVE_REL/chain.pem"

chmod 600 "$LE_ETC/$LIVE_REL/privkey.pem"
chmod 644 "$LE_ETC/$LIVE_REL/fullchain.pem" "$LE_ETC/$LIVE_REL/chain.pem"

echo
echo "Issued a self-signed certificate. Clients verify it against this fingerprint:"
openssl_run x509 -in "/etc/letsencrypt/$LIVE_REL/fullchain.pem" \
    -noout -subject -dates -fingerprint -sha256
echo
echo "Apply it with: docker compose up -d --force-recreate nginx"

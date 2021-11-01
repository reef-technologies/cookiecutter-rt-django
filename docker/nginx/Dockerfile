FROM alpine:3.14

RUN apk add --no-cache \
        nginx nginx-mod-http-vts \
        curl ca-certificates certbot-nginx gettext tzdata \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && mkdir /docker-entrypoint.d \
    && mkdir -p /usr/share/nginx/html \
    && touch /usr/share/nginx/html/index.html

# entrypoint scripts copied from official nginx site and adapted
# to alpine nginx version
COPY docker-entrypoint.sh /
COPY entrypoint/*.sh /docker-entrypoint.d/

# copy updated nginx with loading modules and vhost_traffic_status_zone
COPY etc/nginx.conf /etc/nginx/nginx.conf

ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 80 443
STOPSIGNAL SIGQUIT

CMD ["nginx", "-g", "daemon off;"]
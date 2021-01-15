ARG BASE_IMAGE=python:3.8-alpine

FROM $BASE_IMAGE AS base-image

WORKDIR /root/

RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --no-cache-dir b2

COPY ./send_backup.sh /root/
COPY ./retrieve_backup.sh /root/
COPY ./list_backups.sh /root/


ARG BASE_IMAGE=python:3.8-alpine

FROM $BASE_IMAGE AS base-image

WORKDIR /root/

RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --no-cache-dir b2

COPY ./send_backup.sh /root/
RUN chmod u+x send_backup.sh

COPY ./retrieve_backup.sh /root/
RUN chmod u+x retrieve_backup.sh

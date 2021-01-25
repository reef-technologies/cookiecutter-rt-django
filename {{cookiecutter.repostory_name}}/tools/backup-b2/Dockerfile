ARG BASE_IMAGE=python:3.8-alpine

FROM $BASE_IMAGE AS base-image

WORKDIR /root/

RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --no-cache-dir b2

COPY *.sh /root/


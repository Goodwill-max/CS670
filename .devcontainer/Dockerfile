FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git python3 libssl-dev libboost-all-dev libgmp-dev ca-certificates gdb && rm -rf /var/lib/apt/lists/*

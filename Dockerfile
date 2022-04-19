# Taken from: https://gist.github.com/patrickfuller/08d3dffec086845d3a3249629677ffce#file-alias_dns-py

# FROM alpine:latest
FROM ubuntu:latest

# Defaults
ENV USER=ubnt
ENV PASS=ubnt
ENV HOST=192.168.0.1
ENV SCRIPT=/alias_dns/alias_dns.py

# RUN apk update
# RUN apk upgrade
# RUN apk add openssh-client py3-paramiko py3-pip
# RUN python3 -m pip install pymongo
RUN apt update
RUN apt dist-upgrade --yes
RUN apt install --yes openssh-client python3-pip
RUN python3 -m pip install pymongo paramiko

RUN mkdir /alias_dns
ADD https://gist.github.com/patrickfuller/08d3dffec086845d3a3249629677ffce/raw/3bfa583654a8bdacc83e36a8f21891c1317fae5e/alias_dns.py /alias_dns/alias_dns.py
RUN chmod +x /alias_dns/alias_dns.py
COPY entry_point.sh /alias_dns/entry_point.sh
RUN chmod +x /alias_dns/entry_point.sh

ENTRYPOINT [ "/bin/bash", "/alias_dns/entry_point.sh" ]

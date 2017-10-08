FROM debian

RUN mkdir -p /home/user ;\
    useradd -r -d /home/user -s /sbin/nologin user ;\
    mkdir build ;\
    apt-get update ;\
    apt-get install -y file man manpages manpages-dev man-db less

WORKDIR "/home/user"


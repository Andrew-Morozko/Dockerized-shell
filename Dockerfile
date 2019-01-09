FROM alpine:3.8

RUN apk add g++

COPY dockerized-shell/shell/ /build

RUN g++ -Wall -O2 /build/shell.cpp -o /build/shell

# —————————————————————————————————————————————————————————————————————————————

FROM alpine:3.8

COPY --from=0 /build/shell /usr/bin/dockerized-shell

RUN apk add --no-cache openssh docker python3                  &&\
    pip3 install --upgrade pip                                 &&\
    pip3 install pipenv                                        &&\
    echo "/usr/bin/dockerized-shell" >>/etc/shells             &&\
    mkdir -p /home/test                                        &&\
    adduser -D -h /home/test -s /usr/bin/dockerized-shell test &&\
    chown -R test:root /home/test                              &&\
    echo "root:BkXLzMqngvuXdeRtxCDVNzPt" | chpasswd            &&\
    echo "test:cevpamZpztUfvBtKaRMpsCUu" | chpasswd

COPY rootfs /

COPY dockerized-shell/server/ /server

RUN cd '/server/'                                              &&\
    pipenv sync

# RUN ssh-keygen -A

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]

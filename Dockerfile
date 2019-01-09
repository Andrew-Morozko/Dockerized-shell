ARG DEFAULT_SOCKET_PATH="/tmp/dockerized-shell.sock"

FROM alpine:3.8
ARG DEFAULT_SOCKET_PATH
ENV SOCKET_PATH=$DEFAULT_SOCKET_PATH

RUN apk add g++

COPY dockerized-shell/shell/ /build

RUN g++ -Wall -O2 -D SOCKET_PATH="$SOCKET_PATH" /build/shell.cpp -o /build/shell

# —————————————————————————————————————————————————————————————————————————————

FROM alpine:3.8
ARG DEFAULT_SOCKET_PATH
ENV SOCKET_PATH=$DEFAULT_SOCKET_PATH
ENV SOCKET_GROUP="dockerized_group"
ENV SHELL_PATH="/usr/bin/dockerized-shell"

COPY --from=0 /build/shell "$SHELL_PATH"

RUN apk add --no-cache openssh docker python3  &&\
    pip3 install --upgrade pip                 &&\
    pip3 install pipenv                        &&\
    addgroup "$SOCKET_GROUP"                   &&\
    chown "root:$SOCKET_GROUP" "$SHELL_PATH"   &&\
    chmod 750 "$SHELL_PATH"                    &&\
    echo "$SHELL_PATH" >>/etc/shells

WORKDIR '/server/'
COPY dockerized-shell/server/ .
RUN pipenv sync

# RUN ssh-keygen -A
# Debug stuff

RUN mkdir -p /home/test                                               &&\
    adduser -D -h /home/test -G "$SOCKET_GROUP" -s "$SHELL_PATH" test &&\
    echo "root:BkXLzMqngvuXdeRtxCDVNzPt" | chpasswd                   &&\
    echo "test:cevpamZpztUfvBtKaRMpsCUu" | chpasswd

COPY rootfs /

#TODO: create server process (run as not-root)


EXPOSE 22

ENTRYPOINT "/server/entrypoint.sh"

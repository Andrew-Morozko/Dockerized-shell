FROM task_base

COPY ./container-init.sh /build

RUN chmod +x /build/container-init.sh ;\
    /build/container-init.sh ;\
    rm -rf /build ;\
    chown -R user:user /home/user/


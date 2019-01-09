// compile: g++ -Wall -O2 shell.cpp -o shell

#include <sys/socket.h>

#include <sys/un.h>
#include <stdlib.h>

// #include <sys/ioctl.h>

#include <unistd.h>

#include <errno.h>
#include <cstring>

#include <stdio.h>


#define eprintf(...) fprintf(stderr, __VA_ARGS__);


using namespace std;

#ifdef SOCKET_PATH
    #define STRINGIZE(x) #x
    #define STRINGIZE_VALUE_OF(x) STRINGIZE(x)
    #define SOCKET_PATH_STR STRINGIZE_VALUE_OF(SOCKET_PATH)
#else
    #error SOCKET_PATH is not defined. Define it as a compiler argument: -D SOCKET_PATH="/my/path"
#endif

extern char **environ;

bool run() {
    const int STD_FDS[] = {STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO};
    const int STD_FDS_SIZE = sizeof(STD_FDS);

    int sock;

    if ((sock = socket(AF_UNIX, SOCK_DGRAM, 0)) == -1) {
        eprintf("Socket error %d: %s\n", errno, strerror(errno));
        return false;
    }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH_STR, sizeof(addr.sun_path)-1);

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        eprintf("Connect error %d: %s\n", errno, strerror(errno));
        return false;
    }


    //////////////////////// Send stdin, stdout, stderr through unix socket
    // Required reading:
    // http://alas.matf.bg.ac.rs/manuals/lspe/snode=153.html
    // https://linux.die.net/man/3/cmsg

    char cmsgbuf[CMSG_SPACE(STD_FDS_SIZE)] = {0}; // CMSG_SPACE - full section size with headers and padding
    struct msghdr msg = {0};

    msg.msg_name = NULL;                  // filled by recv
    msg.msg_namelen = 0;                  // filled by recv
    msg.msg_iov = NULL;                   // pointer to iovec array, filled later
    msg.msg_iovlen = 0;                   // iovecs in array, filled later
    msg.msg_control = cmsgbuf;            // ancillary data buffer
    msg.msg_controllen = sizeof(cmsgbuf); // ancillary data buffer length
    msg.msg_flags = 0;                    // filled by recv

    struct cmsghdr* cmsg = CMSG_FIRSTHDR(&msg); // pointer to the first cmsghdr struct
    cmsg->cmsg_level = SOL_SOCKET;
    cmsg->cmsg_type = SCM_RIGHTS;
    cmsg->cmsg_len = CMSG_LEN(STD_FDS_SIZE);

    int* fdptr = (int *) CMSG_DATA(cmsg); // pointer to data (follows header and padding)

    memcpy(fdptr, STD_FDS, STD_FDS_SIZE);

    //////////////////////// Prepare message with env vars

    char** environ_p = environ;

    // Go to the end of the array
    while (*environ_p++){}

    // Count env vars
    int env_var_count = environ_p - environ;

    // Allocate necessary memory
    struct iovec* iov = (iovec*) malloc(sizeof(iovec) * env_var_count);

    struct iovec* iov_p = iov;
    environ_p = environ;

    // Go again through array, fill in iovec structs
    while(*environ_p){
        iov_p->iov_base = *environ_p;           // String start address
        iov_p->iov_len = strlen(*environ_p)+1;  // String length in bytes, +1 to capture \0

        environ_p++;
        iov_p++;
    }

    msg.msg_iov = iov;
    msg.msg_iovlen = env_var_count;


    if (sendmsg(sock, &msg, 0) == -1) {
        eprintf("Sendmsg error: %s\n", strerror(errno));

        free(iov);
        close(sock);
        return false;
    }

    free(iov);
    close(sock);

    /* detach this process from controlling tty
     * (https://github.com/Yelp/dumb-init/blob/f594e57209d1882e18772d04ec4b0f3b2e52cec0/dumb-init.c#L264)
     * do we need this? Docker handles it's own tty
     * #include <sys/ioctl.h> if you need this
     */
    /*
    if (ioctl(0, TIOCNOTTY, NULL) == -1) {
        eprintf("ioctl detach failed %d: %s\n", errno, strerror(errno));
    }
    */

    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);

    // TODO: change signal mask, check if all signals are passed through

    return true;
}


int main() {
    if(run()){
        for (;;) {pause();}  // just hang in there for ssh not to close connection
        return 0;
    }
    return -1;
}

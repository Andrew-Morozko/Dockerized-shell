#!/bin/bash
# This is a library of useful shell functions for redirecting streams
# and hiding unwanted output

# Store original stderr and stdout (to user's ssh shell) on fd # 501 and 502
exec 501>&1
exec 502>&2

function hide_output
{
    exec 1>/dev/null
    exec 2>/dev/null
}

function restore_output
{
    # Restore original stdin and stdout
    exec 1>&501
    exec 2>&502
}

function with_output {
    # Pseudo context manager from python, wraps command
    # FROM https://stackoverflow.com/a/24780266/
    cmd=("$@")

    restore_output
    "${cmd[@]}" # Execute command
    EXIT_CODE=$?
    hide_output
    return $EXIT_CODE
}

function with_stdout {
    # Pseudo context manager from python, wraps command
    # FROM https://stackoverflow.com/a/24780266/
    cmd=("$@")

    exec 1>&501
    "${cmd[@]}" # Execute command
    EXIT_CODE=$?
    exec 1>/dev/null
    return $EXIT_CODE
}

# I want to explicitly specify when script can communicate with user
hide_output

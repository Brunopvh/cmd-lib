#!/usr/bin/env python3

from platform import system

if system() == 'Linux':
    from .__main__ import (
        is_admin,
        sudo_command,
        device_ismounted,
        LinuxShellCore,
        gpg_utils,
    )


from .__main__ import (
    __version__,
    shellcore,
    ExecShellCommand,
    PythonShellCore,
    File,
    ByteSize,
    unpack,
    get_term_col,
    get_bytes,
    shasum,
)

import os.path
from typing import Optional

from paramiko.sftp_client import SFTPClient
from paramiko.transport import Transport

import gportal


def sftp(username: Optional[str] = None, password: Optional[str] = None) -> "SFTP":
    """Opens an SFTP session with G-Portal.

    Args:
        username: G-Portal username. If not provided, the value of `gportal.username` is used.
        password: G-Portal password. If not provided, the value of `gportal.password` is used.

    Returns:
        An instance of [`SFTP`][gportal.sftp.SFTP].
    """

    username = username or gportal.username
    password = password or gportal.password

    if username is None or password is None:
        raise ValueError("username and password are required")

    return SFTP.connect(username, password)


class SFTP:
    """Wrapper of the G-Portal SFTP interface.

    Attributes:
        client: An instance of [`paramiko.SFTPClient`][paramiko.sftp_client.SFTPClient].
    """

    HOST = "ftp.gportal.jaxa.jp"
    PORT = 2051

    def __init__(self, sftp_client: SFTPClient):
        self.client: SFTPClient = sftp_client

    def __enter__(self):  # type: ignore
        return self

    def __exit__(self, type, value, traceback):  # type: ignore
        self.close()

    @classmethod
    def connect(cls, username: str, password: str) -> "SFTP":
        """Opens an SFTP session with G-Portal.

        Args:
            username: G-Portal username.
            password: G-Portal password.

        Returns:
            An instance of [`SFTP`][gportal.sftp.SFTP].
        """
        transport = Transport((cls.HOST, cls.PORT))
        transport.connect(username=username, password=password)
        sftp_client = transport.open_sftp_client()
        if sftp_client is None:  # will never happen
            raise RuntimeError("Failed to open SFTP session")

        return cls(sftp_client)

    def close(self) -> None:
        """Closes the SFTP session."""
        self.client.close()

    def listdir(self, path: str) -> list[str]:
        """Returns a list of entries in the given directory.

        Wraps [`paramiko.SFTPClient.listdir`][paramiko.sftp_client.SFTPClient.listdir].

        Args:
            path: Remote path to list.

        Returns:
            A list of entries.
        """
        return self.client.listdir(path)

    def download(self, remote_paths: list[str], local_dir: str) -> None:
        """Downloads files to a local directory.

        Args:
            remote_paths: List of remote paths to download.
            local_dir: Local directory to download to.
        """
        for remote_path in list(remote_paths):
            self.client.get(remote_path, os.path.join(local_dir, os.path.basename(remote_path)))

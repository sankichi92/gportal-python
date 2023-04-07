import os.path
import re
from collections.abc import Iterable
from typing import Optional, Union

from paramiko.sftp_client import SFTPClient
from paramiko.transport import Transport

import gportal

from .product import Product


def download(
    target: Union[str, Product, Iterable[Union[str, Product]]],
    local_dir: str = ".",
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> list[str]:
    """Downloads files to a local directory via SFTP.

    Args:
        target: Remote path, Product object, or a list of them.
        local_dir: Local directory to download to.
        username: G-Portal username. If not provided, the value of `gportal.username` is used.
        password: G-Portal password. If not provided, the value of `gportal.password` is used.

    Returns:
        A list of local paths of the downloaded files.
    """
    with SFTP.connect(username, password) as sftp:
        return sftp.download(target, local_dir)


class SFTP:
    """Wrapper of the G-Portal SFTP interface.

    Attributes:
        client: An instance of [`paramiko.SFTPClient`][paramiko.sftp_client.SFTPClient].
    """

    HOST = "ftp.gportal.jaxa.jp"
    PORT = 2051

    def __init__(self, sftp_client: SFTPClient):
        self.client: SFTPClient = sftp_client

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore[no-untyped-def]
        self.close()

    @classmethod
    def connect(cls, username: Optional[str] = None, password: Optional[str] = None) -> "SFTP":
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

        transport = Transport((cls.HOST, cls.PORT))
        transport.connect(username=username, password=password)

        sftp_client = transport.open_sftp_client()
        if sftp_client is None:  # will never happen
            raise RuntimeError("Failed to open SFTP session")

        return cls(sftp_client)

    def close(self) -> None:
        """Closes the SFTP session."""
        self.client.close()

    def listdir(self, path: str = "/", /, filter_pattern: Optional[str] = None, fullpath: bool = False) -> list[str]:
        """Returns a list containing the names of the entries in the given path.

        Wraps [`paramiko.SFTPClient.listdir`][paramiko.sftp_client.SFTPClient.listdir].

        Args:
            path: Remote path to list. It must be absolute.
            filter_pattern: Regular expression to filter the entries.
            fullpath: If `True`, the returned list contains full paths of the entries.

        Returns:
            A list containing the names of the entries.
        """
        self._reset_cwd()
        entries = self.client.listdir(path)

        if filter_pattern:
            entries = [entry for entry in entries if re.search(filter_pattern, entry)]

        if fullpath:
            return [os.path.join(path, entry) for entry in entries]
        else:
            return entries

    def download(
        self, target: Union[str, Product, Iterable[Union[str, Product]]], local_dir: str
    ) -> Union[str, list[str]]:
        """Downloads files to a local directory.

        Args:
            target: Remote path, Product object, or a list of them.
            local_dir: Local directory to download to.

        Returns:
            If `target` is a single path or Product object, returns the local path of the downloaded file.
            If `target` is a list of paths or Product objects, returns a list of local paths of the downloaded files.

        Raises:
            ValueError: If the given product has no URL to download.
        """
        self._reset_cwd()

        if isinstance(target, Iterable) and not isinstance(target, str):
            return [self._download_single(t, local_dir) for t in target]
        else:
            return self._download_single(target, local_dir)

    def _download_single(self, target: Union[str, Product], local_dir: str) -> str:
        if isinstance(target, Product):
            if target.data_path is None:
                raise ValueError(f"Product {target.id} has no URL to download")

            target = target.data_path

        local_path = os.path.join(local_dir, os.path.basename(target))
        self.client.get(target, local_path)
        return local_path

    def _reset_cwd(self) -> None:
        self.client.chdir()

import pytest
from paramiko import SFTPClient

from gportal.product import Product
from gportal.sftp import SFTP


class TestSFTP:
    @pytest.fixture
    def paramiko_client(self, mocker):
        return mocker.create_autospec(SFTPClient, instance=True)

    @pytest.fixture
    def sftp(self, paramiko_client):
        return SFTP(paramiko_client)

    def test_close(self, sftp, paramiko_client):
        # When
        sftp.close()

        # Then
        paramiko_client.close.assert_called_once()

    def test_listdir(self, sftp, paramiko_client):
        # Given
        paramiko_client.listdir.return_value = ["file1.h5", "file2.h5"]

        # When
        entries = sftp.listdir("/dir")

        # Then
        paramiko_client.listdir.assert_called_once_with("/dir")
        assert entries == ["file1.h5", "file2.h5"]

    def test_listdir_filter_pattern(self, sftp, paramiko_client):
        # Given
        paramiko_client.listdir.return_value = ["file1.h5", "file2.h5"]

        # When
        entries = sftp.listdir("/dir", filter_pattern=r"1\.h5")

        # Then
        assert entries == ["file1.h5"]

    def test_listdir_fullpath(self, sftp, paramiko_client):
        # Given
        paramiko_client.listdir.return_value = ["file1.h5", "file2.h5"]

        # When
        entries = sftp.listdir("/dir", fullpath=True)

        # Then
        assert entries == ["/dir/file1.h5", "/dir/file2.h5"]

    def test_download(self, sftp, paramiko_client):
        # Given
        target = ["/GCOM-C/file1.h5", "/GCOM-C/file2.h5"]

        # When
        downloaded = sftp.download(target, local_dir="/downloads")

        # Then
        paramiko_client.get.assert_any_call(target[0], "/downloads/file1.h5")
        paramiko_client.get.assert_any_call(target[1], "/downloads/file2.h5")
        assert downloaded == ["/downloads/file1.h5", "/downloads/file2.h5"]

    def test_download_product(self, sftp, paramiko_client):
        # Given
        target = Product(
            {"properties": {"product": {"fileName": "https://gportal.jaxa.jp/download/GCOM-C/file.h5"}}},
        )

        # When
        downloaded = sftp.download(target, local_dir="/downloads")

        # Then
        paramiko_client.get.assert_called_once_with(target.data_path, "/downloads/file.h5")
        assert downloaded == ["/downloads/file.h5"]

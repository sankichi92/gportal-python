import os.path

from paramiko import Transport


def sftp(username, password):
    return SFTP.connect(username, password)


class SFTP:
    HOST = "ftp.gportal.jaxa.jp"
    PORT = 2051

    def __init__(self, sftp_client):
        self.client = sftp_client

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @classmethod
    def connect(cls, username, password):
        transport = Transport((cls.HOST, cls.PORT))
        transport.connect(username=username, password=password)
        return cls(transport.open_sftp_client())

    def close(self):
        self.client.close()

    def ls(self, path):
        return self.client.listdir(path)

    def download(self, remote_paths, local_dir):
        for remote_path in list(remote_paths):
            self.client.get(remote_path, os.path.join(local_dir, os.path.basename(remote_path)))

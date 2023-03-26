import os

from .datasets import datasets
from .search import search
from .sftp import sftp

# Configuration variables
username = os.getenv("GPORTAL_USERNAME", None)
password = os.getenv("GPORTAL_PASSWORD", None)

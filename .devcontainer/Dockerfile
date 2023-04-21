FROM mcr.microsoft.com/devcontainers/python:0-3.11

ENV PYTHONUNBUFFERED 1

# For cartopy:
# https://scitools.org.uk/cartopy/docs/latest/installing.html#ubuntu-debian
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends libgeos-dev

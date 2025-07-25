# Dockerfile
FROM debian:stable-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl jq make git \
  python3-pygments gnuplot \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended \
  ghostscript imagemagick poppler-utils && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /data
VOLUME ["/data"]
COPY entrypoint.sh /data/entrypoint.sh
RUN chmod +x /data/entrypoint.sh
ENTRYPOINT ["/data/entrypoint.sh"]

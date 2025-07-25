FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive \
  BUILD_ENV=development

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl jq make git \
  python3-pygments gnuplot \
  ghostscript imagemagick poppler-utils


RUN if [ "$BUILD_ENV" = "production" ]; then \
        apt-get install -y --no-install-recommends texlive-full; \
    else \
        apt-get install -y --no-install-recommends \
        texlive-latex-base texlive-latex-recommended texlive-latex-extra \
        texlive-fonts-recommended texlive-fonts-extra; \
    fi && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /data
VOLUME ["/data"]
COPY entrypoint.sh /data/entrypoint.sh
RUN chmod +x /data/entrypoint.sh
ENTRYPOINT ["/data/entrypoint.sh"]

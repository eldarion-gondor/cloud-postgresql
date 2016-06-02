FROM ubuntu:xenial

ENV GOSU_VERSION 1.9

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential bison flex curl \
        ca-certificates libreadline6-dev zlib1g-dev python3 \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture)" > /usr/local/bin/gosu \
    && curl -sL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture).asc" > /usr/local/bin/gosu.asc \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
    && gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
    && rm -r "$GNUPGHOME" /usr/local/bin/gosu.asc \
    && chmod +x /usr/local/bin/gosu \
    && gosu nobody true \
    && cd /usr/local/src \
    && curl -s https://ftp.postgresql.org/pub/source/v9.5.3/postgresql-9.5.3.tar.gz | tar zxvf - \
    && cd postgresql-9.5.3 \
    && ./configure && make && make install \
    && apt-get purge -y --auto-remove \
        build-essential bison flex curl

RUN groupadd -r postgres --gid=999 && useradd -r -g postgres --uid=999 postgres
ENV PATH /usr/local/pgsql/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN mkdir -p /etc/ec-db
ADD pg_hba.conf /etc/ec-db/
ADD postgresql.conf /etc/ec-db/

ADD entrypoint.py /usr/bin/entrypoint
RUN chmod +x /usr/bin/entrypoint

ENTRYPOINT ["entrypoint"]

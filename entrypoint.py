#!/usr/bin/env python3

import os
import subprocess
import sys


PGDATA = os.environ.setdefault("PGDATA", "/data/db")
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
APP_USER = os.environ.get("APP_USER", "app")
APP_PASSWORD = os.environ["APP_PASSWORD"]
APP_DB = os.environ.get("APP_DB", APP_USER)

CONFIG = {
    "auth_method": os.environ.get("POSTGRES_CONFIG_AUTH_METHOD", "md5"),
    "shared_buffers": os.environ.get("POSTGRES_CONFIG_SHARED_BUFFERS", "128MB"),
    "temp_buffers": os.environ.get("POSTGRES_CONFIG_TEMP_BUFFERS", "8MB"),
    "work_mem": os.environ.get("POSTGRES_CONFIG_WORK_MEM", "4MB"),
    "maintenance_work_mem": os.environ.get("POSTGRES_CONFIG_MAINTENANCE_WORK_MEM", "64MB"),
    "effective_cache_size": os.environ.get("POSTGRES_CONFIG_EFFECTIVE_CACHE_SIZE", "4GB")
}


def prepare():
    subprocess.run(["mkdir", "-p", PGDATA])
    subprocess.run(["chmod", "700", PGDATA])
    subprocess.run(["chown", "-R", "postgres", PGDATA])


def initdb():
    if not os.path.exists(os.path.join(PGDATA, ".initdb")):
        subprocess.run(["gosu", "postgres:postgres", "initdb"])
        subprocess.run(["touch", os.path.join(PGDATA, ".initdb")])


def write_config(src, dest, **ctx):
    with open(src) as src_fp, open(dest, "w") as dest_fp:
        dest_fp.write(src_fp.read().format(**ctx))


def configure():
    subprocess.run(["gosu", "postgres", "pg_ctl", "-D", PGDATA, "-o", "-c listen_addresses='localhost'", "-w", "start"])
    psql = ["psql", "-v", "ON_ERROR_STOP=1"]
    subprocess.run(
        psql + ["--username", "postgres"],
        input="""ALTER USER postgres WITH PASSWORD '{password}'""".format(
            password=POSTGRES_PASSWORD,
        ).encode("utf-8"),
    )
    subprocess.run(
        psql + ["--username", "postgres"],
        input="""CREATE USER "{user}" WITH PASSWORD '{password}'""".format(
            user=APP_USER,
            password=APP_PASSWORD,
        ).encode("utf-8"),
    )
    subprocess.run(
        psql + ["--username", "postgres"],
        input="""CREATE DATABASE "{db}" WITH OWNER '{user}'""".format(
            db=APP_DB,
            user=APP_USER,
        ).encode("utf-8"),
    )
    subprocess.run(["gosu", "postgres", "pg_ctl", "-D", PGDATA, "-m", "fast", "-w", "stop"])


def run():
    if len(sys.argv) == 1 or sys.argv[1] == "postgres":
        os.execlp("gosu", "gosu", "postgres:postgres", "postgres")
    else:
        os.execlp(sys.argv[1], os.path.basename(sys.argv[1]))


def main():
    prepare()
    initdb()
    write_config(
        "/etc/ec-db/pg_hba.conf",
        os.path.join(PGDATA, "pg_hba.conf"),
        **CONFIG
    )
    write_config(
        "/etc/ec-db/postgresql.conf",
        os.path.join(PGDATA, "postgresql.conf"),
        **CONFIG
    )
    configure()
    run()


if __name__ == "__main__":
    main()

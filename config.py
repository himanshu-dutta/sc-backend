import os
import yaml
import argparse
from decouple import config

dev_config = {
    "services": {
        "backend": {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "command": "python manage.py runserver 0.0.0.0:8000",
            "depends_on": ["redis"],
            "ports": ["8000:8000"],
            "volumes": [".:/app"],
        },
        "redis": {
            "environment": [
                "ALLOW_EMPTY_PASSWORD=yes",
                "REDIS_DISABLE_COMMANDS=FLUSHDB,FLUSHALL",
            ],
            "image": "docker.io/bitnami/redis:6.2-debian-10",
            "ports": ["6379:6379"],
            "volumes": [".redis_data:/bitnami/redis/data"],
        },
    },
    "version": "3.8",
}

prod_config = {
    "services": {
        "backend": {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "command": "python manage.py runserver 0.0.0.0:8000",
            "depends_on": ["redis"],
            "ports": ["8000:8000"],
            "volumes": [".:/app"],
        },
        "db": {
            "environment": {
                "MYSQL_DATABASE": config("DB_NAME"),
                "MYSQL_PASSWORD": config("DB_PASSWORD"),
                "MYSQL_ROOT_PASSWORD": config("DB_PASSWORD"),
                "MYSQL_USER": config("DB_USER"),
            },
            "image": "mysql:5.7.22",
            "restart": "always",
            "volumes": [".dbdata:/var/lib/mysql"],
        },
        "redis": {
            "depends_on": ["db"],
            "environment": [
                "ALLOW_EMPTY_PASSWORD=no",
                "REDIS_DISABLE_COMMANDS=FLUSHDB,FLUSHALL",
            ],
            "image": "docker.io/bitnami/redis:6.2-debian-10",
            "ports": ["6379:6379"],
            "volumes": [".redis_data:/bitnami/redis/data"],
        },
    },
    "version": "3.8",
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Deployment Config Generator")
    parser.add_argument("mode", type=str, default="dev", choices=["dev", "prod"])

    args = parser.parse_args()

    if os.path.isfile("./docker-compose.yml"):
        os.remove("./docker-compose.yml")

    if args.mode == "dev":
        with open("./docker-compose.yml", "w") as fl:
            yaml.dump(dev_config, fl)

    if args.mode == "prod":
        with open("./docker-compose.yml", "w") as fl:
            yaml.dump(prod_config, fl)

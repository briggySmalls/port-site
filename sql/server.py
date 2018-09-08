import docker
from dataclasses import dataclass
import time
import tarfile
import os
import logging


logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT_S = 15


def _get_tar_bytes(file_name):
    # Create a tarball
    tarball = "{}.tar".format(file_name)
    with tarfile.open(tarball, "w") as tar:
        tar.add(file_name)
    # Read the file's bytes
    with open(tarball, mode='rb') as file:
        content = file.read()
    # Delete the temprary file
    os.remove(tarball)
    return content


@dataclass
class SqlConnectionParams:
    host: str
    port: int
    username: str
    password: str


class SqlServer:
    INTERNAL_PORT = 3306
    CONTAINER_NAME = 'mariadb'

    CONNECTION_PARAMS = SqlConnectionParams(
        host='127.0.0.1',
        port=3306,
        username='root',
        password='password')

    """Managed resource for an SQL docker instance"""
    def __init__(self):
        # Create a docker client
        self.client = docker.from_env()
        self.container = None

    def __enter__(self):
        # Start the docker container
        self._start_container()
        # Wait till the SQL connection can be made
        self._wait_till_initialised()
        return self

    def __exit__(self, *args):
        # Kill the container
        self._kill_container()

    @property
    def db_params(self):
        return self.CONNECTION_PARAMS

    def is_connected(self):
        try:
            self.execute(
                "mysqladmin status -u{} -p{}".format(
                    self.db_params.username,
                    self.db_params.password))
            return True
        except RuntimeError:
            return False

    def restore(self, database, backup):
        logger.debug("Creating tarball of backup")
        tar_bytes = _get_tar_bytes(backup)
        # Copy the back up the container
        logger.debug("Moving archive to container")
        self.container.put_archive("/", tar_bytes)
        # Create the database
        logger.debug("Creating database")
        self.execute(
            'mysql -u{} -p{} '
            '-e "CREATE DATABASE IF NOT EXISTS {};"'.format(
                self.db_params.username,
                self.db_params.password,
                database))
        # Resore the backup to the database
        self.execute(
            'sh -c "cat {} | mysql -u{} -p{} {}"'.format(
                backup,
                self.db_params.username,
                self.db_params.password,
                database))

    def dump(self, filename, database, tables):
        self.container.exec_run(
            "mysqldump -u{} -p{} {} {} > {}".format(
                self.db_params.username,
                self.db_params.password,
                database,
                " ".join(tables),
                filename))

    def execute(self, command):
        exit_code, output = self.container.exec_run(command)
        if exit_code != 0:
            raise RuntimeError(
                "Command failed with exit code: {}\nCommand: {}\nOutput: {}".format(
                    exit_code, command, output))

    def _wait_till_initialised(self, timeout=DEFAULT_TIMEOUT_S):
        # Wait till either connected or timeout
        start = time.time()
        while not self.is_connected() and time.time() - start < timeout:
            time.sleep(1)
        # Check if we timed out
        if not self.is_connected():
            raise RuntimeError("SQL connection timeout ({}s)".format(timeout))

    def _start_container(self):
        # Run the MariaDB docker container (detach to continue execution)
        self.container = self.client.containers.run(
            "mariadb:latest",
            detach=True,
            ports={self.INTERNAL_PORT: (
                self.db_params.host, self.db_params.port)},
            environment={'MYSQL_ROOT_PASSWORD': self.db_params.password},
            name=self.CONTAINER_NAME,
            auto_remove=True)

    def _kill_container(self):
        if self.container:
            self.container.kill()
            self.container = None

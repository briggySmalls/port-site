"""Command line interface for the conversion tool"""

import click
import sys
import logging

from port import process
from sql.server import SqlServer
from sql.client import SqlClient

DATABASE = "wp"


@click.command()
@click.argument("backup", type=click.Path(exists=True))
def main(backup):
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Creating SQL docker container")
    with SqlServer() as server:
        # First backup from the archive
        logging.info("Restoring data from backup")
        server.restore(DATABASE, backup)
        # Create an SQLAlchemy manager
        logging.info("Establishing SQLAlchemy connection to database")
        manager = SqlClient(server.db_params, DATABASE)
        # Now process using the manager
        process(manager)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

"""Command line interface for the conversion tool"""

import sys
import logging

import click

from port import process
from sql.server import SqlServer, SqlConnectionParams
from sql.client import SqlClient

DATABASE = "wp"


def run(server, backup, target_client):
    # First backup from the archive
    logging.info("Restoring data from backup")
    server.restore(DATABASE, backup)
    # Create an SQLAlchemy manager for the source server
    logging.info("Establishing SQLAlchemy connection to source database")
    source_client = SqlClient(server.db_params, DATABASE)
    # Now process using the manager
    process(source_client, target_client)
    # Obtain a dump
    # server.dump("dump.sql", target_params.[
    #     "wp_posts",
    #     "wp_postmeta",
    #     "wp_terms",
    #     "wp_termmeta",
    #     "wp_term_taxonomy",
    #     "wp_term_relationships",
    # ])


@click.command()
@click.argument("backup", type=click.Path(exists=True))
# @click.argument("output", type=click.Path(exists=False))
@click.option("-d", "--database", help="Target SQL database", required=True)
@click.option("-u", "--username", help="Target SQL username", required=True)
@click.option("-p", "--password", help="Target SQL password", required=True)
@click.option("-h", "--host", help="Target SQL host/port", required=True)
@click.option("-po", "--port", help="Target SQL port", required=True)
def main(backup, database, username, password, host, port):
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Create an SQLAlchemy manager for the target server
    logging.info("Establishing SQLAlchemy connection to target database")
    target_params = SqlConnectionParams(
        username=username,
        password=password,
        host=host,
        port=port)
    target_client = SqlClient(target_params, database)

    logging.info("Creating SQL docker container")

    server = SqlServer()
    server._start_container()
    server._wait_till_initialised()
    try:
        run(server, backup, target_client)
    except Exception as exc:
        logging.exception("Error during conversion")


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

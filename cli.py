"""Command line interface for the conversion tool"""

import click
import sys
import logging

from port import process
import sql


@click.command()
@click.option('-u', '--username', help="database username", required=True)
@click.option('-p', '--password', help="database password", required=True)
def main(username, password):
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # First get a session
    manager = sql.DbManager(
        username=username,
        password=password)

    process(manager)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

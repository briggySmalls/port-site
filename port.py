"""Tool to port original site to site under development"""

import sys

import click

import sql
import wpalchemy.classes as wp


@click.command()
@click.option('-u', '--username', help="database username", required=True)
@click.option('-p', '--password', help="database password", required=True)
def main(username, password):
    # First get a session
    manager = sql.DbManager(
        username=username,
        password=password)

    # Query terms for now
    for term in manager.session.query(wp.Term):
        print(term.name)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

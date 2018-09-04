"""Tool to port original site to site under development"""

import sys
import logging

import click
from sqlalchemy import or_, not_
import wpalchemy.classes as wp

import sql
import converters


class ConverterFactory:
    def __init__(self, manager):
        self.manager = manager

    def create(self, converter):
        class_ = getattr(converters, converter)
        return class_(self.manager)


def cleanup(manager):
    # Remove unwanted posts
    desired_post_types = [
        'post',
        'sd-event',
        'sd-product',
        'acf-field',
        'acf-field-group',
        'attachment',
        'revision',
        'page',
        'nav_menu_item',
    ]
    manager.session.query(wp.Post).filter(
        not_(or_(*[wp.Post.post_type == pt for pt in desired_post_types]))).delete(
            synchronize_session='fetch')
    # Remove unwanted terms
    desired_taxonomies = [
        'sd-author',
        'category',
        'sd-product-cat',
        'nav_menu',
        'post_format'
    ]
    manager.session.query(wp.Term).filter(
        not_(or_(*[wp.Term.taxonomy == pt for pt in desired_taxonomies]))).delete()


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

    # Create a converter factory
    factory = ConverterFactory(manager)

    # Convert the database
    factory.create('AuthorsConverter').convert()
    factory.create('EventsConverter').convert()
    factory.create('ProductsConverter').convert()

    # Commit changes
    cleanup(manager)
    manager.session.commit()


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

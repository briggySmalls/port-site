"""Tool to port original site to site under development"""

import sys

import click

import sql
import wpalchemy.classes as wp


def split_authors(manager):
    """Finds all posts with multiple authors and splits them out

    Args:
        manager (DbManager): Manager for the SQL connection
    """
    # Find all author fields with more than one author
    multi_authors = manager.session.query(wp.PostMeta).filter(
        wp.PostMeta.meta_key == 'author',
        wp.PostMeta.meta_value.like('%&%'))  # Has an ampersand in string

    # Process each multi-author
    for entry in multi_authors:
        # Extract the authors from the entry
        author_names = entry.meta_value.split(' & ')
        # Update the current author with just the first
        for i, author_name in enumerate(author_names):
            if i == 1:
                # Update the first author
                entry.meta_value = author_name
            else:
                # Create a new author
                new_author = wp.PostMeta(
                    meta_key=entry.meta_key,  # Copy the key ('author')
                    meta_value=author_name)  # Use the separated name
                new_author.post_id = entry.post_id  # Link to the same post

    # Push the updates
    manager.session.commit()


@click.command()
@click.option('-u', '--username', help="database username", required=True)
@click.option('-p', '--password', help="database password", required=True)
def main(username, password):
    # First get a session
    manager = sql.DbManager(
        username=username,
        password=password)

    # Query terms for now
    split_authors(manager)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter


def convert_authors(manager):
    # First get all the old authors
    authors = manager.session.query(wp.PostMeta).filter_by(meta_key='author')

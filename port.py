"""Tool to port original site to site under development"""

import sys
import logging
import pdb

import click

import sql
from sqlalchemy.sql.expression import func
from sqlalchemy import and_, or_, not_
import wpalchemy.classes as wp


def split_authors(manager):
    """Finds all posts with multiple authors and splits them out

    Args:
        manager (DbManager): Manager for the SQL connection
    """
    # Find all author fields with more than one author
    multi_authors = manager.session.query(wp.PostMeta).filter(
        wp.PostMeta.meta_key == 'author',
        wp.PostMeta.meta_value.contains('&'))  # Has an ampersand in string

    # Process each multi-author
    new_authors = []
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
                new_authors.append(new_author)

    # Trim all whitespace
    manager.session.query(wp.PostMeta).filter_by(
        meta_key='author').update(
            {wp.PostMeta.meta_value: func.ltrim(func.rtrim(wp.PostMeta.meta_value))},
            synchronize_session='fetch')

    # Push the updates
    manager.session.add_all(new_authors)


def convert_authors(manager):
    # First split up any dual-authored values
    split_authors(manager)
    # Add authors as terms, with associated posts
    new_terms = []
    current_term = None
    for author in manager.session.query(wp.PostMeta).filter_by(
            meta_key='author').order_by(wp.PostMeta.meta_value):
        # Ensure we have a term for the current author
        if current_term is None or current_term.name != author.meta_value:
            logging.debug("New author: '%s'", author.meta_value)
            if current_term is not None:
                # Add the previously built term
                new_terms.append(current_term)
            # Create a new term for this new author
            current_term = wp.Term(
                name=author.meta_value,
                slug=author.meta_value.lower().replace(' ', '-'),
                term_group=0,
                taxonomy='sd-author')

        # Add the post for the current term
        current_term.posts.append(author.post)

        # Remove the author
        manager.session.delete(author)

    # Add new terms
    manager.session.add_all(new_terms)


def convert_events(manager):
    cat = manager.session.query(wp.Term).filter_by(slug='events').first()
    if cat:
        # Get all posts that have the 'events' category
        condition = and_(
            wp.Post.terms.any(taxonomy='category'),
            wp.Post.terms.any(slug='events'))
        event_posts = manager.session.query(wp.Post).filter(condition)

        # Update the post type to 'sd-event'
        event_posts.update(
            {wp.Post.post_type: 'sd-event'},
            synchronize_session='fetch')

        # Remove the category term
        manager.session.delete(cat)


def convert_products(manager):
    # Update post type of products
    manager.session.query(wp.Post).filter_by(
        post_type='it_exchange_prod').update(
            {wp.Post.post_type: 'sd-product'},
            synchronize_session='fetch')

    # Update product category
    manager.session.query(wp.Term).filter_by(
        taxonomy='it_exchange_category').update(
            {wp.Term.taxonomy: 'sd-product-cat'})


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
    # manager.session.query(wp.Term).filter(
    #     not_(or_(*[wp.Term.taxonomy == pt for pt in desired_taxonomies]))).delete()


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

    # Convert authors
    convert_authors(manager)
    convert_events(manager)
    convert_products(manager)

    # Commit changes
    cleanup(manager)
    manager.session.commit()


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter

"""Tool to port original site to site under development"""
from sqlalchemy import or_, not_, exists
import wpalchemy.classes as wp

import sql
import converters


class ConverterFactory:
    def __init__(self, manager):
        self.manager = manager

    def create(self, converter):
        class_ = getattr(converters, converter)
        return class_(self.manager)

def process(manager):
    # Create a converter factory
    factory = ConverterFactory(manager)

    # Convert the database
    factory.create('AuthorsConverter').convert()
    factory.create('EventsConverter').convert()
    factory.create('ProductsConverter').convert()
    factory.create('MenuConverter').convert()
    factory.create('PagesConverter').convert()

    # Commit changes
    cleanup(manager)
    manager.session.commit()


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
    sql_taxonomies = " OR ".join(["wp_term_taxonomy.taxonomy = '{}'".format(tax) for tax in desired_taxonomies])
    manager.engine.execute(
        "DELETE wp_terms, wp_term_taxonomy, wp_termmeta FROM wp_terms "
        "INNER JOIN wp_term_taxonomy "
        "ON wp_terms.term_id = wp_term_taxonomy.term_id "
        "INNER JOIN wp_termmeta "
        "ON wp_terms.term_id = wp_termmeta.term_id "
        "WHERE NOT ({})".format(sql_taxonomies))

    # Remove orphans
    manager.session.query(wp.Post).filter(~exists().where(wp.Post.ID == wp.PostMeta.post_id)).delete(
        synchronize_session='fetch')
    # manager.session.query(wp.Term).filter(~exists().where(wp.Term.id == wp.TermMeta.term_id)).delete(
    #     synchronize_session='fetch')
    manager.session.query(wp.User).filter(~exists().where(wp.User.ID == wp.UserMeta.user_id)).delete(
        synchronize_session='fetch')

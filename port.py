"""Tool to port original site to site under development"""
from sqlalchemy import or_, not_, exists
import wpalchemy.classes as wp
import wpalchemy.tables as tables

import converters


class ConverterFactory:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def create(self, converter):
        class_ = getattr(converters, converter)
        return class_(self.source, self.target)


def process(source, target):
    # Initial sanitisation
    cleanup_orphans(source)

    # Create a converter factory
    factory = ConverterFactory(source, target)

    # Convert the database
    factory.create('AuthorsConverter').convert()
    factory.create('EventsConverter').convert()
    factory.create('ProductsConverter').convert()
    factory.create('MenuConverter').convert()
    factory.create('CategoriesConverter').convert()

    cleanup(source)
    copy(source, target)


def cleanup_orphans(source):
    # Remove orphaned meta rows
    source.session.query(wp.PostMeta).filter(
        wp.PostMeta.post_id.notin_(source.session.query(wp.Post.ID))).delete(
            synchronize_session='fetch')
    source.session.query(wp.TermMeta).filter(
        wp.TermMeta.term_id.notin_(source.session.query(
            wp.Term.id))).delete(
                synchronize_session='fetch')
    source.session.query(wp.UserMeta).filter(
        wp.UserMeta.user_id.notin_(source.session.query(wp.User.ID))).delete(
            synchronize_session='fetch')

    # Remove orphaned term relationships
    source.session.query(tables.term_relationships).filter(
        tables.term_relationships.c.object_id.notin_(
            source.session.query(wp.Post.ID))).delete(
                synchronize_session='fetch')


def cleanup(manager):
    # Ensure things are committed
    manager.session.commit()
    # Remove unwanted posts
    desired_post_types = [
        'post',
        'sd-event',
        'sd-product',
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

    # cleanup_orphans(manager)


def copy(source, target):
    # Ensure any pending session changes are flushed to tables
    source.session.commit()
    target.session.commit()
    # Identify tables of interest
    desired_tables = [
        tables.posts,
        tables.postmeta,
        tables.terms,
        tables.termmeta,
        tables.term_taxonomies,
        tables.term_relationships,
    ]
    for table in desired_tables:
        # Clear the target's current contents
        target.engine.execute(table.delete())
        # Copy the source's contents to the target
        for row in source.engine.execute(table.select()):
            target.engine.execute(table.insert(row))

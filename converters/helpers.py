"""Helper functions for manipulating wordpress classes"""
from typing import Sequence, Callable, Any

from sqlalchemy.orm.session import Session
import wpalchemy.classes as wp
from slugify import slugify


def get_element(sequence: Sequence, test: Callable[[Sequence], Any]):
    """Return the element in a sequence that passes the test

    Args:
        sequence (Sequence): Sequence to search
        test (Callable[[Sequence], Any]): Test to apply to elements

    Returns:
        Any: The first element of the sequence that passes the test
    """
    for item in sequence:
        if test(item):
            return item

    raise RuntimeError("No element found")


def get_meta(obj: wp.Base, key: str) -> str:
    """Return the value of the specified meta data

    Args:
        obj (Base): SQLAlchemy mapper class
        key (str): Meta key to identify the object with

    Returns:
        str: The meta_value for the matching meta data
    """
    return get_element(obj.meta, lambda x: x.meta_key == key).meta_value


def create_post_meta(session: Session, post_id: int, data: dict):
    create_meta(session, wp.PostMeta, 'post_id', post_id, data)


def create_meta(session: Session, class_type, id_column: str, id: int, data: dict):
    for key, value in data.items():
        # Create the post meta object
        session.add(class_type(
            **{id_column: id},
            meta_key=key,
            meta_value=value))


class Page:
    def __init__(self, manager, title, template=None):
        # Create the page
        self._page = create_post(
            manager,
            post_type="page",
            post_content='',
            post_excerpt='',
            post_title=title)
        # Set the template (if necessary)
        if template:
            manager.session.add(wp.PostMeta(
                post_id=self._page.ID,
                meta_key="_wp_page_template",
                meta_value=template))

    @property
    def object(self):
        return self._page


def kebabify(string):
    return slugify(string)


def create_post(manager, **kwargs):
    # Create the post (with handy defaults set)
    post = wp.Post(
        **kwargs,
        post_name=kebabify(kwargs['post_title']),
        guid='',
        post_mime_type='',
        comment_status="closed",
        ping_status="closed")
    manager.session.add(post)
    # Flush the post to get populate the ID
    manager.session.flush()
    # Update the guid with the post ID
    post.guid = "http://skindeepmag.com/?p={}".format(post.ID)
    return post


def create_acf_meta(manager, class_ref, object_id, value, acf_name, acf_key):
    # Determine class-dependent keyword arguments
    if class_ref == wp.PostMeta:
        kwargs = {'post_id': object_id}
    else:
        kwargs = {'term_id': object_id}

    # Add image metadata
    manager.session.add(class_ref(
        meta_key=acf_name,
        meta_value=value,
        **kwargs))
    # Add the ACF metadata
    manager.session.add(class_ref(
        meta_key="_{}".format(acf_name),
        meta_value=acf_key,
        **kwargs))

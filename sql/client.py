"""ORM for SQL connection"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import inflection
import logging

import wpalchemy.classes as wp


logger = logging.getLogger(__name__)
_CONNECTION_FORMAT = '{dialect}://{username}:{password}@{host}:{port}/{database}'


class SqlClient:
    def __init__(self, params, database):
        self.params = params
        self._database = database

        # Create the connection string
        connection_string = _CONNECTION_FORMAT.format(
            dialect='mysql+pymysql',
            username=params.username,
            password=params.password,
            host=params.host,
            port=params.port,
            database=database)
        # Create a connection
        self._engine = create_engine(connection_string, echo=True)
        # Create SQLAlchemy session objects
        self._session_class = sessionmaker(bind=self._engine)
        self._session = self._session_class()

    @property
    def engine(self):
        return self._engine

    @property
    def session(self):
        return self._session

    @property
    def database(self):
        return self._database

    @staticmethod
    def kebabify(string):
        return inflection.dasherize(inflection.underscore(string))

    def create_post(self, **kwargs):
        # Create the post (with handy defaults set)
        print(kwargs)
        post = wp.Post(
            **kwargs,
            post_name=self.kebabify(kwargs['post_title']),
            guid='',
            post_mime_type='',
            comment_status="closed",
            ping_status="closed")
        self.session.add(post)
        # Flush the post to get populate the ID
        self.session.flush()
        # Update the guid with the post ID
        post.guid = "http://skindeepmag.com/?p={}".format(post.ID)
        return post

"""ORM for SQL connection"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


_CONNECTION_FORMAT = '{dialect}://{username}:{password}@{host}:{port}/{database}'


class DbManager:
    def __init__(self, username, password):
        connection_string = _CONNECTION_FORMAT.format(
            dialect='mysql+pymysql',
            username=username,
            password=password,
            host='127.0.0.1',
            port=3306,
            database='wp')
        engine = create_engine(connection_string, echo=True)
        self._session_class = sessionmaker(bind=engine)
        self._session = self._session_class()

    @property
    def session(self):
        return self._session

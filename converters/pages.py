import logging

import wpalchemy.classes as wp
from sqlalchemy import or_

from converters.converter import Converter


logger = logging.getLogger(__name__)


class PagesConverter(Converter):
    def convert(self):
        # Delete unnecessary pages
        page_ids = [25, 27, 397, 398, 426, 428, 422, 295, 399, 2, 1858, 427]
        self.source.session.query(wp.Post).filter(
            or_(*[wp.Post.ID == id for id in page_ids])).delete(
                synchronize_session='fetch')

import wpalchemy.classes as wp
from sqlalchemy import and_

from converters.converter import Converter


class EventsConverter(Converter):
    def convert(self):
        cat = self.session.query(wp.Term).filter_by(slug='events').first()
        if cat:
            # Get all posts that have the 'events' category
            condition = and_(
                wp.Post.terms.any(taxonomy='category'),
                wp.Post.terms.any(slug='events'))
            event_posts = self.session.query(wp.Post).filter(condition)

            # Update the post type to 'sd-event'
            event_posts.update(
                {wp.Post.post_type: 'sd-event'},
                synchronize_session='fetch')

            # Remove the category term
            self.session.delete(cat)

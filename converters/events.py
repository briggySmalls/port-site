import wpalchemy.classes as wp
from sqlalchemy import and_

from converters.converter import Converter


class EventsConverter(Converter):
    def convert(self):
        # Get the events category
        events_category = self.source.session.query(wp.Term).filter_by(
            slug='events').one()

        # Get all posts that have the 'events' category
        condition = and_(
            wp.Post.terms.any(taxonomy='category'),
            wp.Post.terms.any(slug=events_category.slug))
        event_posts = self.source.session.query(wp.Post).filter(condition)

        # Update each post type to 'sd-event'
        event_posts.update(
            {wp.Post.post_type: 'sd-event'},
            synchronize_session='fetch')

        # Remove the category term
        self.source.session.delete(events_category)

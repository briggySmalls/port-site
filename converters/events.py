import wpalchemy.classes as wp
from sqlalchemy import and_

from converters.converter import Converter
from converters.helpers import create_post_meta


# Facebook events to attach to event posts
FACEBOOK_EVENTS = {
    2717: 408977832915985,
    2838: 408977832915985,
    2480: 1991989291022482,
    2840: 1991989291022482,
    2059: 1519186918200845,
    2877: 1519186918200845,
    1723: 1245388985568706,
    2878: 1245388985568706,
    1998: 219818301849805,
    2879: 219818301849805,
    1670: 742875849213338,
    2880: 742875849213338,
    1625: 1241648545915838,
    2881: 1241648545915838,
    1523: 693827704114924,
    2882: 693827704114924,
    1472: 693827704114924,
    2883: 693827704114924,
    1371: 323297304705639,
    2884: 323297304705639,
    1287: 323297304705639,
    2885: 323297304705639,
    1065: 302739840069635,
    2886: 302739840069635,
    832: 582355721933792,
    2887: 582355721933792,
    2890: 457764397724406,
    2891: 582355721933792,
}


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

        for event in event_posts:
            if event.ID in FACEBOOK_EVENTS:
                create_post_meta(
                    self.source.session,
                    event.ID,
                    {'sd_event_facebook_event': FACEBOOK_EVENTS[event.ID]})

        # Remove the category term
        self.source.session.delete(events_category)

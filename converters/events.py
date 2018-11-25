import wpalchemy.classes as wp
from sqlalchemy import and_

from converters.converter import Converter
from converters.helpers import create_post_meta


# Facebook events to attach to event posts
_EVENT_DETAILS = {
    2717: {'facebook_id': 408977832915985},
    2838: {'facebook_id': 408977832915985},
    2480: {'facebook_id': 1991989291022482},
    2840: {'facebook_id': 1991989291022482},
    2059: {'facebook_id': 1519186918200845},
    2877: {'facebook_id': 1519186918200845},
    1723: {'facebook_id': 1245388985568706},
    2878: {'facebook_id': 1245388985568706},
    1998: {'facebook_id': 219818301849805},
    2879: {'facebook_id': 219818301849805},
    1670: {'facebook_id': 742875849213338},
    2880: {'facebook_id': 742875849213338},
    1625: {'facebook_id': 1241648545915838},
    2881: {'facebook_id': 1241648545915838},
    1523: {'facebook_id': 693827704114924},
    2882: {'facebook_id': 693827704114924},
    1472: {'facebook_id': 693827704114924},
    2883: {'facebook_id': 693827704114924},
    1371: {'facebook_id': 323297304705639},
    2884: {'facebook_id': 323297304705639},
    1287: {'facebook_id': 323297304705639},
    2885: {'facebook_id': 323297304705639},
    1065: {'facebook_id': 302739840069635},
    2886: {'facebook_id': 302739840069635},
    832: {'facebook_id': 582355721933792},
    2887: {'facebook_id': 582355721933792},
    2890: {'facebook_id': 457764397724406},
    2891: {'facebook_id': 582355721933792},
    2858: {'facebook_id': 2282918201936712},
    354: {'start_time': '2015-07-10 00:00:00'},
    629: {'start_time': '2015-12-02 00:00:00'},
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
            details = _EVENT_DETAILS[event.ID]
            if 'facebook_id' in details:
                # Event has a corresponding facebook event
                create_post_meta(
                    self.source.session,
                    event.ID,
                    {'sd_event_facebook_event': details['facebook_id']})
            else:
                # We need to set the date/time ourselves
                create_post_meta(
                    self.source.session,
                    {'sd_event_details_start_time': details['start_time']})

        # Remove the category term
        self.source.session.delete(events_category)

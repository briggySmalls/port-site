import wpalchemy.classes as wp

from converters.converter import Converter

POSTS_PER_PAGE = 12


class OptionsConverter(Converter):
    def convert(self):
        # Set to show a static front page
        self.target.session.query(wp.Option).filter_by(
            option_name="show_on_front").update(
                {wp.Option.option_value: "page"})

        # Update the number of posts-per-page
        self.target.session.query(wp.Option).filter_by(
            option_name="posts_per_page").update(
                {wp.Option.option_value: POSTS_PER_PAGE})

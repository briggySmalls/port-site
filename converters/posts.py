import wpalchemy.classes as wp
from dataclasses import dataclass

from converters.converter import Converter
from converters.helpers import create_acf_meta, find_or_create_term

POSTS_PER_PAGE = 12

VIDEO_POSTS = {
    2669: "https://vimeo.com/271414687",
    2596: "https://vimeo.com/262359596",
    2538: "https://vimeo.com/259006486",
    2461: "https://vimeo.com/250450297",
    2376: "https://vimeo.com/241841143",
    2561: "https://vimeo.com/260694457",
    2674: "https://www.youtube.com/watch?v=oiCakt5mCFI",
}

MAGAZINE_POSTS = {
    2614: 2341,
    2606: 2341,
    2578: 2341,
}


@dataclass
class AcfField:
    name: str
    key: str


ACF_MAGAZINE = AcfField(name="sd_article_magazine", key="field_5b9f09181e0c1")
ACF_VIDEO = AcfField(name="sd_featured_video", key="field_5b21a633286bf")


class PostsConverter(Converter):
    def convert(self):
        self.set_videos()
        self.set_magazines()

    def set_videos(self):
        # Ensure video term exists
        video_term = find_or_create_term(
            self.source,
            taxonomy="post_format",
            name="post-format-video",
            slug="post-format-video")

        for post_id, embed_url in VIDEO_POSTS.items():
            # Set the featured video
            create_acf_meta(
                self.source, wp.PostMeta, post_id,
                embed_url, ACF_VIDEO.name, ACF_VIDEO.key)
            # Set the format (add term)
            post = self.source.session.query(wp.Post).filter_by(ID=post_id).one()
            post.terms.append(video_term)

    def set_magazines(self):
        for post_id, magazine_id in MAGAZINE_POSTS.items():
            create_acf_meta(
                self.source, wp.PostMeta, post_id,
                magazine_id, ACF_MAGAZINE.name, ACF_MAGAZINE.key)
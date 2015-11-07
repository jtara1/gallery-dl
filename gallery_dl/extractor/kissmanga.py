# -*- coding: utf-8 -*-

# Copyright 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract manga pages from http://kissmanga.com/"""

from .common import Extractor, Message
from .. import text, cloudflare
import os.path
import re

info = {
    "category": "kissmanga",
    "extractor": "KissmangaExtractor",
    "directory": ["{category}", "{manga}", "c{chapter:>03}{chapter-minor} - {title}"],
    "filename": "{manga}_c{chapter:>03}{chapter-minor}_{page:>03}.{extension}",
    "pattern": [
        r"(?:https?://)?(?:www\.)?kissmanga\.com/Manga/.+/.+\?id=\d+",
    ],
}

class KissmangaExtractor(Extractor):

    def __init__(self, match):
        Extractor.__init__(self)
        self.url = match.group(0)

    def items(self):
        cloudflare.bypass_ddos_protection(self.session, "http://kissmanga.com")
        page = self.request(self.url).text
        data = self.get_job_metadata(page)
        imgs = self.get_image_urls(page)
        data["count"] = len(imgs)
        yield Message.Version, 1
        yield Message.Directory, data
        for num, url in enumerate(imgs, 1):
            filename = text.unquote(text.filename_from_url(url))
            name, ext = os.path.splitext(filename)
            data["page"] = num
            data["name"] = name
            data["extension"] = ext[1:]
            yield Message.Url, url, data

    @staticmethod
    def get_job_metadata(page):
        """Collect metadata for extractor-job"""
        manga, pos = text.extract(page, "Read manga\n", "\n")
        cinfo, pos = text.extract(page, "", "\n", pos)
        match = re.match(
            r"(?:Vol.0*(\d+) )?(?:Ch.)?0*(\d+)(?:\.0*(\d+))?(?:: (.+))?", cinfo)
        chminor = match.group(3)
        return {
            "category": info["category"],
            "manga": manga,
            "volume": match.group(1) or "",
            "chapter": match.group(2),
            "chapter-minor": "."+chminor if chminor else "",
            "title": match.group(4) or "",
            "lang": "en",
            "language": "English",
        }

    @staticmethod
    def get_image_urls(page):
        """Extract list of all image-urls for a manga chapter"""
        pos = 0
        images = []
        while True:
            url, pos = text.extract(page, 'lstImages.push("', '"', pos)
            if not url:
                return images
            images.append(url)

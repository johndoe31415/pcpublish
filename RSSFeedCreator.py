#	pcpublish - Authoring RSS feed and custom MP3s for a podcast
#	Copyright (C) 2022-2022 Johannes Bauer
#
#	This file is part of pcpublish.
#
#	pcpublish is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pcpublish is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pcpublish; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import xml.dom.minidom
import json
import sys
from Tools import TimeTools

class RSSFeedCreator():
	_NS = {
		"atom":			"http://www.w3.org/2005/Atom",
		"itunes":		"http://www.itunes.com/dtds/podcast-1.0.dtd",
		"googleplay":	"http://www.google.com/schemas/play-podcasts/1.0",
	}
	def __init__(self, meta, show_episodes_without_mp3 = False):
		self._data = meta
		self._show_episodes_without_mp3 = show_episodes_without_mp3

	@property
	def authors(self):
		author_join = self._data["meta"].get("author_join", ", ")
		return author_join.join(self._data["meta"]["author"])

	def _add_node(self, parent, name, text = None, ns = None):
		doc = parent.ownerDocument
		if ns is None:
			node = parent.appendChild(doc.createElement(name))
		else:
			uri = self._NS[ns]
			node = parent.appendChild(doc.createElementNS(uri, f"{ns}:{name}"))
		if text is not None:
			node.appendChild(doc.createTextNode(text))
		return node

	def _add_episode(self, channel, episode):
		if "guid" not in episode:
			print(f"Warning: episode \"{episode['title']}\" does not have a GUID set, not including it in XML. Run pcpublish with '-a' to add one.", file = sys.stderr)
			return
		if (not self._show_episodes_without_mp3) and (not episode["have_audiofile"]):
			# Audio file not present
			return
		item = self._add_node(channel, "item")
		self._add_node(item, "title", episode["title"])
		self._add_node(item, "description", episode["description"])
		self._add_node(item, "title", episode["title"], ns = "itunes")
		self._add_node(item, "subtitle", episode["description_short"], ns = "itunes")
		self._add_node(item, "author", self.authors, ns = "itunes")
		self._add_node(item, "summary", episode["description"], ns = "itunes")
		self._add_node(item, "pubDate", TimeTools.format_rfc822(episode["pubdate"]))
		enclosure = self._add_node(item, "enclosure")
		enclosure.setAttribute("url", episode["remote_uri"]["episode"])
		enclosure.setAttribute("type", "audio/mpeg")
		enclosure.setAttribute("length", str(episode["info"]["format"]["size"]))
		self._add_node(item, "duration", episode["ext_info"]["duration"])
		guid = self._add_node(item, "guid", episode["guid"])
		guid.setAttribute("isPermaLink", "false")

	def make(self):
		doc = xml.dom.minidom.Document()

		rss = doc.appendChild(doc.createElement("rss"))
		rss.setAttribute("version", "2.0")
		for (nsname, nsuri) in self._NS.items():
			rss.setAttribute(f"xmlns:{nsname}", nsuri)

		channel = rss.appendChild(doc.createElement("channel"))

		self._add_node(channel, "title", self._data["meta"]["title"])
		link = self._add_node(channel, "link", ns = "atom")
		link.setAttribute("href", self._data["meta"]["remote_uri"]["rss_feed"])
		link.setAttribute("rel", "self")
		link.setAttribute("type", "application/rss+xml")

		owner = self._add_node(channel, "owner", ns = "itunes")
		self._add_node(owner, "name", self.authors, ns = "itunes")
		self._add_node(owner, "email", self._data["meta"]["email"], ns = "itunes")
		self._add_node(channel, "author", self.authors, ns = "itunes")
		category = self._add_node(channel, "category", ns = "itunes")
		category.setAttribute("text", self._data["meta"]["category"])
		self._add_node(channel, "explicit", "no", ns = "itunes")
		self._add_node(channel, "keywords", ",".join(self._data["meta"]["keywords"]), ns = "itunes")
		self._add_node(channel, "subtitle", self._data["meta"]["description"], ns = "itunes")
		self._add_node(channel, "type", "episodic", ns = "itunes")
		self._add_node(channel, "summary", self._data["meta"]["description"], ns = "itunes")

		category = self._add_node(channel, "category", ns = "googleplay")
		category.setAttribute("text", self._data["meta"]["category"])

		self._add_node(channel, "description", self._data["meta"]["description"])
		img = self._add_node(channel, "image", ns = "itunes")
		img.setAttribute("href", self._data["meta"]["remote_uri"]["cover_image"])

		self._add_node(channel, "language", self._data["meta"]["locale"]["rss"])
		self._add_node(channel, "link", self._data["meta"]["remote_uri"]["website"])
		for episode in self._data["episodes"]:
			self._add_episode(channel, episode)

		return doc

	def write_xml(self, filename):
		xml = self.make()
		with open(filename, "w") as f:
			xml.writexml(f, encoding = "utf-8")

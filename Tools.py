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

import json
import subprocess
import re
import pytz
import datetime
import email.utils

class MP3Tools():
	@classmethod
	def get_info(cls, filename):
		cmd = [ "ffprobe", "-loglevel", "0", "-print_format", "json", "-show_format", "-show_streams", filename ]
		return json.loads(subprocess.check_output(cmd))

	@classmethod
	def strip_tags(cls, filename):
		cmd = [ "eyeD3", "--remove-all", filename ]
		subprocess.check_call(cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

	@classmethod
	def add_tag(cls, filename, author = None, album_name = None, track_title = None, track_number = None, genre = None, year = None, comment = None, uri = None, cover_image = None, comment_language = "eng"):
		cmd = [ "eyeD3" ]
		if author is not None:
			cmd += [ "-a", author ]
		if album_name is not None:
			cmd += [ "-A", album_name ]
		if track_title is not None:
			cmd += [ "-t", track_title ]
		if track_number is not None:
			cmd += [ "-n", str(track_number) ]
		if genre is not None:
			cmd += [ "-G", genre ]
		if year is not None:
			cmd += [ "-Y", str(year) ]
		if comment is not None:
			cmd += [ "--add-comment", f"{comment}:comment:{comment_language}" ]
		if uri is not None:
			cmd += [ "--url-frame", f"WOAS:{uri}" ]
		if cover_image is not None:
			cmd += [ "--add-image", f"{cover_image}:FRONT_COVER" ]
		cmd += [ filename ]
		subprocess.check_call(cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

class TimeTools():
	_TS_TIMEZONE = re.compile("(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(\s+(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\s+(?P<timezone>.+))?)?")

	@classmethod
	def format_hms(cls, secs_total):
		secs_total = round(secs_total)
		h = secs_total // 3600
		m = secs_total % 3600 // 60
		s = secs_total % 3600 % 60
		if h == 0:
			return f"{m}:{s:02d}"
		else:
			return f"{h}:{m:02d}:{s:02d}"

	@classmethod
	def parse(cls, text):
		result = cls._TS_TIMEZONE.fullmatch(text)
		if result is None:
			raise ValueError(f"Cannot parse as datetime: {text}")

		result = result.groupdict()
		if result["timezone"] is not None:
			# day time tz
			ts = datetime.datetime(int(result["year"]), int(result["month"]), int(result["day"]), int(result["hour"]), int(result["minute"]), int(result["second"]))
			tz = pytz.timezone(result["timezone"])
			return tz.localize(ts)
		elif result["hour"] is not None:
			# day time
			ts = datetime.datetime(int(result["year"]), int(result["month"]), int(result["day"]), int(result["hour"]), int(result["minute"]), int(result["second"]))
			return pytz.UTC.localize(ts)
		else:
			# day
			ts = datetime.datetime(int(result["year"]), int(result["month"]), int(result["day"]))
			return pytz.UTC.localize(ts)

	@classmethod
	def format_rfc822(cls, dt):
		return email.utils.format_datetime(dt)

class TextTools():
	_REPLACEMENTS = (
		(" ", "_"),
		("ä", "ae"),
		("ö", "oe"),
		("ü", "ue"),
		("Ä", "Ae"),
		("Ö", "Oe"),
		("Ü", "Ue"),
		("ß", "ss"),
	)
	_REMAINING_REGEX = re.compile("[^-_a-zA-Z]")

	@classmethod
	def make_filename(cls, text):
		filename = text
		for (src, dst) in cls._REPLACEMENTS:
			filename = filename.replace(src, dst)
		filename = cls._REMAINING_REGEX.sub("", filename)
		return filename

if __name__ == "__main__":
	print(TimeTools.parse("2022-06-09 12:34:56 Europe/Berlin"))
	print(TimeTools.parse("2022-06-09 12:34:56"))
	print(TimeTools.parse("2022-06-09"))
	print(TimeTools.format_rfc822(TimeTools.parse("2022-06-09 12:34:56 Europe/Berlin")))

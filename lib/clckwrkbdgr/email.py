from __future__ import absolute_import
import os, re
import email, email.message, email.header
try:
	email.message.Charset
except AttributeError: # pragma: no cover
	email.message.Charset = email.charset.Charset
import logging
Log = logging.getLogger('email')
import six

CHARSET_PATTERN = re.compile(r'^\w+/\w+;\s*charset="?(.*)"?\s*$')

class BinaryPayload:
	def __init__(self, content_type, data, filename=None):
		self.content_type = content_type
		self.data = data
		self.filename = filename
	def __repr__(self): # pragma: no cover
		return 'BinaryPayload({0}, <{1} bytes...>)'.format(repr(self.content_type), len(self.data))
	def __str__(self):
		lines = ['Content-Type: {0}'.format(self.content_type)]
		if self.filename:
			lines.append('Filename: {0}'.format(self.filename))
		lines.append(repr(self.data))
		return '\n'.join(lines)

class Message(object):
	def __init__(self, data, unique_filenames=False):
		if isinstance(data, email.message.EmailMessage):
			self.data = data
		elif isinstance(data, six.string_types):
			self.data = email.message_from_string(data)
		elif isinstance(data, six.binary_type): # pragma: no cover -- py2
			self.data = email.message_from_bytes(data)
		else:
			raise ValueError("Message should be either MailMessage, or str, or bytes, but not {0}".format(type(data)))
		self.unique_filenames = unique_filenames
		self.cids = {}
	def get_subject(self):
		return self.get_header('Subject').replace('\r', '').replace('\n', '')
	def get_header(self, header_name):
		header = self.data[header_name]
		result = ''
		for part, encoding in email.header.decode_header(header):
			result += self._decode_string(part, encoding)
		return result
	def get_full_text(self):
		return ''.join(map(str, self._decode_payloads(self.data)))
	def get_payloads(self):
		return self._decode_payloads(self.data)

	def _guess_payload_charset(self, payload):
		charset = payload.get_charset()
		if payload.get_charset() is not None: # pragma: no cover -- TODO need real case
			return charset
		charset = CHARSET_PATTERN.match(payload['Content-Type'] or '')
		if charset:
			charset = charset.group(1)
			payload.set_charset(charset)
			Log.debug("Attachment guessed charset: {0}".format(charset))
		return charset
	def _guess_content_id(self, payload):
		content_id = payload['Content-ID']
		if not content_id: # pragma: no cover -- TODO need real case
			# Possibly a proper attachment.
			return str(time.time())
		content_id = content_id.replace('<', '').replace('>', '')
		if not re.match(r'[a-z0-9]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}', content_id):
			content_id = content_id.split('@', 1)[0]
		return content_id
	def _guess_filename(self, payload): # pragma: no cover -- TODO need real case
		img_filename = payload['Content-Description']
		if img_filename: # pragma: no cover -- TODO need real case
			Log.debug("Taken from Content-Description header.")
			return img_filename
		content_disposition = payload['Content-Disposition']
		if content_disposition:
			img_filename = re.search(r'.*filename="([^"]+)"', content_disposition)
			if img_filename and img_filename.group(1) != 'null':
				Log.debug("Found 'filename' in Content-Disposition header.")
				return img_filename.group(1)
		content_type = payload['Content-Type']
		img_filename = re.search(r'.*name="([^"]+)"', content_type)
		if img_filename and img_filename.group(1) != 'null':
			Log.debug("Found 'name' in Content-Type header.")
			return img_filename.group(1)
		content_type = content_type.split(';', 1)[0]
		extension = '.' + content_type.split('/')[-1]
		if not content_type.endswith(extension):
			content_type += extension
		Log.debug("Using Content-ID.")
		return content_type
	def _decode_string(self, data, encoding=None):
		if isinstance(data, six.string_types) and not hasattr(data, 'decode'): # pragma: no cover -- py2
			return data
		if isinstance(encoding, email.message.Charset):
			encoding = encoding.input_charset
			if '"' in encoding: # pragma: no cover -- TODO need real case.
				encoding = encoding.split('"', 1)[0]
		if encoding == 'unknown-8bit' or encoding is None:
			try:
				return data.decode('utf-8')
			except: # pragma: no cover
				pass
		return data.decode(encoding if encoding else 'ascii', 'replace')
	def _decode_single_payload(self, data):
		if data.get_content_type().startswith('text/'):
			self._guess_payload_charset(data)
			content_transfer_encoding = data['Content-Transfer-Encoding']
			Log.debug("Content transfer encoding: {0}".format(content_transfer_encoding))
			body = data.get_payload(decode=(content_transfer_encoding in ('base64', 'quoted-printable')))
			body = self._decode_string(body, data.get_charset())
			if data.get_content_type() == 'text/html':
				import bs4
				return bs4.BeautifulSoup(body, "html.parser")
			return body
		elif data.get_content_type().startswith('image/'):
			content_id = self._guess_content_id(data)
			img_filename = self._guess_filename(data)
			if self.unique_filenames:
				name, ext = os.path.splitext(img_filename)
				unique_id = str(content_id)
				if not unique_id.startswith('.'):
					unique_id = '.' + unique_id
				img_filename = name + unique_id + ext
			self.cids[content_id] = img_filename
			return BinaryPayload(
					data.get_content_type(),
					data.get_payload(decode=True),
					filename=img_filename,
					)
		elif data.get_content_type() in ('multipart/alternative', 'multipart/related'): # pragma: no cover -- TODO need real case
			return self._decode_payloads(data)
		elif data.get_content_type() == 'message/rfc822': # pragma: no cover -- TODO need real case
			return Message(data) # Another mail.
		else: # pragma: no cover
			return BinaryPayload(
					data.get_content_type(),
					data.get_payload(decode=True),
					filename=self._guess_filename(data),
					)
	def _decode_payloads(self, data):
		if not data.is_multipart():
			body = self._decode_single_payload(data)
			return [body]
		else:
			total = []
			for part in data.get_payload():
				try:
					part = str(part)
				except KeyError as e: # pragma: no cover -- TODO need real case.
					if str(e) == "'content-transfer-encoding'":
						part['Content-Transfer-Encoding'] = 'quoted-printable'
						part = str(part)
					else:
						raise
				part = email.message_from_string(str(part))
				total += self._decode_payloads(part)
			return total

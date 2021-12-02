from __future__ import absolute_import
import email, email.message
import six

class Message(object):
	def __init__(self, data):
		if isinstance(data, email.message.EmailMessage):
			self.data = data
		elif isinstance(data, six.string_types):
			self.data = email.message_from_string(data)
		elif isinstance(data, six.binary_type): # pragma: no cover -- py2
			self.data = email.message_from_bytes(data)
		else:
			raise ValueError("Message should be either MailMessage, or str, or bytes, but not {0}".format(type(data)))
	def get_header(self, header_name):
		header = self.data[header_name]
		result = ''
		for part, encoding in email.header.decode_header(header):
			if isinstance(part, six.string_types):
				result += part
			else: # pragma: no cover -- TODO need real case.
				result += part.decode(encoding if encoding else 'ascii', 'replace')
		return result
	def get_full_text(self):
		return self._decode_payloads(self.data)
	def _decode_payloads(self, data):
		if not data.is_multipart():
			body = data.get_payload(decode=True)
			try:
				if not isinstance(body, six.string_types): # pragma: no cover -- py2
					charset = data.get_charset()
					body = body.decode(charset if charset else 'utf-8')
			except: # pragma: no cover
				pass
			return str(body)
		else:
			total = ''
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

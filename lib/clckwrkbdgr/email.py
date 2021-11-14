import email

class Message(object): # pragma: no cover -- TODO
	def __init__(self, data):
		self.data = email.message_from_bytes(data)
	def get_header(self, header_name):
		header = self.data[header_name]
		result = ''
		for part, encoding in email.header.decode_header(header):
			if isinstance(part, str):
				result += part
			else:
				try:
					result += part.decode(encoding if encoding else 'ascii')
				except:
					result += repr(part)
		return result
	def get_full_text(self):
		return self._decode_payloads(self.data)
	def _decode_payloads(self, data):
		if not data.is_multipart():
			body = data.get_payload(decode=True)
			try:
				if isinstance(body, bytes):
					charset = data.get_charset()
					body = body.decode(charset if charset else 'utf-8')
			except:
				pass
			return str(body)
		else:
			total = ''
			for part in data.get_payload():
				try:
					part = str(part)
				except KeyError as e:
					if str(e) == "'content-transfer-encoding'":
						part['Content-Transfer-Encoding'] = 'quoted-printable'
						part = str(part)
					else:
						raise
				part = email.message_from_string(str(part))
				total += self._decode_payloads(part)
			return total

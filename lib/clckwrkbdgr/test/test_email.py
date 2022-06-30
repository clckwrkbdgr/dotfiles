# -*- coding: utf-8 -*-
from __future__ import absolute_import
from clckwrkbdgr import unittest
import clckwrkbdgr.email as E
import email, email.message, email.mime, email.mime.base, email.mime.text, email.mime.multipart, email.mime.application
import six
try:
	email.message.EmailMessage
except AttributeError: # pragma: no cover
	email.message.EmailMessage = email.message.Message

class TestEmail(unittest.TestCase):
	def _create(self,
			subject='Hello world!',
			plain_body='hello world\n',
			html_body='<p>hello world</p>\n',
			multipart=False,
			):
		if multipart:
			msg = email.mime.multipart.MIMEMultipart()
			msg.attach(email.mime.text.MIMEText(plain_body, 'plain'))
			msg.attach(email.mime.text.MIMEText(html_body, 'html'))
		else:
			msg = email.message.EmailMessage()
			if six.PY2: # pragma: no cover
				msg.set_payload(plain_body)
			else: # pragma: no cover
				msg.set_content(plain_body)
		msg['Subject'] = subject
		msg['From'] = 'JC Denton'
		msg['To'] = 'Paul Denton'
		return msg
	def _attach(self, content_type, data, content_id=None, filename=None):
		main_type, subtype = content_type.split('/')
		attachment = email.mime.base.MIMEBase(main_type, subtype)
		attachment.set_payload(data)
		if content_id:
			attachment['Content-ID'] = content_id
		if filename:
			attachment.add_header('Content-Disposition', 'attachment', filename=filename)
		return attachment
	def should_construct_email_from_bytes(self):
		msg = self._create()
		if six.PY2: # pragma: no cover
			msg = msg.as_string()
		else: # pragma: no cover
			msg = msg.as_bytes()
		msg = E.Message(msg)
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		self.assertEqual(msg.get_full_text(), 'hello world\n')
	def should_construct_email_from_string(self):
		msg = E.Message(self._create().as_string())
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		self.assertEqual(msg.get_full_text(), 'hello world\n')
	def should_construct_email_from_object(self):
		msg = E.Message(self._create())
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		self.assertEqual(msg.get_full_text(), 'hello world\n')
	def should_not_construct_email_from_anything_else(self):
		with self.assertRaises(ValueError):
			msg = E.Message(dict())
	def should_decode_headers(self):
		subject = u'Привет Мир!'
		header = subject
		if six.PY2: # pragma: no cover
			header = email.header.Header(subject, 'utf-8')
		msg = E.Message(self._create(
			subject=header,
			))
		self.assertEqual(msg.get_subject(), subject)
		self.assertEqual(msg.get_full_text(), 'hello world\n')
	def should_parse_multipart_message(self):
		msg = E.Message(self._create(
			multipart=True,
			).as_string())
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		self.assertEqual(msg.get_full_text(), 'hello world\n<p>hello world</p>\n')
	def should_parse_message_with_binary_attachment(self):
		msg = self._create(
			multipart=True,
			)
		msg.attach(self._attach('image/jpeg', 'data', content_id='666', filename='attach.jpg'))
		msg = E.Message(msg.as_string())
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		payloads = msg.get_payloads()
		self.assertEqual(len(payloads), 3)
		self.assertEqual(payloads[0], 'hello world\n')
		self.assertEqual(str(payloads[1]), '<p>hello world</p>\n')
		self.assertTrue(isinstance(payloads[2], E.BinaryPayload))
		self.assertEqual(msg.get_full_text(), 'hello world\n<p>hello world</p>\nContent-Type: image/jpeg\nFilename: attach.jpg\n' + repr(b'data'))
	def should_store_ids_for_images(self):
		msg = self._create(
			multipart=True,
			)
		msg.attach(self._attach('image/jpeg', 'data', content_id='666', filename='attach.jpg'))
		msg = E.Message(msg.as_string(), unique_filenames=True)
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		payloads = msg.get_payloads()
		self.assertEqual(payloads[2].filename, 'attach.666.jpg')
		self.assertEqual(msg.cids, {'666':'attach.666.jpg'})

class TestParserIssues(unittest.TestCase):
	def should_try_to_autoguess_unknown_8bit_encoding(self):
		data = b'To: user@example.com\r\nSubject: \xd0\xbf\xd1\x80\xd0\xbe\xd0\xb5\xd0\xba\xd1\x82\r\nContent-type:text/html;charset=UTF-8\r\nFrom: <other@example.com> \r\n' + b'\r\n\xd0\xbf\xd1\x80\xd0\xbe\xd0\xb5\xd0\xba\xd1\x82\r\n'
		msg = E.Message(data)
		self.assertEqual(msg.get_header('Subject'), u'проект')
		self.assertEqual(msg.get_full_text(), 'проект\r\n')

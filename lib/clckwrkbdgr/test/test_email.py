# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.email as E
import email, email.message, email.mime, email.mime.text, email.mime.multipart
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
		subject = 'Привет Мир!'
		msg = E.Message(self._create(
			subject=subject,
			))
		self.assertEqual(msg.get_header('Subject'), subject)
		self.assertEqual(msg.get_full_text(), 'hello world\n')
	def should_parse_multipart_message(self):
		msg = E.Message(self._create(
			multipart=True,
			).as_string())
		self.assertEqual(msg.get_header('Subject'), 'Hello world!')
		self.assertEqual(msg.get_full_text(), 'hello world\n<p>hello world</p>\n')

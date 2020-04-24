# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from bs4 import BeautifulSoup
from frappe.utils import set_request
from frappe.website.render import render


class TestWebTemplate(unittest.TestCase):
	def test_render_web_template_with_values(self):
		doc = frappe.get_doc("Web Template", "Hero with Right Image")
		values = {
			"title": "Test Hero",
			"subtitle": "Test subtitle content",
			"primary_action": "/test",
			"primary_action_label": "Test Button",
		}
		html = doc.render(values)

		soup = BeautifulSoup(html, "html.parser")
		heading = soup.find("h2")
		self.assertTrue("Test Hero" in heading.text)

		subtitle = soup.find("p")
		self.assertTrue("Test subtitle content" in subtitle.text)

		button = soup.find("a")
		self.assertTrue("Test Button" in button.text)
		self.assertTrue("/test" == button.attrs["href"])

	def test_web_page_with_page_builder(self):
		if not frappe.db.exists("Web Page", "test-page"):
			frappe.get_doc(
				{
					"doctype": "Web Page",
					"title": "test-page",
					"name": "test-page",
					"published": 1,
					"route": "testpage",
					"content_type": "Page Builder",
					"page_blocks": [
						{
							"web_template": "Section with Image",
							"web_template_values": frappe.as_json(
								{"title": "Test Title", "subtitle": "test lorem ipsum"}
							),
						},
						{
							"web_template": "Section with Cards",
							"web_template_values": frappe.as_json(
								{
									"title": "Test Title",
									"subtitle": "test lorem ipsum",
									"card_size": "Medium",
									"card_1_title": "Card 1 Title",
									"card_1_content": "Card 1 Content",
									"card_1_url": "/card1url",
									"card_2_title": "Card 2 Title",
									"card_2_content": "Card 2 Content",
									"card_2_url": "/card2url",
									"card_3_title": "Card 3 Title",
									"card_3_content": "Card 3 Content",
									"card_3_url": "/card3url",
								}
							),
						},
					],
				}
			).insert()

		set_request(method="GET", path="testpage")
		response = render()

		self.assertEquals(response.status_code, 200)

		html = frappe.safe_decode(response.get_data())

		soup = BeautifulSoup(html, "html.parser")
		sections = soup.find("main").find_all("section")

		self.assertEqual(len(sections), 2)
		self.assertEqual(sections[0].find("h2").text, "Test Title")
		self.assertEqual(sections[0].find("p").text, "test lorem ipsum")
		self.assertEqual(len(sections[1].find_all("a")), 3)

		frappe.db.delete_doc("Web Page", "test-page")

	def test_tailwind_styles_in_developer_mode(self):
		self.create_tailwind_theme()

		set_request(method="GET", path="testpage")
		response = render()
		self.assertEquals(response.status_code, 200)
		html = frappe.safe_decode(response.get_data())

		soup = BeautifulSoup(html, "html.parser")
		stylesheet = soup.select_one('link[rel="stylesheet"]')

		self.assertEqual(stylesheet.attrs['href'], '/assets/css/tailwind.css')

		self.delete_tailwind_theme()

	def test_tailwind_styles_in_production(self):
		self.create_tailwind_theme()

		frappe.conf.developer_mode = 0

		set_request(method="GET", path="testpage")
		response = render()
		self.assertEquals(response.status_code, 200)
		html = frappe.safe_decode(response.get_data())

		soup = BeautifulSoup(html, "html.parser")
		style = soup.select_one("style[data-tailwind]")

		self.assertTrue(style)
		self.assertTrue('.py-20' in style.text)
		self.assertTrue('.text-gray-800' in style.text)

		self.delete_tailwind_theme()

	def create_tailwind_theme(self):
		theme = frappe.get_doc({
			'doctype': 'Website Theme',
			'theme': 'Tailwind',
			'based_on': 'Tailwind'
		}).insert()
		theme.set_as_default()

	def delete_tailwind_theme(self):
		frappe.get_doc('Website Theme', 'Standard').set_as_default()
		frappe.delete_doc('Website Theme', 'Tailwind')

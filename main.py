#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import logging
import cgi

from google.appengine.ext import webapp, db
from google.appengine.api import users
from google.appengine.ext.webapp import util, template

import helper

template_dir = os.path.join(os.path.dirname(__file__), 'templates/')

class Tab(db.Model):
	"""Models a saved tab"""
	author = db.UserProperty()
	tab_content = db.StringProperty(multiline=True)
	
	name = db.StringProperty()
	description = db.StringProperty(multiline=True)
	instrument = db.StringProperty()
	tuning = db.StringProperty()
	
	likes = db.IntegerProperty()
	
	dateCreated = db.DateTimeProperty(auto_now_add=True)
	dateModified = db.DateTimeProperty(auto_now=True)

class MainHandler(webapp.RequestHandler):
    def get(self):
		user = users.get_current_user()
		
		filter_instrument = self.request.get('instrument').lower()
		filter_tuning = self.request.get('tuning').lower()
	
		filters = []
	
		if filter_instrument:
			filters.append("instrument = '" + filter_instrument + "'")
		if filter_tuning:
			filters.append("tuning = '" + filter_tuning + "'")
		
		tabs = None
		if len(filters) > 0:
			tabs = Tab.gql("WHERE %s" % " AND ".join(filters))
			logging.debug("#Running query")
		else:
			tabs = Tab.all()
			logging.debug("#Pulling all items")
			
		template_values = {
			'user': user,
			'tabs': tabs,
			'logout_url': users.create_logout_url("/")
		}
		self.response.out.write(template.render(template_dir+"index.html", template_values))


class CreateHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		
		tab = { 'tab_content': """tabstave
notes 

tabstave
notes"""
		}

		template_values = {
			'user': user,
			'tab': tab,
			'logout_url': users.create_logout_url("/"),
			'login_url': users.create_login_url("/")
		}
		self.response.out.write(template.render(template_dir+"create.html", template_values))

class EditHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		tab_id = long(cgi.escape(self.request.get('tab_id')))
		
		logging.debug("tab_id: %d" % tab_id)
		
		tab = Tab.get_by_id(tab_id)
		
		template_values = {
			'user': user,
			'tab': tab,
			'logout_url': users.create_logout_url("/"),
			'login_url': users.create_login_url("/")
		}
		self.response.out.write(template.render(template_dir+"create.html", template_values))

class CopyHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		tab_id = long(cgi.escape(self.request.get('tab_id')))

		toCopy = Tab.get_by_id(tab_id)
		tab = {
			'author': user,
			'tab_content': toCopy.tab_content,
			'name': toCopy.name + " Copy",
			'description': toCopy.description,
			'instrument': toCopy.instrument,
			'tuning': helper.format_tuning(toCopy.tuning)
		}

		template_values = {
			'user': user,
			'tab': tab,
			'logout_url': users.create_logout_url("/"),
			'login_url': users.create_login_url("/")
		}
		self.response.out.write(template.render(template_dir+"create.html", template_values))

class SaveTabHandler(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		
		tab_id = cgi.escape(self.request.get('tab_id'))
		tab_content = cgi.escape(self.request.get('tab_content')).strip()
		name = cgi.escape(self.request.get('name'))
		description = cgi.escape(self.request.get('description')).strip()
		instrument = cgi.escape(self.request.get('instrument')).lower()
		tuning = cgi.escape(self.request.get('tuning')).lower()
		
		if not tab_id:
			tab = Tab(
				author = user,
				tab_content = tab_content,
				name = name,
				description = description,
				instrument = instrument,
				tuning = helper.format_tuning(tuning)
			)
			tab.put()
			tab_id = tab.key().id()
		else:
			tab = Tab.get_by_id(long(tab_id))
			tab.tab_content = tab_content
			tab.name = name
			tab.description = description
			tab.instrument = instrument
			tab.tuning = helper.format_tuning(tuning)
			tab.put()
		
		self.redirect("/edit?tab_id=%d" % long(tab_id))
		

def main():
    application = webapp.WSGIApplication(
		[
			('/', MainHandler),
			('/create', CreateHandler),
			('/edit', EditHandler),
			('/save', SaveTabHandler),
			('/copy', CopyHandler)
		],                              
		debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

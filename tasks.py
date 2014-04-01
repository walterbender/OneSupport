# -*- coding: utf-8 -*-
# Copyright (c) 2014 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import os
import email.utils
import re
from gettext import gettext as _

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.datastore import datastore

import logging
_logger = logging.getLogger('training-activity-tasks')

from activity import (NAME_UID, EMAIL_UID, SCHOOL_UID, SCHOOL_NAME,
                      POST_CODE, PHONE_NUMBER_UID)
from graphics import Graphics, FONT_SIZES
import utils
from reporter import send_report

# These tasks are requirements for other tasks
_ENTER_NAME_TASK = 'enter-name-task'
_ENTER_EMAIL_TASK = 'enter-email-task'
_VALIDATE_EMAIL_TASK = 'validate-email-task'
_ENTER_PHONE_NUMBER_TASK = 'enter-phone-number-task'
_ENTER_SCHOOL_TASK = 'enter-school-task'
_ENTER_BUG_REPORT_TASK = 'enter-bug-report-task'

def get_tasks(task_master):
    task_list = [
        {'name': _('One Support'),
         'icon': 'badge-intro',
         'tasks': [Support1Task(task_master),
                   Support2Task(task_master),
                   Support3Task(task_master),
                   Support4Task(task_master),
                   Support5Task(task_master),
                   Support6Task(task_master),
                   Support7Task(task_master),
                   Support8Task(task_master),
                   Support9Task(task_master)]},
    ]
    return task_list


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, task_master):
        self._name = 'Generic Task'
        self.uid = None
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0
        self._pause_between_checks = 1000
        self._requires = []
        self._prompt = _('Next')

    def get_yes_no_tasks(self):
        return None, None

    def set_font_size(self, size):
        if size < len(FONT_SIZES):
            self._font_size = size

    def get_font_size(self):
        return self._font_size

    font_size = GObject.property(type=object, setter=set_font_size,
                                 getter=get_font_size)

    def set_zoom_level(self, level):
        self._zoom_level = level

    def get_zoom_level(self):
        return self._zoom_level

    zoom_level = GObject.property(type=object, setter=set_zoom_level,
                                  getter=get_zoom_level)

    def test(self, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def grab_focus(self):
        return

    def after_button_press(self):
        ''' Anything special to do after the task is completed? '''
        return True

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_refresh(self):
        ''' Does the task need a refresh button for its graphics? '''
        return False

    def get_my_turn(self):
        ''' Does the task need a my turn button to goto home view? '''
        return False

    def get_skip(self):
        ''' Does the task need a skip button to goto the next section? '''
        return False

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def skip_if_completed(self):
        ''' Should we skip this task if it is already complete? '''
        return False

    def get_pause_time(self):
        ''' How long should we pause between testing? '''
        return self._pause_between_checks

    def set_requires(self, requires):
        self._requires = requires[:]

    def get_requires(self):
        ''' Return list of tasks (uids) required prior to completing this
            task '''
        return []

    requires = GObject.property(type=object, setter=set_requires,
                                getter=get_requires)

    def is_collectable(self):
        ''' Should this task's data be collected? '''
        return False

    def get_name(self):
        ''' String to present to the user to define the task '''
        return self._name

    def get_help_info(self):
        ''' Is there help associated with this task? '''
        return (None, None)  # title, url (from Help.activity)

    def get_graphics(self):
        ''' Graphics to present with the task '''
        self._task_master.activity.set_copy_widget()
        self._task_master.activity.set_paste_widget()
        return None, _('Next')

    def is_completed(self):
        ''' Has this task been marked as complete? '''
        return True

    def _get_user_name(self):
        ''' Get user's name. '''
        name = self._task_master.read_task_data(NAME_UID)
        if name is not None:
            return name
        else:
            return ''


class HTMLTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._uri = 'introduction1.html'
        self._height = 610

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Support1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Support')
        self.uid = 'support-1-task'
        self._uri = ['support1.html', 'support1a.html']
        self._prompt = _("Let's go!")

    def get_graphics(self):
        name = self._task_master.read_task_data(NAME_UID)
        email = self._task_master.read_task_data(EMAIL_UID)
        phone_number = self._task_master.read_task_data(PHONE_NUMBER_UID)
        school = self._task_master.read_task_data(SCHOOL_NAME)

        if name is None or email is None or phone_number is None or \
           school is None:
            url = os.path.join(self._task_master.get_bundle_path(),
                               'html-content', self._uri[0])
        else:
            url = os.path.join(self._task_master.get_bundle_path(),
                               'html-content', self._uri[1])

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        return graphics, self._prompt


class Support2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Your Name')
        self.uid = _ENTER_NAME_TASK
        self._uri = 'support2.html'
        self._first_entry = None
        self._last_entry = None
        self._height = 400
        self._task_data = None

    def is_collectable(self):
        return True

    def _first_enter_entered(self, widget):
        # Switch focus to last entry
        if len(self._first_entry.get_text()) > 1:
            self.grab_focus()

    def _last_enter_entered(self, widget):
        if len(self._first_entry.get_text()) > 1 and \
           len(self._last_entry.get_text()) > 1:
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        self._task_data = task_data
        return len(self._first_entry.get_text()) > 1 and \
            len(self._last_entry.get_text()) > 1

    def after_button_press(self):
        name = '%s,%s' % (self._first_entry.get_text(),
                          self._last_entry.get_text())
        self._task_master.write_task_data(NAME_UID, name)
        return True

    def get_graphics(self):
        target = self._get_user_name()
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        if target is not None and len(target) > 0:
            first, last = target.split(',')
        else:
            first = ''
            last = ''
        self._first_entry, self._last_entry = graphics.add_two_entries(
            _('First name(s):'), first, _('Last name(s):'), last)

        self._first_entry.connect('activate', self._first_enter_entered)
        self._last_entry.connect('activate', self._last_enter_entered)

        return graphics, self._prompt

    def grab_focus(self):
        self._first_entry.set_can_focus(True)
        self._last_entry.set_can_focus(True)
        if len(self._first_entry.get_text()) == 0:
            self._first_entry.grab_focus()
            self._task_master.activity.set_copy_widget(
                text_entry=self._last_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._first_entry)
        else:
            self._last_entry.grab_focus()
            self._task_master.activity.set_copy_widget(
                text_entry=self._first_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._last_entry)


class Support3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Greetings')
        self.uid = 'support-3-task'
        self._uri = 'support3.html'

    def get_graphics(self):
        name = self._get_user_name().split(',')[0]
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' %
                           (self._uri, utils.get_safe_text(name)))
        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Support4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Your Email')
        self.uid = _ENTER_EMAIL_TASK
        self._uri = 'support4.html'
        self._entry = None
        self._height = 400
        self._task_data = None

    def get_requires(self):
        return [_ENTER_NAME_TASK]

    def _enter_entered(self, widget):
        if self._is_valid_email_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_email_entry()

    def _is_valid_email_entry(self):
        entry = self._entry.get_text()
        if len(entry) == 0:
            return False
        realname, email_address = email.utils.parseaddr(entry)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        _logger.debug('Writing email address: %s' % self._entry.get_text())
        self._task_master.write_task_data(EMAIL_UID, self._entry.get_text())
        return True

    def get_graphics(self):
        email = self._task_master.read_task_data(EMAIL_UID)
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if email is not None:
            self._entry = graphics.add_entry(text=email)
        else:
            self._entry = graphics.add_entry()

        self._entry.connect('activate', self._enter_entered)
        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt

    def grab_focus(self):
        self._entry.set_can_focus(True)
        self._entry.grab_focus()


class Support5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Validate Email')
        self.uid = _VALIDATE_EMAIL_TASK
        self._uri = 'support5.html'
        self._entries = []
        self._task_data = None

    def is_collectable(self):
        return True

    def get_requires(self):
        return [_ENTER_EMAIL_TASK]

    def _enter_entered(self, widget):
        if self._is_valid_email_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_email_entry()

    def _is_valid_email_entry(self):
        entry0 = self._entries[0].get_text()
        entry1 = self._entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        if entry0.lower() != entry1.lower():
            return False
        realname, email_address = email.utils.parseaddr(entry0)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        self._task_master.write_task_data(EMAIL_UID,
                                          self._entries[1].get_text())
        return True

    def get_graphics(self):
        self._entries = []
        email = self._task_master.read_task_data(EMAIL_UID)
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        if email is None:
            # This should not happen except if data file is corrupted
            self._entries.append(graphics.add_entry(text=''))
            _logger.error('email was missing in Task %s' % self.uid)
        else:
            self._entries.append(graphics.add_entry(text=email))
        graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        if email is None:  # Should never happen
            email = ''
        self._entries.append(graphics.add_entry())

        self._entries[0].connect('activate', self._enter_entered)
        self._entries[1].connect('activate', self._enter_entered)
        # Paste to second entry
        self._task_master.activity.set_copy_widget(text_entry=self._entries[0])
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[-1])

        return graphics, self._prompt

    def grab_focus(self):
        self._entries[-1].set_can_focus(True)
        self._entries[-1].grab_focus()


class Support6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Your Phone Number')
        self.uid = _ENTER_PHONE_NUMBER_TASK
        self._uri = 'support6.html'
        self._entry = None
        self._height = 400
        self._task_data = None

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def _enter_entered(self, widget):
        if self._is_valid_phone_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_phone_entry()

    def _is_valid_phone_entry(self):
        entry = self._entry.get_text()
        if len(entry) == 0:
            return False
        return self._valid_number(entry)

    def _valid_number(self, phone_number):
        # xx xxxx xxxx (AU)
        pattern = re.compile("(^[\dA-Z]{2}) [\dA-Z]{4} [\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # xxxx xxx xxx (AU)
        pattern = re.compile("^[\dA-Z]{4} [\dA-Z]{3} [\dA-Z]{3}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # +61 xxx xxx xxx (AU)
        pattern = re.compile("\+61 [\dA-Z]{3} [\dA-Z]{3} [\dA-Z]{3}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # +61 x xxxx xxxx (AU)
        pattern = re.compile("\+61 [\dA-Z]{1} [\dA-Z]{4} [\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # xxx-xxx-xxxx (US)
        pattern = re.compile("^[\dA-Z]{3}-[\dA-Z]{3}-[\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # xxx xxx xxxx (US)
        pattern = re.compile("^[\dA-Z]{3} [\dA-Z]{3} [\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # xxxxxxxxxx (US)
        pattern = re.compile("^[\dA-Z]{3}[\dA-Z]{3}[\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # +1-xxx-xxx-xxxx (US)
        pattern = re.compile("\+1-^[\dA-Z]{3}-[\dA-Z]{3}-[\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        # 1-xxx-xxx-xxxx (US)
        pattern = re.compile("1-^[\dA-Z]{3}-[\dA-Z]{3}-[\dA-Z]{4}$",
                             re.IGNORECASE)
        if pattern.match(phone_number) is not None:
            return True
        return False

    def after_button_press(self):
        _logger.debug('Writing phone number: %s' % self._entry.get_text())
        self._task_master.write_task_data(PHONE_NUMBER_UID,
                                          self._entry.get_text())
        return True

    def get_graphics(self):
        phone_number = self._task_master.read_task_data(PHONE_NUMBER_UID)
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if phone_number is not None:
            self._entry = graphics.add_entry(text=phone_number)
        else:
            self._entry = graphics.add_entry()

        self._entry.connect('activate', self._enter_entered)
        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt

    def grab_focus(self):
        self._entry.set_can_focus(True)
        self._entry.grab_focus()


class Support7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter School Name')
        self.uid = _ENTER_SCHOOL_TASK
        self._uri = ['support7a.html',
                     'support7b.html']
        self._height = 60
        self._graphics = None
        self._school_entry = None
        self._postal_code_entry = None
        self._postal_code_changed = True
        self._postal_code = -1
        self._buttons = []
        self._schools = []
        self._sf_ids = []
        self._results = []
        self._default_sf_id = '0019000000pETbT'
        self._completer = None
        self._task_data = None

    def is_collectable(self):
        return True

    def _postal_code_enter_entered(self, widget):
        # Force new list
        self._postal_code_changed = True
        if self._is_valid_postal_code_entry():
            self._school_entry.grab_focus()
            self._is_valid_school_entry()

    def _postal_code_entry_cb(self, widget, event):
        if self._is_valid_postal_code_entry():
            self._is_valid_school_entry()

    def _is_valid_postal_code_entry(self, target=None):
        if target is None:
            target = self._postal_code_entry.get_text()
        if len(target) < 3:
            return False
        try:
            i = int(target)
        except:
            return False
        if i >= 0 and i < 9999:
            self._postal_code_changed = True
            self._postal_code = i
            self._task_master.write_task_data(POST_CODE, target)
            return True
        else:
            return False

    def _school_enter_entered(self, widget):
        if self._is_valid_school_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_school_entry()

    def _is_valid_school_entry(self):
        # build a completer for this postal code
        if self._postal_code < 0:
            return False

        if self._postal_code_changed:
            # get rid of any old buttons
            for button in self._buttons:
                button.destroy()

            f = open(os.path.join(self._task_master.activity.bundle_path,
                                  'schools.txt'), 'r')
            schools = f.read().split('\n')
            f.close()
            self._schools = []
            self._sf_ids = []
            for school in schools:
                if len(school) == 0:
                    continue
                try:
                    sf_id, name, campus, address, city, state, postal_code = \
                        school.split(',')
                except:
                    _logger.debug('bad school data? (%s)' % school)
                # save the SF_ID from One Education in case we need it
                if name == 'One Education School':
                    self._default_sf_id = sf_id
                try:
                    if int(postal_code) != self._postal_code:
                        continue
                except:
                    _logger.error('bad postal code? (%s: %s)' % 
                                  (name, postal_code))
                    continue
                if len(campus) > 0:
                    self._schools.append('%s %s, %s, %s' %
                                         (name, campus, city, state))
                else:
                    self._schools.append('%s, %s, %s' % (name, city, state))
                self._sf_ids.append(sf_id)
            # _logger.debug('%d schools in the list' %  (len(self._schools)))
            self._completer = utils.Completer(self._schools)
            if len(self._schools) < 10:
                self._make_buttons(self._schools)

        self._postal_code_changed = False
        if len(self._school_entry.get_text()) == 0:
            return False
        else:
            return True

    def _make_buttons(self, school_list):
        for button in self._buttons:
            button.destroy()
        self._buttons = []
        for i, school in enumerate(school_list):
            self._buttons.append(
                self._graphics.add_button(school, self._button_cb, arg=school))
            self._buttons[-1].show()

    def _button_cb(self, widget, text):
        self._school_entry.set_text(text)
        for button in self._buttons:
            button.destroy()

    def _school_entry_focus_cb(self, widget, event):
        if not self._is_valid_postal_code_entry():
            return
        elif len(widget.get_text()) == 0 and len(self._schools) > 0:
            self._make_buttons(self._schools)

    def _school_entry_release_cb(self, widget, event):
        if len(self._results) == 1:
            widget.set_text(self._results[0])
            for button in self._buttons:
                button.destroy()
        elif len(self._results) < 10:
            for button in self._buttons:
                button.destroy()
            self._make_buttons(self._results)

    def _school_entry_press_cb(self, widget, event):
        if not self._is_valid_postal_code_entry():
            return
        self._results = self._completer.complete(
            widget.get_text() + Gdk.keyval_name(event.keyval), 0)

    def _yes_no_cb(self, widget, arg):
        if arg == 'yes':
            self._task_master.write_task_data(SCHOOL_UID, None)
            school = self._school_entry.get_text()
            postal_code = self._postal_code_entry.get_text()
            self._task_data[SCHOOL_NAME] = school
            self._task_data[POST_CODE] = postal_code
            self._task_master.write_task_data(self.uid, self._task_data)
            self._task_master.write_task_data(SCHOOL_NAME, school)
            self._task_master.write_task_data(POST_CODE, postal_code)
            self._task_master.write_task_data(SCHOOL_UID, self._default_sf_id)
            self._task_master.current_task += 1
            self._task_master.write_task_data('current_task',
                                              self._task_master.current_task)
        self._task_master.task_master()

    def after_button_press(self):
        school = self._school_entry.get_text()
        if school in self._schools:
            i = self._schools.index(school)
            self._task_master.write_task_data(SCHOOL_UID, self._sf_ids[i])
            self._task_master.write_task_data(SCHOOL_NAME, school)
            return True
        else:
            # Confirm that it is OK to use a school not in the list.
            self._task_master.task_button.hide()
            self._graphics.add_text(_('Your school does not appear in our '
                                      'list of schools in Australia. '
                                      'OK to continue?'))
            self._graphics.add_yes_no_buttons(self._yes_no_cb)
            return False

    def get_graphics(self):
        self._graphics = Graphics()

        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri[0])
        self._graphics.add_uri('file://' + url, height=self._height)
        self._graphics.set_zoom_level(self._zoom_level)

        target = self._task_master.read_task_data(POST_CODE)
        if target is not None and \
           self._is_valid_postal_code_entry(target=target):
            self._postal_code_entry = self._graphics.add_entry(text=target)
        else:
            self._postal_code_entry = self._graphics.add_entry()

        self._postal_code_entry.connect('key-release-event',
                                        self._postal_code_entry_cb)
        self._postal_code_entry.connect('key-press-event',
                                        self._postal_code_entry_cb)
        self._postal_code_entry.connect('activate',
                                        self._postal_code_enter_entered)

        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri[1])
        self._graphics.add_uri('file://' + url, height=self._height)
        self._graphics.set_zoom_level(self._zoom_level)

        target = self._task_master.read_task_data(SCHOOL_NAME)
        if target is not None:
            self._school_entry = self._graphics.add_entry(text=target)
        else:
            self._school_entry = self._graphics.add_entry()

        self._school_entry.connect('key-release-event',
                                   self._school_entry_release_cb)
        self._school_entry.connect('key-press-event',
                                   self._school_entry_press_cb)
        self._school_entry.connect('focus-in-event',
                                   self._school_entry_focus_cb)
        self._school_entry.connect('activate', self._school_enter_entered)

        self._postal_code_entry.grab_focus()

        return self._graphics, self._prompt

    def grab_focus(self):
        self._postal_code_entry.set_can_focus(True)
        self._school_entry.set_can_focus(True)
        if len(self._postal_code_entry.get_text()) < 3:
            self._task_master.activity.set_copy_widget(
                text_entry=self._postal_code_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._postal_code_entry)
        else:
            self._task_master.activity.set_copy_widget(
                text_entry=self._school_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._school_entry)


class Support8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Confirmation')
        self.uid = 'support-8-task'
        self._uri = 'support8.html'

    def get_requires(self):
        return [_ENTER_NAME_TASK, _VALIDATE_EMAIL_TASK, _ENTER_SCHOOL_TASK]

    def get_graphics(self):
        self._entries = []
        name = self._task_master.read_task_data(NAME_UID)
        if name is None:  # Should never happen
            name = ''
        email = self._task_master.read_task_data(EMAIL_UID)
        if email is None:  # Should never happen
            email = ''
        phone_number = self._task_master.read_task_data(PHONE_NUMBER_UID)
        if phone_number is None:  # Should never happen
            phone_number = ''
        school = self._task_master.read_task_data(SCHOOL_NAME)
        if school is None:  # Should never happen
            school = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s&EMAIL=%s&PHONE=%s&SCHOOL=%s' %
                           (self._uri,
                            utils.get_safe_text(name),
                            utils.get_safe_text(email),
                            utils.get_safe_text(phone_number),
                            utils.get_safe_text(school)))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Support9Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Your Bug Report')
        self.uid = _ENTER_BUG_REPORT_TASK
        self._uri = 'support9.html'
        self._entry = None
        self._height = 200
        self._task_data = None
        self._prompt = _('Submit')

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_bug_report_entry()

    def _is_valid_bug_report_entry(self):
        text_buffer = self._entry.get_buffer()
        bounds = text_buffer.get_bounds()
        text = text_buffer.get_text(bounds[0], bounds[1], True)
        if len(text) == 0:
            return False
        return True

    def after_button_press(self):
        if self._task_master.completed:
            return True

        text_buffer = self._entry.get_buffer()
        bounds = text_buffer.get_bounds()
        text = text_buffer.get_text(bounds[0], bounds[1], True)

        name = self._task_master.read_task_data(NAME_UID)
        if name is None:  # Should never happen
            name = ''
        email = self._task_master.read_task_data(EMAIL_UID)
        if email is None:  # Should never happen
            email = ''
        phone_number = self._task_master.read_task_data(PHONE_NUMBER_UID)
        if phone_number is None:  # Should never happen
            phone_number = ''
        school = self._task_master.read_task_data(SCHOOL_NAME)
        if school is None:  # Should never happen
            school = ''

        data = {'subject': 'bug report from One Support',
                'body': text,
                'name': name, 
                'email': email,
                'school': school,
                'phone': phone_number,
                'serial': utils.get_serial_number(),
                'build': utils.get_build_number(),
                'files': []}

        self._task_master.activity.busy_cursor()
        GObject.idle_add(self._send_report, data)
        return True

    def _send_report(self, data):
        send_report(data)
        self._task_master.activity.reset_cursor()

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        self._entry = graphics.add_text_view()

        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt

    def grab_focus(self):
        self._entry.set_can_focus(True)
        self._entry.grab_focus()

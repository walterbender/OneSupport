# -*- coding: utf-8 -*-
#Copyright (c) 2014 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import dbus
import os
from ConfigParser import ConfigParser
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GConf

from gi.repository import SugarExt

from sugar3.activity import activity
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics import style

NAME_UID = 'name'
EMAIL_UID = 'email_address'
SCHOOL_UID = 'school_sf_id'
SCHOOL_NAME = 'school_name'
POST_CODE = 'post_code'
PHONE_NUMBER_UID = 'phone_number'
ROLE_UID = 'role'
ERROR_REPORT = 'error_report'

from aboutpanel import AboutPanel
from taskmaster import TaskMaster
from graphics import Graphics, FONT_SIZES
import utils
from power import get_power_manager

import logging
_logger = logging.getLogger('one-support-activity')


def _check_gconf_settings():
    client = GConf.Client.get_default()

    # Zendesk
    client.set_string('/desktop/sugar/services/zendesk/url',
                      'https://oneedu.zendesk.com')
    client.set_string('/desktop/sugar/services/zendesk/token',
                      'eG8tc3VwcG9ydEBsYXB0b3Aub3JnLmF1L3Rva2VuOlZTaWM4'
                      'TThZbjZBRTJkMWxYNkFGbFhkZzUxSjlJSHFUQ01DYzNjOHY=')
    try:
        SugarExt.gconf_client_set_string_list(
            client, '/desktop/sugar/services/zendesk/fields',
            ['21891880', '21729904', '21729914'])
    except Exception as e:
        _logger.error('Could not set zendesk fields: %s' % e)


class OneSupportActivity(activity.Activity):
    ''' An activity for sending bug reports '''

    def __init__(self, handle):
        ''' Initialize the toolbar '''
        try:
            super(OneSupportActivity, self).__init__(handle)
        except dbus.exceptions.DBusException as e:
            _logger.error(str(e))

        self.connect('realize', self.__realize_cb)

        if hasattr(self, 'metadata') and 'font_size' in self.metadata:
            self.font_size = int(self.metadata['font_size'])
        else:
            self.font_size = 8
        self.zoom_level = self.font_size / float(len(FONT_SIZES))
        _logger.debug('zoom level is %f' % self.zoom_level)

        # _check_gconf_settings()  # For debugging purposes

        self._setup_toolbars()
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.bundle_path = activity.get_bundle_path()
        self.tmp_path = os.path.join(activity.get_activity_root(), 'tmp')

        self._copy_entry = None
        self._paste_entry = None
        self._webkit = None
        self._clipboard_text = ''
        self._fixed = None
        self._notify_transfer_status = False

        get_power_manager().inhibit_suspend()
        self._launch_task_master()

    def can_close(self):
        get_power_manager().restore_suspend()
        return True

    def busy_cursor(self):
        self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

    def reset_cursor(self):
        self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))

    def _launch_task_master(self):
        # Most things need only be done once
        if self._fixed is None:
            self._fixed = Gtk.Fixed()
            self._fixed.set_size_request(Gdk.Screen.width(),
                                         Gdk.Screen.height())

            # Offsets from the bottom of the screen
            dy1 = 3 * style.GRID_CELL_SIZE
            dy2 = 2 * style.GRID_CELL_SIZE

            self._progress_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._progress_area.set_size_request(Gdk.Screen.width(), -1)
            self._fixed.put(self._progress_area, 0, Gdk.Screen.height() - dy2)
            self._progress_area.show()

            self._button_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._button_area.set_size_request(Gdk.Screen.width(), -1)
            self._fixed.put(self._button_area, 0, Gdk.Screen.height() - dy1)
            self._button_area.show()

            self._scrolled_window = Gtk.ScrolledWindow()
            self._scrolled_window.set_size_request(
                Gdk.Screen.width(), Gdk.Screen.height() - dy1)
            self._set_scroll_policy()
            self._graphics_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._scrolled_window.add_with_viewport(self._graphics_area)
            self._graphics_area.show()
            self._fixed.put(self._scrolled_window, 0, 0)
            self._scrolled_window.show()

            self._task_master = TaskMaster(self)
            self._task_master.show()

            Gdk.Screen.get_default().connect('size-changed',
                                             self._configure_cb)
            self._toolbox.connect('hide', self._resize_hide_cb)
            self._toolbox.connect('show', self._resize_show_cb)

            self._task_master.set_events(Gdk.EventMask.KEY_PRESS_MASK)
            self._task_master.connect('key_press_event',
                                      self._task_master.keypress_cb)
            self._task_master.set_can_focus(True)
            self._task_master.grab_focus()

        self.set_canvas(self._fixed)
        self._fixed.show()

        self._task_master.task_master()

    def reset_scrolled_window_adjustments(self):
        adj = self._scrolled_window.get_hadjustment()
        if adj is not None:
            adj.set_value(0)
        adj = self._scrolled_window.get_vadjustment()
        if adj is not None:
            adj.set_value(0)

    def load_graphics_area(self, widget):
        self._graphics_area.add(widget)

    def load_button_area(self, widget):
        self._button_area.add(widget)

    def load_progress_area(self, widget):
        self._progress_area.add(widget)

    def _load_intro_graphics(self, file_name='generic-problem.html',
                             message=None):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        url = os.path.join(self.bundle_path, 'html-content', file_name)
        graphics = Graphics()
        if message is None:
            graphics.add_uri('file://' + url)
        else:
            graphics.add_uri('file://' + url + '?MSG=' +
                             utils.get_safe_text(message))
        graphics.set_zoom_level(0.667)
        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _resize_hide_cb(self, widget):
        self._resize_canvas(widget, True)

    def _resize_show_cb(self, widget):
        self._resize_canvas(widget, False)

    def _configure_cb(self, event):
        self._fixed.set_size_request(Gdk.Screen.width(), Gdk.Screen.height())
        self._set_scroll_policy()
        self._resize_canvas(None)
        self._task_master.reload_graphics()

    def _resize_canvas(self, widget, fullscreen=False):
        # When a toolbar is expanded or collapsed, resize the canvas
        # to ensure that the progress bar is still visible.
        if hasattr(self, '_task_master'):
            if self.toolbar_expanded():
                dy1 = 4 * style.GRID_CELL_SIZE
                dy2 = 3 * style.GRID_CELL_SIZE
            else:
                dy1 = 3 * style.GRID_CELL_SIZE
                dy2 = 2 * style.GRID_CELL_SIZE

            if fullscreen:
                dy1 -= 2 * style.GRID_CELL_SIZE
                dy2 -= 2 * style.GRID_CELL_SIZE

            self._scrolled_window.set_size_request(
                Gdk.Screen.width(), Gdk.Screen.height() - dy1)
            self._fixed.move(self._progress_area, 0, Gdk.Screen.height() - dy2)
            self._fixed.move(self._button_area, 0, Gdk.Screen.height() - dy1)

    def toolbar_expanded(self):
        if self.activity_button.is_expanded():
            return True
        elif self.edit_toolbar_button.is_expanded():
            return True
        elif self.view_toolbar_button.is_expanded():
            return True
        return False

    def get_activity_version(self):
        info_path = os.path.join(self.bundle_path, 'activity', 'activity.info')
        try:
            info_file = open(info_path, 'r')
        except Exception as e:
            _logger.error('Could not open %s: %s' % (info_path, e))
            return 'unknown'

        cp = ConfigParser()
        cp.readfp(info_file)

        section = 'Activity'

        if cp.has_option(section, 'activity_version'):
            activity_version = cp.get(section, 'activity_version')
        else:
            activity_version = 'unknown'
        return activity_version

    def get_uid(self):
        if len(self.volume_data) == 1:
            return self.volume_data[0]['uid']
        else:
            return 'unknown'

    def write_file(self, file_path):
        self.metadata['font_size'] = str(self.font_size)

    def _setup_toolbars(self):
        ''' Setup the toolbars. '''
        self.max_participants = 1  # No sharing

        self._toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self.activity_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(self._toolbox)
        self._toolbox.show()
        self.toolbar = self._toolbox.toolbar

        view_toolbar = Gtk.Toolbar()
        self.view_toolbar_button = ToolbarButton(
            page=view_toolbar,
            label=_('View'),
            icon_name='toolbar-view')
        self.view_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.view_toolbar_button, 1)
        view_toolbar.show()
        self.view_toolbar_button.show()

        button = ToolButton('view-fullscreen')
        button.set_tooltip(_('Fullscreen'))
        button.props.accelerator = '<Alt>Return'
        view_toolbar.insert(button, -1)
        button.show()
        button.connect('clicked', self._fullscreen_cb)

        self._zoom_in = ToolButton('zoom-in')
        self._zoom_in.set_tooltip(_('Increase size'))
        view_toolbar.insert(self._zoom_in, -1)
        self._zoom_in.show()
        self._zoom_in.connect('clicked', self._zoom_in_cb)

        self._zoom_out = ToolButton('zoom-out')
        self._zoom_out.set_tooltip(_('Decrease size'))
        view_toolbar.insert(self._zoom_out, -1)
        self._zoom_out.show()
        self._zoom_out.connect('clicked', self._zoom_out_cb)

        self._zoom_eq = ToolButton('zoom-original')
        self._zoom_eq.set_tooltip(_('Restore original size'))
        view_toolbar.insert(self._zoom_eq, -1)
        self._zoom_eq.show()
        self._zoom_eq.connect('clicked', self._zoom_eq_cb)

        self._set_zoom_buttons_sensitivity()

        edit_toolbar = Gtk.Toolbar()
        self.edit_toolbar_button = ToolbarButton(
            page=edit_toolbar,
            label=_('Edit'),
            icon_name='toolbar-edit')
        self.edit_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.edit_toolbar_button, 1)
        edit_toolbar.show()
        self.edit_toolbar_button.show()

        self._copy_button = ToolButton('edit-copy')
        self._copy_button.set_tooltip(_('Copy'))
        self._copy_button.props.accelerator = '<Ctrl>C'
        edit_toolbar.insert(self._copy_button, -1)
        self._copy_button.show()
        self._copy_button.connect('clicked', self._copy_cb)
        self._copy_button.set_sensitive(False)

        self._paste_button = ToolButton('edit-paste')
        self._paste_button.set_tooltip(_('Paste'))
        self._paste_button.props.accelerator = '<Ctrl>V'
        edit_toolbar.insert(self._paste_button, -1)
        self._paste_button.show()
        self._paste_button.connect('clicked', self._paste_cb)
        self._paste_button.set_sensitive(False)

        self._about_button = ToolButton('computer')
        self._about_button.set_tooltip(_('About Computer'))
        self._toolbox.toolbar.insert(self._about_button, -1)
        self._about_button.show()
        self._about_button.connect('clicked', self._about_cb)

        about_panel = AboutPanel()
        about_panel.show()
        self._about_palette = self._about_button.get_palette()
        self._about_palette.set_content(about_panel)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self._toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        self._toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def set_copy_widget(self, webkit=None, text_entry=None):
        # Each task is responsible for setting a widget for copy
        if webkit is not None:
            self._webkit = webkit
        else:
            self._webkit = None
        if text_entry is not None:
            self._copy_entry = text_entry
        else:
            self._copy_entry = None

        self._copy_button.set_sensitive(webkit is not None or
                                        text_entry is not None)

    def _copy_cb(self, button):
        if self._copy_entry is not None:
            self._copy_entry.copy_clipboard()
        elif self._webkit is not None:
            self._webkit.copy_clipboard()
        else:
            _logger.debug('No widget set for copy.')

    def set_paste_widget(self, text_entry=None):
        # Each task is responsible for setting a widget for paste
        if text_entry is not None:
            self._paste_entry = text_entry
        self._paste_button.set_sensitive(text_entry is not None)

    def _paste_cb(self, button):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard_text = clipboard.wait_for_text()
        if self._paste_entry is not None:
            self._paste_entry.paste_clipboard()
        else:
            _logger.debug('No widget set for paste (%s).' %
                          self.clipboard_text)

    def _about_cb(self, button):
        self._about_palette.popup(
            immediate=True,
            state=self._about_palette.SECONDARY)

    def _fullscreen_cb(self, button):
        ''' Hide the Sugar toolbars. '''
        self.fullscreen()

    def _set_zoom_buttons_sensitivity(self):
        if self.font_size < len(FONT_SIZES) - 1:
            self._zoom_in.set_sensitive(True)
        else:
            self._zoom_in.set_sensitive(False)
        if self.font_size > 0:
            self._zoom_out.set_sensitive(True)
        else:
            self._zoom_out.set_sensitive(False)

        if hasattr(self, '_scrolled_window'):
            self._set_scroll_policy()

    def _set_scroll_policy(self):
        if Gdk.Screen.width() < Gdk.Screen.height() or self.zoom_level > 0.667:
            self._scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                             Gtk.PolicyType.AUTOMATIC)
        else:
            self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                             Gtk.PolicyType.AUTOMATIC)

    def _zoom_eq_cb(self, button):
        self.font_size = 8
        self.zoom_level = 0.667
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_in_cb(self, button):
        if self.font_size < len(FONT_SIZES) - 1:
            self.font_size += 1
            self.zoom_level *= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_out_cb(self, button):
        if self.font_size > 0:
            self.font_size -= 1
            self.zoom_level /= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _remove_alert_cb(self, alert, response_id):
        self.remove_alert(alert)

    def _close_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            self.close()

    def _reboot_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            try:
                utils.reboot()
            except Exception as e:
                _logger.error('Cannot reboot: %s' % e)

    def _mount_added_cb(self, volume_monitor, device):
        _logger.error('mount added')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()

    def _mount_removed_cb(self, volume_monitor, device):
        _logger.error('mount removed')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()

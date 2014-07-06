# Copyright (C) 2014 Martin Abente Lahaye - tch@sugarlabs.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GLib

from sugar3.graphics import style

from backend.logcollect import MachineProperties


class AboutPanel(Gtk.Grid):

    SERIAL_TEXT = _('Serial Number: %s')
    BUILD_TEXT = _('Build: %s')
    SNAPSHOT_TEXT = _('Snapshot: %s')

    def __init__(self):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(style.DEFAULT_SPACING)
        self.set_column_spacing(style.DEFAULT_SPACING)
        self.set_column_homogeneous(True)
        self.set_border_width(style.DEFAULT_SPACING)

        self._pos = 0
        self._machine = MachineProperties()

        self._add_information(
            self.SERIAL_TEXT % self._machine.laptop_serial_number())
        self._add_information(
            self.BUILD_TEXT % self._machine.build_information())

        self.connect('realize', self.__realize_cb)

    def __realize_cb(self, panel):
        GLib.idle_add(self._display_snapshot)

    def _display_snapshot(self):
        self._add_information(
            self.SNAPSHOT_TEXT % self._machine.packages_snapshot())

    def _add_information(self, text):
        alignment = Gtk.Alignment.new(0., 0.5, 0., 0.)
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_markup(
            '<span foreground="%s" size="large">%s</span>' %
            (style.COLOR_WHITE.get_html(), text))
        alignment.add(label)
        label.show()
        self.attach(alignment, 0, self._pos, 4, 1)
        alignment.show()
        self._pos += 2

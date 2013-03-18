# This file is a part of Fedora gnome-tagger
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA
#
# Refer to the README.rst and LICENSE files for full details of the license
# -*- coding: utf-8 -*-

'''
main gnome-tagger file.
'''

import urllib2
import json
import requests
import sys

from gi.repository import Pango
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import Gtk

TAGGERAPI = 'http://209.132.184.171/'


class GnomeTaggerWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        window = Gtk.Window.__init__(self, title='GNOME Tagger', application=app)

        self.pkgname = None
        self.statistics = None

        #self.set_default_size(400, 200)

        # a grid to attach the toolbar (see below)
        grid = Gtk.Grid()
        self.add(grid)
        # we have to show the grid (and therefore the toolbar) with show(),
        # as show_all() would show also the buttons in the toolbar that we want to
        # be hidden (such as the leave_fullscreen button)
        grid.show()

        # a builder to add the UI designed with Glade to the grid:
        self.builder = Gtk.Builder()
        # get the file (if it is there)
        try:
            self.builder.add_from_file('tagger.ui')
        except:
            print 'file not found'
            sys.exit()
        # and attach it to the grid
        grid.attach(self.builder.get_object('vbox1'), 0, 0, 1, 1)

        # option 'about'
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self.about_action)
        app.add_action(about_action)

        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True

        like_icon = GdkPixbuf.Pixbuf.new_from_file_at_size('like.png', 25, 25)
        dislike_icon = GdkPixbuf.Pixbuf.new_from_file_at_size('dislike.png',
                                                              25, 25)

        image = Gtk.Image()
        image.set_from_pixbuf(like_icon)
        image.show()
        likebutton = self.builder.get_object('button_like')
        likebutton.add(image)

        image = Gtk.Image()
        image.set_from_pixbuf(dislike_icon)
        image.show()
        dislikebutton = self.builder.get_object('button_dislike')
        dislikebutton.add(image)

        treeview = self.builder.get_object('treeview1')
        treeselection = treeview.get_selection()
        treeselection.set_mode(Gtk.SelectionMode.MULTIPLE)

        cell_tag = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Tags')
        column_text.pack_start(cell_tag, True)
        column_text.set_attributes(cell_tag, text=0)
        treeview.append_column(column_text)

        dic = {
            'on_button_next_pkg_clicked': self.next_pkg_action,
            'on_button_add_tag_clicked': self.add_tag_action,
            'on_button_like_clicked': self.like_action,
            'on_button_dislike_clicked': self.dislike_action,
            'on_button_stats_clicked': self.stats_action,
        }
        self.builder.connect_signals(dic)

        self.get_package('firefox')

    def next_pkg_action(self, *args, **kw):
        """ Retrieve information about the next (random) package and update
        the GUI accordingly.
        """
        print 'next_pkg_action'
        msg = self.builder.get_object('label_msg')
        msg.set_text('')
        self.get_package()

    def add_tag_action(self, *args, **kw):
        """ Retrieve the tags from `entry_tag` and send them to the server,
        update the GUI afterward.
        """
        print 'add_tag_action'

        cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_root_window().set_cursor(cursor)
        Gdk.flush()

        msg = self.builder.get_object('label_msg')
        msg.set_text('')
        tagfield = self.builder.get_object('entry_tag')
        entries = tagfield.get_text()
        entries = [entry.strip() for entry in entries.split(',')]
        tagfield.set_text('')
        if entries != ['']:
            data = {'pkgname': self.pkgname, 'tag': ','.join(entries)}
            req = requests.put('%s/tag/guake/' % TAGGERAPI, data=data)
            print req.text
            jsonreq = json.loads(req.text)
            if req.status_code != 200:
                msg.set_text(jsonreq['error'])
            else:
                msg.set_text('\n'.join(jsonreq['messages']))
            self.get_package(self.pkgname)
        else:
            msg.set_text('No tag(s) to add')

    def like_action(self, *args, **kw):
        """ Retrieve the list of tags which are selected and send to the
        server that they have been 'licked'.
        If no tags are selected show an error dialog.
        """
        print 'like_click'
        msg = self.builder.get_object('label_msg')
        msg.set_text('')
        data = {'pkgname': self.pkgname, 'vote': '1'}
        treeview = self.builder.get_object('treeview1')
        selection = treeview.get_selection()
        tree_model, rows = selection.get_selected_rows()
        for tree_iter in rows:
            if tree_iter:
                tag = tree_model[tree_iter][0]
                data['tag'] = tag
                req = requests.put('%s/vote/guake/' % TAGGERAPI,
                                   data=data)
                print req.text
                jsonreq = json.loads(req.text)
                if req.status_code != 200:
                    msg.set_text(jsonreq['error'])
                else:
                    msg.set_text('\n'.join(jsonreq['messages']))
        else:
            msg.set_text('No tag(s) selected')

    def dislike_action(self, *args, **kw):
        """ Retrieve the list of tags which are selected and send to the
        server that they have been 'dislicked'.
        If no tags are selected show an error dialog.
        """
        print 'dislike_click'
        msg = self.builder.get_object('label_msg')
        msg.set_text('')
        data = {'pkgname': self.pkgname, 'vote': '-1'}
        treeview = self.builder.get_object('treeview1')
        selection = treeview.get_selection()
        tree_model, rows = selection.get_selected_rows()
        for tree_iter in rows:
            if tree_iter:
                tag = tree_model[tree_iter][0]
                data['tag'] = tag
                req = requests.put('%s/vote/guake/' % TAGGERAPI,
                                   data=data)
                print req.text
                jsonreq = json.loads(req.text)
                if req.status_code != 200:
                    msg.set_text(jsonreq['error'])
                else:
                    msg.set_text('\n'.join(jsonreq['messages']))
        else:
            msg.set_text('No tag(s) selected')

    def stats_action(self, *args, **kw):
        """ Retrieves statistics from the server and display them in a new
        dialog.
        These statistics include general statistics on the coverage of Tag
        per packages and the leaderboard of the game.
        """
        print 'stats_action'

        win = Gtk.Window(title='GNOME Tagger - Statistics')
        win.connect('delete-event', Gtk.main_quit)

        cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_root_window().set_cursor(cursor)
        Gdk.flush()

        if not self.statistics:
            data = requests.get(TAGGERAPI + '/statistics/')
            jsondata = json.loads(data.text)
            self.statistics = jsondata['summary']

        listmodel = Gtk.ListStore(str, str)
        listmodel.append(['Total number of packages',
                         str(self.statistics['total_packages'])])
        listmodel.append(['Total number of tags',
                         str(self.statistics['total_unique_tags'])])
        listmodel.append(['Packages with no tags',
                         str(self.statistics['no_tags'])])
        listmodel.append(['Packages with tags',
                         str(self.statistics['with_tags'])])
        listmodel.append(['Average tags per package',
                         '%.2f' % self.statistics['tags_per_package']])
        listmodel.append(['Average tags per package (that have at least one tag)',
                         '%.2f' % self.statistics['tags_per_package_no_zeroes']])

        # a treeview to see the data stored in the model
        view = Gtk.TreeView(model=listmodel)
        view.set_headers_visible(False)
        # for each column
        for i in range(2):
            # cellrenderer to render the text
            cell = Gtk.CellRendererText()
            # the text in the first column should be in boldface
            if i == 0:
                cell.props.weight_set=True
                cell.props.weight=Pango.Weight.BOLD
            # the column is created
            col = Gtk.TreeViewColumn('', cell, text=i)
            # and it is appended to the treeview
            view.append_column(col)

        # a grid to attach the widgets
        grid = Gtk.Grid()
        grid.attach(view, 0, 0, 6, 1)

        button = Gtk.Button(label="ok")
        button.connect("clicked", self.win_close, win)
        button_refresh = Gtk.Button(label="Refresh")
        button_refresh.connect("clicked", self.refresh_stats, win, grid)

        grid.attach(button_refresh, 4, 1, 1, 1)
        grid.attach(button, 5, 1, 1, 1)

        # attach the grid to the window
        win.add(grid)
        cursor = Gdk.Cursor.new(Gdk.CursorType.ARROW)
        self.get_root_window().set_cursor(cursor)
        win.show_all()

    def get_package(self, name=None):
        """ Retrieve the information about a package if the name if set, a
        random package if the name is None.
        """
        cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_root_window().set_cursor(cursor)
        Gdk.flush()
        url = '%s/random/' % (TAGGERAPI)
        if name:
            url = '%s/%s/' % (TAGGERAPI, name)
        data = requests.get(url)
        jsondata = json.loads(data.text)
        self.set_package_info(
            name=jsondata['name'],
            summary=jsondata['summary'],
            tags=[tag['tag'] for tag in jsondata['tags']],
            icon_url=jsondata['icon'],
        )
        cursor = Gdk.Cursor.new(Gdk.CursorType.ARROW)
        self.get_root_window().set_cursor(cursor)

    def set_package_info(self, name, summary, tags, icon_url):
        """ Set the package information into the GUI.
        """
        self.pkgname = name

        image = self.builder.get_object('image_pkg')
        response = urllib2.urlopen(icon_url)
        loader = GdkPixbuf.PixbufLoader()
        loader.write(response.read())
        image.set_from_pixbuf(loader.get_pixbuf())
        loader.close()

        label = self.builder.get_object('label_pkg')
        label.set_text('<b>%s</b>\n%s' % (name, summary or ''))
        label.set_use_markup(True)

        treeview = self.builder.get_object('treeview1')
        liststore = Gtk.ListStore(str)
        for tag in tags:
            liststore.append([tag])
        treeview.set_model(liststore)

    def about_action(self, action, parameter):
        """ Show the about window. """
        aboutdialog = Gtk.AboutDialog()

        # lists of authors and documenters (will be used later)
        authors = ['Pierre-Yves Chibon', 'Ralph Bean']
        #documenters = ['GNOME Documentation Team']

        # we fill in the aboutdialog
        aboutdialog.set_program_name('GNOME Tagger')
        aboutdialog.set_copyright('Copyright \xc2\xa9 2013 Pierre-Yves Chibon')
        aboutdialog.set_authors(authors)
        #aboutdialog.set_documenters(documenters)
        aboutdialog.set_comments('Tag the Fedora packages and win badges!')
        aboutdialog.set_license('GPLv2 or any later version at your choice')
        aboutdialog.set_website('http://github.com/fedora-infra/gnome-tagger')
        aboutdialog.set_website_label('GNOME Tagger Website')

        # we do not want to show the title, which by default would be 'About AboutDialog Example'
        # we have to reset the title of the messagedialog window after setting the program name
        aboutdialog.set_title('')

        # to close the aboutdialog when 'close' is clicked we connect the
        # 'response' signal to on_close
        aboutdialog.connect('response', self.on_close)
        # show the aboutdialog
        aboutdialog.show()

    def on_close(self, action, parameter=None):
        """ Called to close the about dialog. """
        action.destroy()

    def win_close(self, action, window):
        """ Called to close the statistics window. """
        window.destroy()

    def refresh_stats(self, action, window, grid):
        """ Refresh the statistics on the statistics window. """
        print "refresh_stats"
        cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_root_window().set_cursor(cursor)
        Gdk.flush()

        data = requests.get(TAGGERAPI + '/statistics/')
        jsondata = json.loads(data.text)
        self.statistics = jsondata['summary']

        listmodel = Gtk.ListStore(str, str)
        listmodel.append(['Total number of packages',
                         str(self.statistics['total_packages'])])
        listmodel.append(['Total number of tags',
                         str(self.statistics['total_unique_tags'])])
        listmodel.append(['Packages with no tags',
                         str(self.statistics['no_tags'])])
        listmodel.append(['Packages with tags',
                         str(self.statistics['with_tags'])])
        listmodel.append(['Average tags per package',
                         '%.3f' % self.statistics['tags_per_package']])
        listmodel.append(['Average tags per package (that have at least one tag)',
                         '%.4f' % self.statistics['tags_per_package_no_zeroes']])

        # a treeview to see the data stored in the model
        view = Gtk.TreeView(model=listmodel)
        view.set_headers_visible(False)
        # for each column
        for i in range(2):
            # cellrenderer to render the text
            cell = Gtk.CellRendererText()
            # the text in the first column should be in boldface
            if i == 0:
                cell.props.weight_set=True
                cell.props.weight=Pango.Weight.BOLD
            # the column is created
            col = Gtk.TreeViewColumn('', cell, text=i)
            # and it is appended to the treeview
            view.append_column(col)

        # a grid to attach the widgets
        grid.attach(view, 0, 0, 6, 1)

        cursor = Gdk.Cursor.new(Gdk.CursorType.ARROW)
        self.get_root_window().set_cursor(cursor)
        window.show_all()


class GnomeTagger(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        win = GnomeTaggerWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        # create a menu
        menu = Gio.Menu()
        # append to the menu three options
        menu.append('Preferences', 'app.preference')
        menu.append('About', 'app.about')
        menu.append('Quit', 'app.quit')
        # set the menu as menu of the application
        self.set_app_menu(menu)

        # option 'preference'
        new_action = Gio.SimpleAction.new('preference', None)
        new_action.connect('activate', self.preference_action)
        self.add_action(new_action)

        # option 'quit'
        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.quit_action)
        self.add_action(quit_action)

    # callback function for 'new'
    def preference_action(self, action, parameter):
        print 'preference clicked'

    # callback function for 'quit'
    def quit_action(self, action, parameter):
        print 'You have quit.'
        self.quit()


def main():
    """ Main function. """
    app = GnomeTagger()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == '__main__':
    main()

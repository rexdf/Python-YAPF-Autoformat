"""
@name     Python-YAPF-Autoformat
@package  sublime_plugin
@author   rexdf

"""
import sublime
import sublime_plugin
import tempfile
import configparser
import os
import subprocess

if sublime.platform() == 'windows':
    USER_CONFIG_NAME = 'YAPF.sublime-settings'
else:
    USER_CONFIG_NAME = 'YAPF.sublime-settings'


def get_settings(name, default):
    """Return value by name from user settings."""
    view = sublime.active_window().active_view()
    project_config = view.settings().get('pythonyapf', {})
    global_config = sublime.load_settings(USER_CONFIG_NAME)
    return project_config.get(name, global_config.get(name, default))


def save_style_to_tempfile(in_dict):
    """
    Take a dictionary of yapf style settings and return the file
    name of a tempfile containing the expected config formatted
    style settings
    """
    cfg = configparser.ConfigParser()
    cfg['style'] = in_dict
    fobj, filename = tempfile.mkstemp(suffix=".cfg")
    print(fobj)
    cfg.write(os.fdopen(fobj, "w"))
    return filename


class PyapfCommand(sublime_plugin.TextCommand):
    """Call yapf from system."""
    view = None
    debug = False

    def save_selection_to_tempfile(self, selection):
        """
        dump the current selection to a tempfile
        and return the filename.  caller is responsible
        for cleanup.
        """
        fobj, filename = tempfile.mkstemp(suffix=".py")
        encoded = self.view.substr(selection)
        with os.fdopen(fobj, 'w') as f:
            f.write(encoded)
        return filename

    def run(self, edit):
        """Plugin trigger."""
        self.debug = get_settings('debug', False)
        for region in self.view.sel():
            if region.empty():
                if get_settings("use_entire_file_if_no_selection", True):
                    selection = sublime.Region(0, self.view.size())
                else:
                    sublime.error_message('A selection is required')
                    selection = None
            else:
                selection = region

            if selection:
                py_filename = self.save_selection_to_tempfile(selection)

                if py_filename:
                    style_filename = save_style_to_tempfile(
                        get_settings("config", {}))

                    yapf = os.path.expanduser(
                        get_settings("yapf_command", "/usr/local/bin/yapf"))

                    cmd = [yapf, "--style={0}".format(style_filename),
                           "--verify", "--in-place", py_filename]

                    print('Running {0}'.format(cmd))
                    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

                    output, output_err = proc.communicate()

                    with open(py_filename, "r") as f:
                        output = f.read()

                    if not output_err:
                        self.view.replace(edit, selection, output)
                    else:
                        try:
                            print(output_err)

                        # Catching too general exception
                        # pylint: disable=W0703
                        except Exception as err:
                            print('Unable to parse %r', err)
                            sublime.error_message(output_err)

                    if self.debug:
                        with open(style_filename) as file_handle:
                            print(file_handle.read())

                    os.unlink(py_filename)
                os.unlink(style_filename)

        print('restoring cursor to ', region, repr(region))
        self.view.show_at_center(region)

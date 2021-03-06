import json
import mdpopups
import os
import plistlib
import sublime
import sublime_plugin
from time import time
import webbrowser


settings = {}
TOOLTIP_DATA = None
SETTINGS_FILE = None
INDENT_STYLE = None
INDENT_STYLE_ALLMAN = None
INDENT_STYLE_K_AND_R = None
SL_WIKI_LINK = None


def plugin_loaded():

    global settings
    global TOOLTIP_DATA
    global SETTINGS_FILE
    global INDENT_STYLE
    global INDENT_STYLE_ALLMAN
    global INDENT_STYLE_K_AND_R
    global SL_WIKI

    SETTINGS_FILE = 'LSL.sublime-settings'
    INDENT_STYLE = os.path.join(sublime.packages_path(), 'User', 'LSL_indent_style.tmPreferences')
    INDENT_STYLE_ALLMAN = sublime.load_resource('Packages/LSL/metadata/LSL_indent_style.tmPreferences.allman')
    INDENT_STYLE_K_AND_R = sublime.load_resource('Packages/LSL/metadata/LSL_indent_style.tmPreferences.k_and_r')
    SL_WIKI = 'https://wiki.secondlife.com/w/index.php?title=Special:Search&go=Go&search='

    try:
        settings = sublime.load_settings(SETTINGS_FILE)
    except Exception as e:
        print(e)

    if not os.path.exists(INDENT_STYLE):
        with open(INDENT_STYLE, mode='w', newline='\n') as file:
            file.write(INDENT_STYLE_ALLMAN)

    try:
        TOOLTIP_DATA = json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_float.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_integer.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_integer_boolean.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_rotation.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_string.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/constant_vector.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/control_conditional.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/control_flow.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/control_loop.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/event.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/function.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/keyword.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/state.json'))
        TOOLTIP_DATA += json.loads(sublime.load_resource('Packages/LSL/other/tooltips/storage_type.json'))
    except Exception as e:
        print(e)

# TODO: add to "mdpopups.sublime_user_lang_map", not replace it
#
#       pref = sublime.load_settings('Preferences.sublime-settings')
#       pref.set('mdpopups.use_sublime_highlighter', True)
#       pref.set('mdpopups.sublime_user_lang_map', { 'lsl': [['lsl'], ['LSL/syntaxes/LSL']] } )
#       sublime.save_settings(pref)


class ChangeEditorSchemeCommand(sublime_plugin.WindowCommand):

    _is_checked = False

    def __init__(self, view):
        self._is_checked = settings.has('color_scheme')

    def run(self):
        if self._is_checked:
            settings.erase('color_scheme')
        else:
            settings.set('color_scheme', 'Packages/LSL/other/LSL.hidden-tmTheme')
        sublime.save_settings(SETTINGS_FILE)
        self._is_checked = not self._is_checked

    def is_checked(self):
        return self._is_checked


class ChangeStyleCommand(sublime_plugin.WindowCommand):

    _is_checked = False

    def __init__(self, view):
        if os.path.exists(INDENT_STYLE):
            pl = plistlib.readPlist(INDENT_STYLE)
            self._is_checked = (pl['name'] == 'Indent Style - K & R')

    def run(self):
        if self._is_checked:
            with open(INDENT_STYLE, mode='w', newline='\n') as file:
                file.write(INDENT_STYLE_ALLMAN)
        else:
            with open(INDENT_STYLE, mode='w', newline='\n') as file:
                file.write(INDENT_STYLE_K_AND_R)
        self._is_checked = not self._is_checked

    def is_checked(self):
        return self._is_checked


class Lsl(sublime_plugin.EventListener):

    def on_navigate(self, link):
        webbrowser.open_new_tab(link)

    def on_hide(self, view):
        mdpopups.hide_popup(view)

    def on_hover(self, view, point, hover_zone):

        if view.settings().get('is_widget'):
            return

        if not view.settings().get('show_definitions'):
            return

        if hover_zone != sublime.HOVER_TEXT:
            return

        if not view.score_selector(point, 'source.lsl'):
            return

        word = view.substr(view.word(point))

        if not word:
            return

        if TOOLTIP_DATA is None:
            return

        try:
            tooltipRows = []
            for result in TOOLTIP_DATA:
                if result.get('name', None) == word:
                    if 'type' in result or result['name'].startswith('ll'):
                        tooltipRows.append('### (%s) <a href="%s%s">%s</a>' % (result.get('type', 'void'), SL_WIKI, result['name'], result['name']))
                    else:
                        tooltipRows.append('### <a href="%s%s">%s</a>' % (SL_WIKI, result['name'], result['name']))
                    if 'value' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('**Value**: %s' % str(result['value']))
                    if 'version' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('**SL server version**: %s' % result['version'])
                    if 'status' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('<body class="danger">**Status**: %s</body>' % result['status'])
                    if 'delay' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('**Delay**: %s' % str(result['delay']))
                    if 'energy' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('**Energy**: %s' % str(result['energy']))
                    if 'param' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('#### Parameters')
                        if type(result['param']) is dict:
                            tooltipRows.append('* (%s) **%s**' % (result['param']['type'], result['param']['name']))
                        elif type(result['param']) is list:
                            for param in result['param']:
                                tooltipRows.append('* (%s) **%s**' % (param['type'], param['name']))
                    if 'description' in result:
                        tooltipRows.append(' ')
                        tooltipRows.append('#### Description')
                        tooltipRows.append(' ')
                        tooltipRows.append('%s' % result['description']['en_US'])
                    if 'snippets' in result:
                        tooltipRows.append('#### Snippets')
                        for snippet in result['snippets']:
                            tooltipRows.append(' ')
                            tooltipRows.append('```lsl')
                            tooltipRows.append('%s' % snippet)
                            tooltipRows.append('```')
            if 0 < len(tooltipRows):
                mdpopups.show_popup(view, '\n'.join(tooltipRows),
                                    flags=(sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HIDE_ON_MOUSE_MOVE_AWAY),
                                    location=point,
                                    wrapper_class='lsl',
                                    max_width=1280,
                                    max_height=960,
                                    on_navigate=self.on_navigate,
                                    on_hide=self.on_hide(view)
                )
                return
        except Exception as e:
            print(e)

        mdpopups.hide_popup(view)

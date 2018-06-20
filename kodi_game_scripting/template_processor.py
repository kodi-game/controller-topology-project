#!/usr/bin/env python3

# Copyright (C) 2016 Christian Fetzer
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Process Jinja2 templates """

import os
import re
import shutil
import xml.etree.ElementTree
import xmljson

import jinja2

from . import utils

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'templates')


class TemplateProcessor:
    """ Process Jinja2 templates """

    @classmethod
    def process(cls, template_dir, destination, template_vars):
        """ Process templates """

        class _TreeUndefined(jinja2.Undefined):
            def __getitem__(self, key):
                return self

            def __getattr__(self, key):
                return self

        template_dir = os.path.join(TEMPLATE_DIR, template_dir)
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
            undefined=_TreeUndefined)

        def surround(items, string, prepend=True, append=True):
            """ Surrounds each element in a list by the given string """
            return ['{}{}{}'.format(string if prepend is True else '', element,
                                    string if append is True else '')
                    for element in items]
        template_env.filters["surround"] = surround

        def regex_replace(string, find, replace, multiline=False):
            """ Replaces regex in string """
            flags = 0
            if multiline:
                flags += re.MULTILINE
            return re.sub(find, replace, string, flags=flags)
        template_env.filters["regex_replace"] = regex_replace

        def get_list(value):
            """ Returns a list (existing list or new single elemented list) """
            return value if isinstance(value, list) else [value]
        template_env.filters["get_list"] = get_list

        # Loop over all templates
        for infile in utils.list_all_files(template_dir):

            # Files may have templatized names
            if '{{' in infile and '}}' in infile:
                outfile = jinja2.Template(infile).render(template_vars)
            else:
                outfile = infile
            outfile_name, extension = os.path.splitext(outfile)

            # Create directories if necessary
            utils.ensure_directory_exists(
                os.path.dirname(os.path.join(destination, outfile)))

            # Files that end with .j2 are templates
            if extension == '.j2':
                print("  Generating {}".format(outfile_name))
                outfile_path = os.path.join(destination, outfile_name)

                # Make content of already existing XML files available in
                # the template. That way templates can decide what data to keep
                # or override.
                if '.xml' in infile and os.path.isfile(outfile_path):
                    with open(outfile_path, 'r') as xmlfile_ctx:
                        xml_content = xmlfile_ctx.read()

                    # Remove variables from xml.in files
                    xml_content = re.sub(r'@([A-Za-z0-9_]+)@', r'AT_\1_AT',
                                         xml_content)
                    xml_data = {}
                    try:
                        # Like Yahoo converter, but don't omit 'content' if
                        # there are no attributes.
                        converter = xmljson.XMLData(
                            xml_fromstring=False,
                            simple_text=False,
                            text_content="content"
                        )
                        root = xml.etree.ElementTree.fromstring(xml_content)
                        xml_data = converter.data(root)

                        # Parsed XML Data will contain OrderedDict() as empty
                        # value which converts to 'OrderedDict()' instead of ''
                        # in the templates. Remove empty fields instead.
                        xml_data = utils.purify(xml_data)
                    except xml.etree.ElementTree.ParseError as err:
                        print("Failed to parse {}: {}".format(
                            outfile_path, err))
                    template_vars.update({'xml': xml_data})

                # Make the datetime of strings files the existing datetime
                if '.po' in infile and os.path.isfile(outfile_path):
                    with open(outfile_path, 'r') as stringsfile_ctx:
                        strings_content = stringsfile_ctx.read()

                    datere = re.compile(r'"POT-Creation-Date: (.*)\\n"')
                    try:
                        timestamp = datere.search(strings_content).group(1)
                        template_vars.update({'datetime': timestamp})
                    except AttributeError:
                        raise

                template = template_env.get_template(infile)
                content = template.render(template_vars)
                if content:
                    with open(outfile_path, 'w') as outfile_ctx:
                        outfile_ctx.write(content)

            # Other files are just copied
            else:
                print("     Copying {}{}".format(outfile_name, extension))
                shutil.copyfile(os.path.join(template_dir, infile),
                                os.path.join(destination, outfile))

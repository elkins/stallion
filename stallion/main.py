"""
.. module:: main
   :platform: Unix, Windows
   :synopsis: Main Stallion entry-point.

.. moduleauthor:: Christian S. Perone <christian.perone@gmail.com>

:mod:`main` -- main Stallion entry-point
==================================================================
"""
import warnings

import requests

# Suppress pkg_resources and other deprecation warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*pkg_resources is deprecated.*')
warnings.filterwarnings('ignore', category=DeprecationWarning)

from optparse import OptionParser

try:
    from importlib import reload
except ImportError:
    # For older Python 3 versions (< 3.4)
    from imp import reload

import sys
import platform
import logging
import os

try:
    import xmlrpclib
except ImportError:
    # Python 3 compatibility
    import xmlrpc.client as xmlrpclib

# Use the full compatibility layer instead of direct modern imports
from stallion.compat import get_distribution, working_set, parse_version, iter_entry_points

from flask import Flask, render_template, url_for, jsonify
from docutils.core import publish_parts

import stallion
from stallion import metadata

app = Flask(__name__)

# Change from XML-RPC to base URL
PYPI_BASE_URL = 'https://pypi.org'

# This is a cache with flags to show if a distribution has an update available
DIST_PYPI_CACHE = set()


class Crumb(object):
    """ Represents each level on the bootstrap breadcrumb. """
    def __init__(self, title, href='#'):
        """ Instatiates a new breadcrum level.

        :param title: the title
        :param href: the link
        """
        self.title = title
        self.href = href


def get_shared_data():
    """ Returns a new dictionary with the shared-data between different
    Stallion views (ie. a list of distribution packages).

    :rtype: dict
    :return: the dictionary with the shared data.
    """
    print("DEBUG: Building shared data using compatibility layer")
    try:
        distributions = list(working_set)
        print(f"DEBUG: Found {len(distributions)} distributions in working set")

        shared_data = {
            'pypi_update_cache': DIST_PYPI_CACHE,
            'distributions': distributions
        }
        return shared_data
    except Exception as e:
        print(f"DEBUG: Error building shared data: {e}")
        # Return minimal shared data on error
        return {
            'pypi_update_cache': set(),
            'distributions': []
        }


def get_pypi_proxy():
    """Legacy function - kept for compatibility but not used"""
    print("DEBUG: XML-RPC proxy requested but deprecated")
    # Return a dummy object that won't crash if called
    class DummyProxy:
        def package_releases(self, *args, **kwargs):
            raise Exception("XML-RPC API deprecated - use JSON API instead")
        def search(self, *args, **kwargs):
            raise Exception("XML-RPC API deprecated - use JSON API instead")
    return DummyProxy()


def get_pypi_releases(dist_name):
    """Modern replacement using PyPI JSON API instead of deprecated XML-RPC"""
    print(f"DEBUG: Getting PyPI releases for {dist_name} using JSON API")

    try:
        # Use PyPI's JSON API
        url = f"https://pypi.org/pypi/{dist_name}/json"
        response = requests.get(url)

        if response.status_code == 404:
            print(f"DEBUG: Package {dist_name} not found on PyPI")
            return []
        elif response.status_code != 200:
            print(f"DEBUG: PyPI API error for {dist_name}: {response.status_code}")
            return []

        data = response.json()
        releases = list(data.get('releases', {}).keys())

        # Filter out pre-releases and sort properly
        stable_releases = []
        for release in releases:
            # Skip pre-releases, betas, etc.
            if not any(identifier in release for identifier in ['a', 'b', 'rc', 'dev']):
                stable_releases.append(release)

        if stable_releases:
            stable_releases.sort(key=lambda v: parse_version(v), reverse=True)
            print(f"DEBUG: Found {len(stable_releases)} stable releases for {dist_name}, latest: {stable_releases[0]}")
            return stable_releases
        else:
            # Fallback to all releases if no stable ones found
            releases.sort(key=lambda v: parse_version(v), reverse=True)
            print(f"DEBUG: Found {len(releases)} releases for {dist_name}, latest: {releases[0]}")
            return releases

    except Exception as e:
        print(f"DEBUG: Error getting PyPI releases for {dist_name}: {e}")
        return []


def get_pypi_search(spec, operator='or'):
    """Modern replacement using PyPI JSON search API"""
    print(f"DEBUG: Searching PyPI with spec: {spec}")

    try:
        # PyPI's JSON search API
        url = "https://pypi.org/search/"
        params = {
            'q': spec.get('name', '') if isinstance(spec, dict) else spec,
            'format': 'json'
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"DEBUG: PyPI search API error: {response.status_code}")
            return []

        data = response.json()
        results = []

        for item in data.get('results', []):
            results.append({
                'name': item.get('name', ''),
                'version': item.get('version', ''),
                'summary': item.get('summary', ''),
                '_pypi_ordering': item.get('score', 0)
            })

        results.sort(key=lambda v: v['_pypi_ordering'], reverse=True)
        print(f"DEBUG: Found {len(results)} search results")
        return results

    except Exception as e:
        print(f"DEBUG: Error searching PyPI: {e}")
        return []

@app.route('/pypi/check_update/<dist_name>')
def check_pypi_update(dist_name):
    """ Just check for updates and return a json with the attribute "has_update".

    :param dist_name: distribution name
    :rtype: json
    :return: json with the attribute "has_update"
    """
    print(f"DEBUG: Checking update for {dist_name}")
    try:
        pkg_dist = get_distribution(dist_name)
        pkg_dist_version = pkg_dist.version
        pypi_rel = get_pypi_releases(dist_name)

        if pypi_rel:
            pypi_last_version = parse_version(pypi_rel[0])
            current_version = parse_version(pkg_dist_version)

            if pypi_last_version > current_version:
                DIST_PYPI_CACHE.add(dist_name.lower())
                print(f"DEBUG: Update available for {dist_name}: {pypi_rel[0]} > {pkg_dist_version}")
                return jsonify({"has_update": 1})

        try:
            DIST_PYPI_CACHE.remove(dist_name.lower())
        except KeyError:
            pass

        print(f"DEBUG: No update for {dist_name}")
        return jsonify({"has_update": 0})
    except Exception as e:
        print(f"DEBUG: Error checking update for {dist_name}: {e}")
        return jsonify({"has_update": 0, "error": str(e)})


@app.route('/pypi/releases/<dist_name>')
def releases(dist_name):
    """ This is the /pypi/releases/<dist_name> entry point, it is the interface
    between Stallion and the PyPI RPC service when checking for updates.

    :param dist_name: the package name (distribution name).
    """
    print(f"DEBUG: Showing releases for {dist_name}")
    try:
        pkg_dist = get_distribution(dist_name)

        data = {}

        pkg_dist_version = pkg_dist.version
        pypi_rel = get_pypi_releases(dist_name)

        data["dist_name"] = dist_name
        data["pypi_info"] = pypi_rel
        data["current_version"] = pkg_dist_version

        if pypi_rel:
            pypi_last_version = parse_version(pypi_rel[0])
            current_version = parse_version(pkg_dist_version)
            last_version = pkg_dist_version.lower() != pypi_rel[0].lower()

            data["last_is_great"] = pypi_last_version > current_version
            data["last_version_differ"] = last_version

            if data["last_is_great"]:
                DIST_PYPI_CACHE.add(dist_name.lower())
            else:
                try:
                    DIST_PYPI_CACHE.remove(dist_name.lower())
                except KeyError:
                    pass

        print(f"DEBUG: Successfully prepared release data for {dist_name}")
        return render_template('pypi_update.html', **data)
    except Exception as e:
        print(f"DEBUG: Error in releases for {dist_name}: {e}")
        return f"Error loading releases for {dist_name}: {e}", 500


@app.route('/')
def index():
    """ The main Flask entry-point (/) for the Stallion server. """
    print("DEBUG: Rendering index page")
    try:
        data = {'breadpath': [Crumb('Main')]}

        data.update(get_shared_data())
        data['menu_home'] = 'active'

        sys_info = {'Python Platform': sys.platform,
                    'Python Version': sys.version,
                    'Python Prefix': sys.prefix,
                    'Machine Type': platform.machine(),
                    'Platform': platform.platform(),
                    'Processor': platform.processor()}

        try:
            sys_info['Python Implementation'] = platform.python_implementation()
        except AttributeError:
            sys_info['Python Implementation'] = 'Unknown'

        sys_info['System'] = platform.system()
        sys_info['System Arch'] = platform.architecture()

        data['system_information'] = sys_info

        print("DEBUG: Successfully rendered index page")
        return render_template('system_information.html', **data)
    except Exception as e:
        print(f"DEBUG: Error rendering index page: {e}")
        return f"Error loading index: {e}", 500


@app.route('/console_scripts')
def console_scripts():
    """ Entry point for the global console scripts """
    print("DEBUG: Rendering console scripts page")
    try:
        data = {}
        data.update(get_shared_data())
        data['menu_console_scripts'] = 'active'
        data['breadpath'] = [Crumb('Console Scripts')]

        # Use compatibility layer for entry points
        entry_console = list(iter_entry_points('console_scripts'))
        data['scripts'] = entry_console

        print(f"DEBUG: Found {len(entry_console)} console scripts")
        return render_template('console_scripts.html', **data)
    except Exception as e:
        print(f"DEBUG: Error rendering console scripts: {e}")
        return f"Error loading console scripts: {e}", 500


@app.route('/about')
def about():
    """ The About entry-point (/about) for the Stallion server. """
    print("DEBUG: Rendering about page")
    try:
        data = {}
        data.update(get_shared_data())
        data['menu_about'] = 'active'

        data['breadpath'] = [Crumb('About')]
        data['version'] = stallion.__version__
        data['author'] = stallion.__author__
        data['author_url'] = stallion.__author_url__

        print("DEBUG: Successfully rendered about page")
        return render_template('about.html', **data)
    except Exception as e:
        print(f"DEBUG: Error rendering about page: {e}")
        return f"Error loading about page: {e}", 500


@app.route('/distribution/<dist_name>')
def distribution(dist_name=None):
    """ The Distribution entry-point (/distribution/<dist_name>)
    for the Stallion server.

    :param dist_name: the package name
    """
    print(f"DEBUG: Rendering distribution page for {dist_name}")
    try:
        # This now uses the compatibility layer - returns legacy-compatible object
        pkg_dist = get_distribution(dist_name)
        print(f"DEBUG: Retrieved distribution: {pkg_dist.project_name} {pkg_dist.version}")

        data = {}
        data.update(get_shared_data())

        data['dist'] = pkg_dist
        data['breadpath'] = [Crumb('Main', url_for('index')),
                             Crumb('Package'), Crumb(pkg_dist.project_name)]

        settings_overrides = {
            'raw_enabled': 0,  # no raw HTML code
            'file_insertion_enabled': 0,  # no file/URL access
            'halt_level': 2,  # at warnings or errors, raise an exception
            'report_level': 5,  # never report problems with the reST code
        }

        # Use original metadata parsing - compatibility layer makes this work
        print(f"DEBUG: Reading metadata for {dist_name}")
        try:
            pkg_metadata = pkg_dist.get_metadata(metadata.METADATA_NAME)
            parsed, key_known = metadata.parse_metadata(pkg_metadata)
            distinfo = metadata.metadata_to_dict(parsed, key_known)
            print(f"DEBUG: Successfully parsed metadata for {dist_name}")
        except Exception as e:
            print(f"DEBUG: Error parsing metadata for {dist_name}: {e}")
            # Fallback to basic info
            distinfo = {
                'Name': pkg_dist.project_name,
                'Version': pkg_dist.version,
                'Summary': '',
                'Description': '',
            }

        parts = None
        try:
            description = distinfo.get('Description', '')
            if description:
                print(f"DEBUG: Rendering description for {dist_name} (length: {len(description)})")
                parts = publish_parts(source=description,
                                      writer_name='html',
                                      settings_overrides=settings_overrides)
        except Exception as e:
            print(f"DEBUG: Error rendering description for {dist_name}: {e}")

        data['distinfo'] = distinfo

        # Use legacy-compatible entry map method
        data['entry_map'] = pkg_dist.get_entry_map()
        print(f"DEBUG: Found {sum(len(eps) for eps in data['entry_map'].values())} entry points across {len(data['entry_map'])} groups")

        if parts is not None:
            data['description_render'] = parts['body']
            print(f"DEBUG: Successfully rendered description for {dist_name}")
        else:
            print(f"DEBUG: No description rendered for {dist_name}")

        print(f"DEBUG: Successfully rendered distribution page for {dist_name}")
        return render_template('distribution.html', **data)

    except Exception as e:
        print(f"DEBUG: Error rendering distribution page for {dist_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading distribution {dist_name}: {e}", 500


def run_main():
    """ The main entry-point of Stallion. """

    print('Stallion %s - Python Package Manager' % (stallion.__version__,))
    print('By %s 2013\n' % (stallion.__author__,))
    print('DEBUG: Starting Stallion with Python %s' % sys.version)
    print('DEBUG: Using compatibility layer for package management')

    parser = OptionParser()

    parser.add_option('-s', '--host', dest='host',
                    help='The hostname to listen on, ' \
                         'set to \'0.0.0.0\' to have the '
                         'server available externally as well. '
                         'Default is \'127.0.0.1\' (localhost only).',
                    metavar="HOST", default='127.0.0.1')

    parser.add_option('-d', '--debug', action='store_true',
                  help='Start Stallion in Debug mode (useful to report bugs).',
                  dest='debug', default=False)

    parser.add_option('-r', '--reloader', action='store_true',
                  help='Uses the reloader.', dest='reloader', default=False)

    parser.add_option('-i', '--interactive', action='store_true',
                  help='Enable the interactive interpreter' \
                       ' for debugging (useful to debug errors).',
                  dest='evalx', default=False)

    parser.add_option('-p', '--port', dest='port',
                    help='The port to listen on. ' \
                         'Default is the port \'5000\'.',
                    metavar="PORT", default='5000')

    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                    help='Turn on verbose messages (show HTTP requests).' \
                         ' Default is False.',
                    default=False)

    parser.add_option('-w', '--web-browser', dest='web_browser', action='store_true',
                    help='Open a web browser to show Stallion.' \
                         ' Default is False.',
                    default=False)

    (options, args) = parser.parse_args()

    if not options.verbose:
        print(" * Running on http://%s:%s/" % (options.host, options.port))
        print(" * Debug mode: %s" % options.debug)
        print(" * Reloader: %s" % options.reloader)
        werk_log = logging.getLogger('werkzeug')
        werk_log.setLevel(logging.WARNING)

    if options.web_browser:
        import webbrowser
        print("DEBUG: Opening web browser")
        webbrowser.open('http://%s:%s/' % (options.host, options.port))

    print("DEBUG: Starting Flask application with compatibility layer...")
    try:
        app.run(debug=options.debug, host=options.host, port=int(options.port),
                use_evalex=options.evalx, use_reloader=options.reloader)
    except Exception as e:
        print(f"DEBUG: Error starting Flask application: {e}")
        raise

if __name__ == '__main__':
    run_main()

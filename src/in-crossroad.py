#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file is part of crossroad.
# Copyright (C) 2013 Jehan <jehan at girinstud.io>
#
# crossroad is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# crossroad is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with crossroad.  If not, see <http://www.gnu.org/licenses/>.

import importlib.machinery
import subprocess
import inspect
import os.path
import sys
import re

### Current Crossroad Environment ###
crossroad_platform = None
try:
    crossroad_platform = os.environ['CROSSROAD_PLATFORM']
except KeyError:
    sys.stderr.write('Error: no Crossroad environment found. Contact the developers.')
    sys.exit(os.EX_DATAERR)

### Check all available platforms. ###

# This string will be replaced by the setup.py at installation time,
# depending on where you installed default data.
install_datadir = os.path.join(os.path.abspath('@DATADIR@'), 'share/')

xdg_data_home = None
try:
    xdg_data_home = os.environ['XDG_DATA_HOME']
except KeyError:
    # os.path.expanduser will first check the $HOME env variable, then the current user home.
    # It is cleverer than checking the environment variable only.
    home_dir = os.path.expanduser('~')
    if home_dir != '~':
        xdg_data_home = os.path.join(home_dir, '.local/share')

def get_datadirs():
    '''
    {datadir} is evaluated using XDG rules.
    '''
    # User personal script have priority.
    if xdg_data_home is not None:
        datadirs = [xdg_data_home]
    else:
        datadirs = []

    # Then installation-time files.
    datadirs += [install_datadir]

    # Finally platform global files.
    try:
        other_datadirs = os.environ['XDG_DATA_HOME']
        if other_datadirs.strip() == '':
            datadirs += ['/usr/local/share/', '/usr/share/']
        else:
            datadirs += other_datadirs.split(':')
    except KeyError:
        datadirs += ['/usr/local/share/', '/usr/share/']
    return datadirs

def load_platform(platform_name):
    '''
    All platforms are available in {datadir}/crossroads/platforms/.
    '''
    datadirs = get_datadirs()
    platform_file = None
    for dir in datadirs:
        # XXX: rename win64.py in w64.py OR load each and check name?
        f = os.path.abspath(os.path.join (dir, 'crossroad/platforms', platform_name + '.py'))
        if os.path.exists(f):
            platform_file = f
            break
    if platform_file is None:
        return None
    # It is supposed to be a python script. Let's try and import it.
    loader = importlib.machinery.SourceFileLoader(platform_name, platform_file)
    try:
        platform = loader.load_module(platform_name)
    except (ImportError, FileNotFoundError):
        return None
    try:
        if not platform.is_available():
            return None
    except AttributeError:
        # not a valid platform.
        return None
    return platform

platform = load_platform(crossroad_platform)
if platform is None:
    sys.stderr.write('Error: the current crossroad environment does not seem to exist. Contact the developers.')
    sys.exit(os.EX_DATAERR)

commands = [command[10:] for command in dir(platform) if command[:10] == 'crossroad_' and callable(getattr(platform, command))]

program = 'crossroad'
version = '@VERSION@'
maintainer = 'jehan at girinstud.io'

usage = 'Usage: {} [--help] [--version] <command> [<args>]'.format(program)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stdout.write('{} version {} <{}>\n'.format(program, version, maintainer))
        sys.stdout.write(usage + '\n')
        sys.exit(os.EX_USAGE)
    command = None
    command_name = None
    command_args = []
    command_kwargs = {}
    command_kwarg_no_value = None
    usage_error = False
    show_help = False
    if crossroad_platform == 'arm' or \
       crossroad_platform == 'arm-gnu':
        install_prefix='/usr/'
    else:
        install_prefix='$CROSSROAD_PREFIX'
    for arg in sys.argv[1:]:
        if command is not None:
            if arg[:2] == '--':
                # TODO: support not boolean options too.
                command_fun = getattr(platform, 'crossroad_' + command)
                (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations) = inspect.getfullargspec(command_fun)
                command_kwarg = arg[2:].replace('-', '_')
                command_arg = None
                command_arg_value = None
                if command_kwarg.find('=') != -1:
                  eq_pos = command_kwarg.find('=')
                  command_arg = command_kwarg[:eq_pos]
                  command_arg_value = command_kwarg[eq_pos+1:]
                  command_kwarg = None
                else:
                  command_arg = command_kwarg
                if command_kwarg is not None and command_kwarg in kwonlyargs:
                    command_kwargs[command_kwarg] = True
                elif command_arg is not None and command_arg in args:
                    if command_arg_value is not None:
                      command_kwargs[command_arg] = command_arg_value
                    else:
                      command_kwarg_no_value = command_arg
                else:
                    command_usage = '{} {}'.format(program, command_name)
                    for positional_arg in args:
                        sig = inspect.signature(command_fun)
                        if sig.parameters[positional_arg].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and \
                           sig.parameters[positional_arg].annotation == str:
                          # Process it as a keyword argument.
                          command_usage += ' [--{}={}]'.format(positional_arg, sig.parameters[positional_arg].default)
                        else:
                          command_usage += ' <{}>'.format(positional_arg)
                    if varargs is not None:
                        command_usage += ' <{}...>'.format(varargs)
                    for option in kwonlyargs:
                        command_usage += ' [--{}]'.format(option)
                    if command_fun.__doc__ is not None:
                        command_usage += '\n{}\n'.format(command_fun.__doc__)
                    else:
                        command_usage += '\n'
                    sys.stderr.write(command_usage)
                    sys.exit(os.EX_USAGE)
            else:
                if command_kwarg_no_value is not None:
                    command_kwargs[command_kwarg_no_value] = arg
                else:
                    command_args.append(arg)
            continue
        elif show_help:
            if arg.replace('-', '_') in commands:
                command_fun = getattr(platform, 'crossroad_' + arg.replace('-', '_'))
                (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations) = inspect.getfullargspec(command_fun)
                command_usage = '{} {}'.format(program, arg)
                for positional_arg in args:
                    command_usage += ' <{}>'.format(positional_arg)
                    #if positional_arg in annotations and annotations[positional_arg] == list:
                    #    command_usage += '...'
                    #command_usage += '>'
                if varargs is not None:
                    command_usage += ' <{}...>'.format(varargs)
                for option in kwonlyargs:
                    command_usage += ' [--{}]'.format(option.replace('_', '-'))
                if command_fun.__doc__ is not None:
                    command_usage += '\n{}\n'.format(command_fun.__doc__)
                else:
                    command_usage += '\n'
                sys.stdout.write(command_usage)
                sys.exit(os.EX_OK)
            else:
                sys.stderr.write('Unknown option for the "help" command: {}\n'.format(arg))
                sys.exit(os.EX_USAGE)
        elif arg == '-v' or arg == '--version' or arg == 'version':
            sys.stdout.write('{} version {} <{}>\n'.format(program, version, maintainer))
            sys.exit(os.EX_OK)
        elif arg == '-h' or arg == '--help' or arg == 'help':
            show_help = True
            continue
        #elif arg == 'prefix':
            #prefix = os.path.join(xdg_data_home, 'crossroad/roads', crossroad_platform)
            #sys.stdout.write(prefix)
            #sys.exit(os.EX_OK)
        elif arg == 'configure' or arg.endswith('/configure'):
            conf_dir = os.path.dirname(arg)
            if conf_dir == '':
                conf_dir = '.'
            if not os.path.exists(conf_dir):
                sys.stderr.write('Error: directory "{}" does not exist.\n'.format(conf_dir))
                sys.exit(os.EX_NOINPUT)
            if hasattr(platform, 'preconfigure'):
                sys.stdout.write('Running pre-configure script.\n')
                platform.preconfigure()
            if not os.path.exists(arg) and os.path.exists(os.path.join(conf_dir, 'autogen.sh')):
                if arg == 'configure' or arg == './configure':
                    sys.stderr.write('Warning: there is no ./configure script in the current directory, but there is an autogen.sh. Running it first.\n')
                else:
                    sys.stderr.write('Warning: there is no configure script in "{}", but there is an autogen.sh. Running it first.\n'.format(conf_dir))
                # autogen.sh is usually not meant to handle VPATH builds. Better cd to it first.
                cwd = os.getcwd()
                os.chdir(conf_dir)

                arg_pos = sys.argv.index(arg)
                # NOTE: some projects would configure their autogen.sh to actually run ./configure
                # Though I'd prefer not to run ./configure if possible, because that would make it twice.
                # Some projects (in GNOME projects at least) use $NOCONFIGURE env variable. So I set it.
                command = './autogen.sh ' + ' '.join(sys.argv[arg_pos + 1:])
                environ = os.environ
                environ['NOCONFIGURE'] = '1'
                sys.stdout.write('crossroad info: running "{}"\n'.format(command))
                autogen_return = subprocess.call(command, shell=True, env=environ)
                # run autoreconf by hand if there is a configure.ac otherwise?
                os.chdir(cwd)
                if autogen_return != 0:
                    sys.stderr.write('autogen.sh failed.\n')
                    sys.exit(autogen_return)
            if not os.path.exists(arg):
                if arg == 'configure' or arg == './configure':
                    sys.stderr.write('Error: there is no ./configure script in the current directory.\n')
                else:
                    sys.stderr.write('Error: there is no configure script in "{}".\n'.format(conf_dir))
                sys.exit(os.EX_USAGE)
            # The position should normally be 2 since any other command or option before
            # would be an error. But just in case the logics evolve.
            configure = arg
            if arg == 'configure':
                configure = './configure'
            arg_pos = sys.argv.index(arg)
            # NOTE: with shell=True, subprocess does not deal well with list as a command.
            if crossroad_platform == 'native':
                command = '{} --prefix={} '.format(configure, install_prefix) + \
                          ' '.join(sys.argv[arg_pos + 1:])
            else:
                command = '{} --prefix={} --host=$CROSSROAD_HOST --build=$CROSSROAD_BUILD '.format(configure, install_prefix) + \
                          ' '.join(sys.argv[arg_pos + 1:])
            sys.stdout.write('crossroad info: running "{}"\n'.format(command))
            sys.exit(subprocess.call(command, shell=True))
        elif arg == 'scons':
            if hasattr(platform, 'preconfigure'):
                sys.stdout.write('Running pre-configure script.\n')
                platform.preconfigure()
            environ = os.environ
            set_CROSSROAD_PREFIX = False
            arg_pos = sys.argv.index(arg)
            for param in sys.argv[arg_pos + 1:]:
                # Checking if the user seems to have set the prefix.
                # Since there is no standard way to do so with scons,
                # we unfortunately can't force our prefix ourselves.
                if '$CROSSROAD_PREFIX' in param or \
                   environ['CROSSROAD_PREFIX'] in param:
                    set_CROSSROAD_PREFIX = True
                    break
            if not set_CROSSROAD_PREFIX:
                sys.stdout.write("WARNING: you don't seem to set a prefix in the command line.\n")
                sys.stdout.write('Check the options provided by the upstream developers with `scons --help` ')
                sys.stdout.write('(usually `--prefix=` or `prefix=`). ')
                sys.stdout.write('It is important to run scons with the appropriate $CROSSROAD_PREFIX prefix.\n')
                sys.stdout.write('Example: scons install --prefix=$CROSSROAD_PREFIX\n')
                run_scons = input('Run the command anyway? [y/N]: ')
                if run_scons.strip().lower() != 'y':
                    sys.stderr.write('Exiting\n')
                    sys.exit(os.EX_DATAERR)

            command = '{} '.format(arg) + ' '.join(sys.argv[arg_pos + 1:])

            if crossroad_platform != 'native':
                # It seems there is no cross-compilation rules for scons. But there
                # are some hacks commonly used across various projects using
                # environment values. So the following is very very hackish. It
                # works with libmypaint at least. Not sure how many other projects it
                # would fail with.
                environ['CC']    = environ['CROSSROAD_HOST'] + '-gcc'
                environ['CXX']   = environ['CROSSROAD_HOST'] + '-g++'
                environ['LD']    = environ['CROSSROAD_HOST'] + '-ld'
                environ['AR']    = environ['CROSSROAD_HOST'] + '-ar'
                environ['STRIP'] = environ['CROSSROAD_HOST'] + '-strip'
            sys.stdout.write('crossroad info: running "{}"\n'.format(command))
            sys.exit(subprocess.call(command, shell=True, env=environ))
        elif arg == 'cmake' or arg == 'ccmake':
            if hasattr(platform, 'preconfigure'):
                sys.stdout.write('Running pre-configure script.\n')
                platform.preconfigure()
            # The position should normally be 2 since any other command or option before
            # would be an error. But just in case the logics evolve.
            arg_pos = sys.argv.index(arg)
            if crossroad_platform == 'native':
                command = '{} -DCMAKE_INSTALL_PREFIX:PATH={} '.format(arg, install_prefix)
            else:
                command = '{} -DCMAKE_INSTALL_PREFIX:PATH={} -DCMAKE_TOOLCHAIN_FILE=$CROSSROAD_CMAKE_TOOLCHAIN_FILE '.format(arg, install_prefix)
            command += ' '.join(sys.argv[arg_pos + 1:])
            sys.stdout.write('crossroad info: running "{}"\n'.format(command))
            sys.exit(subprocess.call(command, shell=True))
        elif arg == 'meson':
            if hasattr(platform, 'preconfigure'):
                sys.stdout.write('Running pre-configure script.\n')
                platform.preconfigure()
            # The position should normally be 2 since any other command or option before
            # would be an error. But just in case the logics evolve.
            arg_pos = sys.argv.index(arg)
            if crossroad_platform == 'native':
                command = 'meson --prefix {} '.format(install_prefix)
            else:
                command = 'meson --prefix {} --cross-file=$CROSSROAD_MESON_TOOLCHAIN_FILE '.format(install_prefix)
            command += ' '.join(sys.argv[arg_pos + 1:])
            sys.stdout.write('crossroad info: running "{}"\n'.format(command))
            sys.exit(subprocess.call(command, shell=True))
        elif arg[:1] == '-':
            sys.stderr.write('Unknown option: {}\n{}\n'.format(arg, usage))
            sys.exit(os.EX_USAGE)
        elif arg.replace('-', '_') in commands:
            command = arg.replace('-', '_')
            command_name = arg
            continue
        else:
            sys.stderr.write('Unknown command: {}\n'.format(arg))
            show_help = True
            usage_error = True
            break

    if show_help:
        command_list = usage
        command_list += '\n\nAny crossroad environment provides the following commands:'
        command_list += '\n- {:<20} {}'.format('configure', 'Run `./configure` in the following directory for your cross-compilation environment.')
        command_list += '\n- {:<20} {}'.format('cmake', 'Run cmake for your cross-compilation environment.')
        command_list += '\n- {:<20} {}'.format('ccmake', 'Run ccmake for your cross-compilation environment.')
        command_list += '\n- {:<20} {}'.format('meson', 'Run meson for your cross-compilation environment.')
        command_list += '\n- {:<20} {}'.format('scons', 'Run scons for your cross-compilation environment.')

        #command_list += '\n- {:<20} {}'.format('prefix', 'Return the installation prefix.')

        command_list += '\n- {:<20} {}'.format('help', 'Print usage information.')
        command_list += "\n\nCrossroad's {} environment proposes the following commands:".format(crossroad_platform)
        for command in commands:
            command_fun = getattr(platform, 'crossroad_' + command)
            (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations) = inspect.getfullargspec(command_fun)
            if command_fun.__doc__ is not None:
                # shortdesc is the first line of the whole command description.
                shortdesc = command_fun.__doc__.strip()
                shortdesc = re.sub(r'\n.*', '', shortdesc)
                command_list += '\n- {:<20} {}'.format(command.replace('_', '-'), shortdesc)
            else:
                command_list += '\n{}'.format(command)
        command_list += '\n\nSee `crossroad help <command>` for more information on an environment-specific command.\n'
        sys.stdout.write(command_list)
        if usage_error:
            sys.exit(os.EX_USAGE)
        else:
            sys.exit(os.EX_OK)

    if command is None:
        sys.stdout.write('{} version {} <{}>\n'.format(program, version, maintainer))
        sys.stdout.write(usage + '\n')
        sys.exit(os.EX_USAGE)
    else:
        command_fun = getattr(platform, 'crossroad_' + command)
        (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations) = inspect.getfullargspec(command_fun)
        try:
          sys.exit(command_fun(*command_args, **command_kwargs))
        except KeyboardInterrupt:
          pass
        sys.exit(os.EX_OK)


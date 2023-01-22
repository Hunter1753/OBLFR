#!/usr/bin/env python3
#
# @file from https://github.com/Neutree/c_cpp_project_framework
# @author neucrack
#

import argparse
import os, sys

kconfig_lib_path = sys.path[0]+"/Kconfiglib"
sys.path.append(kconfig_lib_path)

import kconfiglib


def _cmake_contents(kconfig, header):
    chunks = [header]
    add = chunks.append
    config_vars = []
    for sym in kconfig.unique_defined_syms:
        # _write_to_conf is determined when the value is calculated. This
        # is a hidden function call due to property magic.
        val = sym.str_value
        # print("sym: " + sym.name + " val: " + val)
        if not sym._write_to_conf:
            continue
        if sym.orig_type in (kconfiglib.BOOL, kconfiglib.TRISTATE): 
            if val == "n":
                add("set({}{} 0)\n".format(
                    kconfig.config_prefix, sym.name))
            else:
                add("set({}{} 1)\n".format(
                    kconfig.config_prefix, sym.name))
        else:        
            add("set({}{} \"{}\")\n".format(
                kconfig.config_prefix, sym.name, val))

        config_vars.append(str(kconfig.config_prefix+sym.name))
    return "".join(chunks)


def write_config(kconfig):
    filename = args.projectdir + "/" + "sdkconfig"
    print("-- Write Project config to: " + filename)
    kconfig.write_config(filename)

def write_cmake(kconfig):
    filename = args.projectdir + "/" + "proj.conf"
    print("-- Write CMake config to: " + filename)
    cmake_conf_header = "# Generated by KConfig!\n"
    cmake_conf_header += "### DO NOT edit this file!! ###\n"
    cmake_conf_header += "### Run make config instead ###\n\n"
    cmake_conf_content = _cmake_contents(kconfig, cmake_conf_header)
    # don't change file info if config no change
    if os.path.exists(filename):
        with open(filename) as f:
            if f.read() == cmake_conf_content:
                return
    f = open(filename, "w")
    f.write(cmake_conf_content)
    f.close()


def write_header(kconfig):
    filename = "sdkconfig.h"
    print("-- write C header file at: " + args.header + "/" + filename)
    print(kconfig.write_autoconf( args.header + "/" + filename))

OUTPUT_FORMATS = {
                  "makefile": write_config,
                  "header": write_header,
                  "cmake": write_cmake
                  }

parser = argparse.ArgumentParser(description='menuconfig tool', prog=os.path.basename(sys.argv[0]))

parser.add_argument('--sdkpath',
                    help='SDK path',
                    default='../../',
                    required=None,
                    metavar='SDKPATH')

parser.add_argument('--defaults',
                    action='append',
                    default=["sdkconfig.default"],
                    help='Optional project defaults file. '
                            'Multiple files can be specified using multiple --defaults arguments.',
                    metavar="FILENAME"
                    )

parser.add_argument('--env',
                    action='append',
                    default=[],
                    help='Environment to set when evaluating the config file', 
                    metavar='VAR=VALUE'
                    )

parser.add_argument("--menuconfig",
                    help="Open menuconfig GUI interface",
                    )

parser.add_argument("--cmake", 
                    help="Generate CMake config file",
                    )

parser.add_argument("--header",
                    help="Generate C header file",
                    )

parser.add_argument("--projectdir",
                    default=".",
                    help="Project Directory (for .config and config_default)",
                    )

args = parser.parse_args()

for env in args.env:
    env = env.split("=")
    var = env[0]
    value = env[1]
    os.environ[var] = value

out_format = ["makefile", "header", "cmake"]
os.environ["KCONFIG_CONFIG"] = args.projectdir + "/sdkconfig"
os.environ["srctree"] = args.projectdir
print("Project Config File Path: " + os.environ["KCONFIG_CONFIG"])

sdkconfig = args.sdkpath + "/cmake/SDKconfig"

kconfig = kconfiglib.Kconfig(sdkconfig)
kconfig.warn = True

if args.defaults:
    for path in args.defaults:
        path = args.projectdir + "/" + path
        print("Attemping to load default config: " + path)
        if os.path.exists(path):
            print("Load Default config: " + path)
            kconfig.load_config(path, replace=False)
        else:
            print("Warning: Default Config file not found: " + path)

if os.path.exists(args.projectdir + "/sdkconfig"):
    print("Load Project config: " + args.projectdir + "/sdkconfig")
    kconfig.load_config(args.projectdir + "/sdkconfig")


if args.menuconfig:
    from menuconfig import menuconfig
    menuconfig(kconfig)

write_config(kconfig)

if args.cmake:
    write_cmake(kconfig)
if args.header:
    write_header(kconfig)

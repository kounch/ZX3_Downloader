#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# Do not modify previous lines. See PEP 8, PEP 263.
"""
Copyright (c) 2023, kounch
All rights reserved.

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import print_function
from typing import Any
import logging
import sys
import platform
import argparse
import pathlib
import os
import json
import hashlib
import ssl
from zipfile import ZipFile, is_zipfile
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote, unquote, urljoin
import socket
import shutil
import subprocess
import time

__MY_VERSION__ = '0.0.1'

MY_BASEPATH: str = os.path.dirname(sys.argv[0])
MY_DIRPATH: str = os.path.abspath(MY_BASEPATH)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOG_FORMAT = logging.Formatter(
    '%(asctime)s [%(levelname)-5.5s] - %(name)s: %(message)s')
LOG_STREAM = logging.StreamHandler(sys.stdout)
LOG_STREAM.setFormatter(LOG_FORMAT)
LOGGER.addHandler(LOG_STREAM)

if sys.version_info < (3, 9, 0):
    LOGGER.error('This software requires Python version 3.9 or greater')
    sys.exit(1)

ssl._create_default_https_context = ssl._create_unverified_context  # pylint: disable=protected-access
socket.setdefaulttimeout(900)


def main():
    """Main routine"""

    arg_data: dict[str, Any] = parse_args()
    LOGGER.debug('Starting up...')

    s_cache_path: str = arg_data['cache_dir']
    s_out_path: str = arg_data['out_dir']

    if arg_data['clean_sd']:
        print('Cleaning SD path...')
        if os.path.isdir(s_out_path):
            shutil.rmtree(s_out_path)

    print('Checking Main DB...')
    s_urlbase = 'https://github.com/kounch/ZX3_Downloader/raw/bd/'
    d_main_db: dict[str, Any] = load_db(s_cache_path,
                                        'zx3_main_db.json',
                                        s_urlbase,
                                        b_force=not arg_data['keep'])
    if not d_main_db:
        LOGGER.error('Unable to obtain main DB file...')
        sys.exit(2)

    d_tags = d_main_db['tag_dictionary']
    for s_pack, d_pack in d_main_db['packs'].items():
        LOGGER.debug('Processing %s', s_pack)
        b_do_pack = True
        if d_pack['tags']:
            b_do_pack = False
            for i_tg in d_tags:
                if d_tags[i_tg] in d_pack['tags'] and i_tg in arg_data['tags']:
                    b_do_pack = True
                    break

        if b_do_pack:
            b_ok: bool = False
            if d_pack["type"] == "zip":
                print(f'Checking/Building {d_pack["name"]} files from ZIP...')
                b_ok = build_sd_fromdb(s_cache_path, d_pack, s_out_path)
            elif d_pack["type"] == "files":
                print(f'Checking/Building {d_pack["name"]} files...')
                b_ok = build_sd_files_fromdb(s_cache_path, d_pack, arg_data)
            elif d_pack["type"] == "arcade":
                print(f'Checking/Building {d_pack["name"]}:')
                b_ok = build_arcade_sd_fromdb(s_cache_path, d_pack, s_out_path)
            if not b_ok:
                LOGGER.error("Error building %s files", d_pack["name"])

    #TMP for esxdos
    s_tmp_path = os.path.join(s_out_path, 'TMP')
    if not os.path.isdir(s_tmp_path):
        pathlib.Path(s_tmp_path).mkdir(parents=True, exist_ok=True)

    print("Finished")


def parse_args() -> dict[str, Any]:
    """
    Parses command line
    :return: Dictionary with different options
    """
    global LOGGER  # pylint: disable=global-variable-not-assigned

    values: dict[str, Any] = {}
    values['clean_sd'] = False
    values['cache_dir'] = os.path.join(MY_DIRPATH, 'cache')
    values['out_dir'] = os.path.join(MY_DIRPATH, 'SD')
    values['kinds'] = []
    values['types'] = ['bit', 'zx3']
    values['tags'] = ['arcade', 'console', 'computer', 'util']
    values['group_types'] = False
    values['group_tags'] = False
    values['keep'] = False

    parser = argparse.ArgumentParser(description='ZX3 Downloader',
                                     epilog='Downloads files for ZX3 microSD')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version=f'%(prog)s {__MY_VERSION__}')

    parser.add_argument('-c',
                        '--clean_sd',
                        required=False,
                        action='store_true',
                        dest='clean_sd',
                        help='Make a clean build of the SD')

    parser.add_argument('-C',
                        '--cache_dir',
                        required=False,
                        action='store',
                        dest='cache_dir',
                        help='Cache directory name and location')

    parser.add_argument('-O',
                        '--out_dir',
                        required=False,
                        action='store',
                        dest='out_dir',
                        help='Output directory name and location')

    parser.add_argument('-K',
                        '--keep',
                        required=False,
                        action='store_true',
                        dest='keep',
                        help='Keep previous existing files and directories')

    parser.add_argument('-k',
                        '--kinds',
                        required=True,
                        action='append',
                        dest='kinds',
                        help='List of kinds of fpgas to include')

    parser.add_argument('-t',
                        '--types',
                        required=False,
                        action='append',
                        dest='types',
                        help='List of types of core files to include')

    parser.add_argument('-T',
                        '--tags',
                        required=False,
                        action='append',
                        dest='tags',
                        help='List of tags to include')

    parser.add_argument('-g',
                        '--group_types',
                        required=False,
                        action='store_true',
                        dest='group_types',
                        help='Group core files by file type')

    parser.add_argument('-G',
                        '--group_tags',
                        required=False,
                        action='store_true',
                        dest='group_tags',
                        help='Group core files by tag')

    parser.add_argument('--debug',
                        required=False,
                        action='store_true',
                        dest='debug')

    arguments = parser.parse_args()

    if arguments.debug:
        LOGGER.setLevel(logging.DEBUG)
    LOGGER.debug(sys.argv)

    if arguments.clean_sd:
        values['clean_sd'] = arguments.clean_sd

    if arguments.cache_dir:
        values['cache_dir'] = os.path.abspath(arguments.cache_dir)

    if arguments.out_dir:
        values['out_dir'] = os.path.abspath(arguments.out_dir)

    if arguments.keep:
        values['keep'] = True

    if arguments.kinds:
        values['kinds'] = []
        all_kinds: list[str] = ['a35t', 'a100t', 'a200t']
        for s_kinds in arguments.kinds:
            l_kinds = s_kinds.split(',')
            for s_kind in l_kinds:
                if s_kind.lower() in all_kinds:
                    values['kinds'].append(s_kind.lower())
                else:
                    LOGGER.error('Bad kind of FPGA: %s', s_kind)

    if arguments.types:
        all_types: list[str] = values['types']
        values['types'] = []
        for s_types in arguments.types:
            l_types = s_types.split(',')
            for s_type in l_types:
                if s_type.lower() in all_types:
                    values['types'].append(s_type.lower())
                else:
                    LOGGER.error('Bad type of file: %s', s_type)

    if arguments.tags:
        all_tags: list[str] = values['tags']
        values['tags'] = []
        for s_tags in arguments.tags:
            l_tags = s_tags.split(',')
            for s_tag in l_tags:
                if s_tag.lower() in all_tags:
                    values['tags'].append(s_tag.lower())
                else:
                    LOGGER.error('Bad tag: %s', s_tag)

    if arguments.group_types:
        values['group_types'] = True

    if arguments.group_tags:
        values['group_tags'] = True

    if not values['types']:
        LOGGER.error('Need at least one kind of FPGA')
        sys.exit(3)

    if not values['types']:
        LOGGER.error('Need at least one type of file')
        sys.exit(3)

    if not values['tags']:
        LOGGER.error('Need at least one valid tag')
        sys.exit(3)

    LOGGER.debug(values)
    return values


def load_db(s_dirpath: str,
            s_name: str,
            s_urlbase: str = '',
            s_hash: str = '',
            i_size: int = 0,
            b_force: bool = False) -> dict[str, Any]:
    """
    Loads Database from JSON or from JSON inside ZIP file
    :param s_dirpath: Directory where the file should be
    :param s_name: JSON file name
    :param s_urlbase: Base URL to compose the path to download
    :param s_hash: Hash of ZIP file
    :param i_size: Size of ZIP file
    :param b_force: If True, delete an existing file and download again
    :return: Dictionary with data
    """

    s_zipname: str = s_name + '.zip'
    s_dirpath = os.path.join(s_dirpath, 'db')
    s_json: str = os.path.join(s_dirpath, s_name)
    s_jsonzip: str = os.path.join(s_dirpath, s_zipname)

    if b_force and os.path.isfile(s_jsonzip):
        os.remove(s_jsonzip)

    b_ok: bool = chk_or_download(s_dirpath, s_zipname, s_hash, i_size,
                                 urljoin(s_urlbase, s_zipname))
    if not b_ok:
        print(f'{s_name} Bad file!')

    d_result: dict[str, Any] = {}
    if os.path.isfile(s_json):
        with open(s_json, 'r', encoding='utf-8') as json_handle:
            LOGGER.debug('Loading database...')
            d_result = json.load(json_handle)
            LOGGER.debug('%s loaded OK', s_name)
    elif is_zipfile(s_jsonzip):
        with ZipFile(s_jsonzip, "r") as z_handle:
            for s_filename in z_handle.namelist():
                if s_filename == s_name:
                    LOGGER.debug('Loading Arcade DB...')
                    with z_handle.open(s_filename) as json_handle:
                        json_data: bytes = json_handle.read()
                        d_result = json.loads(json_data.decode("utf-8"))
                    LOGGER.debug('%s loaded OK', s_jsonzip)
                    break
    else:
        print(f'{s_name} Not found or not in a ZIP file!')

    return d_result


def build_sd_fromdb(s_dir: str, d_db_params: dict[str, Any],
                    s_outdir: str) -> bool:
    """
    Builds SD from ZIP file using DB of URLs, etc.
    :param s_dir: Path where DB file is to be found or downloaded
    :param d_db_params: Dictionary with all DB file info (hash, etc.)
    :param s_outdir: Base directory where the files are copied
    :return: Boolean indicating success
    """

    s_name: str = d_db_params['file']
    s_url: str = d_db_params['url']
    s_hash: str = d_db_params['hash']
    i_size: int = d_db_params['size']

    b_ok: bool = False

    LOGGER.debug('Checking %s ZIP DB...', s_name)
    d_db: dict[str, Any] = load_db(s_dir, s_name, s_url, s_hash, i_size, False)

    s_base_url: str = d_db.get('base_url', '')
    s_content: str = s_base_url.split('/')[-1]

    LOGGER.debug('Checking files (for %s DB)...', s_name)
    b_content: bool = chk_or_download(s_dir, s_content, d_db['base_hash'],
                                      d_db['base_size'], s_base_url)
    if not b_content:
        LOGGER.error('Unable to obtain files for %s DB...', s_name)
        sys.exit(2)

    if s_content:
        LOGGER.debug('Copying files for SD from %s DB...', s_name)
        b_ok = build_sd_fromzip(os.path.join(s_dir, s_content), d_db['files'],
                                s_outdir)
    else:
        LOGGER.error('Content not defined in %s', s_name)

    return b_ok


def build_sd_files_fromdb(s_path: str, d_db_params: dict[str, Any],
                          d_params: dict[str, Any]) -> bool:
    """
    Builds SD downloading individual files using DB of URLs, etc.
    :param s_dir: Path where DB file is to be found or downloaded
    :param d_db_params: Dictionary with all DB file info (hash, etc.)
    :param d_params: Dictionary with global params (out dir, etc.)
    :return: Boolean indicating success
    """

    b_ok: bool = False

    s_json_db: str = d_db_params['file']
    s_name: str = d_db_params['path']
    s_url: str = d_db_params['url']
    s_hash: str = d_db_params['hash']
    i_size: int = d_db_params['size']
    s_out_path: str = d_db_params['out_path']
    b_keep: bool = True
    if d_db_params['args_keep']:
        b_keep = d_params['keep']
    b_force: bool = False

    s_files_path: str = os.path.join(s_path, s_name)
    d_files_db: dict[str, Any] = load_db(s_path, s_json_db, s_url, s_hash,
                                         i_size, b_force)
    if not d_files_db:
        LOGGER.error("There's no files JSON data for %s", s_json_db)
        sys.exit(2)

    LOGGER.debug('Checking Files Cache for %s...', s_json_db)
    chk_files_cache(d_files_db, d_params['kinds'], d_params['types'],
                    d_params['tags'], s_files_path, b_force)

    LOGGER.debug('Copying Files for SD...')
    b_ok = build_sd_files(d_files_db, d_params['kinds'], d_params['types'],
                          d_params['tags'], s_files_path, d_params['out_dir'],
                          s_out_path, d_params['group_tags'],
                          d_params['group_types'], b_keep)

    return b_ok


def build_sd_fromzip(s_zip_path: str, d_zip_files: dict[str, Any],
                     s_out_dir: str) -> bool:
    """
    Builds SD files extracting from a zip file
    :param s_zip_path: Full path to ZIP file containing original files
    :param d_zip_files: Dictionary with all the ZIP files to exttact
    :param s_out_dir: Path to directory wher files will be extracted
    :return: True if the extraction finishes without problems
    """

    b_ok = False
    d_files: dict[str, Any] = d_zip_files
    for s_orig in d_files:
        s_dest: str = s_out_dir
        l_subdirs: list[str] = d_files[s_orig].get('path', [])
        if l_subdirs:
            s_dest: str = os.path.join(s_dest, os.path.join(*l_subdirs))
        s_dest: str = os.path.join(s_dest, d_files[s_orig]['file'])
        s_hash: str = d_files[s_orig]['hash']
        i_size: int = d_files[s_orig]['size']
        b_ok = chk_or_extract(s_orig, s_dest, s_hash, i_size, s_zip_path)

    return b_ok


def build_arcade_sd_fromdb(s_dir: str, d_db_params: dict[str, Any],
                           s_outdir: str) -> bool:
    """
    Buils ARC and ROM files structure for arcade cores
    :param sdir: Cache base directory
    :param d_db_params: Dictionary with all DB file info (hash, etc.)
    :param s_outdir: Base directory where the files are created
    :return: True if everything is done correctly
    """
    s_roms_path: str = os.path.join(s_dir, 'roms')
    s_mras_path: str = os.path.join(s_dir, 'mra')

    l_arcade_dbs = ['arcade_rom_db', 'mra_db', 'jtcores_db']
    d_arcade_dbs: dict[str, dict[str, Any]] = {}
    for db_key in l_arcade_dbs:
        db_value = d_db_params['dbs'][db_key]
        s_name: str = db_value['file']
        s_urlbase: str = db_value['url']
        s_hash = db_value['hash']
        i_size = db_value['size']
        d_arcade_dbs[db_key] = load_db(s_dir, s_name, s_urlbase, s_hash,
                                       i_size, False)
        if not d_arcade_dbs[db_key]:
            LOGGER.error("There's no Arcade %s JSON data", db_key)
            sys.exit(2)

    print(f'* Checking {d_db_params["name"]} ZIP files cache...')
    chk_zip_cache(d_arcade_dbs['arcade_rom_db'], d_arcade_dbs['jtcores_db'],
                  s_roms_path, False)

    print(f'* Checking {d_db_params["name"]} MRA files cache...')
    s_baseurl: str = d_db_params['mra_url']
    d_mras: dict[str, Any] = chk_mra_cache(d_arcade_dbs['mra_db'],
                                           d_arcade_dbs['jtcores_db'],
                                           s_mras_path, False, s_baseurl)

    print(f'* Building {d_db_params["name"]} ARC files...')
    build_arc_files(d_mras, d_arcade_dbs['jtcores_db'],
                    os.path.join(s_outdir, 'JOTEGO'), s_mras_path, s_roms_path,
                    s_dir)

    return True


def chk_zip_cache(d_arcade_db: dict[str, Any], d_cores_db: dict[str, Any],
                  s_roms_path: str, b_force: bool):
    """
    Populates ROM ZIP files disk cache
    :param d_arcade_db: Dict with arcade DB
    :param d_cores_db: Dict with cores DB
    :param s_roms_path: Path for the ROM files cache
    :param b_force: If True, delete (if exists) and download again
    :return: Nothing
    """

    d_files: dict[str, Any] = d_arcade_db['files']
    d_tags: dict[str, Any] = d_arcade_db['tag_dictionary']

    for s_file in d_files:
        s_name: str = s_file.split('/')[-1]
        for i_item in d_files[s_file]['tags']:
            for j_item in d_tags:
                if d_tags[j_item] == i_item and j_item in d_cores_db:
                    b_ok = chk_or_download(s_roms_path, s_name,
                                           d_files[s_file]['hash'],
                                           d_files[s_file]['size'],
                                           d_files[s_file]['url'], b_force)
                    if not b_ok:
                        print(f'{s_name} Bad file!')


def chk_files_cache(d_files_db: dict[str, Any], l_kind: list[str],
                    l_type: list[str], l_tags: list[str], s_files_path: str,
                    b_force: bool):
    """
    Populates files disk cache, checking the existing ones and downloading when
    needed
    :param d_files_db: Dict with files DB
    :param l_kind: List of kind of core files to populate/check (e.g. a200t)
    :param l_type: List of type of core files (e.g. bit, zx3)
    :param l_tags: List with tags that apply
    :param s_files_path: Path for the files cache
    :param b_force: If True, delete (if exists) and download again
    :return: Nothing
    """

    d_files: dict[str, Any] = d_files_db.get('files', {})
    d_tags: dict[str, Any] = d_files_db.get('tag_dictionary', {})

    for s_file in d_files:
        s_name: str = s_file.split('/')[-1]

        b_download: bool = True  # If there are no tags, download always
        if d_tags:
            b_download = False
            s_kind = d_files[s_file].get('kind', '')
            if s_kind in l_kind and d_files[s_file].get(
                    'type', None) in l_type:  # Fully tagged
                b_download = True
            elif not s_kind:  # Partial tag, download always
                b_download = True

        if b_download:
            if d_tags:
                b_download = False
                for i_item in d_files[s_file]['tags']:
                    for j_item in d_tags:
                        if d_tags[j_item] == i_item and j_item in l_tags:
                            b_download = True

            if b_download:
                s_file_path = s_files_path
                l_files_subpath = d_files[s_file].get('path', [])
                if l_files_subpath:
                    s_file_path = os.path.join(s_file_path,
                                               os.path.join(*l_files_subpath))
                b_ok = chk_or_download(s_file_path, s_name,
                                       d_files[s_file]['hash'],
                                       d_files[s_file]['size'],
                                       d_files[s_file]['url'], b_force)
                if not b_ok:
                    print(f'{s_name} Bad file!')


def build_sd_files(d_files_db: dict[str, Any], l_kinds: list[str],
                   l_types: list[str], l_tags: list[str], s_files_path: str,
                   s_out_path: str, s_out_subpath, b_taggroups: bool,
                   b_typegroups: bool, b_keep: bool) -> bool:
    """
    Builds SD downloading individual files according to filterin criteria
    :param d_files_db: Database with all the files information
    :param l_kinds: Kind of core files to use (a100t, a35t, etc.)
    :param l_types: Type of core files to use (bit, zx3, etc.)
    :param l_tags: Tags of the files to use (computer, arcade, etc.)
    :param s_files_path: Path where the original files are
    :param s_out_path: Path where the files are to be copied
    :param s_out_subpath: Subpath of s_out_path to copy the files into
    :param b_taggroups: Group the files in directories by tag
    :param b_typegroups: Group the files in directories ty type
    :param b_keep: If true, do not delete previously existing files
    :return: Boolean indicating success
    """

    b_ok: bool = True

    if not b_keep:
        s_sdpath: str = os.path.join(s_out_path, s_out_subpath)
        if os.path.isdir(s_sdpath):
            shutil.rmtree(s_sdpath)

    d_files: dict[str, Any] = d_files_db['files']
    d_tags: dict[str, Any] = d_files_db.get('tag_dictionary', {})
    for s_file in d_files:
        s_name: str = s_file.split('/')[-1]
        s_sdpath: str = os.path.join(s_out_path, s_out_subpath)
        if d_tags:
            s_kind = d_files[s_file].get('kind', '')
            if s_kind in l_kinds and d_files[s_file][
                    'type'] in l_types:  # Fully tagged item, copy if tag matches
                if b_typegroups:
                    s_sdpath = os.path.join(s_sdpath, d_files[s_file]['type'])
                for i_item in d_files[s_file]['tags']:
                    for j_item in d_tags:
                        if d_tags[j_item] == i_item and j_item in l_tags:
                            if b_taggroups:
                                s_sdpath = os.path.join(s_sdpath, j_item)

                            s_orig: str = os.path.join(s_files_path, s_name)
                            s_dest: str = os.path.join(s_sdpath, s_name)
                            LOGGER.debug('Copy %s to %s...', s_orig, s_dest)
                            if not os.path.isdir(s_sdpath):
                                pathlib.Path(s_sdpath).mkdir(parents=True,
                                                             exist_ok=True)
                            try:
                                shutil.copyfile(s_orig, s_dest)
                            except OSError as err:
                                LOGGER.error(err)
                                b_ok = False
            elif not s_kind:  # Partially tagged item?
                for i_item in d_files[s_file]['tags']:
                    for j_item in d_tags:
                        if d_tags[j_item] == i_item and j_item in l_tags:
                            l_subpath = d_files[s_file].get("path", [])
                            s_orig: str = s_files_path
                            if l_subpath:
                                s_orig = os.path.join(s_orig,
                                                      os.path.join(*l_subpath))
                                s_sdpath = os.path.join(
                                    s_sdpath, os.path.join(*l_subpath))
                            s_orig = os.path.join(s_orig, s_name)
                            s_dest = os.path.join(s_sdpath, s_name)
                            LOGGER.debug('Copy %s to %s...', s_orig, s_dest)
                            if not os.path.isdir(s_sdpath):
                                pathlib.Path(s_sdpath).mkdir(parents=True,
                                                             exist_ok=True)
                            try:
                                shutil.copyfile(s_orig, s_dest)
                            except OSError as err:
                                LOGGER.error(err)
                                b_ok = False

        else:  # No tags, always copy
            s_orig_subpath: str = s_files_path
            l_origsubpath: list[str] = d_files[s_file].get('path', [])
            if l_origsubpath:
                s_orig_subpath = os.path.join(s_orig_subpath,
                                              os.path.join(*l_origsubpath))
                s_sdpath = os.path.join(s_sdpath, os.path.join(*l_origsubpath))

            s_orig: str = os.path.join(s_orig_subpath, s_name)
            s_dest: str = os.path.join(s_sdpath, s_name)
            LOGGER.debug('Copy %s to %s...', s_orig, s_dest)
            if not os.path.isdir(s_sdpath):
                pathlib.Path(s_sdpath).mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(s_orig, s_dest)
            except OSError as err:
                LOGGER.error(err)
                b_ok = False

    return b_ok


def chk_mra_cache(d_mra_db: dict[str, Any], d_cores_db: dict[str, Any],
                  s_mras_path: str, b_force: bool,
                  s_baseurl: str) -> dict[str, Any]:
    """
    Populates MRA text files disk cache
    :param d_mra_db: Dict with MRA DB
    :param d_cores_db: Dict with cores DB
    :param s_mras_path: Path for the MRA files cache
    :param b_force: If True, delete existing files and download again
    :param s_commit: If not empyt, commit id to use to download the MRA files
    :return: Dict with MRA groups info
    """

    d_mras: dict[str, Any] = {}
    d_files: dict[str, Any] = d_mra_db['files']
    d_tags: dict[str, Any] = d_mra_db['tag_dictionary']
    for s_file in d_files:
        s_name: str = s_file.split('/')[-1]
        if s_name.endswith('.mra') and not '_alternatives' in s_file:
            for s_item in d_files[s_file]['tags']:
                for s_tagitem in d_tags:
                    if d_tags[s_tagitem] == s_item and ''.join(
                            s_tagitem.split('arcade')) in d_cores_db:
                        if not s_tagitem in d_mras:
                            d_mras[s_tagitem] = []
                        d_mras[s_tagitem].append(s_name)
                        b_ok = chk_or_download(s_mras_path, s_name,
                                               d_files[s_file]['hash'],
                                               d_files[s_file]['size'],
                                               s_baseurl + s_name, b_force)
                        if not b_ok:
                            print(f'{s_name} Bad file!')

    return d_mras


def build_arc_files(d_mras: dict[str, Any], d_cores_db: dict[str, Any],
                    s_out_path: str, s_mras_path: str, s_roms_path,
                    s_cache_path: str):
    """
    Builds ARC and ROM files from MRA and ROM ZIP files
    :param d_mras: Dict with MRA groups info
    :param s_out_path: Base path where the ARC and ROM files are created
    :param s_mras_path: Path for the MRA files cache
    :param s_roms_path: Path for the ROM ZIP files cache
    :param s_cache_path: Path to the main cache (to find the bin)
    :return: Nothing
    """

    if not os.path.isdir(s_out_path):
        pathlib.Path(s_out_path).mkdir(parents=True, exist_ok=True)

    s_mra_bindirpath: str = os.path.join(s_cache_path, 'bin')
    s_mra_binpath: str = chk_or_download_mrabin(s_mra_bindirpath)
    if s_mra_binpath != '':
        for s_mra, l_mra in d_mras.items():
            s_basename_arc: str = ''.join(s_mra.split('arcade'))
            s_subdir_arc: str = ''
            if len(l_mra) > 1:
                s_subdir_arc: str = ''.join(s_basename_arc.split('jt')).upper()

            for s_submra in l_mra:
                s_mra_path: str = os.path.join(s_mras_path, s_submra)
                default_mra = d_cores_db[s_basename_arc]['default_mra']
                l_mra_params: list[str] = []

                s_arc_path: str = s_out_path
                if s_subdir_arc == '' or (default_mra != '' and
                                          s_submra.startswith(default_mra)):
                    s_arc_name: str = ''.join(s_mra.split('arcade')) + '.arc'
                    if d_cores_db[s_basename_arc]['default_arc'] != '':
                        s_arc_name = d_cores_db[s_basename_arc][
                            'default_arc'] + '.arc'

                    l_mra_params = [
                        s_mra_binpath, '-A', '-z', s_roms_path, '-O',
                        s_arc_path, '-a',
                        s_arc_name.upper(), s_mra_path
                    ]
                    LOGGER.debug(' '.join(l_mra_params))
                    run_process(l_mra_params, s_submra)

                if s_subdir_arc != '':
                    s_arc_path = os.path.join(s_arc_path, s_subdir_arc)
                    if not os.path.isdir(s_arc_path):
                        pathlib.Path(s_arc_path).mkdir(parents=True,
                                                       exist_ok=True)

                l_mra_params = [
                    s_mra_binpath, '-A', '-z', s_roms_path, '-O', s_arc_path,
                    s_mra_path
                ]
                LOGGER.debug(' '.join(l_mra_params))
                run_process(l_mra_params, s_submra)


def chk_or_download_mrabin(s_mrabin_dirpath: str,
                           b_force: bool = False) -> str:
    """
    Download mra binary file if does not exist
    :param s_mra_dirpath: Path to dir where the file should be
    :param b_force: If True, delete an existing file and download again
    :return: String with the full path to the binary file
    """

    b_ok: bool = True

    s_mra_binname: str = 'mra'
    s_mra_binurl: str = 'https://github.com/kounch/mra-tools-c/raw/master/release/'

    if sys.platform == 'darwin':
        s_mra_binurl = urljoin(s_mra_binurl, 'macos/')
    elif sys.platform == 'win32':
        s_mra_binurl = urljoin(s_mra_binurl, 'windows/')
        s_mra_binname = 'mra.exe'
    else:  # Assume Linux
        s_mra_binurl = urljoin(s_mra_binurl, 'linux/')
        if platform.machine() == 'armv7l':
            s_mra_binname = 'mra.armv7l'
        elif platform.machine() == 'aarch64':
            s_mra_binname = 'mra.aarch64'

    s_mra_binpath: str = os.path.join(s_mrabin_dirpath, s_mra_binname)
    s_mra_binurl = urljoin(s_mra_binurl, s_mra_binname)

    if not os.path.isfile(s_mra_binpath):
        b_ok = chk_or_download(s_mrabin_dirpath,
                               s_mra_binname,
                               s_url=s_mra_binurl,
                               b_force=b_force)
        time.sleep(15)  # Give Windows some time to check the file
        if sys.platform != 'win32':
            run_process(['chmod', 'a+x', s_mra_binpath], 'mra tool binary')
        if not b_ok:
            s_mra_binpath = ''

    return s_mra_binpath


def chk_or_download(s_path: str,
                    s_name: str,
                    s_hash: str = '',
                    i_size: int = 0,
                    s_url: str = '',
                    b_force: bool = False) -> bool:
    """
    Download a file if does not exist and, optionally check hash
    :param s_path: Path to dir where the file should be
    :param s_name: File name
    :param s_hash: Optional MD5 hash to check
    :param i_size: Optional size (bytes) to check
    :param s_url : Optional URL to download from
    :param b_force: If True, delete an existing file and download again
    :return: Boolean indicating download, check, etc. where all ok
    """

    b_ok: bool = True

    if not os.path.isdir(s_path):
        pathlib.Path(s_path).mkdir(parents=True, exist_ok=True)

    s_fpath: str = os.path.join(s_path, s_name)

    if b_force and os.path.isfile(s_fpath):
        os.remove(s_fpath)

    if os.path.isfile(s_fpath):
        if s_hash != '':
            i_fsize: int = os.stat(s_fpath).st_size
            LOGGER.debug('%s exists, checking...', s_name)
            s_hashcheck: str = get_file_hash(s_fpath)
            if s_hash == s_hashcheck and i_fsize == i_size:
                LOGGER.debug('%s is OK!', s_name)
            else:
                LOGGER.debug('%s wrong hash. Replacing...', s_name)
                os.remove(s_fpath)

    if not os.path.isfile(s_fpath):
        if s_url != '':
            print(f'Downloading {s_name}...')
            s_turl = unquote(s_url, encoding='utf-8', errors='replace')
            if len(s_turl) == len(s_url):
                s_turl = urlparse(s_url)
                s_url = s_turl.scheme + "://" + s_turl.netloc + quote(
                    s_turl.path)
                if s_turl.query != '':
                    s_url += "?" + quote(s_turl.query)

            try:
                urllib.request.urlretrieve(s_url, s_fpath)
            except HTTPError as error:
                LOGGER.debug('Cannot fetch %s! %s', s_url, error)
            except URLError as error:
                LOGGER.error('Connection error: %s! %s', s_url, error)
                b_ok = False
        else:
            LOGGER.error('%s not found!', s_name)
            b_ok = False

    if os.path.isfile(s_fpath):
        if s_hash != '' and i_size != 0:
            i_fsize: int = os.stat(s_fpath).st_size
            LOGGER.debug('%s downloaded, checking...', s_name)
            s_hashcheck: str = get_file_hash(s_fpath)
            if s_hash == s_hashcheck and i_fsize == i_size:
                LOGGER.debug('%s is OK!', s_name)
            else:
                LOGGER.error('%s wrong file!', s_name)
                b_ok = False
    else:
        LOGGER.error('Error downloading %s!', s_name)
        b_ok = False

    return b_ok


def chk_or_extract(s_orig: str, s_fpath: str, s_hash: str, i_size: int,
                   s_zip_path: str) -> bool:
    """
    Extract a file from inside a ZIP archive if does not exist and, optionally,
    check hash
    :param s_orig: Path to where the file should be inside the ZIP archive
    :param s_fpath: File path of the extracted file
    :param s_hash: MD5 hash to check
    :param i_size: Size (bytes) to check
    :param s_zip_path: Path to the ZIP archive file
    :return: Boolean indicating extraction, check, etc. where all ok
    """
    b_ok: bool = True

    s_name: str = s_fpath.split('/')[-1]
    s_path: str = os.path.dirname(s_fpath)
    if not os.path.isdir(s_path):
        pathlib.Path(s_path).mkdir(parents=True, exist_ok=True)

    if os.path.isfile(s_fpath):
        if s_hash != '':
            i_fsize: int = os.stat(s_fpath).st_size
            LOGGER.debug('%s exists, checking...', s_name)
            s_hashcheck: str = get_file_hash(s_fpath)
            if s_hash == s_hashcheck and i_fsize == i_size:
                LOGGER.debug('%s is OK!', s_name)
            else:
                LOGGER.debug('%s wrong hash. Replacing...', s_name)
                os.remove(s_fpath)

    if not os.path.isfile(s_fpath):
        if s_zip_path != '':
            LOGGER.debug('Extracting %s...', s_orig)
            with ZipFile(s_zip_path, "r") as z_handle:
                with z_handle.open(s_orig) as member:
                    with open(s_fpath, 'wb') as outfile:
                        shutil.copyfileobj(member, outfile)
                    b_ok = True

    if os.path.isfile(s_fpath):
        if s_hash != '' and i_size != 0:
            i_fsize: int = os.stat(s_fpath).st_size
            LOGGER.debug('%s extracted, checking...', s_name)
            s_hashcheck: str = get_file_hash(s_fpath)
            if s_hash == s_hashcheck and i_fsize == i_size:
                LOGGER.debug('%s is OK!', s_name)
            else:
                LOGGER.error('%s wrong file!', s_name)
                b_ok = False
    else:
        LOGGER.error('Error extracting %s!', s_name)
        b_ok = False

    return b_ok


def get_file_hash(str_in_file: str) -> str:
    """
    Get file md5 hash
    :param str_in_file: Path to file
    :return: String with hash data
    """
    md5_hash: object = hashlib.md5()
    with open(str_in_file, "rb") as f_data:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f_data.read(4096), b""):
            md5_hash.update(byte_block)

    return md5_hash.hexdigest()


def run_process(l_mra_params: list[str], s_item: str):
    """
    Runs a process, printing stdout, and logging an errir if stderr not empty
    :param l_mra_params: list of command line command and parameters
    :param s_item: Text to show as element in error if stderr not empty
    :return: Nothing
    """

    mra_process = subprocess.run(l_mra_params,
                                 capture_output=True,
                                 check=False,
                                 encoding='utf8')
    if mra_process.stdout != '':
        LOGGER.debug(mra_process.stdout)
    if mra_process.stderr != '':
        LOGGER.error('Problem processing %s: %s', s_item, mra_process.stderr)


if __name__ == "__main__":
    main()

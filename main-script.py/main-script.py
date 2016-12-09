#!/usr/bin/env python

#
# Linux Script to download automatically subtitles from open subtitles. 
# You can download several subtitles at the same time.
# Se puede utilizar desde linea de comandos o desde entorno grafico Linux.
#
# Todo: change file encoding if needed
#

from subprocess import call
from os.path import basename
import os
import os.path
import sys

script_directory = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, script_directory)
from OpenSubsManager import OpenSubsManager

#######################################################################################################################
#           USER CONFIGUATION VARIABLES                                                                               #
#######################################################################################################################

# Array with subtitle languages to download
#   Portuguese  por
#   Spanish     spa
#   English     eng
#   French      fre
#   You can check the languages table on here: https://github.com/divhide/node-subtitler/blob/master/langs.dump.txt
array_languages = ["spa","eng"]

# Open subtitles credentials. Leave blank in case you havent
opensubs_username = "ramaznor"
opensubs_password = "bdsp10hxp"

# encoding: not working for now.
encoding = ""

#######################################################################################################################
#           FUNCTIONS                                                                                                 #
#######################################################################################################################

def show_error_and_exit(msg):
    sys.stderr.write("error: %s\n" % msg)
    if is_executed_from_x():
        call(["zenity", "--error","--text="+msg+""])
    sys.exit(1)

def is_executed_from_x():
    if 'NAUTILUS_SCRIPT_SELECTED_FILE_PATHS' in os.environ or 'NEMO_SCRIPT_SELECTED_FILE_PATHS' in os.environ:
        return True
    return False

def get_films_paths():
    films_path_array = []
    if 'NAUTILUS_SCRIPT_SELECTED_FILE_PATHS' in os.environ:
        films_path_array = os.environ['NAUTILUS_SCRIPT_SELECTED_FILE_PATHS'].split("\n")
    elif 'NEMO_SCRIPT_SELECTED_FILE_PATHS' in os.environ:
        films_path_array = os.environ['NEMO_SCRIPT_SELECTED_FILE_PATHS'].split("\n")
    elif len(sys.argv) > 1:
        sys.argv.pop(0)
        films_path_array = sys.argv

    films_path_array = [x for x in films_path_array if os.path.isfile(x) ]

    return films_path_array

def download_files_subtitles(user,password,files_array):
    array_errors = []
    open_subs_manager = OpenSubsManager(False)
    if open_subs_manager.loginServer(user,password) == False:
        array_errors.append("Cant login into open subtitles server")
    else:
        for i, film_path in enumerate(files_array):
            if os.path.isfile(film_path):
                return_codes = open_subs_manager.automatically_download_subtitles(film_path,array_languages,"srt")
                for key, val in enumerate(return_codes):
                    if val == 2:
                        array_errors.append(basename(film_path)+" ( " + array_languages[key] + " ) : Download limit reached")
                    if val == 4:
                        array_errors.append(basename(film_path)+" ( " + array_languages[key] + " ) : Couldnt write subtitle to disk")
                    elif val != 1:
                        array_errors.append(basename(film_path)+" ( " + array_languages[key] + " ) : Not found valid subtitle")
        # Logout
        open_subs_manager.logoutServer()
    return array_errors

#########################################################################################################################
#           MAIN                                                                                                        #
#########################################################################################################################

# Get movies array 
films_path_array = get_films_paths()
if len(films_path_array) == 0:
    show_error_and_exit("You have to select some film file")

# Download movies subtitles
array_errors = download_files_subtitles(opensubs_username,opensubs_password,films_path_array)

# Show errors if neccesary
if len(array_errors) > 0:
    show_error_and_exit("No se pudo bajar subs para:\n\t"+"\n\t ".join(array_errors))

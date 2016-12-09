#!/usr/bin/env python

#
# Linux Script para descarga de varios subtitulos
#
# Just copy  this script to:
#
# Script es un contenedor de:
#   - OpenSubsManagerClass.py class
#   - Main script main-script.py
#

import os
import re
import io
import sys
import json
import struct
import ntpath
import os.path
import logging
import gzip
from subprocess import call
from os.path import basename
from os.path import expanduser
from xmlrpclib import ServerProxy, Error

#######################################################################################################################
#           USER CONFIGUATION VARIABLES                                                                               #
#######################################################################################################################

# Array with subtitle languages to download
#   Spanish     spa
#   English     eng
#   Portuguese  por
#   French      fre
#   You can check the languages table on here: https://github.com/divhide/node-subtitler/blob/master/langs.dump.txt
array_languages = ["spa","eng"]

# Open subtitles credentials. Leave blank in case you havent.
opensubs_username = ""
opensubs_password = ""

# encoding: not working for now.
encoding = ""

#########################################################################################################################
#           OpenSubsManager.py Class                                                                                    #
#########################################################################################################################

USER_AGENT="OSTestUserAgentTemp"
OPEN_SUBTITLES_SERVER = "http://api.opensubtitles.org/xml-rpc"

class OpenSubsManager:

    def __init__(self,enable_comprehensive_search):
        self.server = ServerProxy(OPEN_SUBTITLES_SERVER)
        self.token = ""
        self.enable_comprehensive_search = True if enable_comprehensive_search == True else False

    def __del__(self):
        if self.token != "":
            self.logoutServer()

    def getOpenSubsHashFromFile(self,file_path):
          try:
                long_long_format = 'q'  # long long 
                bytesize = struct.calcsize(long_long_format)
    
                f = open(file_path, "rb")
    
                filesize = os.path.getsize(file_path)
                hash = filesize
    
                if filesize < 65536 * 2:
                       return "SizeError"
    
                for x in range(65536/bytesize):
                        buffer = f.read(bytesize)
                        (l_value,)= struct.unpack(long_long_format, buffer)
                        hash += l_value
                        hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
    
                f.seek(max(0,filesize-65536),0)
                for x in range(65536/bytesize):
                        buffer = f.read(bytesize)
                        (l_value,)= struct.unpack(long_long_format, buffer)
                        hash += l_value
                        hash = hash & 0xFFFFFFFFFFFFFFFF
    
                f.close()
                returnedhash =  "%016x" % hash
                return returnedhash
    
          except(IOError):
                    return "IOError"

    def loginServer(self,username,password):
        logging.info("Logging into server")
        try:
            session =  self.server.LogIn(username,password,"en",USER_AGENT)
        except:
            logging.info("Problems logging to server. Maybe opensubtitles has changed user agent. Update the script.")
            return False

        if session["status"] != "200 OK":
            logging.info("Problems logging to server. Maybe opensubtitles has changed user agent. Update the script.")
            return False

        logging.info("Connected correctly to open subtitles server")
        self.token=session["token"]

        return True

    def logoutServer(self):
        logging.info("Logging out from open subtitles server")
        self.server.Logout(self.token)
        return True

    def automatically_download_subtitles(self,film_path,languages_list,subtitle_format):

        return_codes = []
        if ( not os.path.isfile(film_path)  ):
            return return_codes

        for language_id in languages_list:
            ol_sub_list = self.get_movie_subs_list_from_server(film_path,language_id,subtitle_format)
            return_codes.append( self.download_first_subtitle(ol_sub_list,film_path,1) )
        return return_codes

    ####### Below methods supposed to internal use

    def get_imdb_id(self,film_path,film_imdb_hash):
        imdb_id = self.get_imdb_id_with_hash(film_imdb_hash,os.path.getsize(film_path))
        if imdb_id == 0 and self.enable_comprehensive_search:
            imdb_id = self.get_imdb_id_from_file_name_comprehensively(ntpath.basename(film_path))
        return imdb_id
    
    # 
    def get_imdb_id_with_hash(self,film_imdb_hash,film_size):
        search_list = []
        search_list.append({'moviehash':film_imdb_hash,'moviebytesize':str(film_size)})
        sub_list_response = self.server.SearchSubtitles(self.token, search_list)
        if (len(sub_list_response) > 0) and (len(sub_list_response['data']) > 0):
            logging.info("Encontrado por hash")
            return sub_list_response['data'][0]['IDMovieImdb']
        else:
            return 0

    def get_imdb_id_from_file_name_comprehensively(self,file_name):
        
        imdb_id = self.get_imdb_id_from_name(file_name)
        if imdb_id == 0:
            film_name_trimmed_1 = self.get_film_name_trimmed(ntpath.basename(file_name),1)
            logging.info("No encontrado con file name normal("+file_name+"), probando level 1("+film_name_trimmed_1+")")
            imdb_id = self.get_imdb_id_from_name(film_name_trimmed_1)
            if imdb_id == 0:
                film_name_trimmed_2 = self.get_film_name_trimmed(ntpath.basename(file_name),2)
                logging.info("No encontrado con file name level 1, probando level 2("+film_name_trimmed_2+")")
                imdb_id = self.get_imdb_id_from_name(film_name_trimmed_2)
                if imdb_id == 0:
                    logging.info("No encontrado con file level 2 ")
        return imdb_id

    def get_imdb_id_from_name(self,film_name):
        search_list = []
        search_list.append({'tag':film_name})
        sub_list_response = self.server.SearchSubtitles(self.token, search_list)
        if (len(sub_list_response) > 0) and (len(sub_list_response['data']) > 0):
            logging.info ("Encontrado por nombre("+film_name+")" )
            return sub_list_response['data'][0]['IDMovieImdb']
        else:
            return 0

    def trim_file_name(self,film_name):
        film_name=film_name.strip()
        film_name=re.sub('^[^a-zA-Z0-9]*','',film_name)
        film_name=re.sub('[^a-zA-Z0-9]*$','',film_name)
        film_name=film_name.strip()
        return film_name

    def get_film_name_trimmed(self, film_name,comprehensive_level):

        # first, remove additional info
        film_name=re.sub('\(.*?\)','',film_name)
        film_name=re.sub('\[.*?\]','',film_name)

        # remove extension
        film_name=os.path.splitext(film_name)[0]
        film_name=re.sub('\.',' ',film_name)
        film_name=re.sub('\,',' ',film_name)

        if comprehensive_level == 1:
            array_acronims = [ 'HDTVRip','720p','x264','25fps','DVDrip','HDTV','aXXo','BRRip','bluray','XviD','www','1080p','YIFY','640x256','DVDScr']
            for acronim in array_acronims:
                film_name = re.sub(acronim+'.*', '', film_name,  flags=re.I)
            
            film_name=self.trim_file_name(film_name)
            return film_name

        elif comprehensive_level == 2:
            # remove season and episode data
            film_name=re.sub('S\d\dE\d\d.*','',film_name,flags=re.I)
            film_name=self.trim_file_name(film_name)
            return film_name
            
    ########################################################################################################################3

    def get_movie_subs_list_from_server(self,film_path,sublanguageid,sub_format):
        """
        Main function to get one movie subtitle
        """
            
        if ( not os.path.isfile(film_path)  ):
            return []

        search_list = [ {'moviehash':self.getOpenSubsHashFromFile(film_path),'moviebytesize':str(os.path.getsize(film_path)),'sublanguageid':sublanguageid}  ]
        sub_list_response = self.server.SearchSubtitles(self.token, search_list)
        
        if sub_list_response["status"] == "401 Unauthorized":
            return []
        elif sub_list_response["status"] != '200 OK':
            return []

        if 'data' in sub_list_response and sub_list_response['data']:
            #ptodo: sometimes it is better the last..
            #sub_list_response['data'] = sorted(sub_list_response['data'], key=lambda k: k['SubAddDate'],reverse=True)
            sub_list_response['data'] = [item for item in sub_list_response['data'] if item['SubFormat'] == sub_format]
            return sub_list_response['data']
        else:
            return []

    def download_first_subtitle(self,sub_list_response,path_film,add_iso_sufix):
        """
        Usual return code problems: 2: download limit reached. 4: Problems writting subtitle to disk.
        """

        if len(sub_list_response) == 0:
            return 6
        for item in sub_list_response:
            #print item#fixme
            response = self.server.DownloadSubtitles(self.token, [item['IDSubtitleFile']])
            if response['status'] == '200 OK':
                compressed_data = response['data'][0]['data'].decode('base64')
                sub_data = gzip.GzipFile(fileobj=io.BytesIO(compressed_data)).read()
                if not self.write_subtitle_to_disk(self.get_subtitle_path(path_film,add_iso_sufix,item['ISO639'],item['SubFormat']),sub_data):
                    return 4
                return 1
            elif response['status'] == '407 Download limit reached':
                return 2
            else:
                return 3
        return  5

    def write_subtitle_to_disk(self,path_file,data):
        try:
            text_file = open(path_file, "w")
            text_file.write(data)
            text_file.close()
        except Exception as e:
            logging.warning("Problems writting file to disk.")
            return 0
        return 1

    def get_subtitle_path(self,path_film,add_iso_sufix,iso_sufix,sub_format):
        file_name, file_extension = os.path.splitext(path_film)
        if add_iso_sufix:
            path_to_download = file_name +  "_" + iso_sufix + "." + sub_format
        else:
            path_to_download = file_name + "." + sub_format
        return path_to_download

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

# Show errors if necessary
if len(array_errors) > 0:
    show_error_and_exit("No se pudo bajar subs para:\n\t"+"\n\t ".join(array_errors))


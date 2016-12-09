#!/usr/bin/env python

import unittest
import sys
import os

script_directory = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, script_directory)
from OpenSubsManager import OpenSubsManager

class openSubsUnityTest(unittest.TestCase):

    def testHash1(self):
        open_subs_manager = OpenSubsManager(False)
        self.failUnless( open_subs_manager.getOpenSubsHashFromFile(script_directory + '/test-files/1.data') == "SizeError")

    def testHash2(self):
        #self.failIf(IsOdd(2))
        open_subs_manager = OpenSubsManager(False)
        self.failUnless( open_subs_manager.getOpenSubsHashFromFile(script_directory + '/test-files/nofile.data') == "IOError" )

    def testHash3(self):
        open_subs_manager = OpenSubsManager(False)
        self.failUnless( open_subs_manager.getOpenSubsHashFromFile(script_directory + '/test-files/2.data') == "1a4e30bdef2debb7")

    def testHash4(self):
        open_subs_manager = OpenSubsManager(False)
        self.failUnless( open_subs_manager.getOpenSubsHashFromFile(script_directory + '/test-files/series1.mkv') == "1599f5bd17f492ae")

    def testServerConnection1(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("falseUser","falsePassword")
        self.failUnless(  open_subs_manager.loginServer("falseUser","falsePassword") == False )

    def testServerConnection2Anonymous(self):
        open_subs_manager = OpenSubsManager(False)
        self.failUnless(  open_subs_manager.loginServer("","") == True )

    def testGetImdbId1(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless( open_subs_manager.get_imdb_id(script_directory +'/test-files/series1.mkv','falsehash' ) == 0 )

    def testGetImdbId2(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless( open_subs_manager.get_imdb_id(script_directory +'/test-files/series1.mkv','1599f5bd17f492ae' ) == "2169080" )

    def testGetImdbIdComprehensive1(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless( open_subs_manager.get_imdb_id_from_name("") == 0 )

    def testGetImdbIdComprehensive2(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless( open_subs_manager.get_imdb_id_from_name("rick.and.morty.2014.s01e01.pilot.720p.hdtv.x264.mkv") == "2169080" )

    def testGetSubtitle1(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless(  open_subs_manager.get_movie_subs_list_from_server('nofile',"eng","srt")  == [] )

    def testGetSubtitle2(self):
        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        self.failUnless(  len( open_subs_manager.get_movie_subs_list_from_server(script_directory +'/test-files/series1.mkv',"x","srt") ) > 15 )

    def testGetSubtitle3(self):
        expected_file_path = script_directory + "/test-files/series1_es.srt"

        if os.path.isfile(expected_file_path) :
            os.remove(expected_file_path) 

        open_subs_manager = OpenSubsManager(False)
        open_subs_manager.loginServer("","")
        sub_list_response = open_subs_manager.get_movie_subs_list_from_server(script_directory +'/test-files/series1.mkv',"spa","srt")
        # Open subtitles puede cambiar, forzamos a utilizar siempre el mismo item subtitulo
        for item in sub_list_response:
            if item['SubHash'] == "df06910ae4c96051f49b800eda12c55f":
                new_sub_list_response = [item]
                open_subs_manager.download_first_subtitle(new_sub_list_response,script_directory +'/test-files/series1.mkv',1)


        # Size can change depending on the adds..
        self.failUnless ( os.path.isfile(expected_file_path) and ( os.path.getsize( expected_file_path ) > 40000 and os.path.getsize( expected_file_path ) < 45000  ) )

def main():
    unittest.main()
        
if __name__ == '__main__':
    main()


#-*- coding: UTF-8 -*-
import sys
import os
import urllib
import re
import xbmc
from utilities import *
from song import *
import lyrics

__language__ = sys.modules[ "__main__" ].__language__
__title__ = __language__(30031)
__allow_exceptions__ = True

class WikiaFormat:
    @staticmethod
    def __condense_strings(parseList):
        while(True):
            if ( len(parseList) < 2 
                 or not isinstance(parseList[-1], basestring)
                 or not isinstance(parseList[-2], basestring) ):
                return parseList
            lastStr = parseList[-1]
            parseList.pop()
            for i in range(len(parseList)-1, -1, -1):
                if ( isinstance(parseList[i], basestring) ):
                    lastStr = parseList[i] + lastStr
                    parseList.pop()
                else:
                    parseList.append(lastStr)
                    return parseList
            parseList.append(lastStr)
    
    @staticmethod
    def __parse_stack(parseList):
        while(True):
            if ( len(parseList) < 3 
                 or isinstance(parseList[-1], basestring)
                 or not isinstance(parseList[-2], basestring)
                 or isinstance(parseList[-3], basestring) ):
                return parseList
            
            beginTags = {2:'[I]', 3:'[B]', 5:'[I][B]'}
            endTags = {2:'[/I]', 3:'[/B]', 5:'[/I][/B]'}
            
            begin = parseList[-3]
            str = parseList[-2]
            end = parseList[-1]
            if ( begin == end ):
                parseList = parseList[:-3]
                if ( str ):
                    parseList.append(beginTags[begin] + str + endTags[end])
            elif ( begin == 5 ):
                parseList = parseList[:-3]
                begin = 5-end
                parseList.append(begin)
                if ( str ):
                    parseList.append(beginTags[end] + str + endTags[end])
            elif ( end == 5 ):
                parseList = parseList[:-3]
                end = 5-begin
                if ( str ):
                    parseList.append(beginTags[begin] + str + endTags[begin])
                parseList.append(end)
            else:
                return parseList
    
    @staticmethod
    def __push_stack(q, str, stack):
        if ( q >= 5 ):
            stack.append(5)
            q -= 5
        elif ( q >= 3 ):
            stack.append(3)
            q -= 3
        elif ( q >= 2 ):
            stack.append(2)
            q -= 2
        stack = WikiaFormat.__parse_stack(stack)
        str = "'"*q + str
        q = 0
        if ( str ):
           stack.append(str)
        WikiaFormat.__condense_strings(stack)
        return stack
    
    @staticmethod
    def to_xbmc_format(s):
        t = s.split("'")
        numQuotes = 0
        stack = []
        for line in t:
            if (line):
                stack = WikiaFormat.__push_stack(numQuotes, line, stack)
                numQuotes = 1
            else:
                numQuotes += 1
        if ( numQuotes > 1 ):
            stack = WikiaFormat.__push_stack(numQuotes, "", stack)
        
        #Take care of any unclosed tags
        if ( not isinstance(stack[-1], basestring) ):
            stack.append("")
        stack = WikiaFormat.__push_stack(5, "", stack)
        if ( not isinstance(stack[-1], basestring) ):
            stack.pop()
        return str.join("", stack)

class XmlUtils :
    def getText (self, nodeParent, childName ):
        # Get child node...
        node = nodeParent.getElementsByTagName( childName )[0]
        
        if node == None :
            return None
        
        # Get child text...
        text = ""
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE :
                text = text + child.data
        return text
    
    @staticmethod
    def removeComments(text):
        begin = text.split("<!--")
        if ( len(begin) > 1 ):
            end = str.join("", begin[1:]).split("-->")
            if ( len(end) > 1 ):
                return XmlUtils.removeComments(begin[0] + str.join("", end[1:]))
        return text


class LyricsFetcher:
    def __init__( self ):
        self.clean_lyrics_regex = re.compile( "<.+?>" )
        self.normalize_lyrics_regex = re.compile( "&#[x]*(?P<name>[0-9]+);*" )
        self.clean_br_regex = re.compile( "<br[ /]*>[\s]*", re.IGNORECASE )
        self.clean_info_regex = re.compile( "\[[a-z]+?:.*\]\s" )
        
    def get_lyrics_start(self, *args):
        lyricThread = threading.Thread(target=self.get_lyrics_thread, args=args)
        lyricThread.setDaemon(True)
        lyricThread.start()
    
    
    def get_lyrics_thread(self, song):
        print "SCRAPER-DEBUG-lyricstime: LyricsFetcher.get_lyrics_thread %s" % (song)
        l = lyrics.Lyrics()
        l.song = song
        try: # first try direct url
            direct_url = "http://www.tekstowo.pl/piosenka,%s,%s.html" % (song.artist.lower().replace(" ","_").replace(",","_"), song.title.lower().replace(" ","_").replace(",","_"), )
            direct_url = direct_url.replace("__","_")
            print "TEKSTOWO: try direct url: %s" % (direct_url)
            song_html = urllib.urlopen(direct_url).read()
            #print "TEKSTOWO: html: %s" % (song_html)
            if ( song_html.find("404 - Nie ma takiego pliku") >= 0):
                print "TEKSTOWO: 404 for: %s" % (song_html)
                # direct url miss, so perform search
                # example url for artist "Budka Suflera" and title "Zostañ jeszcze" is: 
                # http://www.tekstowo.pl/szukaj,wykonawca,budka+suflera,tytul,zostan+jeszcze.html
                search_url = "http://www.tekstowo.pl/szukaj,wykonawca,%s,tytul,%s.html" % (song.artist.lower().replace(" ","+").replace(",","+"), song.title.lower().replace(" ","+").replace(",","+"), )
                print "TEKSTOWO: search url: %s" % (search_url)
                search_html = urllib.urlopen(search_url).read()
                #print "TEKSTOWO: Search html: %s" % (search_html)
                # look for search results - example response is: 
                # <h2>Znalezione utwory:</h2>
                #<div class="box-przeboje">
                #<b>1.</b>
                #<a class="title" title="Budka Suflera - Zostañ Jeszcze" href="/piosenka,budka_suflera,zosta__jeszcze.html">Budka Suflera - Zostañ Jeszcze </a>
                #<b class="icon_kamera" title="teledysk"></b>
                #</div>
                first_search_result = search_html.split('<h2>Znalezione utwory:</h2>')[1]    
                #print "TEKSTOWO: first_search_result: %s" % (first_search_result)
                first_search_result = first_search_result.split('<div class="box-przeboje">')[1].split('</div>')[0] 
                #print "TEKSTOWO: first_search_result: %s" % (first_search_result)
                # get relative url to first hit
                first_hit_relative_url = first_search_result.split('href="')[1].split('"')[0] 
                #print "TEKSTOWO: first hit relative url: %s" % (first_hit_relative_url)
                # first hit absolute url
                first_hit_absolute_url = "http://www.tekstowo.pl" + first_hit_relative_url
                print "TEKSTOWO: first hit url: %s" % (first_hit_absolute_url)
                song_html = urllib.urlopen(first_hit_absolute_url).read()
                if ( song_html.find("404 - Nie ma takiego pliku") >= 0):
                    return None, __language__(30032) % (url)      
                
            lyr = song_html.split('<div class="song-text">')[1].split('</div>')[0]     
            lyr = lyr.replace("Tekst piosenki:","")
            lyr = lyr.split('<p>&nbsp;</p>')[0]
            # sometimes search gets unexpected results, so get artist and title for found song
            artist_and_title = song_html.split('<div class="belka short">')[1]     
            print "TEKSTOWO: artist_and_title: %s" % (artist_and_title)
            artist_and_title = artist_and_title.split('<strong')[1].split('</strong>')[0].split('>')[1]     
            artist = artist_and_title.split("-")[0].strip()
            title = artist_and_title.split("-")[1].strip()
            # find translated lyrics 
            #<div id="translation"
            translation = song_html.split('<div id="translation"')[1].split('">')[1].split('</div>')[0].split('<p>&nbsp;</p>')[0] 
            #print "TEKSTOWO: transl: %s" % (transl)
            result = lyr  + "<br/>"+"tekstowo.pl<br/>"+artist+"<br/>" + title + "<br/>* * *<br/>" + translation
            result = self.clean_br_regex.sub( "\n", result ).strip()
            result = self.clean_lyrics_regex.sub( "", result ).strip()
            result = self.normalize_lyrics_regex.sub( lambda m: unichr( int( m.group( 1 ) ) ), result.decode("UTF-8") )
            result = u"\n".join( [ lyric.strip() for lyric in result.splitlines() ] )
            result = self.clean_info_regex.sub( "", result )     
            #print "TEKSTOWO: result clean: %s" % (result)
            l.lyrics = result
            l.source = __title__
            return l, None            
        except:
            print "%s::%s (%d) [%s]" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ])
            return None, __language__(30004) % (__title__)      


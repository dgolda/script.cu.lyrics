
import sys
import os
import xbmc
import xbmcgui
import unicodedata
import urllib
from utilities import *
__settings__ = xbmc.Settings( path=os.getcwd() )

try:
    current_dlg_id = xbmcgui.getCurrentWindowDialogId()
except:
    current_dlg_id = 0
current_win_id = xbmcgui.getCurrentWindowId()

_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__
__svn_revision__ = sys.modules[ "__main__" ].__svn_revision__

SELECT_ITEM = ( 11, 256, 61453, )
EXIT_SCRIPT = ( 6, 10, 247, 275, 61467, 216, 257, 61448, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )
GET_EXCEPTION = ( 216, 260, 61448, )
SELECT_BUTTON = ( 229, 259, 261, 61453, )
MOVEMENT_UP = ( 166, 270, 61478, )
MOVEMENT_DOWN = ( 167, 271, 61480, )

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )

    def onInit( self ):
        self.setup_all()
        
    def setup_all( self ):
        self.setup_variables()
        self.get_settings()
        self.get_scraper()
        self.getMyPlayer()
#        self.show_viz_window()

    def get_settings( self ):
        self.settings = Settings().get_settings()
        
    def get_scraper( self ):
        import lyricsScraper as lyricsScraper
        self.LyricsScraper = lyricsScraper.LyricsFetcher()
        self.scraper_title = lyricsScraper.__title__
        self.scraper_exceptions = lyricsScraper.__allow_exceptions__

    def setup_variables( self ):
        self.artist = None
        self.song = None
        self.controlId = -1
        self.allow_exception = False


    def show_control( self, controlId ):
        self.getControl( 100 ).setVisible( controlId == 100 )
        self.getControl( 110 ).setVisible( controlId == 110 )
        self.getControl( 120 ).setVisible( controlId == 120 )
        page_control = ( controlId == 100 )

        xbmcgui.unlock()
        xbmc.sleep( 5 )
        try:
            self.setFocus( self.getControl( controlId + page_control ) )
        except:
            self.setFocus( self.getControl( controlId ) )

    def get_lyrics(self, artist1, song1, show):
        if show:
	        self.reset_controls()
	        self.getControl( 100 ).setText( "" )
	        self.getControl( 200 ).setLabel( "" )

        self.menu_items = []
        self.allow_exception = False
        artist2 = unicode(artist1, 'utf-8')				# de-accent Search String
        artist = unicodedata.normalize('NFKD', unicode(artist2)).encode('ascii','ignore')
        song2 = unicode(song1, 'utf-8')				# de-accent Search String
        song = unicodedata.normalize('NFKD', unicode(song2)).encode('ascii','ignore')
        lyrics = ""
        current_song = self.song
        lyrics, kind = self.get_lyrics_from_file( artist, song, show )
        if (artist.find( "\'" )) or (song.find( "\'", )):
	        quote = False
        else:
	        quote = True
        if show :
	        if ( lyrics != "" ):
	            if ( current_song == self.song ):
	                self.show_lyrics( lyrics )
	                self.getControl( 200 ).setEnabled( False )
	                self.getControl( 200 ).setLabel( "File" )
	        else:
	            self.getControl( 200 ).setEnabled( True )
	            self.getControl( 200 ).setLabel( "LyricWiki API" )
	                    
	            lyrics = self.LyricsScraper.get_lyrics_thread( artist, song, quote )

	            if ( current_song == self.song ):
	                self.show_lyrics( lyrics, True )
        else:
            if ( len(lyrics) > 100):
                
                print "Next Lyrics Already Exist"
            else:
                lyrics = self.LyricsScraper.get_lyrics_thread( artist, song, quote )
                if ( len(lyrics) > 100):
	                success = self.save_lyrics_to_file( lyrics )
	                print "Next Lyrics Saved"                

    def get_lyrics_from_list( self, item ):
        lyrics = self.LyricsScraper.get_lyrics_from_list( self.menu_items[ item ] )
        self.show_lyrics( lyrics, True )

    def get_lyrics_from_file( self, artist, song, embeded ):
        try:
            xbmc.sleep( 60 )
            if ( xbmc.getInfoLabel( "MusicPlayer.Lyrics" ) and embeded):
                return unicode( xbmc.getInfoLabel( "MusicPlayer.Lyrics" ), "utf-8" ), True
            self.song_path = make_legal_filepath( unicode( os.path.join( self.settings[ "lyrics_path" ], artist.replace( "\\", "_" ).replace( "/", "_" ), song.replace( "\\", "_" ).replace( "/", "_" ) + ( "", ".txt", )[ self.settings[ "use_extension" ] ] ), "utf-8" ), self.settings[ "compatible" ], self.settings[ "use_extension" ] )
            lyrics_file = open( self.song_path, "r" )
            lyrics = lyrics_file.read()
            lyrics_file.close()
            return unicode( lyrics, "utf-8" ), False
        except IOError:
            lyr = ""
            return lyr, False

    def save_lyrics_to_file( self, lyrics ):
        try:
            if ( not os.path.isdir( os.path.dirname( self.song_path ) ) ):
                os.makedirs( os.path.dirname( self.song_path ) )
            lyrics_file = open( self.song_path, "w" )
            lyrics_file.write( lyrics )
            lyrics_file.close()
            return True
        except IOError:
            LOG( LOG_ERROR, "%s (rev: %s) %s::%s (%d) [%s]", __scriptname__, __svn_revision__, self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False

    def unescape(self,s):
        s = s.replace("&lt;", "<")
        s = s.replace("&quot;", '"')
        s = s.replace("&apos;", "'")
        s = s.replace("&gt;", ">")
        s = s.replace("&amp;", "&")
        return s

    
    
    def show_lyrics( self, lyrics1, save=False ):
        xbmcgui.lock()
        lyrics = self.unescape(lyrics1)
        if ( lyrics == "" ):
            self.getControl( 100 ).setText( _( 632 ) )
            self.getControl( 110 ).addItem( _( 632 ) )
        else:

            if (len(lyrics) < 100 and lyrics.find("{{Instrumental}}")):
           		lyrics = lyrics.replace("{","")
           		lyrics = lyrics.replace("}","")
           		self.getControl( 100 ).setText( lyrics )
           		lyrics1 = lyrics.splitlines()
           		for x in lyrics1:
           			self.getControl( 110 ).addItem( x )
           		save = True                		
            	
            if ((len(lyrics) < 100) and (lyrics.find("{{Instrumental}}") < 1)):
            	self.getControl( 100 ).setText( "No lyrics have been found for ' %s '" % (self.song)  )
            	save = False
            if (len(lyrics) > 100):	
            	self.getControl( 100 ).setText( lyrics )
            	lyrics1 = lyrics.splitlines()
             	for x in lyrics1:
 	                self.getControl( 110 ).addItem( x )
            self.getControl( 110 ).selectItem( 0 )
            
            if ( __settings__.getSetting( "save_lyrics" ) == "true" and save ): success = self.save_lyrics_to_file( lyrics )
        self.show_control( 100 + ( int(__settings__.getSetting( "smooth_scrolling" ) == "true") * 10 ) )
        
        next_artist = xbmc.getInfoLabel( "MusicPlayer.offset(1).Artist" )
        next_song = xbmc.getInfoLabel( "MusicPlayer.offset(1).Title" )
        print "Next Artist: " + next_artist
        print "Next Song: " + next_song
        if ( next_song and  next_artist ):
        	self.get_lyrics( next_artist, next_song, False )
        else:
        	print "Missing Artist or Song name in ID3 tag for next track"	
        

        
    def show_choices( self, choices ):
        xbmcgui.lock()
        for song in choices:
            self.getControl( 120 ).addItem( song[ 0 ] )
        self.getControl( 120 ).selectItem( 0 )
        self.menu_items = choices
        self.show_control( 120 )
    
    def reset_controls( self ):
        self.getControl( 100 ).reset()
        self.getControl( 110 ).reset()
        self.getControl( 120 ).reset()
        

    def get_exception( self ):
        """ user modified exceptions """
        if ( self.scraper_exceptions ):
            artist = self.LyricsScraper._format_param( self.artist, False )
            alt_artist = get_keyboard( artist, "%s: %s" % ( _( 100 ), unicode( self.artist, "utf-8", "ignore" ), ) )
            if ( alt_artist != artist ):
                exception = ( artist, alt_artist, )
                self.LyricsScraper._set_exceptions( exception )
                self.myPlayerChanged( 2, True )

    def exit_script( self, restart=False ):
        self.close()
        if ( restart ): xbmc.executebuiltin( "XBMC.RunScript(%s)" % ( os.path.join( os.getcwd(), "default.py" ), ) )

    def onClick( self, controlId ):
        if ( controlId == 120 ):
            self.get_lyrics_from_list( self.getControl( 120 ).getSelectedPosition() )

    def onFocus( self, controlId ):

        self.controlId = controlId




    def get_artist_from_filename( self, filename ):
        try:
            artist = filename
            song = filename
            basename = os.path.basename( filename )
            # Artist - Song.ext
            if ( self.settings[ "filename_format" ] == 0 ):
                artist = basename.split( "-", 1 )[ 0 ].strip()
                song = os.path.splitext( basename.split( "-", 1 )[ 1 ].strip() )[ 0 ]
            # Artist/Album/Song.ext or Artist/Album/Track Song.ext
            elif ( self.settings[ "filename_format" ] in ( 1, 2, ) ):
                artist = os.path.basename( os.path.split( os.path.split( filename )[ 0 ] )[ 0 ] )
                # Artist/Album/Song.ext
                if ( self.settings[ "filename_format" ] == 1 ):
                    song = os.path.splitext( basename )[ 0 ]
                # Artist/Album/Track Song.ext
                elif ( self.settings[ "filename_format" ] == 2 ):
                    song = os.path.splitext( basename )[ 0 ].split( " ", 1 )[ 1 ]
        except:
            # invalid format selected
            LOG( LOG_ERROR, "%s (rev: %s) %s::%s (%d) [%s]", __scriptname__, __svn_revision__, self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        return artist, song

    def getMyPlayer( self ):
        self.MyPlayer = MyPlayer( xbmc.PLAYER_CORE_PAPLAYER, function=self.myPlayerChanged )
        self.myPlayerChanged( 2 )

    def myPlayerChanged( self, event, force_update=False ):
        LOG( LOG_DEBUG, "%s (rev: %s) GUI::myPlayerChanged [%s]", __scriptname__, __svn_revision__, [ "stopped","ended","started" ][ event ] )
        if ( event < 2 ): 
            self.exit_script()
        else:
            for cnt in range( 5 ):
                song = xbmc.getInfoLabel( "MusicPlayer.Title" )
                print "Song: " + song
                artist = xbmc.getInfoLabel( "MusicPlayer.Artist" )
                print "Artist: " + artist                
                if ( song and  not artist ):
                    artist, song = self.get_artist_from_filename( xbmc.Player().getPlayingFile() )
                if ( song and ( self.song != song or self.artist != artist or force_update ) ):
                    self.artist = artist
                    self.song = song
                    self.get_lyrics( artist, song, True )
                    break
                xbmc.sleep( 50 )



## Thanks Thor918 for this class ##
class MyPlayer( xbmc.Player ):
    """ Player Class: calls function when song changes or playback ends """
    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        self.function = kwargs[ "function" ]

    def onPlayBackStopped( self ):
        xbmc.sleep( 300 )
        if ( not xbmc.Player().isPlayingAudio() ):
            self.function( 0 )
    
    def onPlayBackEnded( self ):
        xbmc.sleep( 300 )
        if ( not xbmc.Player().isPlayingAudio() ):
            self.function( 1 )      
    
    def onPlayBackStarted( self ):
        self.function( 2 )

def onAction( self, action ):
    actionId = action.getId()
    if ( action.getButtonCode() in CANCEL_DIALOG ):
        self.exit_script()
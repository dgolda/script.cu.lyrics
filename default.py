# main import's 
import sys
import os
import xbmc

# Script constants 
__scriptname__ = "CU Lyrics"
__author__ = "Amet"
__url__ = "http://xbmc.org/forum/showthread.php?p=449687"
__svn_url__ = ""
__credits__ = "EnderW,Nuka1195"
__version__ = "0.7.6"
__XBMC_Revision__ = "22240"
__svn_revision__ = 0

# Shared resources 
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )

sys.path.append (BASE_RESOURCE_PATH)
__language__ = xbmc.Language( os.getcwd() ).getLocalizedString
__settings__ = xbmc.Settings( path=os.getcwd() )


# Start the main gui or settings gui 
if ( __name__ == "__main__" ):
    if ( xbmc.Player().isPlayingAudio() ):
        import gui as gui
        window = "main"
        ui = gui.GUI( "script-XBMC_Lyrics-main.xml" , os.getcwd(), "Default" )
        ui.doModal()
        del ui
        #sys.modules.clear()
    else:
        __settings__.openSettings()
    
    
    sys.modules.clear()
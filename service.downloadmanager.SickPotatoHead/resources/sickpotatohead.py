# Initializes and launches Couchpotato V2, Sickbeard and Headphones
from xml.dom.minidom import parseString
from lib.configobj import ConfigObj
import os
import time
import subprocess
import hashlib
import xbmc
import xbmcaddon
import xbmcvfs


def main():
    # helper functions
    def create_dir(dirname):
        if not xbmcvfs.exists(dirname):
            xbmcvfs.mkdirs(dirname)
            xbmc.log('SickPotatoHead: Created directory ' + dirname, level=xbmc.LOGDEBUG)
    # define some things that we're gonna need, mainly paths
    # ------------------------------------------------------
    
    # addon
    __addon__             = xbmcaddon.Addon(id='service.downloadmanager.SickPotatoHead')
    __addonpath__         = xbmc.translatePath(__addon__.getAddonInfo('path'))
    __addonhome__         = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    __dependencies__      = xbmc.translatePath(xbmcaddon.Addon(id='script.module.audo-dependencies').getAddonInfo('path'))
    
    # settings
    pdefaultsuitesettings 		= xbmc.translatePath(__addonpath__ + '/settings-default.xml')
    psuitesettings        		= xbmc.translatePath(__addonhome__ + 'settings.xml')
    pxbmcsettings         		= xbmc.translatePath('special://home/userdata/guisettings.xml')
    psickbeardsettings    		= xbmc.translatePath(__addonhome__ + 'sickbeard.ini')
    pcouchpotatoserversettings  = xbmc.translatePath(__addonhome__ + 'couchpotatoserver.ini')
    pheadphonessettings   		= xbmc.translatePath(__addonhome__ + 'headphones.ini')
    
    # create the settings file if missing
    if not xbmcvfs.exists(psuitesettings):
        xbmcvfs.copy(pdefaultsuitesettings, psuitesettings)
    
    # Get Device Home DIR
    phomedir = os.path.expanduser('~/')
    
    # directories
    psickpotatoheadcomplete    = phomedir + 'downloads'
    psickpotatoheadcompletetv  = phomedir + 'downloads/tvshows'
    psickpotatoheadcompletemov = phomedir + 'downloads/movies'
    psickpotatoheadwatchdir    = phomedir + 'downloads/watch'
    
    # pylib
    ppylib            = xbmc.translatePath(__addonpath__ + '/resources/lib')
    
    # service commands
    sickbeard         = ['python', xbmc.translatePath(__addonpath__ + '/resources/SickBeard/SickBeard.py'),
                         '--daemon', '--datadir', __addonhome__, '--pidfile=/var/run/sickbeard.pid', '--config',
                         psickbeardsettings]
    couchpotatoserver = ['python', xbmc.translatePath(__addonpath__ + '/resources/CouchPotatoServer/CouchPotato.py'),
                         '--daemon', '--pid_file=/var/run/couchpotato.pid', '--config_file', pcouchpotatoserversettings]
    headphones        = ['python', xbmc.translatePath(__addonpath__ + '/resources/Headphones/Headphones.py'),
                         '-d', '--datadir', __addonhome__, '--pidfile=/var/run/headphones.pid', '--config',
                         pheadphonessettings]
    
    # create directories and settings if missing
    # -----------------------------------------------
    
    sbfirstlaunch = not xbmcvfs.exists(psickbeardsettings)
    cpfirstlaunch = not xbmcvfs.exists(pcouchpotatoserversettings)
    hpfirstlaunch = not xbmcvfs.exists(pheadphonessettings)
    
    xbmc.log('SickPotatoHead: Creating directories if missing', level=xbmc.LOGDEBUG)
    create_dir(__addonhome__)
    create_dir(psickpotatoheadcomplete)
    create_dir(psickpotatoheadcompletetv)
    create_dir(psickpotatoheadcompletemov)
    create_dir(psickpotatoheadwatchdir)
    
    # read addon and xbmc settings
    # ----------------------------
    
    # Transmission-Daemon
    transauth = False
    try:
        transmissionaddon = xbmcaddon.Addon(id='service.downloadmanager.transmission')
        transauth = (transmissionaddon.getSetting('TRANSMISSION_AUTH').lower() == 'true')
    
        if transauth:
            xbmc.log('SickPotatoHead: Transmission Authentication Enabled', level=xbmc.LOGDEBUG)
            transuser = (transmissionaddon.getSetting('TRANSMISSION_USER').decode('utf-8'))
            if transuser == '':
                transuser = None
            transpwd = (transmissionaddon.getSetting('TRANSMISSION_PWD').decode('utf-8'))
            if transpwd == '':
                transpwd = None
        else:
            xbmc.log('SickPotatoHead: Transmission Authentication Not Enabled', level=xbmc.LOGDEBUG)
    
    except Exception, e:
        xbmc.log('SickPotatoHead: Transmission Settings are not present', level=xbmc.LOGNOTICE)
        xbmc.log(str(e), level=xbmc.LOGNOTICE)
        pass
    
    # SickPotatoHead-Suite
    user = (__addon__.getSetting('SICKPOTATOHEAD_USER').decode('utf-8'))
    pwd = (__addon__.getSetting('SICKPOTATOHEAD_PWD').decode('utf-8'))
    host = (__addon__.getSetting('SICKPOTATOHEAD_IP'))
    sickbeard_launch = (__addon__.getSetting('SICKBEARD_LAUNCH').lower() == 'true')
    couchpotato_launch = (__addon__.getSetting('COUCHPOTATO_LAUNCH').lower() == 'true')
    headphones_launch = (__addon__.getSetting('HEADPHONES_LAUNCH').lower() == 'true')
    
    # XBMC
    fxbmcsettings                 = open(pxbmcsettings, 'r')
    data                          = fxbmcsettings.read()
    fxbmcsettings.close()
    xbmcsettings                  = parseString(data)
    xbmcservices                  = xbmcsettings.getElementsByTagName('services')[0]
    xbmcport                      = xbmcservices.getElementsByTagName('webserverport')[0].firstChild.data
    try:
        xbmcuser                      = xbmcservices.getElementsByTagName('webserverusername')[0].firstChild.data
    except StandardError:
        xbmcuser                      = ''
    try:
        xbmcpwd                       = xbmcservices.getElementsByTagName('webserverpassword')[0].firstChild.data
    except StandardError:
        xbmcpwd                       = ''
    
    # prepare execution environment
    # -----------------------------
    parch                         = os.uname()[4]
    
    xbmc.log('SickPotatoHead: ' + parch + ' architecture detected', level=xbmc.LOGDEBUG)
    
    if not xbmcvfs.exists(xbmc.translatePath(__dependencies__ + '/arch.' + parch)):
	    xbmc.log('AUDO: Setting up binaries:', level=xbmc.LOGDEBUG)
	    try:
	        xbmc.executebuiltin('XBMC.RunScript(%s)' % xbmc.translatePath(__dependencies__ + '/default.py'), True)
	    except Exception, e:
	        xbmc.log('AUDO: Error setting up binaries:', level=xbmc.LOGERROR)
	        xbmc.log(str(e), level=xbmc.LOGERROR)
	    while not xbmcvfs.exists(xbmc.translatePath(__dependencies__ + '/arch.' + parch)):
	        time.sleep(5)
    
    os.environ['PYTHONPATH'] = str(os.environ.get('PYTHONPATH')) + ':' + ppylib + ':' + __dependencies__ + '/lib'
    os.environ['PYTHONPATH'] = str(os.environ.get('PYTHONPATH')) + ':' + (xbmc.translatePath(__addonpath__ + '/bin'))
    
    os_env = os.environ
    os_env["PATH"] = (xbmc.translatePath(__dependencies__ + '/bin:')) + os_env["PATH"]
    
    # SickBeard start
    try:
        # write SickBeard settings
        # ------------------------
        if sbfirstlaunch:
            sickbeardconfig = ConfigObj(psickbeardsettings, create_empty=True)
            defaultconfig = ConfigObj()
            defaultconfig['General'] = {}
            defaultconfig['General']['launch_browser']             = '0'
            defaultconfig['General']['version_notify']             = '1'
            defaultconfig['General']['web_port']                   = '8082'
            defaultconfig['General']['web_host']                   = host
            defaultconfig['General']['web_username']               = user
            defaultconfig['General']['web_password']               = pwd
            defaultconfig['General']['cache_dir']                  = __addonhome__ + 'sbcache'
            defaultconfig['General']['log_dir']                    = __addonhome__ + 'logs'
            defaultconfig['XBMC'] = {}
            defaultconfig['XBMC']['use_xbmc']                      = '1'
            defaultconfig['XBMC']['xbmc_host']                     = 'localhost:' + xbmcport
            defaultconfig['XBMC']['xbmc_username']                 = xbmcuser
            defaultconfig['XBMC']['xbmc_password']                 = xbmcpwd
            defaultconfig['TORRENT'] = {}
            defaultconfig['TORRENT']['torrent_path']               = psickpotatoheadcompletetv

            if transauth:
                defaultconfig['TORRENT']['torrent_username']           = transuser
                defaultconfig['TORRENT']['torrent_password']           = transpwd
                defaultconfig['TORRENT']['torrent_host']               = 'http://localhost:9091/'

            defaultconfig['General']['tv_download_dir']            = psickpotatoheadcomplete
            defaultconfig['General']['metadata_xbmc_12plus']       = '0|0|0|0|0|0|0|0|0|0'
            defaultconfig['General']['keep_processed_dir']         = '0'
            defaultconfig['General']['use_banner']                 = '1'
            defaultconfig['General']['rename_episodes']            = '1'
            defaultconfig['General']['naming_ep_name']             = '0'
            defaultconfig['General']['naming_use_periods']         = '1'
            defaultconfig['General']['naming_sep_type']            = '1'
            defaultconfig['General']['naming_ep_type']             = '1'
            defaultconfig['General']['root_dirs']                  = '0|' + phomedir + 'tvshows'
            defaultconfig['General']['naming_custom_abd']          = '0'
            defaultconfig['General']['naming_abd_pattern']         = '%SN - %A-D - %EN'
            defaultconfig['Blackhole'] = {}
            defaultconfig['Blackhole']['torrent_dir']              = psickpotatoheadwatchdir
            defaultconfig['EZRSS'] = {}
            defaultconfig['EZRSS']['ezrss']                        = '1'
            defaultconfig['PUBLICHD'] = {}
            defaultconfig['PUBLICHD']['publichd']                  = '1'
            defaultconfig['KAT'] = {}
            defaultconfig['KAT']['kat']                            = '1'
            defaultconfig['THEPIRATEBAY'] = {}
            defaultconfig['THEPIRATEBAY']['thepiratebay']          = '1'
            defaultconfig['Womble'] = {}
            defaultconfig['Womble']['womble']                      = '0'
            defaultconfig['XBMC']['xbmc_notify_ondownload']        = '1'
            defaultconfig['XBMC']['xbmc_notify_onsnatch']          = '1'
            defaultconfig['XBMC']['xbmc_update_library']           = '1'
            defaultconfig['XBMC']['xbmc_update_full']              = '1'
    
            sickbeardconfig.merge(defaultconfig)
            sickbeardconfig.write()
    
        # launch SickBeard
        # ----------------
        if sickbeard_launch:
            xbmc.log('SickPotatoHead: Launching SickBeard...', level=xbmc.LOGDEBUG)
            subprocess.call(sickbeard, close_fds=True, env=os_env)
            xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: SickBeard exception occurred', level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)
    # SickBeard end
    
    # CouchPotatoServer start
    try:
        # empty password hack
        if pwd == '':
            md5pwd = ''
        else:
            # convert password to md5
            md5pwd = hashlib.md5(str(pwd)).hexdigest()
    
        # write CouchPotatoServer settings
        # --------------------------
        if cpfirstlaunch:
            couchpotatoserverconfig = ConfigObj(pcouchpotatoserversettings, create_empty=True, list_values=False)
            defaultconfig = ConfigObj()
            defaultconfig['core'] = {}
            defaultconfig['core']['username']                      = user
            defaultconfig['core']['password']                      = md5pwd
            defaultconfig['core']['port']                          = '8083'
            defaultconfig['core']['launch_browser']                = '0'
            defaultconfig['core']['host']                          = host
            defaultconfig['core']['data_dir']                      = __addonhome__
            defaultconfig['updater'] = {}
            defaultconfig['updater']['enabled']                    = '1'
            defaultconfig['updater']['notification']               = '1'
            defaultconfig['updater']['automatic']                  = '0'
            defaultconfig['xbmc'] = {}
            defaultconfig['xbmc']['enabled']                       = '1'
            defaultconfig['xbmc']['host']                          = 'localhost:' + xbmcport
            defaultconfig['xbmc']['username']                      = xbmcuser
            defaultconfig['xbmc']['password']                      = xbmcpwd
            defaultconfig['transmission'] = {}
            defaultconfig['transmission']['directory']             = psickpotatoheadcompletemov

            if transauth:
                defaultconfig['transmission']['username']              = transuser
                defaultconfig['transmission']['password']              = transpwd
                defaultconfig['transmission']['host']                  = 'localhost:9091'

            defaultconfig['xbmc']['xbmc_update_library']           = '1'
            defaultconfig['xbmc']['xbmc_update_full']              = '1'
            defaultconfig['xbmc']['xbmc_notify_onsnatch']          = '1'
            defaultconfig['xbmc']['xbmc_notify_ondownload']        = '1'
            defaultconfig['blackhole'] = {}
            defaultconfig['blackhole']['directory']                = psickpotatoheadwatchdir
            defaultconfig['blackhole']['use_for']                  = 'torrent'
            defaultconfig['blackhole']['enabled']                  = '0'
            defaultconfig['renamer'] = {}
            defaultconfig['renamer']['enabled']                    = '0'
            defaultconfig['renamer']['from']                       = psickpotatoheadcompletemov
            defaultconfig['renamer']['separator']                  = '.'
            defaultconfig['renamer']['cleanup']                    = '0'
            defaultconfig['nzbindex'] = {}
            defaultconfig['nzbindex']['enabled']                   = '0'
            defaultconfig['mysterbin'] = {}
            defaultconfig['mysterbin']['enabled']                  = '0'
            defaultconfig['core']['permission_folder']             = '0644'
            defaultconfig['core']['permission_file']               = '0644'
            defaultconfig['core']['show_wizard']                   = '0'
            defaultconfig['core']['debug']                         = '0'
            defaultconfig['core']['development']                   = '0'
            defaultconfig['searcher'] = {}
            defaultconfig['searcher']['preferred_method']          = 'torrent'
    
            couchpotatoserverconfig.merge(defaultconfig)
            couchpotatoserverconfig.write()
    
        # launch CouchPotatoServer
        # ------------------
        if couchpotato_launch:
            xbmc.log('SickPotatoHead: Launching CouchPotatoServer...', level=xbmc.LOGDEBUG)
            subprocess.call(couchpotatoserver, close_fds=True, env=os_env)
            xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: CouchPotatoServer exception occurred', level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)
    # CouchPotatoServer end
    
    # Headphones start
    try:
        # write Headphones settings
        # -------------------------
        if hpfirstlaunch:
            headphonesconfig = ConfigObj(pheadphonessettings, create_empty=True)
            defaultconfig = ConfigObj()
            defaultconfig['General'] = {}
            defaultconfig['General']['launch_browser']             = '0'
            defaultconfig['General']['http_port']                  = '8084'
            defaultconfig['General']['http_host']                  = host
            defaultconfig['General']['http_username']              = user
            defaultconfig['General']['http_password']              = pwd
            defaultconfig['General']['check_github']               = '0'
            defaultconfig['General']['check_github_on_startup']    = '0'
            defaultconfig['General']['cache_dir']                  = __addonhome__ + 'hpcache'
            defaultconfig['General']['log_dir']                    = __addonhome__ + 'logs'
            defaultconfig['XBMC'] = {}
            defaultconfig['XBMC']['xbmc_enabled']                  = '1'
            defaultconfig['XBMC']['xbmc_host']                     = 'localhost:' + xbmcport
            defaultconfig['XBMC']['xbmc_username']                 = xbmcuser
            defaultconfig['XBMC']['xbmc_password']                 = xbmcpwd
            defaultconfig['Transmission'] = {}

            if transauth:
                defaultconfig['Transmission']['transmission_username'] = transuser
                defaultconfig['Transmission']['transmission_password'] = transpwd
                defaultconfig['Transmission']['transmission_host']     = 'http://localhost:9091'

            defaultconfig['XBMC']['xbmc_update']                   = '1'
            defaultconfig['XBMC']['xbmc_notify']                   = '1'
            defaultconfig['General']['music_dir']                  = phomedir + 'music'
            defaultconfig['General']['destination_dir']            = phomedir + 'music'
            defaultconfig['General']['torrentblackhole_dir']       = psickpotatoheadwatchdir
            defaultconfig['General']['download_torrent_dir']       = psickpotatoheadcomplete
            defaultconfig['General']['move_files']                 = '1'
            defaultconfig['General']['rename_files']               = '1'
            defaultconfig['General']['folder_permissions']         = '0644'
            defaultconfig['General']['isohunt']                    = '1'
            defaultconfig['General']['kat']                        = '1'
            defaultconfig['General']['mininova']                   = '1'
            defaultconfig['General']['piratebay']                  = '1'

            headphonesconfig.merge(defaultconfig)
            headphonesconfig.write()

        # launch Headphones
        # -----------------
        if headphones_launch:
            xbmc.log('SickPotatoHead: Launching Headphones...', level=xbmc.LOGDEBUG)
            subprocess.call(headphones, close_fds=True, env=os_env)
            xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: Headphones exception occurred', level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)
    # Headphones end

# -*- coding: utf-8 -*-
"""
Base ASDF for I/O and plotting of earthquake data
    
:Copyright:
    Author: Lili Feng
    email: lfeng1011@gmail.com
"""
import pyasdf
import numpy as np
import matplotlib.pyplot as plt
import obspy
import obspy.io.sac
from datetime import datetime
import warnings
import tarfile
import shutil
import glob
import os
if os.path.isdir('/home/lili/anaconda3/share/proj'):
    os.environ['PROJ_LIB'] = '/home/lili/anaconda3/share/proj'
from mpl_toolkits.basemap import Basemap, shiftgrid, cm

monthdict   = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}

    
class baseASDF(pyasdf.ASDFDataSet):
    """ An object to for ambient noise cross-correlation analysis based on ASDF database
    =================================================================================================================
    version history:
        2020/07/09
    =================================================================================================================
    """
    def __init__(
        self,
        filename,
        compression="gzip-3",
        shuffle=True,
        debug=False,
        mpi=None,
        mode="a",
        single_item_read_limit_in_mb=4096.0,
        format_version=None,
        ):
        # initialize ASDF
        super(baseASDF, self).__init__( filename = filename, compression=compression, shuffle=shuffle, debug=debug,
            mpi=mpi, mode=mode, single_item_read_limit_in_mb=single_item_read_limit_in_mb, format_version=format_version)
        #======================================
        # initializations of other attributes
        #======================================
        # range of station coverage
        try:
            limits_lonlat_param = self.auxiliary_data.NoiseXcorr['limits_lonlat'].parameters
            self.minlat         = limits_lonlat_param['minlat']
            self.maxlat         = limits_lonlat_param['maxlat']
            self.minlon         = limits_lonlat_param['minlon']
            self.maxlon         = limits_lonlat_param['maxlon']
        except:
            pass
        # station inventory; start/end date of the stations
        self.inv        = obspy.Inventory()
        self.start_date = obspy.UTCDateTime('2599-01-01')
        self.end_date   = obspy.UTCDateTime('1900-01-01')
        # self.update_inv_info()
        return
    
    def update_inv_info(self):
        """update inventory information
        """
        start_date      = self.start_date
        end_date        = self.end_date
        for staid in self.waveforms.list():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.inv    += self.waveforms[staid].StationXML
                if start_date > self.waveforms[staid].StationXML[0][0].start_date:
                    start_date  = self.waveforms[staid].StationXML[0][0].start_date
                if end_date < self.waveforms[staid].StationXML[0][0].end_date:
                    end_date    = self.waveforms[staid].StationXML[0][0].end_date
        self.start_date = start_date
        self.end_date   = end_date
        if len(self.inv) > 0:
            self.get_limits_lonlat()
        return
    
    def get_limits_lonlat(self):
        """get the geographical limits of the stations
        """
        staLst      = self.waveforms.list()
        minlat      = 90.
        maxlat      = -90.
        minlon      = 360.
        maxlon      = 0.
        for staid in staLst:
            tmppos  = self.waveforms[staid].coordinates
            lat     = tmppos['latitude']
            lon     = tmppos['longitude']
            elv     = tmppos['elevation_in_m']
            if lon<0:
                lon         += 360.
            minlat  = min(lat, minlat)
            maxlat  = max(lat, maxlat)
            minlon  = min(lon, minlon)
            maxlon  = max(lon, maxlon)
        print ('latitude range: ', minlat, '-', maxlat, 'longitude range:', minlon, '-', maxlon)
        self.minlat = minlat
        self.maxlat = maxlat
        self.minlon = minlon
        self.maxlon = maxlon
        return
    
    def copy_catalog(self):
        print('Copying catalog from ASDF to memory')
        self.cat    = self.events
        return
    
    def print_info(self):
        """
        Print information of the dataset.
        """
        outstr  = '============================================================ Earthquake Database ===========================================================\n'
        outstr  += self.__str__()+'\n'
        outstr  += '--------------------------------------------------------- Surface wave auxiliary Data ------------------------------------------------------\n'
        if 'DISPbasic1' in self.auxiliary_data.list():
            outstr      += 'DISPbasic1              - Basic dispersion curve, no jump correction\n'
        if 'DISPbasic2' in self.auxiliary_data.list():
            outstr      += 'DISPbasic2              - Basic dispersion curve, with jump correction\n'
        if 'DISPpmf1' in self.auxiliary_data.list():
            outstr      += 'DISPpmf1                - PMF dispersion curve, no jump correction\n'
        if 'DISPpmf2' in self.auxiliary_data.list():
            outstr      += 'DISPpmf2                - PMF dispersion curve, with jump correction\n'
        if 'DISPbasic1interp' in self.auxiliary_data.list():
            outstr      += 'DISPbasic1interp        - Interpolated DISPbasic1\n'
        if 'DISPbasic2interp' in self.auxiliary_data.list():
            outstr      += 'DISPbasic2interp        - Interpolated DISPbasic2\n'
        if 'DISPpmf1interp' in self.auxiliary_data.list():
            outstr      += 'DISPpmf1interp          - Interpolated DISPpmf1\n'
        if 'DISPpmf2interp' in self.auxiliary_data.list():
            outstr      += 'DISPpmf2interp          - Interpolated DISPpmf2\n'
        if 'FieldDISPbasic1interp' in self.auxiliary_data.list():
            outstr      += 'FieldDISPbasic1interp   - Field data of DISPbasic1\n'
        if 'FieldDISPbasic2interp' in self.auxiliary_data.list():
            outstr      += 'FieldDISPbasic2interp   - Field data of DISPbasic2\n'
        if 'FieldDISPpmf1interp' in self.auxiliary_data.list():
            outstr      += 'FieldDISPpmf1interp     - Field data of DISPpmf1\n'
        if 'FieldDISPpmf2interp' in self.auxiliary_data.list():
            outstr      += 'FieldDISPpmf2interp     - Field data of DISPpmf2\n'
        outstr  += '============================================================================================================================================\n'
        print (outstr)
        return
    
    def write_stationxml(self, staxml, source='LF'):
        """write obspy inventory to StationXML data file
        """
        inv     = obspy.core.inventory.inventory.Inventory(networks=[], source=source)
        for staid in self.waveforms.list():
            inv += self.waveforms[staid].StationXML
        inv.write(staxml, format='stationxml')
        return
    
    def copy_stations(self, inasdffname, startdate=None, enddate=None, location=None, channel=None, includerestricted=False,
            minlatitude=None, maxlatitude=None, minlongitude=None, maxlongitude=None, latitude=None, longitude=None, minradius=None, maxradius=None):
        """copy and renew station inventory given an input ASDF file
            the function will copy the network and station names while renew other informations given new limitations
        =======================================================================================================
        ::: input parameters :::
        inasdffname         - input ASDF file name
        startdate, enddata  - start/end date for searching
        network             - Select one or more network codes.
                                Can be SEED network codes or data center defined codes.
                                    Multiple codes are comma-separated (e.g. "IU,TA").
        station             - Select one or more SEED station codes.
                                Multiple codes are comma-separated (e.g. "ANMO,PFO").
        location            - Select one or more SEED location identifiers.
                                Multiple identifiers are comma-separated (e.g. "00,01").
                                As a special case “--“ (two dashes) will be translated to a string of two space
                                characters to match blank location IDs.
        channel             - Select one or more SEED channel codes.
                                Multiple codes are comma-separated (e.g. "BHZ,HHZ").             
        minlatitude         - Limit to events with a latitude larger than the specified minimum.
        maxlatitude         - Limit to events with a latitude smaller than the specified maximum.
        minlongitude        - Limit to events with a longitude larger than the specified minimum.
        maxlongitude        - Limit to events with a longitude smaller than the specified maximum.
        latitude            - Specify the latitude to be used for a radius search.
        longitude           - Specify the longitude to the used for a radius search.
        minradius           - Limit to events within the specified minimum number of degrees from the
                                geographic point defined by the latitude and longitude parameters.
        maxradius           - Limit to events within the specified maximum number of degrees from the
                                geographic point defined by the latitude and longitude parameters.
        =======================================================================================================
        """
        try:
            starttime   = obspy.core.utcdatetime.UTCDateTime(startdate)
        except:
            starttime   = None
        try:
            endtime     = obspy.core.utcdatetime.UTCDateTime(enddate)
        except:
            endtime     = None
        client          = Client('IRIS')
        init_flag       = False
        indset          = pyasdf.ASDFDataSet(inasdffname)
        for staid in indset.waveforms.list():
            network     = staid.split('.')[0]
            station     = staid.split('.')[1]
            print ('Copying/renewing station inventory: '+ staid)
            if init_flag:
                inv     += client.get_stations(network=network, station=station, starttime=starttime, endtime=endtime, channel=channel, 
                            minlatitude=minlatitude, maxlatitude=maxlatitude, minlongitude=minlongitude, maxlongitude=maxlongitude,
                            latitude=latitude, longitude=longitude, minradius=minradius, maxradius=maxradius, level='channel',
                            includerestricted=includerestricted)
            else:
                inv     = client.get_stations(network=network, station=station, starttime=starttime, endtime=endtime, channel=channel, 
                            minlatitude=minlatitude, maxlatitude=maxlatitude, minlongitude=minlongitude, maxlongitude=maxlongitude,
                            latitude=latitude, longitude=longitude, minradius=minradius, maxradius=maxradius, level='channel',
                            includerestricted=includerestricted)
                init_flag= True
        self.add_stationxml(inv)
        try:
            self.inv    +=inv
        except:
            self.inv    = inv
        return
            
    def _get_basemap(self, projection='lambert', resolution='i', blon=0., blat=0.):
        """Get basemap for plotting results
        """
        # fig=plt.figure(num=None, figsize=(12, 12), dpi=80, facecolor='w', edgecolor='k')
        try:
            minlon  = self.minlon-blon
            maxlon  = self.maxlon+blon
            minlat  = self.minlat-blat
            maxlat  = self.maxlat+blat
        except AttributeError:
            self.get_limits_lonlat()
            minlon  = self.minlon-blon
            maxlon  = self.maxlon+blon
            minlat  = self.minlat-blat
            maxlat  = self.maxlat+blat
        lat_centre  = (maxlat+minlat)/2.0
        lon_centre  = (maxlon+minlon)/2.0
        if projection == 'merc':
            m       = Basemap(projection='merc', llcrnrlat=minlat-5., urcrnrlat=maxlat+5., llcrnrlon=minlon-5.,
                        urcrnrlon=maxlon+5., lat_ts=20, resolution=resolution)
            m.drawparallels(np.arange(-80.0,80.0,5.0), labels=[1,0,0,1])
            m.drawmeridians(np.arange(-170.0,170.0,5.0), labels=[1,0,0,1])
            m.drawstates(color='g', linewidth=2.)
        elif projection == 'global':
            m       = Basemap(projection='ortho',lon_0=lon_centre, lat_0=lat_centre, resolution=resolution)
        elif projection == 'regional_ortho':
            m1      = Basemap(projection='ortho', lon_0=minlon, lat_0=minlat, resolution='l')
            m       = Basemap(projection='ortho', lon_0=minlon, lat_0=minlat, resolution=resolution,\
                        llcrnrx=0., llcrnry=0., urcrnrx=m1.urcrnrx/mapfactor, urcrnry=m1.urcrnry/3.5)
            m.drawparallels(np.arange(-80.0,80.0,10.0), labels=[1,0,0,0],  linewidth=2,  fontsize=20)
            m.drawmeridians(np.arange(-170.0,170.0,10.0),  linewidth=2)
        elif projection=='lambert':
            distEW, az, baz = obspy.geodetics.gps2dist_azimuth(minlat, minlon, minlat, maxlon) # distance is in m
            distNS, az, baz = obspy.geodetics.gps2dist_azimuth(minlat, minlon, maxlat+2., minlon) # distance is in m
            m               = Basemap(width = distEW, height=distNS, rsphere=(6378137.00,6356752.3142), resolution='l', projection='lcc',\
                                lat_1=minlat, lat_2=maxlat, lon_0=lon_centre, lat_0=lat_centre+1)
            m.drawparallels(np.arange(-80.0,80.0,10.0), linewidth=1, dashes=[2,2], labels=[1,1,0,0], fontsize=15)
            m.drawmeridians(np.arange(-170.0,170.0,10.0), linewidth=1, dashes=[2,2], labels=[0,0,1,0], fontsize=15)
        try:
            m.drawcoastlines(linewidth=1.0)
        except:
            pass
        m.drawcountries(linewidth=1.)
        # m.fillcontinents(lake_color='#99ffff',zorder=0.2)
        # m.drawmapboundary(fill_color="white")
        return m
    
    def plot_stations(self, projection='lambert', tomo_vertices=[], showfig=True, blon=.5, blat=0.5):
        """plot station map
        ==============================================================================
        ::: input parameters :::
        projection      - type of geographical projection
        geopolygons     - geological polygons for plotting
        blon, blat      - extending boundaries in longitude/latitude
        showfig         - show figure or not
        ==============================================================================
        """
        staLst              = self.waveforms.list()
        stalons             = np.array([])
        stalats             = np.array([])
        for staid in staLst:
            with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    tmppos  = self.waveforms[staid].coordinates
            stla            = tmppos['latitude']
            stlo            = tmppos['longitude']
            evz             = tmppos['elevation_in_m']
            stalons         = np.append(stalons, stlo); stalats=np.append(stalats, stla)
        m                   = self._get_basemap(projection=projection, blon=blon, blat=blat)
        m.etopo()
        # m.shadedrelief()
        stax, stay          = m(stalons, stalats)
        m.plot(stax, stay, 'b^', markersize=10)
        if len(tomo_vertices) >= 3:
            lons    = []
            lats    = []
            for vertice in tomo_vertices:
                lons.append(vertice[0])
                lats.append(vertice[1])
            verx, very          = m(lons, lats)
            m.plot(verx, very, 'r-')
            m.plot([verx[-1], verx[0]], [very[-1], very[0]], 'r-')
        
        if showfig:
            plt.show()
        return
    
    def load_tar_mseed(self, datadir, outdir = None, start_date = None, end_date = None, unit_nm = True, sps = 1., rmresp = True,
            ninterp = 2, vmin=1.0, vmax=6.0, chanrank=['LH', 'BH', 'HH'], channels='Z', perl = 5., perh = 300., rotate = True, \
            pfx='LF_', delete_tar = False, delete_extract = True, verbose = True, verbose2 = False):
        """load tarred mseed data
        """
        if channels != 'EN' and channels != 'ENZ' and channels != 'Z':
            raise ValueError('Unexpected channels = '+channels)
        try:
            print (self.cat)
        except AttributeError:
            self.copy_catalog()
        try:
            stime4load  = obspy.core.utcdatetime.UTCDateTime(start_date)
        except:
            stime4load  = obspy.UTCDateTime(0)
        try:
            etime4load  = obspy.core.utcdatetime.UTCDateTime(end_date)
        except:
            etime4load  = obspy.UTCDateTime()
        # frequencies for response removal 
        f2          = 1./(perh*1.3)
        f1          = f2*0.8
        f3          = 1./(perl*0.8)
        f4          = f3*1.2
        Nnodataev   = 0
        Nevent      = 0
        # loop over events
        for event in self.cat:
            otime           = event.origins[0].time
            event_id        = event.resource_id.id.split('=')[-1]
            event_descrip   = event.event_descriptions[0].text+', '+event.event_descriptions[0].type
            magnitude       = event.magnitudes[0].mag
            Mtype           = event.magnitudes[0].magnitude_type
            timestr         = otime.isoformat()
            evlo            = event.origins[0].longitude
            evla            = event.origins[0].latitude
            evdp            = event.origins[0].depth
            if otime < stime4load or otime > etime4load:
                continue
            Nevent          += 1
            descrip         = event_descrip+', '+Mtype+' = '+str(magnitude)
            oyear           = otime.year
            omonth          = otime.month
            oday            = otime.day
            ohour           = otime.hour
            omin            = otime.minute
            osec            = otime.second
            label           = '%d_%s_%d_%d_%d_%d' %(oyear, monthdict[omonth], oday, ohour, omin, osec)
            tarwildcard     = datadir+'/'+pfx + label +'.*.tar.mseed'
            tarlst          = glob.glob(tarwildcard)
            if len(tarlst) == 0:
                print ('!!! NO DATA: %s %s' %(otime.isoformat(), descrip))
                Nnodataev  += 1
                continue
            elif len(tarlst) > 1:
                print ('!!! MORE DATA DATE: %s %s' %(otime.isoformat(), descrip))
            if verbose:
                print ('[%s] [LOAD_MSEED] loading: %s %s' %(datetime.now().isoformat().split('.')[0], \
                            otime.isoformat(), descrip))
            # extract tar files
            tmptar          = tarfile.open(tarlst[0])
            tmptar.extractall(path = datadir)
            tmptar.close()
            eventdir        = datadir+'/'+(tarlst[0].split('/')[-1])[:-10]
            if outdir is not None:
                outeventdir = outdir+'/'+label
                if not os.path.isdir(outeventdir):
                    os.makedirs(outeventdir)
            # loop over stations
            Nsta            = 0
            Nnodata         = 0
            for staid in self.waveforms.list():
                netcode     = staid.split('.')[0]
                stacode     = staid.split('.')[1]
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    staxml  = self.waveforms[staid].StationXML
                mseedfname  = eventdir + '/' + stacode+'.'+netcode+'.mseed'
                xmlfname    = eventdir + '/IRISDMC-' + stacode+'.'+netcode+'.xml'
                stla        = staxml[0][0].latitude
                stlo        = staxml[0][0].longitude
                Nsta        += 1
                # load data
                if not os.path.isfile(mseedfname):
                    if otime >= staxml[0][0].creation_date and otime <= staxml[0][0].end_date:
                        print ('*** NO DATA STATION: '+staid)
                        Nnodata     += 1
                    continue
                # load data
                st              = obspy.read(mseedfname)
                #=============================
                # get response information
                # rmresp = True, from XML
                #=============================
                if rmresp:
                    if not os.path.isfile(xmlfname):
                        print ('*** NO RESPXML FILE STATION: '+staid)
                        resp_inv = staxml.copy()
                        try:
                            for tr in st:
                                seed_id     = tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location+'.'+tr.stats.channel
                                resp_inv.get_response(seed_id = seed_id, datatime = curtime)
                        except:
                            print ('*** NO RESP STATION: '+staid)
                            Nnodata     += 1
                            continue
                    else:
                        resp_inv = obspy.read_inventory(xmlfname)
                dist, az, baz   = obspy.geodetics.gps2dist_azimuth(evla, evlo, stla, stlo) # distance is in m
                dist            = dist/1000.
                starttime       = otime + dist/vmax
                endtime         = otime + dist/vmin
                # merge data, fill gaps
                st.merge(method = 1, interpolation_samples = ninterp, fill_value = 'interpolate')
                # choose channel type
                chan_type   = None
                for tmpchtype in chanrank:
                    ich     = 0
                    for chan in channels:
                        if len(st.select(channel = tmpchtype + chan)) > 0:
                            ich += 1
                    if ich == len(channels):
                        chan_type   = tmpchtype
                        break
                if chan_type is None:
                    print ('*** NO CHANNEL STATION: '+staid)
                    Nnodata     += 1
                    continue
                stream      = obspy.Stream()
                for chan in channels:
                    tmpst   = st.select(channel = chan_type + chan)
                    tmpst.trim(starttime = starttime, endtime = endtime, pad = False)
                    if len(tmpst) > 0 and verbose2:
                        print ('*** MORE THAN ONE LOCS STATION: '+staid)
                        Nvalid      = (tmpst[0].stats.npts)
                        outtr       = tmpst[0].copy()
                        for tmptr in tmpst:
                            tmp_n   = tmptr.stats.npts
                            if tmp_n > Nvalid:
                                Nvalid  = tmp_n
                                outtr   = tmptr.copy()
                        stream.append(outtr)
                    else:
                        stream.append(tmpst[0])
                if rmresp:
                    stream.detrend()
                    stream.remove_response(inventory = resp_inv, pre_filt = [f1, f2, f3, f4])
                    if unit_nm:
                        for i in range(len(stream)):
                            stream[i].data  *= 1e9
                    try:
                        stream.resample(sampling_rate = sps, no_filter = False)
                    except ArithmeticError:
                        pass
                if len(channels) >= 2:
                    if channels[:2] == 'EN' and rotate:
                        stream.rotate('NE->RT', back_azimuth = baz)
                        channels[:2] = 'RT'
                # save to SAC
                if outdir is not None:
                    for chan in channels:
                        outfname    = outeventdir+'/' + staid + '_'+chan_type+chan+'.SAC'
                        sactr       = obspy.io.sac.SACTrace.from_obspy_trace(stream.select(channel = chan_type + chan)[0])
                        sactr.o     = 0.
                        sactr.b     = starttime - otime
                        sactr.evlo  = evlo
                        sactr.evla  = evla
                        sactr.evdp  = evdp
                        sactr.mag   = magnitude
                        sactr.dist  = dist
                        sactr.az    = az
                        sactr.baz   = baz
                        sactr.write(outfname)
                # save data
                label2      = '%d_%d_%d_%d_%d_%d' %(oyear, omonth, oday, ohour, omin, osec)
                tag         = 'surf_'+label2
                # adding waveforms
                self.add_waveforms(stream, event_id = event_id, tag = tag)
            if verbose:
                print ('[%s] [LOAD_MSEED] %d/%d (data/no_data) groups of traces extracted!'\
                       %(datetime.now().isoformat().split('.')[0], Nsta - Nnodata, Nnodata))
            # delete raw data
            if delete_extract:
                shutil.rmtree(eventdir)
            if delete_tar:
                os.remove(tarlst[0])
            # # # if Nevent - Nnodataev > 3:
            # # #     break
        # End loop over events
        print ('[%s] [LOAD_MSEED] Extracted %d/%d (events_with)data/total_events) events of data'\
               %(datetime.now().isoformat().split('.')[0], Nevent - Nnodataev, Nevent))
        return
    
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
import csv, os
from geodb.models import AfgFldzonea100KRiskLandcoverPop, AfgLndcrva, AfgAdmbndaAdm2, AfgFldzonea100KRiskMitigatedAreas, AfgAvsa, Forcastedvalue, AfgShedaLvl4, districtsummary 
import requests
from django.core.files.base import ContentFile
import urllib2, base64
import urllib
from PIL import Image
from StringIO import StringIO
from django.db.models import Count, Sum, F
import time, sys
import subprocess

from urlparse import urlparse
from geonode.maps.models import Map
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW

from geodb.geoapi import getRiskExecuteExternal

# addded by boedy
from matrix.models import matrix
import datetime
from django.conf import settings
from ftplib import FTP

import StringIO
import gzip
import glob
from django.contrib.gis.gdal import DataSource
from django.db import connection
from django.contrib.gis.geos import fromstr


# from geodb.views import getForecastedDisaster
# getForecastedDisaster()

GS_TMP_DIR = getattr(settings, 'GS_TMP_DIR', '/tmp')

initial_data_path = "/home/ubuntu/DRR-datacenter/geodb/initialdata/" # Production
gdal_path = '/usr/bin/' # production
# initial_data_path = "/Users/budi/Documents/iMMAP/DRR-datacenter/geodb/initialdata/" # in developement
# gdal_path = '/usr/local/bin/' # development


def getLatestShakemap():
    print 'kontol'

def getSnowCover():
    today  = datetime.datetime.now()
    year = today.strftime("%Y")
    
    base_url = 'sidads.colorado.edu' 
    filelist=[]
 
    ftp = FTP(base_url)
    ftp.login()
    ftp.cwd("pub/DATASETS/NOAA/G02156/GIS/1km/"+ "{year}/".format(year=year))

    ftp.retrlines('LIST',filelist.append)

    ftp.retrbinary("RETR " + filelist[-1].split()[8], open(os.path.join(GS_TMP_DIR,filelist[-1].split()[8]),"wb").write)


    decompressedFile = gzip.GzipFile(os.path.join(GS_TMP_DIR,filelist[-1].split()[8]), 'rb')
    s=decompressedFile.read()
    decompressedFile.close()
    outF = file(os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-3]), 'wb')
    outF.write(s)
    outF.close()

    ftp.quit()

    # print filelist[-1].split()[8][:-7]
    # print os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-3])
    # print os.path.join(gdal_path,'gdalwarp')

    subprocess.call('%s -te 2438000 4432000 4429000 6301000 %s %s' %(os.path.join(gdal_path,'gdalwarp'), os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-3]), os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_cropped.tif'),shell=True)
    subprocess.call('%s -t_srs EPSG:4326 %s %s' %(os.path.join(gdal_path,'gdalwarp'), os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_cropped.tif', os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_reproj.tif'),shell=True)

    subprocess.call('%s %s -f "ESRI Shapefile" %s' %(os.path.join(gdal_path,'gdal_polygonize.py'), os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_reproj.tif', os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_poly_temp.shp'),shell=True)
    subprocess.call('%s %s %s -where "DN=4"' %(os.path.join(gdal_path,'ogr2ogr'), os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_poly.shp', os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_poly_temp.shp'),shell=True)
    
    dsSHP = DataSource(os.path.join(GS_TMP_DIR,filelist[-1].split()[8][:-7])+'_poly.shp')
    lyrSHP = dsSHP[0]

    # for feat in lyrSHP:
    #     p = AfgAvsa.objects.filter(wkb_geometry__within=feat.geom.wkt)
    #     for row in p:
    #         print str(row.ogc_fid) + ' - ' + str(row.vuid)

    cleantmpfile('ims')
    

def cleantmpfile(filepattern):

    tmpfilelist = glob.glob("{}*.*".format(
        os.path.join(GS_TMP_DIR, filepattern)))
    for f in tmpfilelist:
        os.remove(f) 

def getForecastedDisaster():
    username = 'wmo'
    password = 'SAsia:14-ffg'
    auth_encoded = base64.encodestring('%s:%s' % (username, password))[:-1]

    year = datetime.datetime.utcnow().strftime("%Y")
    month = datetime.datetime.utcnow().strftime("%m")
    day = datetime.datetime.utcnow().strftime("%d")
    hh = datetime.datetime.utcnow().strftime("%H")

    hh = int(hh)-1

    if len(str(hh)) == 1:
        hhLabel = '0'+str(hh)
    else:
        hhLabel = str(hh)    

    url = 'https://sasiaffg.hrcwater.org/CONSOLE/EXPORTS/AFGHANISTAN/'+year+'/'+month+'/'+day+'/COMPOSITE_CSV/'+year+month+day+'-'+hhLabel+'00_ffgs_prod_composite_table_01hr_afghanistan.csv'
    print url

    req = urllib2.Request(url)
    req.add_header('Authorization', 'Basic %s' % auth_encoded)
    response = urllib2.urlopen(req)

    csv_f = csv.reader(response)
    Forcastedvalue.objects.all()
    pertama=True
    for row in csv_f:
        if not pertama:
            try:
                flashfloodArray = [float(row[21]),float(row[24]),float(row[27])]
                flashflood = max(flashfloodArray)
            except:
                flashflood = 0

            try:
                snowWater  = float(row[29])  
            except:
                snowWater = 0    

            flashFloodState = 0
            if flashflood > 0 and flashflood <= 5:
                flashFloodState = 1 # very low
            elif flashflood > 5 and flashflood <= 10:
                flashFloodState = 2 # low
            elif flashflood > 10 and flashflood <= 25:
                flashFloodState = 3 # moderate
            elif flashflood > 25 and flashflood <= 60:
                flashFloodState = 4 # high           
            elif flashflood > 60 and flashflood <= 100:
                flashFloodState = 5 # very high
            elif flashflood > 100:
                flashFloodState = 6 # Extreme


            snowWaterState = 0
            if snowWater > 60 and snowWater <= 100:
                snowWaterState = 1 #low
            elif snowWater > 100 and snowWater <= 140:
                snowWaterState = 2 #moderate
            elif snowWater > 140:
                snowWaterState = 3 #high    
    
            if flashFloodState>0:
                basin = AfgShedaLvl4.objects.get(value=row[0]) 
                recordExists = Forcastedvalue.objects.all().filter(datadate=year+'-'+month+'-'+day,forecasttype='flashflood',basin=basin)  
                if recordExists.count() > 0:
                    if recordExists[0].riskstate < flashFloodState:
                        c = Forcastedvalue(pk=recordExists[0].pk,basin=basin)  
                        c.riskstate = flashFloodState
                        c.save()
                        print 'flashflood modified'
                    print 'flashflood skip'    
                else:
                    c = Forcastedvalue(basin=basin)  
                    c.datadate = year+'-'+month+'-'+day
                    c.forecasttype = 'flashflood'
                    c.riskstate = flashFloodState 
                    c.save()
                    print 'flashflood added'

            if snowWaterState>0:
                basin = AfgShedaLvl4.objects.get(value=row[0]) 
                recordExists = Forcastedvalue.objects.all().filter(datadate=year+'-'+month+'-'+day,forecasttype='snowwater',basin=basin)  
                if recordExists.count() > 0:
                    if recordExists[0].riskstate < snowWaterState:
                        c = Forcastedvalue(pk=recordExists[0].pk,basin=basin)  
                        c.riskstate = snowWaterState
                        c.save()
                        print 'snowwater modified'
                    print 'snowwater skip'    
                else:
                    c = Forcastedvalue(basin=basin)  
                    c.datadate = year+'-'+month+'-'+day
                    c.forecasttype = 'snowwater'
                    c.riskstate = snowWaterState 
                    c.save()
                    print 'snowwater added'        



        pertama=False    

def getOverviewMaps(request):
    selectedBox = request.GET['send']

    map_obj = _resolve_map(request, request.GET['mapID'], 'base.view_resourcebase', _PERMISSION_MSG_VIEW)
    queryset = matrix(user=request.user,resourceid=map_obj,action='Interactive Map Download')
    queryset.save()

    response = HttpResponse(mimetype="image/png") 
    url = 'http://asdc.immap.org/geoserver/geonode/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&TRANSPARENT=true&LAYERS=geonode%3Aafg_admbnda_adm2%2Cgeonode%3Aafg_admbnda_adm1&STYLES=overview_adm2,overview_adm1&SRS=EPSG%3A4326&WIDTH=192&HEIGHT=121&BBOX=59.150390625%2C28.135986328125%2C76.025390625%2C38.792724609375'
    # url2='http://asdc.immap.org/geoserver/geonode/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&TRANSPARENT=true&SRS=EPSG%3A4326&WIDTH=768&HEIGHT=485&BBOX=59.150390625%2C28.135986328125%2C76.025390625%2C38.792724609375&SLD_BODY='+selectedBox
    url2='http://asdc.immap.org/geoserver/geonode/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&TRANSPARENT=true&SRS=EPSG%3A4326&WIDTH=192&HEIGHT=121&BBOX=59.150390625%2C28.135986328125%2C76.025390625%2C38.792724609375'
    template = '<sld:StyledLayerDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" version="1.0.0">'
    template +='<sld:UserLayer>'
    template +=     '<sld:Name>Inline</sld:Name>'
    template +=      '<sld:InlineFeature>'
    template +=         '<sld:FeatureCollection>'
    template +=             '<gml:featureMember>'
    template +=                 '<feature>'
    template +=                     '<polygonProperty>'
    template +=                         '<gml:Polygon  srsName="4326">'
    template +=                             '<gml:outerBoundaryIs>'
    template +=                                 '<gml:LinearRing>'
    template +=                                     '<gml:coordinates xmlns:gml="http://www.opengis.net/gml" decimal="." cs="," ts=" ">'+selectedBox
    template +=                                     '</gml:coordinates>'
    template +=                                 '</gml:LinearRing>'
    template +=                             '</gml:outerBoundaryIs>'
    template +=                         '</gml:Polygon>'
    template +=                      '</polygonProperty>'
    template +=                      '<title>Pacific NW</title>'
    template +=                 '</feature>'
    template +=             '</gml:featureMember>'
    template +=         '</sld:FeatureCollection>'
    template +=     '</sld:InlineFeature>'
    template +=     '<sld:UserStyle>'
    template +=         '<sld:FeatureTypeStyle>'
    template +=             '<sld:Rule>'
    template +=                 '<sld:PolygonSymbolizer>'
    template +=                     '<sld:Stroke>'
    template +=                         '<sld:CssParameter name="stroke">#FF0000</sld:CssParameter>'
    template +=                         '<sld:CssParameter name="stroke-width">1</sld:CssParameter>'
    template +=                     '</sld:Stroke>'
    template +=                 '</sld:PolygonSymbolizer>'
    template +=             '</sld:Rule>'
    template +=         '</sld:FeatureTypeStyle>'
    template +=     '</sld:UserStyle>'
    template += '</sld:UserLayer>'
    template +='</sld:StyledLayerDescriptor>'

    input_file = StringIO(urllib2.urlopen(url).read())
    background = Image.open(input_file)

    values = {'SLD_BODY' : template }
    data = urllib.urlencode(values)     
    input_file = StringIO(urllib2.urlopen(url2, data).read())
    overlay = Image.open(input_file)
    new_img = Image.blend(background, overlay, 0.5)  #background.paste(overlay, overlay.size, overlay)
    
    new_img.save(response, 'PNG', quality=300)
    
    return response

# Create your views here.
def update_progress(progress, msg, proctime):
    barLength = 100 # Modify this to change the length of the progress bar
    status = ""
    # print float(progress)
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float"
    if progress < 0:
        progress = 0
        status = "Halt..."
    if progress >= 1:
        progress = 1
        status = "Done..."
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2} {3} {4}s \r\n".format( "#"*block + "-"*(barLength-block), progress*100, status, msg, proctime)
    sys.stdout.write(text)
    sys.stdout.flush()

def updateSummaryTable():   
    resources = AfgAdmbndaAdm2.objects.all().order_by('dist_code')  # ingat nanti ganti

    header = []
    ppp = resources.count()
    xxx = 0
    update_progress(float(xxx/ppp), 'start', 0)
    databaseFields = districtsummary._meta.get_all_field_names()
    databaseFields.remove('id')
    databaseFields.remove('district')
    # print databaseFields
    for aoi in resources:
        riskNumber = getRiskExecuteExternal('ST_GeomFromText(\''+aoi.wkb_geometry.wkt+'\',4326)', 'currentProvince', aoi.dist_code)
        px = districtsummary.objects.filter(district=aoi.dist_code)
        
        if px.count()>0:
            # kalo ada
            print px[0].id
            a = districtsummary(id=px[0].id,district=aoi.dist_code)
        else:
            a = districtsummary(district=aoi.dist_code)

        for i in databaseFields:
            setattr(a, i, riskNumber[i])
            # print getattr(a, i)
        # print a.Population
        print aoi.dist_code
        a.save()



    #     start = time.time()
    #     row = []
    #     # test = getRiskExecuteExternal('ST_GeomFromText(\''+aoi.wkb_geometry.wkt+'\',4326)', 'drawArea', None) # real calculation
    #     test = getRiskExecuteExternal('ST_GeomFromText(\''+aoi.wkb_geometry.wkt+'\',4326)', 'currentProvince', aoi.dist_code)
    #     if len(header) == 0:
    #         for i in test:
    #             header.append(i)
   
    #     loadingtime = time.time() - start
    #     xxx=xxx+1
    #     update_progress(float(float(xxx)/float(ppp)), aoi.dist_code, loadingtime)
    return    

def exportdata():   
    outfile_path = '/Users/budi/Documents/iMMAP/out.csv' # for local
    # outfile_path = '/home/ubuntu/DRR-datacenter/geonode/static_root/intersection_stats.csv' # for server

    csvFile = open(outfile_path, 'w')

    # resources = AfgAdmbndaAdm2.objects.all().filter(dist_code__in=['1205']).order_by('dist_code')  # ingat nanti ganti
    resources = AfgAdmbndaAdm2.objects.all().order_by('dist_code')  # ingat nanti ganti

    writer = csv.writer(csvFile)
    header = []
    headerTemp = []
    ppp = resources.count()
    xxx = 0
    update_progress(float(xxx/ppp), 'start', 0)
    for aoi in resources:
        start = time.time()
        row = []
        # test = getRiskExecuteExternal('ST_GeomFromText(\''+aoi.wkb_geometry.wkt+'\',4326)', 'drawArea', None) # real calculation
        test = getRiskExecuteExternal('ST_GeomFromText(\''+aoi.wkb_geometry.wkt+'\',4326)', 'currentProvince', aoi.dist_code)
        
        if len(header) == 0:
            headerTemp.append('aoi_id')
            for i in test:
                header.append(i)
                headerTemp.append(i)
            writer.writerow(headerTemp)    

        row.append(aoi.dist_code)  
    	for i in header:
            row.append(test[i])

        writer.writerow(row)

        loadingtime = time.time() - start
        xxx=xxx+1
        update_progress(float(float(xxx)/float(ppp)), aoi.dist_code, loadingtime)
    return
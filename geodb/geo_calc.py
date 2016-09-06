from geodb.models import AfgFldzonea100KRiskLandcoverPop, FloodRiskExposure, AfgLndcrva, LandcoverDescription, AfgAvsa, AfgAdmbndaAdm1, AfgAdmbndaAdm2, AfgPplp, earthquake_shakemap, earthquake_events, villagesummaryEQ, AfgRdsl, AfgHltfac, forecastedLastUpdate, provincesummary, AfgCaptAdm1ItsProvcImmap, AfgCaptAdm1NearestProvcImmap, AfgCaptAdm2NearestDistrictcImmap, AfgCaptAirdrmImmap, AfgCaptHltfacTier1Immap, AfgCaptHltfacTier2Immap, tempCurrentSC, AfgCaptHltfacTier3Immap, AfgCaptHltfacTierallImmap, AfgIncidentOasis, AfgCapaGsmcvr, AfgAirdrmp
import json
import time, datetime
from tastypie.resources import ModelResource, Resource
from tastypie.serializers import Serializer
from tastypie import fields
from tastypie.constants import ALL
from django.db.models import Count, Sum
from django.core.serializers.json import DjangoJSONEncoder
from tastypie.authorization import DjangoAuthorization
from urlparse import urlparse
from geonode.maps.models import Map
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW
from django.db import connection, connections
from itertools import *
# addded by boedy
from matrix.models import matrix
from tastypie.cache import SimpleCache
from pytz import timezone, all_timezones
from django.http import HttpResponse

from djgeojson.serializers import Serializer as GeoJSONSerializer

from geodb.geoapi import getRiskNumber, getAccessibilities

from graphos.sources.model import ModelDataSource
from graphos.renderers import flot, gchart
from graphos.sources.simple import SimpleDataSource
from django.test import RequestFactory
import urllib2, urllib

def query_to_dicts(cursor, query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return

def getCommonUse(flag, code):
    response = {}
    response['parent_label']='Custom Selection'
    response['parent_label_dash']='Custom Selection'

    if flag == 'entireAfg':
        response['parent_label']='Afghanistan'
        response['parent_label_dash']='Afghanistan'
    elif flag == 'currentProvince':
        if code<=34:
            lblTMP = AfgAdmbndaAdm1.objects.filter(prov_code=code)
            response['parent_label_dash'] = 'Afghanistan - '+lblTMP[0].prov_na_en   
            response['parent_label'] = lblTMP[0].prov_na_en 
        else:
            lblTMP = AfgAdmbndaAdm2.objects.filter(dist_code=code)
            response['parent_label_dash'] = 'Afghanistan - '+ lblTMP[0].prov_na_en + ' - ' +lblTMP[0].dist_na_en
            response['parent_label'] = lblTMP[0].dist_na_en
    return response 

def GetAccesibilityData(filterLock, flag, code):
    response = {}
    if flag=='entireAfg':
        q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
        gsm = AfgCapaGsmcvr.objects.all().aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'))

    elif flag =='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "left(cast(dist_code as text), "+str(len(str(code)))+") = '"+str(code)+"' and length(cast(dist_code as text))="+ str(len(str(code))+2)   
        q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
            where = {
                ff0001       
            })
        if len(str(code)) > 2:
            gsm = AfgCapaGsmcvr.objects.filter(dist_code=code).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'))
        else :
            gsm = AfgCapaGsmcvr.objects.filter(prov_code=code).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'))    

    elif flag =='drawArea':
        tt = AfgPplp.objects.filter(wkb_geometry__intersects=filterLock).values('vuid')
        q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'))
    else:
        tt = AfgPplp.objects.filter(wkb_geometry__intersects=filterLock).values('vuid')
        q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
        gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'))

    for i in q1: 
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__itsx_prov']=round(i['pop'])       
    for i in q2:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_prov']=round(i['pop'])    
    for i in q3:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_dist']=round(i['pop'])      
    for i in q4:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_airp']=round(i['pop'])       
    for i in q5:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_hlt1']=round(i['pop'])     
    for i in q6:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_hlt2']=round(i['pop'])     
    for i in q7:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_hlt3']=round(i['pop'])  
    for i in q8:
        timelabel = i['time'].replace(' ','_')
        timelabel = timelabel.replace('<','l')
        timelabel = timelabel.replace('>','g')
        response[timelabel+'__near_hltall']=round(i['pop'])    

    response['pop_on_gsm_coverage'] = round((gsm['pop'] or 0),0)
    response['area_on_gsm_coverage'] = round((gsm['area'] or 0)/1000000,0)
     
    return response

def getAccessibility(filterLock, flag, code): 
    targetBase = AfgLndcrva.objects.all()
    response = getCommonUse(flag, code)  
    response['Population']=getTotalPop(filterLock, flag, code, targetBase)
    response['Area']=getTotalArea(filterLock, flag, code, targetBase)
    
    rawAccesibility = GetAccesibilityData(filterLock, flag, code)

    # print rawAccesibility

    for i in rawAccesibility:
        response[i]=rawAccesibility[i]

    response['pop_coverage_percent'] = int(round((response['pop_on_gsm_coverage']/response['Population'])*100,0))
    response['area_coverage_percent'] = int(round((response['area_on_gsm_coverage']/response['Area'])*100,0))

    response['l1_h__near_airp_percent'] = int(round((response['l1_h__near_airp']/response['Population'])*100,0)) if 'l1_h__near_airp' in response else 0
    response['l2_h__near_airp_percent'] = int(round((response['l2_h__near_airp']/response['Population'])*100,0)) if 'l2_h__near_airp' in response else 0
    response['l3_h__near_airp_percent'] = int(round((response['l3_h__near_airp']/response['Population'])*100,0)) if 'l3_h__near_airp' in response else 0
    response['l4_h__near_airp_percent'] = int(round((response['l4_h__near_airp']/response['Population'])*100,0)) if 'l4_h__near_airp' in response else 0
    response['l5_h__near_airp_percent'] = int(round((response['l5_h__near_airp']/response['Population'])*100,0)) if 'l5_h__near_airp' in response else 0
    response['l6_h__near_airp_percent'] = int(round((response['l6_h__near_airp']/response['Population'])*100,0)) if 'l6_h__near_airp' in response else 0
    response['l7_h__near_airp_percent'] = int(round((response['l7_h__near_airp']/response['Population'])*100,0)) if 'l7_h__near_airp' in response else 0
    response['l8_h__near_airp_percent'] = int(round((response['l8_h__near_airp']/response['Population'])*100,0)) if 'l8_h__near_airp' in response else 0
    response['g8_h__near_airp_percent'] = int(round((response['g8_h__near_airp']/response['Population'])*100,0)) if 'g8_h__near_airp' in response else 0

    response['l1_h__near_hlt1_percent'] = int(round((response['l1_h__near_hlt1']/response['Population'])*100,0)) if 'l1_h__near_hlt1' in response else 0
    response['l2_h__near_hlt1_percent'] = int(round((response['l2_h__near_hlt1']/response['Population'])*100,0)) if 'l2_h__near_hlt1' in response else 0
    response['l3_h__near_hlt1_percent'] = int(round((response['l3_h__near_hlt1']/response['Population'])*100,0)) if 'l3_h__near_hlt1' in response else 0
    response['l4_h__near_hlt1_percent'] = int(round((response['l4_h__near_hlt1']/response['Population'])*100,0)) if 'l4_h__near_hlt1' in response else 0
    response['l5_h__near_hlt1_percent'] = int(round((response['l5_h__near_hlt1']/response['Population'])*100,0)) if 'l5_h__near_hlt1' in response else 0
    response['l6_h__near_hlt1_percent'] = int(round((response['l6_h__near_hlt1']/response['Population'])*100,0)) if 'l6_h__near_hlt1' in response else 0
    response['l7_h__near_hlt1_percent'] = int(round((response['l7_h__near_hlt1']/response['Population'])*100,0)) if 'l7_h__near_hlt1' in response else 0
    response['l8_h__near_hlt1_percent'] = int(round((response['l8_h__near_hlt1']/response['Population'])*100,0)) if 'l8_h__near_hlt1' in response else 0
    response['g8_h__near_hlt1_percent'] = int(round((response['g8_h__near_hlt1']/response['Population'])*100,0)) if 'g8_h__near_hlt1' in response else 0

    response['l1_h__near_hlt2_percent'] = int(round((response['l1_h__near_hlt2']/response['Population'])*100,0)) if 'l1_h__near_hlt2' in response else 0
    response['l2_h__near_hlt2_percent'] = int(round((response['l2_h__near_hlt2']/response['Population'])*100,0)) if 'l2_h__near_hlt2' in response else 0
    response['l3_h__near_hlt2_percent'] = int(round((response['l3_h__near_hlt2']/response['Population'])*100,0)) if 'l3_h__near_hlt2' in response else 0
    response['l4_h__near_hlt2_percent'] = int(round((response['l4_h__near_hlt2']/response['Population'])*100,0)) if 'l4_h__near_hlt2' in response else 0
    response['l5_h__near_hlt2_percent'] = int(round((response['l5_h__near_hlt2']/response['Population'])*100,0)) if 'l5_h__near_hlt2' in response else 0
    response['l6_h__near_hlt2_percent'] = int(round((response['l6_h__near_hlt2']/response['Population'])*100,0)) if 'l6_h__near_hlt2' in response else 0
    response['l7_h__near_hlt2_percent'] = int(round((response['l7_h__near_hlt2']/response['Population'])*100,0)) if 'l7_h__near_hlt2' in response else 0
    response['l8_h__near_hlt2_percent'] = int(round((response['l8_h__near_hlt2']/response['Population'])*100,0)) if 'l8_h__near_hlt2' in response else 0
    response['g8_h__near_hlt2_percent'] = int(round((response['g8_h__near_hlt2']/response['Population'])*100,0)) if 'g8_h__near_hlt2' in response else 0

    response['l1_h__near_hlt3_percent'] = int(round((response['l1_h__near_hlt3']/response['Population'])*100,0)) if 'l1_h__near_hlt3' in response else 0
    response['l2_h__near_hlt3_percent'] = int(round((response['l2_h__near_hlt3']/response['Population'])*100,0)) if 'l2_h__near_hlt3' in response else 0
    response['l3_h__near_hlt3_percent'] = int(round((response['l3_h__near_hlt3']/response['Population'])*100,0)) if 'l3_h__near_hlt3' in response else 0
    response['l4_h__near_hlt3_percent'] = int(round((response['l4_h__near_hlt3']/response['Population'])*100,0)) if 'l4_h__near_hlt3' in response else 0
    response['l5_h__near_hlt3_percent'] = int(round((response['l5_h__near_hlt3']/response['Population'])*100,0)) if 'l5_h__near_hlt3' in response else 0
    response['l6_h__near_hlt3_percent'] = int(round((response['l6_h__near_hlt3']/response['Population'])*100,0)) if 'l6_h__near_hlt3' in response else 0
    response['l7_h__near_hlt3_percent'] = int(round((response['l7_h__near_hlt3']/response['Population'])*100,0)) if 'l7_h__near_hlt3' in response else 0
    response['l8_h__near_hlt3_percent'] = int(round((response['l8_h__near_hlt3']/response['Population'])*100,0)) if 'l8_h__near_hlt3' in response else 0
    response['g8_h__near_hlt3_percent'] = int(round((response['g8_h__near_hlt3']/response['Population'])*100,0)) if 'g8_h__near_hlt3' in response else 0

    response['l1_h__near_hltall_percent'] = int(round((response['l1_h__near_hltall']/response['Population'])*100,0)) if 'l1_h__near_hltall' in response else 0
    response['l2_h__near_hltall_percent'] = int(round((response['l2_h__near_hltall']/response['Population'])*100,0)) if 'l2_h__near_hltall' in response else 0
    response['l3_h__near_hltall_percent'] = int(round((response['l3_h__near_hltall']/response['Population'])*100,0)) if 'l3_h__near_hltall' in response else 0
    response['l4_h__near_hltall_percent'] = int(round((response['l4_h__near_hltall']/response['Population'])*100,0)) if 'l4_h__near_hltall' in response else 0
    response['l5_h__near_hltall_percent'] = int(round((response['l5_h__near_hltall']/response['Population'])*100,0)) if 'l5_h__near_hltall' in response else 0
    response['l6_h__near_hltall_percent'] = int(round((response['l6_h__near_hltall']/response['Population'])*100,0)) if 'l6_h__near_hltall' in response else 0
    response['l7_h__near_hltall_percent'] = int(round((response['l7_h__near_hltall']/response['Population'])*100,0)) if 'l7_h__near_hltall' in response else 0
    response['l8_h__near_hltall_percent'] = int(round((response['l8_h__near_hltall']/response['Population'])*100,0)) if 'l8_h__near_hltall' in response else 0
    response['g8_h__near_hltall_percent'] = int(round((response['g8_h__near_hltall']/response['Population'])*100,0)) if 'g8_h__near_hltall' in response else 0

    response['l1_h__itsx_prov_percent'] = int(round((response['l1_h__itsx_prov']/response['Population'])*100,0)) if 'l1_h__itsx_prov' in response else 0
    response['l2_h__itsx_prov_percent'] = int(round((response['l2_h__itsx_prov']/response['Population'])*100,0)) if 'l2_h__itsx_prov' in response else 0
    response['l3_h__itsx_prov_percent'] = int(round((response['l3_h__itsx_prov']/response['Population'])*100,0)) if 'l3_h__itsx_prov' in response else 0
    response['l4_h__itsx_prov_percent'] = int(round((response['l4_h__itsx_prov']/response['Population'])*100,0)) if 'l4_h__itsx_prov' in response else 0
    response['l5_h__itsx_prov_percent'] = int(round((response['l5_h__itsx_prov']/response['Population'])*100,0)) if 'l5_h__itsx_prov' in response else 0
    response['l6_h__itsx_prov_percent'] = int(round((response['l6_h__itsx_prov']/response['Population'])*100,0)) if 'l6_h__itsx_prov' in response else 0
    response['l7_h__itsx_prov_percent'] = int(round((response['l7_h__itsx_prov']/response['Population'])*100,0)) if 'l7_h__itsx_prov' in response else 0
    response['l8_h__itsx_prov_percent'] = int(round((response['l8_h__itsx_prov']/response['Population'])*100,0)) if 'l8_h__itsx_prov' in response else 0
    response['g8_h__itsx_prov_percent'] = int(round((response['g8_h__itsx_prov']/response['Population'])*100,0)) if 'g8_h__itsx_prov' in response else 0

    response['l1_h__near_prov_percent'] = int(round((response['l1_h__near_prov']/response['Population'])*100,0)) if 'l1_h__near_prov' in response else 0
    response['l2_h__near_prov_percent'] = int(round((response['l2_h__near_prov']/response['Population'])*100,0)) if 'l2_h__near_prov' in response else 0
    response['l3_h__near_prov_percent'] = int(round((response['l3_h__near_prov']/response['Population'])*100,0)) if 'l3_h__near_prov' in response else 0
    response['l4_h__near_prov_percent'] = int(round((response['l4_h__near_prov']/response['Population'])*100,0)) if 'l4_h__near_prov' in response else 0
    response['l5_h__near_prov_percent'] = int(round((response['l5_h__near_prov']/response['Population'])*100,0)) if 'l5_h__near_prov' in response else 0
    response['l6_h__near_prov_percent'] = int(round((response['l6_h__near_prov']/response['Population'])*100,0)) if 'l6_h__near_prov' in response else 0
    response['l7_h__near_prov_percent'] = int(round((response['l7_h__near_prov']/response['Population'])*100,0)) if 'l7_h__near_prov' in response else 0
    response['l8_h__near_prov_percent'] = int(round((response['l8_h__near_prov']/response['Population'])*100,0)) if 'l8_h__near_prov' in response else 0
    response['g8_h__near_prov_percent'] = int(round((response['g8_h__near_prov']/response['Population'])*100,0)) if 'g8_h__near_prov' in response else 0

    response['l1_h__near_dist_percent'] = int(round((response['l1_h__near_dist']/response['Population'])*100,0)) if 'l1_h__near_dist' in response else 0
    response['l2_h__near_dist_percent'] = int(round((response['l2_h__near_dist']/response['Population'])*100,0)) if 'l2_h__near_dist' in response else 0
    response['l3_h__near_dist_percent'] = int(round((response['l3_h__near_dist']/response['Population'])*100,0)) if 'l3_h__near_dist' in response else 0
    response['l4_h__near_dist_percent'] = int(round((response['l4_h__near_dist']/response['Population'])*100,0)) if 'l4_h__near_dist' in response else 0
    response['l5_h__near_dist_percent'] = int(round((response['l5_h__near_dist']/response['Population'])*100,0)) if 'l5_h__near_dist' in response else 0
    response['l6_h__near_dist_percent'] = int(round((response['l6_h__near_dist']/response['Population'])*100,0)) if 'l6_h__near_dist' in response else 0
    response['l7_h__near_dist_percent'] = int(round((response['l7_h__near_dist']/response['Population'])*100,0)) if 'l7_h__near_dist' in response else 0
    response['l8_h__near_dist_percent'] = int(round((response['l8_h__near_dist']/response['Population'])*100,0)) if 'l8_h__near_dist' in response else 0
    response['g8_h__near_dist_percent'] = int(round((response['g8_h__near_dist']/response['Population'])*100,0)) if 'g8_h__near_dist' in response else 0

    data1 = []
    data1.append(['agg_simplified_description','area_population'])
    data1.append(['Population with GSM coverage',response['pop_on_gsm_coverage']])
    data1.append(['Population without GSM coverage',response['Population']-response['pop_on_gsm_coverage']])
    response['total_pop_coverage_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270})

    data2 = []
    data2.append(['agg_simplified_description','area_population'])
    data2.append(['Area with GSM coverage',response['area_on_gsm_coverage']])
    data2.append(['Area without GSM coverage',response['Area']-response['area_on_gsm_coverage']])
    response['total_area_coverage_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270 })

    dataNearestAirp = []
    dataNearestAirp.append(['time','population'])
    dataNearestAirp.append(['< 1 h',response['l1_h__near_airp'] if 'l1_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 2 h',response['l2_h__near_airp'] if 'l2_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 3 h',response['l3_h__near_airp'] if 'l3_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 4 h',response['l4_h__near_airp'] if 'l4_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 5 h',response['l5_h__near_airp'] if 'l5_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 6 h',response['l6_h__near_airp'] if 'l6_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 7 h',response['l7_h__near_airp'] if 'l7_h__near_airp' in response else 0])
    dataNearestAirp.append(['< 8 h',response['l8_h__near_airp'] if 'l8_h__near_airp' in response else 0])
    dataNearestAirp.append(['> 8 h',response['g8_h__near_airp'] if 'g8_h__near_airp' in response else 0])
    response['nearest_airport_chart'] = gchart.PieChart(SimpleDataSource(data=dataNearestAirp), html_id="pie_chart3", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 
    # response['nearest_airport_chart'] = gchart.PieChart(SimpleDataSource(data=dataNearestAirp), html_id="pie_chart3", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': 'none', 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatier1 = []
    datatier1.append(['time','population'])
    datatier1.append(['< 1 h',response['l1_h__near_hlt1'] if 'l1_h__near_hlt1' in response else 0])
    datatier1.append(['< 2 h',response['l2_h__near_hlt1'] if 'l2_h__near_hlt1' in response else 0])
    datatier1.append(['< 3 h',response['l3_h__near_hlt1'] if 'l3_h__near_hlt1' in response else 0])
    datatier1.append(['< 4 h',response['l4_h__near_hlt1'] if 'l4_h__near_hlt1' in response else 0])
    datatier1.append(['< 5 h',response['l5_h__near_hlt1'] if 'l5_h__near_hlt1' in response else 0])
    datatier1.append(['< 6 h',response['l6_h__near_hlt1'] if 'l6_h__near_hlt1' in response else 0])
    datatier1.append(['< 7 h',response['l7_h__near_hlt1'] if 'l7_h__near_hlt1' in response else 0])
    datatier1.append(['< 8 h',response['l8_h__near_hlt1'] if 'l8_h__near_hlt1' in response else 0])
    datatier1.append(['> 8 h',response['g8_h__near_hlt1'] if 'g8_h__near_hlt1' in response else 0])
    response['tier1_chart'] = gchart.PieChart(SimpleDataSource(data=datatier1), html_id="pie_chart4", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 
    
    datatier2 = []
    datatier2.append(['time','population'])
    datatier2.append(['< 1 h',response['l1_h__near_hlt2'] if 'l1_h__near_hlt2' in response else 0])
    datatier2.append(['< 2 h',response['l2_h__near_hlt2'] if 'l2_h__near_hlt2' in response else 0])
    datatier2.append(['< 3 h',response['l3_h__near_hlt2'] if 'l3_h__near_hlt2' in response else 0])
    datatier2.append(['< 4 h',response['l4_h__near_hlt2'] if 'l4_h__near_hlt2' in response else 0])
    datatier2.append(['< 5 h',response['l5_h__near_hlt2'] if 'l5_h__near_hlt2' in response else 0])
    datatier2.append(['< 6 h',response['l6_h__near_hlt2'] if 'l6_h__near_hlt2' in response else 0])
    datatier2.append(['< 7 h',response['l7_h__near_hlt2'] if 'l7_h__near_hlt2' in response else 0])
    datatier2.append(['< 8 h',response['l8_h__near_hlt2'] if 'l8_h__near_hlt2' in response else 0])
    datatier2.append(['> 8 h',response['g8_h__near_hlt2'] if 'g8_h__near_hlt2' in response else 0])
    response['tier2_chart'] = gchart.PieChart(SimpleDataSource(data=datatier2), html_id="pie_chart5", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatier3 = []
    datatier3.append(['time','population'])
    datatier3.append(['< 1 h',response['l1_h__near_hlt3'] if 'l1_h__near_hlt3' in response else 0])
    datatier3.append(['< 2 h',response['l2_h__near_hlt3'] if 'l2_h__near_hlt3' in response else 0])
    datatier3.append(['< 3 h',response['l3_h__near_hlt3'] if 'l3_h__near_hlt3' in response else 0])
    datatier3.append(['< 4 h',response['l4_h__near_hlt3'] if 'l4_h__near_hlt3' in response else 0])
    datatier3.append(['< 5 h',response['l5_h__near_hlt3'] if 'l5_h__near_hlt3' in response else 0])
    datatier3.append(['< 6 h',response['l6_h__near_hlt3'] if 'l6_h__near_hlt3' in response else 0])
    datatier3.append(['< 7 h',response['l7_h__near_hlt3'] if 'l7_h__near_hlt3' in response else 0])
    datatier3.append(['< 8 h',response['l8_h__near_hlt3'] if 'l8_h__near_hlt3' in response else 0])
    datatier3.append(['> 8 h',response['g8_h__near_hlt3'] if 'g8_h__near_hlt3' in response else 0])
    response['tier3_chart'] = gchart.PieChart(SimpleDataSource(data=datatier3), html_id="pie_chart6", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatierall = []
    datatierall.append(['time','population'])
    datatierall.append(['< 1 h',response['l1_h__near_hltall'] if 'l1_h__near_hltall' in response else 0])
    datatierall.append(['< 2',response['l2_h__near_hltall'] if 'l2_h__near_hltall' in response else 0])
    datatierall.append(['< 3 h',response['l3_h__near_hltall'] if 'l3_h__near_hltall' in response else 0])
    datatierall.append(['< 4 h',response['l4_h__near_hltall'] if 'l4_h__near_hltall' in response else 0])
    datatierall.append(['< 5 h',response['l5_h__near_hltall'] if 'l5_h__near_hltall' in response else 0])
    datatierall.append(['< 6 h',response['l6_h__near_hltall'] if 'l6_h__near_hltall' in response else 0])
    datatierall.append(['< 7 h',response['l7_h__near_hltall'] if 'l7_h__near_hltall' in response else 0])
    datatierall.append(['< 8 h',response['l8_h__near_hltall'] if 'l8_h__near_hltall' in response else 0])
    datatierall.append(['> 8 h',response['g8_h__near_hltall'] if 'g8_h__near_hltall' in response else 0])
    response['tierall_chart'] = gchart.PieChart(SimpleDataSource(data=datatierall), html_id="pie_chart7", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatitsx_prov = []
    datatitsx_prov.append(['time','population'])
    datatitsx_prov.append(['< 1 h',response['l1_h__itsx_prov'] if 'l1_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 2 h',response['l2_h__itsx_prov'] if 'l2_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 3 h',response['l3_h__itsx_prov'] if 'l3_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 4 h',response['l4_h__itsx_prov'] if 'l4_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 5 h',response['l5_h__itsx_prov'] if 'l5_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 6 h',response['l6_h__itsx_prov'] if 'l6_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 7 h',response['l7_h__itsx_prov'] if 'l7_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['< 8 h',response['l8_h__itsx_prov'] if 'l8_h__itsx_prov' in response else 0])
    datatitsx_prov.append(['> 8 h',response['g8_h__itsx_prov'] if 'g8_h__itsx_prov' in response else 0])
    response['itsx_prov_chart'] = gchart.PieChart(SimpleDataSource(data=datatitsx_prov), html_id="pie_chart8", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatnear_prov = []
    datatnear_prov.append(['time','population'])
    datatnear_prov.append(['< 1 h',response['l1_h__near_prov'] if 'l1_h__near_prov' in response else 0])
    datatnear_prov.append(['< 2 h',response['l2_h__near_prov'] if 'l2_h__near_prov' in response else 0])
    datatnear_prov.append(['< 3 h',response['l3_h__near_prov'] if 'l3_h__near_prov' in response else 0])
    datatnear_prov.append(['< 4 h',response['l4_h__near_prov'] if 'l4_h__near_prov' in response else 0])
    datatnear_prov.append(['< 5 h',response['l5_h__near_prov'] if 'l5_h__near_prov' in response else 0])
    datatnear_prov.append(['< 6 h',response['l6_h__near_prov'] if 'l6_h__near_prov' in response else 0])
    datatnear_prov.append(['< 7 h',response['l7_h__near_prov'] if 'l7_h__near_prov' in response else 0])
    datatnear_prov.append(['< 8 h',response['l8_h__near_prov'] if 'l8_h__near_prov' in response else 0])
    datatnear_prov.append(['> 8 h',response['g8_h__near_prov'] if 'g8_h__near_prov' in response else 0])
    response['near_prov_chart'] = gchart.PieChart(SimpleDataSource(data=datatnear_prov), html_id="pie_chart9", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 

    datatnear_dist = []
    datatnear_dist.append(['time','population'])
    datatnear_dist.append(['< 1 h',response['l1_h__near_dist'] if 'l1_h__near_dist' in response else 0])
    datatnear_dist.append(['< 2 h',response['l2_h__near_dist'] if 'l2_h__near_dist' in response else 0])
    datatnear_dist.append(['< 3 h',response['l3_h__near_dist'] if 'l3_h__near_dist' in response else 0])
    datatnear_dist.append(['< 4 h',response['l4_h__near_dist'] if 'l4_h__near_dist' in response else 0])
    datatnear_dist.append(['< 5 h',response['l5_h__near_dist'] if 'l5_h__near_dist' in response else 0])
    datatnear_dist.append(['< 6 h',response['l6_h__near_dist'] if 'l6_h__near_dist' in response else 0])
    datatnear_dist.append(['< 7 h',response['l7_h__near_dist'] if 'l7_h__near_dist' in response else 0])
    datatnear_dist.append(['< 8 h',response['l8_h__near_dist'] if 'l8_h__near_dist' in response else 0])
    datatnear_dist.append(['> 8 h',response['g8_h__near_dist'] if 'g8_h__near_dist' in response else 0])
    response['near_dist_chart'] = gchart.PieChart(SimpleDataSource(data=datatnear_dist), html_id="pie_chart10", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} }) 


    data = getListAccesibility(filterLock, flag, code)
    response['lc_child']=data
    return response 

def getListAccesibility(filterLock, flag, code):
    response = []
    data = getProvinceSummary(filterLock, flag, code)
    for i in data:      
        data ={}
        data['code'] = i['code']
        data['na_en'] = i['na_en']
        data['Population'] = i['Population']
        data['Area'] = i['Area']

        rawAccesibility = GetAccesibilityData(None, 'currentProvince', i['code'])
        for x in rawAccesibility:
            data[x]=rawAccesibility[x]

        data['pop_coverage_percent'] = int(round((data['pop_on_gsm_coverage']/data['Population'])*100,0))
        data['area_coverage_percent'] = int(round((data['area_on_gsm_coverage']/data['Area'])*100,0))

        print 'l1_h__near_airp' in data

        data['l1_h__near_airp_percent'] = int(round((data['l1_h__near_airp']/data['Population'])*100,0)) if 'l1_h__near_airp' in data else 0
        data['l2_h__near_airp_percent'] = int(round((data['l2_h__near_airp']/data['Population'])*100,0)) if 'l2_h__near_airp' in data else 0
        data['l3_h__near_airp_percent'] = int(round((data['l3_h__near_airp']/data['Population'])*100,0)) if 'l3_h__near_airp' in data else 0
        data['l4_h__near_airp_percent'] = int(round((data['l4_h__near_airp']/data['Population'])*100,0)) if 'l4_h__near_airp' in data else 0
        data['l5_h__near_airp_percent'] = int(round((data['l5_h__near_airp']/data['Population'])*100,0)) if 'l5_h__near_airp' in data else 0
        data['l6_h__near_airp_percent'] = int(round((data['l6_h__near_airp']/data['Population'])*100,0)) if 'l6_h__near_airp' in data else 0
        data['l7_h__near_airp_percent'] = int(round((data['l7_h__near_airp']/data['Population'])*100,0)) if 'l7_h__near_airp' in data else 0
        data['l8_h__near_airp_percent'] = int(round((data['l8_h__near_airp']/data['Population'])*100,0)) if 'l8_h__near_airp' in data else 0
        data['g8_h__near_airp_percent'] = int(round((data['g8_h__near_airp']/data['Population'])*100,0)) if 'g8_h__near_airp' in data else 0   
        
        data['l1_h__near_hlt1_percent'] = int(round((data['l1_h__near_hlt1']/data['Population'])*100,0)) if 'l1_h__near_hlt1' in data else 0
        data['l2_h__near_hlt1_percent'] = int(round((data['l2_h__near_hlt1']/data['Population'])*100,0)) if 'l2_h__near_hlt1' in data else 0
        data['l3_h__near_hlt1_percent'] = int(round((data['l3_h__near_hlt1']/data['Population'])*100,0)) if 'l3_h__near_hlt1' in data else 0
        data['l4_h__near_hlt1_percent'] = int(round((data['l4_h__near_hlt1']/data['Population'])*100,0)) if 'l4_h__near_hlt1' in data else 0
        data['l5_h__near_hlt1_percent'] = int(round((data['l5_h__near_hlt1']/data['Population'])*100,0)) if 'l5_h__near_hlt1' in data else 0
        data['l6_h__near_hlt1_percent'] = int(round((data['l6_h__near_hlt1']/data['Population'])*100,0)) if 'l6_h__near_hlt1' in data else 0
        data['l7_h__near_hlt1_percent'] = int(round((data['l7_h__near_hlt1']/data['Population'])*100,0)) if 'l7_h__near_hlt1' in data else 0
        data['l8_h__near_hlt1_percent'] = int(round((data['l8_h__near_hlt1']/data['Population'])*100,0)) if 'l8_h__near_hlt1' in data else 0
        data['g8_h__near_hlt1_percent'] = int(round((data['g8_h__near_hlt1']/data['Population'])*100,0)) if 'g8_h__near_hlt1' in data else 0

        data['l1_h__near_hlt2_percent'] = int(round((data['l1_h__near_hlt2']/data['Population'])*100,0)) if 'l1_h__near_hlt2' in data else 0
        data['l2_h__near_hlt2_percent'] = int(round((data['l2_h__near_hlt2']/data['Population'])*100,0)) if 'l2_h__near_hlt2' in data else 0
        data['l3_h__near_hlt2_percent'] = int(round((data['l3_h__near_hlt2']/data['Population'])*100,0)) if 'l3_h__near_hlt2' in data else 0
        data['l4_h__near_hlt2_percent'] = int(round((data['l4_h__near_hlt2']/data['Population'])*100,0)) if 'l4_h__near_hlt2' in data else 0
        data['l5_h__near_hlt2_percent'] = int(round((data['l5_h__near_hlt2']/data['Population'])*100,0)) if 'l5_h__near_hlt2' in data else 0
        data['l6_h__near_hlt2_percent'] = int(round((data['l6_h__near_hlt2']/data['Population'])*100,0)) if 'l6_h__near_hlt2' in data else 0
        data['l7_h__near_hlt2_percent'] = int(round((data['l7_h__near_hlt2']/data['Population'])*100,0)) if 'l7_h__near_hlt2' in data else 0
        data['l8_h__near_hlt2_percent'] = int(round((data['l8_h__near_hlt2']/data['Population'])*100,0)) if 'l8_h__near_hlt2' in data else 0
        data['g8_h__near_hlt2_percent'] = int(round((data['g8_h__near_hlt2']/data['Population'])*100,0)) if 'g8_h__near_hlt2' in data else 0

        data['l1_h__near_hlt3_percent'] = int(round((data['l1_h__near_hlt3']/data['Population'])*100,0)) if 'l1_h__near_hlt3' in data else 0
        data['l2_h__near_hlt3_percent'] = int(round((data['l2_h__near_hlt3']/data['Population'])*100,0)) if 'l2_h__near_hlt3' in data else 0
        data['l3_h__near_hlt3_percent'] = int(round((data['l3_h__near_hlt3']/data['Population'])*100,0)) if 'l3_h__near_hlt3' in data else 0
        data['l4_h__near_hlt3_percent'] = int(round((data['l4_h__near_hlt3']/data['Population'])*100,0)) if 'l4_h__near_hlt3' in data else 0
        data['l5_h__near_hlt3_percent'] = int(round((data['l5_h__near_hlt3']/data['Population'])*100,0)) if 'l5_h__near_hlt3' in data else 0
        data['l6_h__near_hlt3_percent'] = int(round((data['l6_h__near_hlt3']/data['Population'])*100,0)) if 'l6_h__near_hlt3' in data else 0
        data['l7_h__near_hlt3_percent'] = int(round((data['l7_h__near_hlt3']/data['Population'])*100,0)) if 'l7_h__near_hlt3' in data else 0
        data['l8_h__near_hlt3_percent'] = int(round((data['l8_h__near_hlt3']/data['Population'])*100,0)) if 'l8_h__near_hlt3' in data else 0
        data['g8_h__near_hlt3_percent'] = int(round((data['g8_h__near_hlt3']/data['Population'])*100,0)) if 'g8_h__near_hlt3' in data else 0

        data['l1_h__near_hltall_percent'] = int(round((data['l1_h__near_hltall']/data['Population'])*100,0)) if 'l1_h__near_hltall' in data else 0
        data['l2_h__near_hltall_percent'] = int(round((data['l2_h__near_hltall']/data['Population'])*100,0)) if 'l2_h__near_hltall' in data else 0
        data['l3_h__near_hltall_percent'] = int(round((data['l3_h__near_hltall']/data['Population'])*100,0)) if 'l3_h__near_hltall' in data else 0
        data['l4_h__near_hltall_percent'] = int(round((data['l4_h__near_hltall']/data['Population'])*100,0)) if 'l4_h__near_hltall' in data else 0
        data['l5_h__near_hltall_percent'] = int(round((data['l5_h__near_hltall']/data['Population'])*100,0)) if 'l5_h__near_hltall' in data else 0
        data['l6_h__near_hltall_percent'] = int(round((data['l6_h__near_hltall']/data['Population'])*100,0)) if 'l6_h__near_hltall' in data else 0
        data['l7_h__near_hltall_percent'] = int(round((data['l7_h__near_hltall']/data['Population'])*100,0)) if 'l7_h__near_hltall' in data else 0
        data['l8_h__near_hltall_percent'] = int(round((data['l8_h__near_hltall']/data['Population'])*100,0)) if 'l8_h__near_hltall' in data else 0
        data['g8_h__near_hltall_percent'] = int(round((data['g8_h__near_hltall']/data['Population'])*100,0)) if 'g8_h__near_hltall' in data else 0

        data['l1_h__itsx_prov_percent'] = int(round((data['l1_h__itsx_prov']/data['Population'])*100,0)) if 'l1_h__itsx_prov' in data else 0
        data['l2_h__itsx_prov_percent'] = int(round((data['l2_h__itsx_prov']/data['Population'])*100,0)) if 'l2_h__itsx_prov' in data else 0
        data['l3_h__itsx_prov_percent'] = int(round((data['l3_h__itsx_prov']/data['Population'])*100,0)) if 'l3_h__itsx_prov' in data else 0
        data['l4_h__itsx_prov_percent'] = int(round((data['l4_h__itsx_prov']/data['Population'])*100,0)) if 'l4_h__itsx_prov' in data else 0
        data['l5_h__itsx_prov_percent'] = int(round((data['l5_h__itsx_prov']/data['Population'])*100,0)) if 'l5_h__itsx_prov' in data else 0
        data['l6_h__itsx_prov_percent'] = int(round((data['l6_h__itsx_prov']/data['Population'])*100,0)) if 'l6_h__itsx_prov' in data else 0
        data['l7_h__itsx_prov_percent'] = int(round((data['l7_h__itsx_prov']/data['Population'])*100,0)) if 'l7_h__itsx_prov' in data else 0
        data['l8_h__itsx_prov_percent'] = int(round((data['l8_h__itsx_prov']/data['Population'])*100,0)) if 'l8_h__itsx_prov' in data else 0
        data['g8_h__itsx_prov_percent'] = int(round((data['g8_h__itsx_prov']/data['Population'])*100,0)) if 'g8_h__itsx_prov' in data else 0

        data['l1_h__near_prov_percent'] = int(round((data['l1_h__near_prov']/data['Population'])*100,0)) if 'l1_h__near_prov' in data else 0
        data['l2_h__near_prov_percent'] = int(round((data['l2_h__near_prov']/data['Population'])*100,0)) if 'l2_h__near_prov' in data else 0
        data['l3_h__near_prov_percent'] = int(round((data['l3_h__near_prov']/data['Population'])*100,0)) if 'l3_h__near_prov' in data else 0
        data['l4_h__near_prov_percent'] = int(round((data['l4_h__near_prov']/data['Population'])*100,0)) if 'l4_h__near_prov' in data else 0
        data['l5_h__near_prov_percent'] = int(round((data['l5_h__near_prov']/data['Population'])*100,0)) if 'l5_h__near_prov' in data else 0
        data['l6_h__near_prov_percent'] = int(round((data['l6_h__near_prov']/data['Population'])*100,0)) if 'l6_h__near_prov' in data else 0
        data['l7_h__near_prov_percent'] = int(round((data['l7_h__near_prov']/data['Population'])*100,0)) if 'l7_h__near_prov' in data else 0
        data['l8_h__near_prov_percent'] = int(round((data['l8_h__near_prov']/data['Population'])*100,0)) if 'l8_h__near_prov' in data else 0
        data['g8_h__near_prov_percent'] = int(round((data['g8_h__near_prov']/data['Population'])*100,0)) if 'g8_h__near_prov' in data else 0

        data['l1_h__near_dist_percent'] = int(round((data['l1_h__near_dist']/data['Population'])*100,0)) if 'l1_h__near_dist' in data else 0
        data['l2_h__near_dist_percent'] = int(round((data['l2_h__near_dist']/data['Population'])*100,0)) if 'l2_h__near_dist' in data else 0
        data['l3_h__near_dist_percent'] = int(round((data['l3_h__near_dist']/data['Population'])*100,0)) if 'l3_h__near_dist' in data else 0
        data['l4_h__near_dist_percent'] = int(round((data['l4_h__near_dist']/data['Population'])*100,0)) if 'l4_h__near_dist' in data else 0
        data['l5_h__near_dist_percent'] = int(round((data['l5_h__near_dist']/data['Population'])*100,0)) if 'l5_h__near_dist' in data else 0
        data['l6_h__near_dist_percent'] = int(round((data['l6_h__near_dist']/data['Population'])*100,0)) if 'l6_h__near_dist' in data else 0
        data['l7_h__near_dist_percent'] = int(round((data['l7_h__near_dist']/data['Population'])*100,0)) if 'l7_h__near_dist' in data else 0
        data['l8_h__near_dist_percent'] = int(round((data['l8_h__near_dist']/data['Population'])*100,0)) if 'l8_h__near_dist' in data else 0
        data['g8_h__near_dist_percent'] = int(round((data['g8_h__near_dist']/data['Population'])*100,0)) if 'g8_h__near_dist' in data else 0

        response.append(data)
    return response     

def getFloodForecast(filterLock, flag, code): 
    response = getCommonUse(flag, code)  
    flood_parent = getFloodForecastMatrix(filterLock, flag, code)
    for i in flood_parent:
        response[i]=flood_parent[i]

    data = getProvinceSummary(filterLock, flag, code)
    response['lc_child']=data

    return response    

def getAvalancheForecast(filterLock, flag, code): 
    targetBase = AfgLndcrva.objects.all()
    response = getCommonUse(flag, code)
    response['Population']=getTotalPop(filterLock, flag, code, targetBase)
    rawAvalancheRisk = getRawAvalancheRisk(filterLock, flag, code)
    for i in rawAvalancheRisk:
        response[i]=rawAvalancheRisk[i]

    rawAvalancheForecast = getRawAvalancheForecast(filterLock, flag, code)

    for i in rawAvalancheForecast:
        response[i]=rawAvalancheForecast[i]

    response['total_pop_forecast_percent'] = int(round((response['total_ava_forecast_pop']/response['Population'])*100,0))
    response['high_pop_forecast_percent'] = int(round((response['ava_forecast_high_pop']/response['Population'])*100,0))
    response['med_pop_forecast_percent'] = int(round((response['ava_forecast_med_pop']/response['Population'])*100,0))
    response['low_pop_forecast_percent'] = int(round((response['ava_forecast_low_pop']/response['Population'])*100,0))

    data1 = []
    data1.append(['agg_simplified_description','area_population'])
    data1.append(['',response['total_ava_forecast_pop']])
    data1.append(['',response['Population']-response['total_ava_forecast_pop']])
    response['total_pop_forecast_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })

    data2 = []
    data2.append(['agg_simplified_description','area_population'])
    data2.append(['',response['ava_forecast_high_pop']])
    data2.append(['',response['Population']-response['ava_forecast_high_pop']])
    response['high_pop_forecast_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })

    data3 = []
    data3.append(['agg_simplified_description','area_population'])
    data3.append(['',response['ava_forecast_med_pop']])
    data3.append(['',response['Population']-response['ava_forecast_med_pop']])
    response['med_pop_forecast_chart'] = gchart.PieChart(SimpleDataSource(data=data3), html_id="pie_chart3", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })

    data4 = []
    data4.append(['agg_simplified_description','area_population'])
    data4.append(['',response['ava_forecast_low_pop']])
    data4.append(['',response['Population']-response['ava_forecast_low_pop']])
    response['low_pop_forecast_chart'] = gchart.PieChart(SimpleDataSource(data=data4), html_id="pie_chart4", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })

    data = getProvinceSummary(filterLock, flag, code)

    for i in data:
        i['total_pop_forecast_percent'] = int(round(i['total_ava_forecast_pop']/i['Population']*100,0))
        i['high_pop_forecast_percent'] = int(round(i['ava_forecast_high_pop']/i['Population']*100,0))
        i['med_pop_forecast_percent'] = int(round(i['ava_forecast_med_pop']/i['Population']*100,0))
        i['low_pop_forecast_percent'] = int(round(i['ava_forecast_low_pop']/i['Population']*100,0))

    response['lc_child']=data

    return response

def getRawAvalancheForecast(filterLock, flag, code):
    YEAR = datetime.datetime.utcnow().strftime("%Y")
    MONTH = datetime.datetime.utcnow().strftime("%m")
    DAY = datetime.datetime.utcnow().strftime("%d")
    response = {}

    # Avalanche Forecasted
    if flag=='entireAfg':
        cursor = connections['geodb'].cursor()
        cursor.execute("select forcastedvalue.riskstate, \
            sum(afg_avsa.avalanche_pop) \
            FROM afg_avsa \
            INNER JOIN current_sc_basins ON (ST_WITHIN(ST_Centroid(afg_avsa.wkb_geometry), current_sc_basins.wkb_geometry)) \
            INNER JOIN afg_sheda_lvl4 ON ( afg_avsa.basinmember_id = afg_sheda_lvl4.ogc_fid ) \
            INNER JOIN forcastedvalue ON ( afg_sheda_lvl4.ogc_fid = forcastedvalue.basin_id ) \
            WHERE (NOT (afg_avsa.basinmember_id IN (SELECT U1.ogc_fid FROM afg_sheda_lvl4 U1 LEFT OUTER JOIN forcastedvalue U2 ON ( U1.ogc_fid = U2.basin_id ) WHERE U2.riskstate IS NULL)) \
            AND forcastedvalue.datadate = '%s-%s-%s' \
            AND forcastedvalue.forecasttype = 'snowwater' ) \
            GROUP BY forcastedvalue.riskstate" %(YEAR,MONTH,DAY))  
        row = cursor.fetchall()
        cursor.close()
    elif flag=='currentProvince':
        cursor = connections['geodb'].cursor()
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "prov_code  = '"+str(code)+"'"
        cursor.execute("select forcastedvalue.riskstate, \
            sum(afg_avsa.avalanche_pop) \
            FROM afg_avsa \
            INNER JOIN current_sc_basins ON (ST_WITHIN(ST_Centroid(afg_avsa.wkb_geometry), current_sc_basins.wkb_geometry)) \
            INNER JOIN afg_sheda_lvl4 ON ( afg_avsa.basinmember_id = afg_sheda_lvl4.ogc_fid ) \
            INNER JOIN forcastedvalue ON ( afg_sheda_lvl4.ogc_fid = forcastedvalue.basin_id ) \
            WHERE (NOT (afg_avsa.basinmember_id IN (SELECT U1.ogc_fid FROM afg_sheda_lvl4 U1 LEFT OUTER JOIN forcastedvalue U2 ON ( U1.ogc_fid = U2.basin_id ) WHERE U2.riskstate IS NULL)) \
            AND forcastedvalue.datadate = '%s-%s-%s' \
            AND forcastedvalue.forecasttype = 'snowwater' ) \
            and afg_avsa.%s \
            GROUP BY forcastedvalue.riskstate" %(YEAR,MONTH,DAY,ff0001)) 
        row = cursor.fetchall()
        cursor.close()
    elif flag=='drawArea':
        cursor = connections['geodb'].cursor()
        cursor.execute("select forcastedvalue.riskstate, \
            sum(case \
                when ST_CoveredBy(afg_avsa.wkb_geometry , %s) then afg_avsa.avalanche_pop \
                else st_area(st_intersection(afg_avsa.wkb_geometry, %s)) / st_area(afg_avsa.wkb_geometry)* avalanche_pop end \
            ) \
            FROM afg_avsa \
            INNER JOIN current_sc_basins ON (ST_WITHIN(ST_Centroid(afg_avsa.wkb_geometry), current_sc_basins.wkb_geometry)) \
            INNER JOIN afg_sheda_lvl4 ON ( afg_avsa.basinmember_id = afg_sheda_lvl4.ogc_fid ) \
            INNER JOIN forcastedvalue ON ( afg_sheda_lvl4.ogc_fid = forcastedvalue.basin_id ) \
            WHERE (NOT (afg_avsa.basinmember_id IN (SELECT U1.ogc_fid FROM afg_sheda_lvl4 U1 LEFT OUTER JOIN forcastedvalue U2 ON ( U1.ogc_fid = U2.basin_id ) WHERE U2.riskstate IS NULL)) \
            AND forcastedvalue.datadate = '%s-%s-%s' \
            AND forcastedvalue.forecasttype = 'snowwater' ) \
            GROUP BY forcastedvalue.riskstate" %(filterLock,filterLock,YEAR,MONTH,DAY)) 
        row = cursor.fetchall()
        cursor.close()
    else:
        cursor = connections['geodb'].cursor()
        cursor.execute("select forcastedvalue.riskstate, \
            sum(afg_avsa.avalanche_pop) \
            FROM afg_avsa \
            INNER JOIN current_sc_basins ON (ST_WITHIN(ST_Centroid(afg_avsa.wkb_geometry), current_sc_basins.wkb_geometry)) \
            INNER JOIN afg_sheda_lvl4 ON ( afg_avsa.basinmember_id = afg_sheda_lvl4.ogc_fid ) \
            INNER JOIN forcastedvalue ON ( afg_sheda_lvl4.ogc_fid = forcastedvalue.basin_id ) \
            WHERE (NOT (afg_avsa.basinmember_id IN (SELECT U1.ogc_fid FROM afg_sheda_lvl4 U1 LEFT OUTER JOIN forcastedvalue U2 ON ( U1.ogc_fid = U2.basin_id ) WHERE U2.riskstate IS NULL)) \
            AND forcastedvalue.datadate = '%s-%s-%s' \
            AND forcastedvalue.forecasttype = 'snowwater' ) \
            AND ST_Within(afg_avsa.wkb_geometry, %s) \
            GROUP BY forcastedvalue.riskstate" %(YEAR,MONTH,DAY,filterLock))  
        row = cursor.fetchall()
        cursor.close()    

    response['ava_forecast_low_pop']=round(dict(row).get(1, 0),0) 
    response['ava_forecast_med_pop']=round(dict(row).get(2, 0),0) 
    response['ava_forecast_high_pop']=round(dict(row).get(3, 0),0) 
    response['total_ava_forecast_pop']=response['ava_forecast_low_pop'] + response['ava_forecast_med_pop'] + response['ava_forecast_high_pop']

    return response

def getAvalancheRisk(filterLock, flag, code): 
    targetBase = AfgLndcrva.objects.all()
    response = getCommonUse(flag, code)  
    response['Population']=getTotalPop(filterLock, flag, code, targetBase)
    response['Area']=getTotalArea(filterLock, flag, code, targetBase)
    response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)

    rawAvalancheRisk = getRawAvalancheRisk(filterLock, flag, code)
    for i in rawAvalancheRisk:
        response[i]=rawAvalancheRisk[i]

    response['total_pop_atrisk_percent'] = int(round((response['total_ava_population']/response['Population'])*100,0))
    response['total_area_atrisk_percent'] = int(round((response['total_ava_area']/response['Area'])*100,0))

    response['total_pop_high_atrisk_percent'] = int(round((response['high_ava_population']/response['Population'])*100,0))
    response['total_area_high_atrisk_percent'] = int(round((response['high_ava_area']/response['Area'])*100,0))

    response['total_pop_med_atrisk_percent'] = int(round((response['med_ava_population']/response['Population'])*100,0))
    response['total_area_med_atrisk_percent'] = int(round((response['med_ava_area']/response['Area'])*100,0))

    data1 = []
    data1.append(['agg_simplified_description','area_population'])
    data1.append(['',response['total_ava_population']])
    data1.append(['',response['Population']-response['total_ava_population']])
    response['total_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data2 = []
    data2.append(['agg_simplified_description','area_population'])
    data2.append(['',response['total_ava_area']])
    data2.append(['',response['Area']-response['total_ava_area']])
    response['total_area_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data3 = []
    data3.append(['agg_simplified_description','area_population'])
    data3.append(['',response['high_ava_population']])
    data3.append(['',response['Population']-response['high_ava_population']])
    response['high_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data3), html_id="pie_chart3", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data4 = []
    data4.append(['agg_simplified_description','area_population'])
    data4.append(['',response['med_ava_population']])
    data4.append(['',response['Population']-response['med_ava_population']])
    response['med_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data4), html_id="pie_chart4", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data = getProvinceSummary(filterLock, flag, code)

    for i in data:
        i['total_pop_atrisk_percent'] = int(round(i['total_ava_population']/i['Population']*100,0))
        i['total_area_atrisk_percent'] = int(round(i['total_ava_area']/i['Area']*100,0))
        i['total_pop_high_atrisk_percent'] = int(round(i['high_ava_population']/i['Population']*100,0))
        i['total_area_high_atrisk_percent'] = int(round(i['high_ava_area']/i['Area']*100,0))
        i['total_pop_med_atrisk_percent'] = int(round(i['med_ava_population']/i['Population']*100,0))
        i['total_area_med_atrisk_percent'] = int(round(i['med_ava_area']/i['Area']*100,0))

    response['lc_child']=data

    return response      

def getFloodRisk(filterLock, flag, code):
    targetBase = AfgLndcrva.objects.all() 
    response = getCommonUse(flag, code)  
    response['Population']=getTotalPop(filterLock, flag, code, targetBase)
    response['Area']=getTotalArea(filterLock, flag, code, targetBase)
    response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)

    rawBaseline = getRawBaseLine(filterLock, flag, code)
    rawFloodRisk = getRawFloodRisk(filterLock, flag, code)

    for i in rawBaseline:
        response[i]=rawBaseline[i]

    for i in rawFloodRisk:
        response[i]=rawFloodRisk[i]    

    response['settlement_at_floodrisk'] = getSettlementAtFloodRisk(filterLock, flag, code)
    response['settlement_at_floodrisk_percent'] = int(round((response['settlement_at_floodrisk']/response['settlement'])*100,0))

    response['total_pop_atrisk_percent'] = int(round((response['total_risk_population']/response['Population'])*100,0))
    response['total_area_atrisk_percent'] = int(round((response['total_risk_area']/response['Area'])*100,0))

    response['total_pop_high_atrisk_percent'] = int(round((response['high_risk_population']/response['Population'])*100,0))
    response['total_pop_med_atrisk_percent'] = int(round((response['med_risk_population']/response['Population'])*100,0))
    response['total_pop_low_atrisk_percent'] = int(round((response['low_risk_population']/response['Population'])*100,0))

    response['built_up_pop_risk_percent'] = int(round((response['built_up_pop_risk']/response['built_up_pop'])*100,0))
    response['built_up_area_risk_percent'] = int(round((response['built_up_area_risk']/response['built_up_area'])*100,0))

    response['cultivated_pop_risk_percent'] = int(round((response['cultivated_pop_risk']/response['cultivated_pop'])*100,0))
    response['cultivated_area_risk_percent'] = int(round((response['cultivated_area_risk']/response['cultivated_area'])*100,0))

    response['barren_pop_risk_percent'] = int(round((response['barren_pop_risk']/response['barren_pop'])*100,0))
    response['barren_area_risk_percent'] = int(round((response['barren_area_risk']/response['barren_area'])*100,0))

    data1 = []
    data1.append(['agg_simplified_description','area_population'])
    data1.append(['',response['total_risk_population']])
    data1.append(['',response['Population']-response['total_risk_population']])
    response['total_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })  

    data2 = []
    data2.append(['agg_simplified_description','area_population'])
    data2.append(['',response['high_risk_population']])
    data2.append(['',response['Population']-response['high_risk_population']])
    response['high_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, })  
    
    data3 = []
    data3.append(['agg_simplified_description','area_population'])
    data3.append(['',response['med_risk_population']])
    data3.append(['',response['Population']-response['med_risk_population']])
    response['med_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data3), html_id="pie_chart3", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data4 = []
    data4.append(['agg_simplified_description','area_population'])
    data4.append(['',response['low_risk_population']])
    data4.append(['',response['Population']-response['low_risk_population']])
    response['low_pop_atrisk_chart'] = gchart.PieChart(SimpleDataSource(data=data4), html_id="pie_chart4", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270, 'tooltip': { 'trigger': 'none' }, }) 

    data = getProvinceSummary(filterLock, flag, code)

    for i in data:
        i['settlement_at_floodrisk_percent'] = int(round(i['settlements_at_risk']/i['settlements']*100,0))
        i['total_pop_atrisk_percent'] = int(round(i['total_risk_population']/i['Population']*100,0))
        i['total_area_atrisk_percent'] = int(round(i['total_risk_area']/i['Area']*100,0))
        i['built_up_pop_risk_percent'] = int(round(i['built_up_pop_risk']/i['built_up_pop']*100,0))
        i['built_up_area_risk_percent'] = int(round(i['built_up_area_risk']/i['built_up_area']*100,0))
        i['cultivated_pop_risk_percent'] = int(round(i['cultivated_pop_risk']/i['cultivated_pop']*100,0))
        i['cultivated_area_risk_percent'] = int(round(i['cultivated_area_risk']/i['cultivated_area']*100,0))
        i['barren_pop_risk_percent'] = int(round(i['barren_pop_risk']/i['barren_pop']*100,0))
        i['barren_area_risk_percent'] = int(round(i['barren_area_risk']/i['barren_area']*100,0))

    response['lc_child']=data

    return response

def getSettlementAtFloodRisk(filterLock, flag, code):
    response = {}    
    targetRiskIncludeWater = AfgFldzonea100KRiskLandcoverPop.objects.all()
    targetRisk = targetRiskIncludeWater.exclude(agg_simplified_description='Water body and marshland')

    # Number settlement at risk of flood
    if flag=='drawArea':
        countsBase = targetRisk.exclude(mitigated_pop__gt=0).filter(agg_simplified_description='Built-up').extra(
            select={
                'numbersettlementsatrisk': 'count(distinct vuid)'}, 
            where = {'st_area(st_intersection(wkb_geometry,'+filterLock+')) / st_area(wkb_geometry)*fldarea_sqm > 1 and ST_Intersects(wkb_geometry, '+filterLock+')'}).values('numbersettlementsatrisk')
    elif flag=='entireAfg':
        countsBase = targetRisk.exclude(mitigated_pop__gt=0).filter(agg_simplified_description='Built-up').extra(
            select={
                'numbersettlementsatrisk': 'count(distinct vuid)'}).values('numbersettlementsatrisk')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "prov_code  = '"+str(code)+"'"
        countsBase = targetRisk.exclude(mitigated_pop__gt=0).filter(agg_simplified_description='Built-up').extra(
            select={
                'numbersettlementsatrisk': 'count(distinct vuid)'}, 
            where = {ff0001}).values('numbersettlementsatrisk')
    elif flag=='currentBasin':
        countsBase = targetRisk.exclude(mitigated_pop__gt=0).filter(agg_simplified_description='Built-up').extra(
            select={
                'numbersettlementsatrisk': 'count(distinct vuid)'}, 
            where = {"vuid = '"+str(code)+"'"}).values('numbersettlementsatrisk')    
    else:
        countsBase = targetRisk.exclude(mitigated_pop__gt=0).filter(agg_simplified_description='Built-up').extra(
            select={
                'numbersettlementsatrisk': 'count(distinct vuid)'}, 
            where = {'ST_Within(wkb_geometry, '+filterLock+')'}).values('numbersettlementsatrisk')

    return round(countsBase[0]['numbersettlementsatrisk'],0)

def getRawAvalancheRisk(filterLock, flag, code):
    response = {}
    targetAvalanche = AfgAvsa.objects.all()
    counts =  getRiskNumber(targetAvalanche, filterLock, 'avalanche_cat', 'avalanche_pop', 'sum_area_sqm', flag, code, None)
    # pop at risk level
    temp = dict([(c['avalanche_cat'], c['count']) for c in counts])
    response['high_ava_population']=round(temp.get('High', 0),0)
    response['med_ava_population']=round(temp.get('Moderate', 0), 0)
    response['low_ava_population']=0
    response['total_ava_population']=response['high_ava_population']+response['med_ava_population']+response['low_ava_population']

    # area at risk level
    temp = dict([(c['avalanche_cat'], c['areaatrisk']) for c in counts])
    response['high_ava_area']=round(temp.get('High', 0)/1000000,1)
    response['med_ava_area']=round(temp.get('Moderate', 0)/1000000,1)
    response['low_ava_area']=0    
    response['total_ava_area']=round(response['high_ava_area']+response['med_ava_area']+response['low_ava_area'],2) 

    return response

def getRawFloodRisk(filterLock, flag, code):
    response = {}    
    targetRiskIncludeWater = AfgFldzonea100KRiskLandcoverPop.objects.all()
    targetRisk = targetRiskIncludeWater.exclude(agg_simplified_description='Water body and marshland')

    # Flood Risk
    counts =  getRiskNumber(targetRisk.exclude(mitigated_pop__gt=0), filterLock, 'deeperthan', 'fldarea_population', 'fldarea_sqm', flag, code, None)
    
    # pop at risk level
    temp = dict([(c['deeperthan'], c['count']) for c in counts])
    response['high_risk_population']=round(temp.get('271 cm', 0),0)
    response['med_risk_population']=round(temp.get('121 cm', 0), 0)
    response['low_risk_population']=round(temp.get('029 cm', 0),0)
    response['total_risk_population']=response['high_risk_population']+response['med_risk_population']+response['low_risk_population']

    # area at risk level
    temp = dict([(c['deeperthan'], c['areaatrisk']) for c in counts])
    response['high_risk_area']=round(temp.get('271 cm', 0)/1000000,1)
    response['med_risk_area']=round(temp.get('121 cm', 0)/1000000,1)
    response['low_risk_area']=round(temp.get('029 cm', 0)/1000000,1)    
    response['total_risk_area']=round(response['high_risk_area']+response['med_risk_area']+response['low_risk_area'],2) 

    counts =  getRiskNumber(targetRiskIncludeWater.exclude(mitigated_pop__gt=0), filterLock, 'agg_simplified_description', 'fldarea_population', 'fldarea_sqm', flag, code, None)

    # landcover/pop/atrisk
    temp = dict([(c['agg_simplified_description'], c['count']) for c in counts])
    response['built_up_pop_risk'] = round(temp.get('Built-up', 0),0)
    response['cultivated_pop_risk'] = round(temp.get('Fruit trees', 0),0)+round(temp.get('Irrigated agricultural land', 0),0)+round(temp.get('Rainfed agricultural land', 0),0)+round(temp.get('Vineyards', 0),0)
    response['barren_pop_risk'] = round(temp.get('Barren land', 0),0)+round(temp.get('Permanent snow', 0),0)+round(temp.get('Rangeland', 0),0)+round(temp.get('Sand cover', 0),0)+round(temp.get('Forest and shrubs', 0),0)

    temp = dict([(c['agg_simplified_description'], c['areaatrisk']) for c in counts])
    response['built_up_area_risk'] = round(temp.get('Built-up', 0)/1000000,1)
    response['cultivated_area_risk'] = round(temp.get('Fruit trees', 0)/1000000,1)+round(temp.get('Irrigated agricultural land', 0)/1000000,1)+round(temp.get('Rainfed agricultural land', 0)/1000000,1)+round(temp.get('Vineyards', 0)/1000000,1)
    response['barren_area_risk'] = round(temp.get('Barren land', 0)/1000000,1)+round(temp.get('Permanent snow', 0)/1000000,1)+round(temp.get('Rangeland', 0)/1000000,1)+round(temp.get('Sand cover', 0)/1000000,1)+round(temp.get('Forest and shrubs', 0)/1000000,1)

    return response             

def getRawBaseLine(filterLock, flag, code):
    targetBase = AfgLndcrva.objects.all()
    response = {}
    parent_data = getRiskNumber(targetBase, filterLock, 'agg_simplified_description', 'area_population', 'area_sqm', flag, code, None)
    temp = dict([(c['agg_simplified_description'], c['count']) for c in parent_data])
    
    response['built_up_pop'] = round(temp.get('Built-up', 0),0)
    response['cultivated_pop'] = round(temp.get('Fruit trees', 0),0)+round(temp.get('Irrigated agricultural land', 0),0)+round(temp.get('Rainfed agricultural land', 0),0)+round(temp.get('Vineyards', 0),0)
    response['barren_pop'] = round(temp.get('Water body and marshland', 0),0)+round(temp.get('Barren land', 0),0)+round(temp.get('Permanent snow', 0),0)+round(temp.get('Rangeland', 0),0)+round(temp.get('Sand cover', 0),0)+round(temp.get('Forest and shrubs', 0),0)

    temp = dict([(c['agg_simplified_description'], c['areaatrisk']) for c in parent_data])
    response['built_up_area'] = round(temp.get('Built-up', 0)/1000000,1)
    response['cultivated_area'] = round(temp.get('Fruit trees', 0)/1000000,1)+round(temp.get('Irrigated agricultural land', 0)/1000000,1)+round(temp.get('Rainfed agricultural land', 0)/1000000,1)+round(temp.get('Vineyards', 0)/1000000,1)
    response['barren_area'] = round(temp.get('Water body and marshland', 0)/1000000,1)+round(temp.get('Barren land', 0)/1000000,1)+round(temp.get('Permanent snow', 0)/1000000,1)+round(temp.get('Rangeland', 0)/1000000,1)+round(temp.get('Sand cover', 0)/1000000,1)+round(temp.get('Forest and shrubs', 0)/1000000,1)

    return response

def getBaseline(filterLock, flag, code):
    response = getCommonUse(flag, code)    
    targetBase = AfgLndcrva.objects.all()
    
    response['Population']=getTotalPop(filterLock, flag, code, targetBase)
    response['Area']=getTotalArea(filterLock, flag, code, targetBase)
    response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)
    response['hltfac']=getTotalHealthFacilities(filterLock, flag, code, AfgHltfac)
    response['roadnetwork']=getTotalRoadNetwork(filterLock, flag, code, AfgRdsl)
    
    rawBaseline = getRawBaseLine(filterLock, flag, code)
    for i in rawBaseline:
        response[i]=rawBaseline[i]

    hltParentData = getParentHltFacRecap(filterLock, flag, code) 
    tempHLTBase = dict([(c['facility_types_description'], c['numberhospital']) for c in hltParentData])
    response['hlt_h1'] = round(tempHLTBase.get("Regional / National Hospital (H1)", 0))
    response['hlt_h2'] = round(tempHLTBase.get("Provincial Hospital (H2)", 0))
    response['hlt_h3'] = round(tempHLTBase.get("District Hospital (H3)", 0))
    response['hlt_chc'] = round(tempHLTBase.get("Comprehensive Health Center (CHC)", 0))
    response['hlt_bhc'] = round(tempHLTBase.get("Basic Health Center (BHC)", 0))  
    response['hlt_shc'] = round(tempHLTBase.get("Sub Health Center (SHC)", 0)) 
    response['hlt_others'] = round(tempHLTBase.get("Rehabilitation Center (RH)", 0))+round(tempHLTBase.get("Special Hospital (SH)", 0))+round(tempHLTBase.get("Maternity Home (MH)", 0))+round(tempHLTBase.get("Drug Addicted Treatment Center", 0))+round(tempHLTBase.get("Private Clinic", 0))+round(tempHLTBase.get("Other", 0))+round(tempHLTBase.get("Malaria Center (MC)", 0))+round(tempHLTBase.get("Mobile Health Team (MHT)", 0))

    roadParentData = getParentRoadNetworkRecap(filterLock, flag, code)
    tempRoadBase = dict([(c['type_update'], c['road_length']) for c in roadParentData])
    response['road_primary'] = round(tempRoadBase.get("primary", 0))   
    response['road_secondary'] = round(tempRoadBase.get("secondary", 0))  
    response['road_track'] = round(tempRoadBase.get("track", 0))  
    response['road_tertiary'] = round(tempRoadBase.get("tertiary", 0))
    response['road_path'] = round(tempRoadBase.get("path", 0)) 
    response['road_highway'] = round(tempRoadBase.get("highway", 0))  
    response['road_residential'] = round(tempRoadBase.get("residential", 0)) 
    response['road_river_crossing'] = round(tempRoadBase.get("river crossing", 0)) 
    response['road_bridge'] = round(tempRoadBase.get("bridge", 0))   

    data = getProvinceSummary(filterLock, flag, code)
    response['lc_child']=data

    data = getProvinceAdditionalSummary(filterLock, flag, code)
    response['additional_child']=data
    # print response
    return response

def getParentRoadNetworkRecap(filterLock, flag, code):
    if flag=='drawArea':
        countsRoadBase = AfgRdsl.objects.all().values('type_update').annotate(counter=Count('ogc_fid')).extra(
        select={
            'road_length' : 'SUM(  \
                    case \
                        when ST_CoveredBy(wkb_geometry'+','+filterLock+') then road_length \
                        else ST_Length(st_intersection(wkb_geometry::geography'+','+filterLock+')) / road_length end \
                )/1000'
        },
        where = {
            'ST_Intersects(wkb_geometry'+', '+filterLock+')'
        }).values('type_update','road_length') 

    elif flag=='entireAfg':    
        countsRoadBase = AfgRdsl.objects.all().values('type_update').annotate(counter=Count('ogc_fid')).extra(
                select={
                    'road_length' : 'SUM(road_length)/1000'
                }).values('type_update', 'road_length')
        
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            if len(str(code))==1:
                ff0001 =  "left(cast(dist_code as text),1)  = '"+str(code)+"' and length(cast(dist_code as text))=3"
            else:
                ff0001 =  "left(cast(dist_code as text),2)  = '"+str(code)+"' and length(cast(dist_code as text))=4"    
                
        countsRoadBase = AfgRdsl.objects.all().values('type_update').annotate(counter=Count('ogc_fid')).extra(
            select={
                 'road_length' : 'SUM(road_length)/1000'
            },
            where = {
                ff0001
             }).values('type_update','road_length') 

    elif flag=='currentBasin':
        print 'currentBasin'
    else:
        countsRoadBase = AfgRdsl.objects.all().values('type_update').annotate(counter=Count('ogc_fid')).extra(
            select={
                'road_length' : 'SUM(road_length)/1000'
            },
            where = {
                'ST_Within(wkb_geometry'+', '+filterLock+')'
            }).values('type_update','road_length') 
    return countsRoadBase     

def getParentHltFacRecap(filterLock, flag, code):
    targetBase = AfgHltfac.objects.all().filter(activestatus='Y')
    if flag=='drawArea':
        countsHLTBase = targetBase.values('facility_types_description').annotate(counter=Count('ogc_fid')).extra(
                select={
                    'numberhospital' : 'count(*)'
                },
                where = {
                    'ST_Intersects(wkb_geometry'+', '+filterLock+')'
                }).values('facility_types_description','numberhospital')

    elif flag=='entireAfg':    
        countsHLTBase = targetBase.values('facility_types_description').annotate(counter=Count('ogc_fid')).extra(
                select={
                    'numberhospital' : 'count(*)'
                }).values('facility_types_description','numberhospital')
        
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 = "prov_code  = '"+str(code)+"'"  
                
        countsHLTBase = targetBase.values('facility_types_description').annotate(counter=Count('ogc_fid')).extra(
            select={
                    'numberhospital' : 'count(*)'
            },where = {
                ff0001
            }).values('facility_types_description','numberhospital')
    elif flag=='currentBasin':
        print 'currentBasin'
    else:
        countsHLTBase = targetBase.values('facility_types_description').annotate(counter=Count('ogc_fid')).extra(
            select={
                    'numberhospital' : 'count(*)'
            },where = {
                'ST_Within(wkb_geometry'+', '+filterLock+')'
            }).values('facility_types_description','numberhospital')
    return countsHLTBase   

def getTotalPop(filterLock, flag, code, targetBase):
    # All population number
    if flag=='drawArea':
        countsBase = targetBase.extra(
            select={
                'countbase' : 'SUM(  \
                        case \
                            when ST_CoveredBy(wkb_geometry,'+filterLock+') then area_population \
                            else st_area(st_intersection(wkb_geometry,'+filterLock+')) / st_area(wkb_geometry)*area_population end \
                    )'
            },
            where = {
                'ST_Intersects(wkb_geometry, '+filterLock+')'
            }).values('countbase')
    elif flag=='entireAfg':
        countsBase = targetBase.extra(
            select={
                'countbase' : 'SUM(area_population)'
            }).values('countbase')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "prov_code  = '"+str(code)+"'"
        countsBase = targetBase.extra(
            select={
                'countbase' : 'SUM(area_population)'
            },
            where = {
                ff0001
            }).values('countbase')
    elif flag=='currentBasin':
        countsBase = targetBase.extra(
            select={
                'countbase' : 'SUM(area_population)'
            }, 
            where = {"vuid = '"+str(code)+"'"}).values('countbase')     
    else:
        countsBase = targetBase.extra(
            select={
                'countbase' : 'SUM(area_population)'
            },
            where = {
                'ST_Within(wkb_geometry, '+filterLock+')'
            }).values('countbase')
                
    return round(countsBase[0]['countbase'],0)

def getTotalArea(filterLock, flag, code, targetBase):
    if flag=='drawArea':
        countsBase = targetBase.extra(
            select={
                'areabase' : 'SUM(  \
                        case \
                            when ST_CoveredBy(wkb_geometry,'+filterLock+') then area_sqm \
                            else st_area(st_intersection(wkb_geometry,'+filterLock+')) / st_area(wkb_geometry)*area_sqm end \
                    )'
            },
            where = {
                'ST_Intersects(wkb_geometry, '+filterLock+')'
            }).values('areabase')
    elif flag=='entireAfg':
        countsBase = targetBase.extra(
            select={
                'areabase' : 'SUM(area_sqm)'
            }).values('areabase')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "prov_code  = '"+str(code)+"'"
        countsBase = targetBase.extra(
            select={
                'areabase' : 'SUM(area_sqm)'
            },
            where = {
                ff0001
            }).values('areabase')
    elif flag=='currentBasin':
        countsBase = targetBase.extra(
            select={
                'areabase' : 'SUM(area_sqm)'
            },
            where = {"vuid = '"+str(code)+"'"}).values('areabase')      

    else:
        countsBase = targetBase.extra(
            select={
                'areabase' : 'SUM(area_sqm)'
            },
            where = {
                'ST_Within(wkb_geometry, '+filterLock+')'
            }).values('areabase')

    return round(countsBase[0]['areabase']/1000000,0)      

def getTotalSettlement(filterLock, flag, code, targetBase):     
    if flag=='drawArea':
        countsBase = targetBase.exclude(agg_simplified_description='Water body and marshland').extra(
            select={
                'numbersettlements': 'count(distinct vuid)'}, 
            where = {'st_area(st_intersection(wkb_geometry,'+filterLock+')) / st_area(wkb_geometry)*area_sqm > 1 and ST_Intersects(wkb_geometry, '+filterLock+')'}).values('numbersettlements')
    elif flag=='entireAfg':
        countsBase = targetBase.exclude(agg_simplified_description='Water body and marshland').extra(
            select={
                'numbersettlements': 'count(distinct vuid)'}).values('numbersettlements')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "prov_code  = '"+str(code)+"'"
        countsBase = targetBase.exclude(agg_simplified_description='Water body and marshland').extra(
            select={
                'numbersettlements': 'count(distinct vuid)'}, 
            where = {ff0001}).values('numbersettlements')
    elif flag=='currentBasin':
        countsBase = targetBase.exclude(agg_simplified_description='Water body and marshland').extra(
            select={
                'numbersettlements': 'count(distinct vuid)'}, 
            where = {"vuid = '"+str(code)+"'"}).values('numbersettlements')   
    else:
        countsBase = targetBase.exclude(agg_simplified_description='Water body and marshland').extra(
            select={
                'numbersettlements': 'count(distinct vuid)'}, 
            where = {'ST_Within(wkb_geometry, '+filterLock+')'}).values('numbersettlements')
    
    return round(countsBase[0]['numbersettlements'],0)

def getTotalHealthFacilities(filterLock, flag, code, targetBase):
    # targetBase = targetBase.objects.all().filter(activestatus='Y').values('facility_types_description')
    targetBase = targetBase.objects.all().filter(activestatus='Y')
    if flag=='drawArea':
        countsHLTBase = targetBase.extra(
                select={
                    'numberhospital' : 'count(*)'
                },
                where = {
                    'ST_Intersects(wkb_geometry'+', '+filterLock+')'
                }).values('numberhospital')

    elif flag=='entireAfg':    
        countsHLTBase = targetBase.extra(
                select={
                    'numberhospital' : 'count(*)'
                }).values('numberhospital')
        
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            ff0001 = "prov_code  = '"+str(code)+"'"     
                
        countsHLTBase = targetBase.extra(
            select={
                    'numberhospital' : 'count(*)'
            },where = {
                ff0001
            }).values('numberhospital')
    elif flag=='currentBasin':
        print 'currentBasin'
    else:
        countsHLTBase = targetBase.extra(
            select={
                    'numberhospital' : 'count(*)'
            },where = {
                'ST_Within(wkb_geometry'+', '+filterLock+')'
            }).values('numberhospital')
    return round(countsHLTBase[0]['numberhospital'],0)    

def getTotalRoadNetwork(filterLock, flag, code, targetBase):
    # targetBase = targetBase.objects.all().filter(activestatus='Y').values('facility_types_description')
    if flag=='drawArea':
        countsRoadBase = targetBase.objects.all().extra(
        select={
            'road_length' : 'SUM(  \
                    case \
                        when ST_CoveredBy(wkb_geometry'+','+filterLock+') then road_length \
                        else ST_Length(st_intersection(wkb_geometry::geography'+','+filterLock+')) / road_length end \
                )/1000'
        },
        where = {
            'ST_Intersects(wkb_geometry'+', '+filterLock+')'
        }).values('road_length')

    elif flag=='entireAfg':    
        countsRoadBase = targetBase.objects.all().extra(
                select={
                    'road_length' : 'SUM(road_length)/1000'
                }).values('road_length')
        
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            if len(str(code))==1:
                ff0001 =  "left(cast(dist_code as text),1)  = '"+str(code)+"'  and length(cast(dist_code as text))=3"
            else:
                ff0001 =  "left(cast(dist_code as text),2)  = '"+str(code)+"'  and length(cast(dist_code as text))=4"    
                
        countsRoadBase = targetBase.objects.all().extra(
            select={
                 'road_length' : 'SUM(road_length)/1000'
            },
            where = {
                ff0001
             }).values('road_length')

    elif flag=='currentBasin':
        print 'currentBasin'
    else:
        countsRoadBase = targetBase.objects.all().extra(
            select={
                'road_length' : 'SUM(road_length)/1000'
            },
            where = {
                'ST_Within(wkb_geometry'+', '+filterLock+')'
            }).values('road_length') 
    return round(countsRoadBase[0]['road_length'],0)

def getProvinceSummary(filterLock, flag, code):
    cursor = connections['geodb'].cursor() 

    print flag, code

    if flag == 'entireAfg':
        sql = "select b.prov_code as code, b.prov_na_en as na_en, a.*, \
            a.fruit_trees_pop+a.irrigated_agricultural_land_pop+a.rainfed_agricultural_land_pop+a.vineyards_pop as cultivated_pop,  \
            a.fruit_trees_area+a.irrigated_agricultural_land_area+a.rainfed_agricultural_land_area+a.vineyards_area as cultivated_area,  \
            a.water_body_pop+a.barren_land_pop+a.permanent_snow_pop+a.rangeland_pop+a.sandcover_pop+a.forest_pop as barren_pop,  \
            a.water_body_area+a.barren_land_area+a.permanent_snow_area+a.rangeland_area+a.sandcover_area+a.forest_area as barren_area,  \
             \
            a.fruit_trees_pop_risk+a.irrigated_agricultural_land_pop_risk+a.rainfed_agricultural_land_pop_risk+a.vineyards_pop_risk as cultivated_pop_risk, \
            a.fruit_trees_area_risk+a.irrigated_agricultural_land_area_risk+a.rainfed_agricultural_land_area_risk+a.vineyards_area_risk as cultivated_area_risk, \
            a.barren_land_pop_risk+a.permanent_snow_pop_risk+a.rangeland_pop_risk+a.sandcover_pop_risk+a.forest_pop_risk as barren_pop_risk, \
            a.barren_land_area_risk+a.permanent_snow_area_risk+a.rangeland_area_risk+a.sandcover_area_risk+a.forest_area_risk as barren_area_risk \
            from provincesummary a \
            inner join afg_admbnda_adm1 b on cast(a.province as integer)=b.prov_code \
            order by a.\"Population\" desc"
    elif flag == 'currentProvince':
        sql = "select b.dist_code as code, b.dist_na_en as na_en, a.*, \
            a.fruit_trees_pop+a.irrigated_agricultural_land_pop+a.rainfed_agricultural_land_pop+a.vineyards_pop as cultivated_pop,  \
            a.fruit_trees_area+a.irrigated_agricultural_land_area+a.rainfed_agricultural_land_area+a.vineyards_area as cultivated_area,  \
            a.water_body_pop+a.barren_land_pop+a.permanent_snow_pop+a.rangeland_pop+a.sandcover_pop+a.forest_pop as barren_pop,  \
            a.water_body_area+a.barren_land_area+a.permanent_snow_area+a.rangeland_area+a.sandcover_area+a.forest_area as barren_area,  \
             \
            a.fruit_trees_pop_risk+a.irrigated_agricultural_land_pop_risk+a.rainfed_agricultural_land_pop_risk+a.vineyards_pop_risk as cultivated_pop_risk, \
            a.fruit_trees_area_risk+a.irrigated_agricultural_land_area_risk+a.rainfed_agricultural_land_area_risk+a.vineyards_area_risk as cultivated_area_risk, \
            a.barren_land_pop_risk+a.permanent_snow_pop_risk+a.rangeland_pop_risk+a.sandcover_pop_risk+a.forest_pop_risk as barren_pop_risk, \
            a.barren_land_area_risk+a.permanent_snow_area_risk+a.rangeland_area_risk+a.sandcover_area_risk+a.forest_area_risk as barren_area_risk \
            from districtsummary a \
            inner join afg_admbnda_adm2 b on cast(a.district as integer)=b.dist_code \
            where b.prov_code="+str(code)+" \
            order by a.\"Population\" desc"
    else:
        return []                

    row = query_to_dicts(cursor, sql)

    response = []
    
    for i in row:
        response.append(i)

    cursor.close()    

    return response

def getProvinceAdditionalSummary(filterLock, flag, code):    
    cursor = connections['geodb'].cursor()
    
    if flag == 'entireAfg':
        sql = "select b.prov_code as code, b.prov_na_en as na_en, a.*, \
        a.hlt_special_hospital+a.hlt_rehabilitation_center+a.hlt_maternity_home+a.hlt_drug_addicted_treatment_center+a.hlt_private_clinic+a.hlt_malaria_center+a.hlt_mobile_health_team+a.hlt_other as hlt_others, \
        a.hlt_special_hospital+a.hlt_rehabilitation_center+a.hlt_maternity_home+a.hlt_drug_addicted_treatment_center+a.hlt_private_clinic+a.hlt_malaria_center+a.hlt_mobile_health_team+a.hlt_other+a.hlt_h1+a.hlt_h2+a.hlt_h3+a.hlt_chc+a.hlt_bhc+a.hlt_shc as hlt_total, \
        a.road_highway+a.road_primary+a.road_secondary+a.road_tertiary+a.road_residential+a.road_track+a.road_path+a.road_river_crossing+a.road_bridge as road_total \
        from province_add_summary a \
        inner join afg_admbnda_adm1 b on cast(a.prov_code as integer)=b.prov_code"
    elif flag == 'currentProvince':
        sql = "select b.dist_code as code, b.dist_na_en as na_en, a.*, \
        a.hlt_special_hospital+a.hlt_rehabilitation_center+a.hlt_maternity_home+a.hlt_drug_addicted_treatment_center+a.hlt_private_clinic+a.hlt_malaria_center+a.hlt_mobile_health_team+a.hlt_other as hlt_others, \
        a.hlt_special_hospital+a.hlt_rehabilitation_center+a.hlt_maternity_home+a.hlt_drug_addicted_treatment_center+a.hlt_private_clinic+a.hlt_malaria_center+a.hlt_mobile_health_team+a.hlt_other+a.hlt_h1+a.hlt_h2+a.hlt_h3+a.hlt_chc+a.hlt_bhc+a.hlt_shc as hlt_total, \
        a.road_highway+a.road_primary+a.road_secondary+a.road_tertiary+a.road_residential+a.road_track+a.road_path+a.road_river_crossing+a.road_bridge as road_total \
        from district_add_summary a \
        inner join afg_admbnda_adm2 b on cast(a.dist_code as integer)=b.dist_code \
        where b.prov_code="+str(code)
    else:
        return []

    row = query_to_dicts(cursor, sql)

    response = []
    
    for i in row:
        response.append(i)

    cursor.close()    

    return response

def getFloodForecastMatrix(filterLock, flag, code):
    response = {}

    YEAR = datetime.datetime.utcnow().strftime("%Y")
    MONTH = datetime.datetime.utcnow().strftime("%m")
    DAY = datetime.datetime.utcnow().strftime("%d")

    targetRiskIncludeWater = AfgFldzonea100KRiskLandcoverPop.objects.all()
    targetRisk = targetRiskIncludeWater.exclude(agg_simplified_description='Water body and marshland')

    counts =  getRiskNumber(targetRisk.exclude(mitigated_pop=0), filterLock, 'deeperthan', 'mitigated_pop', 'fldarea_sqm', flag, code, None)
    temp = dict([(c['deeperthan'], c['count']) for c in counts])
    response['high_risk_mitigated_population']=round(temp.get('271 cm', 0),0)
    response['med_risk_mitigated_population']=round(temp.get('121 cm', 0), 0)
    response['low_risk_mitigated_population']=round(temp.get('029 cm', 0),0)
    response['total_risk_mitigated_population']=response['high_risk_mitigated_population']+response['med_risk_mitigated_population']+response['low_risk_mitigated_population']

    # River Flood Forecasted
    counts =  getRiskNumber(targetRisk.exclude(mitigated_pop__gt=0).select_related("basinmembers").defer('basinmember__wkb_geometry').exclude(basinmember__basins__riskstate=None).filter(basinmember__basins__forecasttype='riverflood',basinmember__basins__datadate='%s-%s-%s' %(YEAR,MONTH,DAY)), filterLock, 'basinmember__basins__riskstate', 'fldarea_population', 'fldarea_sqm', flag, code, 'afg_fldzonea_100k_risk_landcover_pop')
    temp = dict([(c['basinmember__basins__riskstate'], c['count']) for c in counts])
    response['riverflood_forecast_verylow_pop']=round(temp.get(1, 0),0) 
    response['riverflood_forecast_low_pop']=round(temp.get(2, 0),0) 
    response['riverflood_forecast_med_pop']=round(temp.get(3, 0),0) 
    response['riverflood_forecast_high_pop']=round(temp.get(4, 0),0) 
    response['riverflood_forecast_veryhigh_pop']=round(temp.get(5, 0),0) 
    response['riverflood_forecast_extreme_pop']=round(temp.get(6, 0),0) 
    response['total_riverflood_forecast_pop']=response['riverflood_forecast_verylow_pop'] + response['riverflood_forecast_low_pop'] + response['riverflood_forecast_med_pop'] + response['riverflood_forecast_high_pop'] + response['riverflood_forecast_veryhigh_pop'] + response['riverflood_forecast_extreme_pop']

    temp = dict([(c['basinmember__basins__riskstate'], c['areaatrisk']) for c in counts])
    response['riverflood_forecast_verylow_area']=round(temp.get(1, 0)/1000000,0) 
    response['riverflood_forecast_low_area']=round(temp.get(2, 0)/1000000,0) 
    response['riverflood_forecast_med_area']=round(temp.get(3, 0)/1000000,0) 
    response['riverflood_forecast_high_area']=round(temp.get(4, 0)/1000000,0) 
    response['riverflood_forecast_veryhigh_area']=round(temp.get(5, 0)/1000000,0) 
    response['riverflood_forecast_extreme_area']=round(temp.get(6, 0)/1000000,0) 
    response['total_riverflood_forecast_area']=response['riverflood_forecast_verylow_area'] + response['riverflood_forecast_low_area'] + response['riverflood_forecast_med_area'] + response['riverflood_forecast_high_area'] + response['riverflood_forecast_veryhigh_area'] + response['riverflood_forecast_extreme_area']


    # flood risk and riverflood forecast matrix
    px = targetRisk.exclude(mitigated_pop__gt=0).select_related("basinmembers").defer('basinmember__wkb_geometry').exclude(basinmember__basins__riskstate=None).filter(basinmember__basins__forecasttype='riverflood',basinmember__basins__datadate='%s-%s-%s' %(YEAR,MONTH,DAY))
    
    if flag=='entireAfg': 
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            if len(str(code))==1:
                ff0001 =  "left(cast(dist_code as text),1)  = '"+str(code)+"'"
            else:
                ff0001 =  "left(cast(dist_code as text),2)  = '"+str(code)+"'"   
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            },where={
                ff0001
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')
    elif flag=='drawArea':
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(  \
                        case \
                            when ST_CoveredBy(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry ,'+filterLock+') then fldarea_population \
                            else st_area(st_intersection(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry,'+filterLock+')) / st_area(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry)* fldarea_population end \
                    )'
            },
            where = {
                'ST_Intersects(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry, '+filterLock+')'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')  
    else:
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            },
            where = {
                'ST_Within(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry, '+filterLock+')'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')      

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 1 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_verylow_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_verylow_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['riverflood_forecast_verylow_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 2 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_low_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_low_risk_med_pop']=round(temp.get('121 cm', 0), 0) 
    response['riverflood_forecast_low_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 3 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_med_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_med_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['riverflood_forecast_med_risk_high_pop']=round(temp.get('271 cm', 0),0) 

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 4 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_high_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_high_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['riverflood_forecast_high_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 5 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_veryhigh_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_veryhigh_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['riverflood_forecast_veryhigh_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 6 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['riverflood_forecast_extreme_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['riverflood_forecast_extreme_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['riverflood_forecast_extreme_risk_high_pop']=round(temp.get('271 cm', 0),0)


    # Flash Flood Forecasted
    # AfgFldzonea100KRiskLandcoverPop.objects.all().select_related("basinmembers").values_list("agg_simplified_description","basinmember__basins__riskstate")
    counts =  getRiskNumber(targetRisk.exclude(mitigated_pop__gt=0).select_related("basinmembers").defer('basinmember__wkb_geometry').exclude(basinmember__basins__riskstate=None).filter(basinmember__basins__forecasttype='flashflood',basinmember__basins__datadate='%s-%s-%s' %(YEAR,MONTH,DAY)), filterLock, 'basinmember__basins__riskstate', 'fldarea_population', 'fldarea_sqm', flag, code, 'afg_fldzonea_100k_risk_landcover_pop')
    temp = dict([(c['basinmember__basins__riskstate'], c['count']) for c in counts])

    response['flashflood_forecast_verylow_pop']=round(temp.get(1, 0),0) 
    response['flashflood_forecast_low_pop']=round(temp.get(2, 0),0) 
    response['flashflood_forecast_med_pop']=round(temp.get(3, 0),0) 
    response['flashflood_forecast_high_pop']=round(temp.get(4, 0),0) 
    response['flashflood_forecast_veryhigh_pop']=round(temp.get(5, 0),0) 
    response['flashflood_forecast_extreme_pop']=round(temp.get(6, 0),0) 
    response['total_flashflood_forecast_pop']=response['flashflood_forecast_verylow_pop'] + response['flashflood_forecast_low_pop'] + response['flashflood_forecast_med_pop'] + response['flashflood_forecast_high_pop'] + response['flashflood_forecast_veryhigh_pop'] + response['flashflood_forecast_extreme_pop']

    temp = dict([(c['basinmember__basins__riskstate'], c['areaatrisk']) for c in counts])
    response['flashflood_forecast_verylow_area']=round(temp.get(1, 0)/1000000,0) 
    response['flashflood_forecast_low_area']=round(temp.get(2, 0)/1000000,0) 
    response['flashflood_forecast_med_area']=round(temp.get(3, 0)/1000000,0) 
    response['flashflood_forecast_high_area']=round(temp.get(4, 0)/1000000,0) 
    response['flashflood_forecast_veryhigh_area']=round(temp.get(5, 0)/1000000,0) 
    response['flashflood_forecast_extreme_area']=round(temp.get(6, 0)/1000000,0) 
    response['total_flashflood_forecast_area']=response['flashflood_forecast_verylow_area'] + response['flashflood_forecast_low_area'] + response['flashflood_forecast_med_area'] + response['flashflood_forecast_high_area'] + response['flashflood_forecast_veryhigh_area'] + response['flashflood_forecast_extreme_area']

    response['total_flood_forecast_pop'] = response['total_riverflood_forecast_pop'] + response['total_flashflood_forecast_pop']
    response['total_flood_forecast_area'] = response['total_riverflood_forecast_area'] + response['total_flashflood_forecast_area']

    # flood risk and flashflood forecast matrix
    px = targetRisk.exclude(mitigated_pop__gt=0).select_related("basinmembers").defer('basinmember__wkb_geometry').exclude(basinmember__basins__riskstate=None).filter(basinmember__basins__forecasttype='flashflood',basinmember__basins__datadate='%s-%s-%s' %(YEAR,MONTH,DAY))
    # px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
    #     select={
    #         'pop' : 'SUM(fldarea_population)'
    #     }).values('basinmember__basins__riskstate','deeperthan', 'pop') 
    if flag=='entireAfg': 
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')
    elif flag=='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "dist_code  = '"+str(code)+"'"
        else :
            if len(str(code))==1:
                ff0001 =  "left(cast(dist_code as text),1)  = '"+str(code)+"'"
            else:
                ff0001 =  "left(cast(dist_code as text),2)  = '"+str(code)+"'"   
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            },where={
                ff0001
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')
    elif flag=='drawArea':
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(  \
                        case \
                            when ST_CoveredBy(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry ,'+filterLock+') then fldarea_population \
                            else st_area(st_intersection(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry,'+filterLock+')) / st_area(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry)* fldarea_population end \
                    )'
            },
            where = {
                'ST_Intersects(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry, '+filterLock+')'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')  
    else:
        px = px.values('basinmember__basins__riskstate','deeperthan').annotate(counter=Count('ogc_fid')).extra(
            select={
                'pop' : 'SUM(fldarea_population)'
            },
            where = {
                'ST_Within(afg_fldzonea_100k_risk_landcover_pop.wkb_geometry, '+filterLock+')'
            }).values('basinmember__basins__riskstate','deeperthan', 'pop')     

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 1 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_verylow_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_verylow_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['flashflood_forecast_verylow_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 2 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_low_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_low_risk_med_pop']=round(temp.get('121 cm', 0), 0) 
    response['flashflood_forecast_low_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 3 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_med_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_med_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['flashflood_forecast_med_risk_high_pop']=round(temp.get('271 cm', 0),0) 

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 4 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_high_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_high_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['flashflood_forecast_high_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 5 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_veryhigh_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_veryhigh_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['flashflood_forecast_veryhigh_risk_high_pop']=round(temp.get('271 cm', 0),0)

    temp = [ num for num in px if num['basinmember__basins__riskstate'] == 6 ]
    temp = dict([(c['deeperthan'], c['pop']) for c in temp])
    response['flashflood_forecast_extreme_risk_low_pop']=round(temp.get('029 cm', 0),0)
    response['flashflood_forecast_extreme_risk_med_pop']=round(temp.get('121 cm', 0), 0)
    response['flashflood_forecast_extreme_risk_high_pop']=round(temp.get('271 cm', 0),0)   

    return response 

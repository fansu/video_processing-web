#!/usr/bin/python

# load the packages needed
from apiclient.discovery import build
from apiclient.errors import HttpError
from django.http import HttpResponse
import os
import boto
import sys
import MySQLdb
import datetime
from pytz import timezone
from isodate import parse_duration
import calendar, datetime, time 

from django.shortcuts import render_to_response, render
from django.core.context_processors import csrf

def search_func(request):

  #default search keywords is "Google", and maximum result number is 25
  search_keywords = "Google"
  max_results = 25

  #making connection to database rds with the following configurations
  USERNAME=''
  PASSWORD=''
  DB_NAME=''

  print 'connecting to rds instance'

  #connecting to MySQL database with above configurations
  conn = MySQLdb.connect(host='',
                       user=USERNAME,
                       passwd=PASSWORD,
                       db=DB_NAME,
                       port=3306,
                       use_unicode=False,
                       charset='utf8'
                       )

  print 'connected to rds'
  # get the cursor
  cursor = conn.cursor()

  # set the developer key, etc for Youtube API
  DEVELOPER_KEY = ""
  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # prepare for searching by Youtube API
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  rows=''
  checkbox_viewCount=0
  checkbox_relevance=0
  checkbox_age=0
  # Call the search.list method to retrieve results matching the specified
  # query term.
  if request.method == 'POST':
    print 'come to post'
    # check which check box is clicked and which check box is not checked
    if len(request.POST.getlist('check_box_viewCount'))!=0:
       checkbox_viewCount=1
    if len(request.POST.getlist('check_box_relevance'))!=0:
       checkbox_relevance=1
    if len(request.POST.getlist('check_box_age'))!=0:
       checkbox_age=1
    
    # use the database to store the check box value
    cursor.execute("""UPDATE check_box set viewCount = %s, relevance=%s,age=%s""",(checkbox_viewCount,checkbox_relevance,checkbox_age))
    conn.commit()

    # do a search by Youtube API 
    search_response = youtube.search().list(
      q=request.POST['search'],
      part="id,snippet",
      maxResults=max_results
    ).execute()

    # delete all rows in the original table video, which helps to make search results up to data every time
    cursor.execute('TRUNCATE video')
    conn.commit()

    # get the results by search().list and videos().list, and insert them into the MySQL database
    for search_result in search_response.get("items", []):
      if search_result["id"]["kind"] == "youtube#video":
        search_response_statistics = youtube.videos().list(
          part="statistics,contentDetails,topicDetails",
          id = search_result["id"]["videoId"]
        ).execute()

        ts = search_result["snippet"]["publishedAt"]
        dt = datetime.datetime.strptime(ts[:-5],'%Y-%m-%dT%H:%M:%S')#+ datetime.timedelta(hours=int(ts[-5:-3]), minutes=int(ts[-2:]))*int(ts[-6:-5]+'1')
        PublishedAtInseconds = time.mktime(dt.timetuple())

        for search_result_statistics in search_response_statistics.get("items", []):
          # if the desired attribute (topicID) does not exist, set null to this value
          if len(search_result_statistics.get("topicDetails", [])) == 0 or len(search_result_statistics.get("topicDetails", []).get("topicIds", [])) == 0:
            cursor.execute("""INSERT INTO video VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(search_result["id"]["videoId"], search_result["snippet"]["title"], search_result["snippet"]["publishedAt"], int(PublishedAtInseconds), search_result["snippet"]["thumbnails"]["default"]["url"],search_result_statistics["statistics"]["viewCount"], search_result_statistics["statistics"]["likeCount"], search_result_statistics["statistics"]["dislikeCount"], str(parse_duration(search_result_statistics["contentDetails"]["duration"])),'no' ))
            conn.commit()
          else:
            cursor.execute("""INSERT INTO video VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(search_result["id"]["videoId"], search_result["snippet"]["title"], search_result["snippet"]["publishedAt"], int(PublishedAtInseconds), search_result["snippet"]["thumbnails"]["default"]["url"],search_result_statistics["statistics"]["viewCount"], search_result_statistics["statistics"]["likeCount"], search_result_statistics["statistics"]["dislikeCount"], str(parse_duration(search_result_statistics["contentDetails"]["duration"])),search_result_statistics["topicDetails"]["topicIds"][0] ))
            conn.commit()

    # set ready_to_process bit, letting the Java code know that it is time to collect data from the database
    cursor.execute("""UPDATE processing_tags set ready_to_process = %s""",1)
    conn.commit()

    # select the ready_to_display. If this bit is set, the video data has been processed and can be shown to the page
    cursor.execute('SELECT ready_to_display FROM processing_tags')
    row = cursor.fetchone()
    print row[0]
#    while row[0] == 0:
#      print ''

    if checkbox_viewCount == 1:
      cursor.execute('SELECT * FROM video ORDER BY viewCount DESC')
      rows = cursor.fetchall() 
    else:
      if checkbox_age == 1:
        cursor.execute('SELECT * FROM video ORDER BY publishedAtInseconds DESC')
        rows = cursor.fetchall() 
      else:
        if checkbox_relevance == 1:
          cursor.execute('SELECT * FROM video_results INNER JOIN video_trend_results ON video_results.video_id = video_trend_results.video_id ORDER BY weight DESC')
          rows = cursor.fetchall() 
        else:
          cursor.execute('SELECT * FROM video')
          rows = cursor.fetchall()   

    cursor.execute('TRUNCATE video_results')
    conn.commit()

    # set all bits to initial value, which is zero
    cursor.execute("""UPDATE processing_tags set ready_to_display = %s""",0)  
    cursor.execute("""UPDATE processing_tags set ready_to_process = %s""",0)
    conn.commit()
  # send the video data to page
  return render(request, 'search_videos.html', {'videos':rows})

def search_trend(request):

  #default search keywords is "la clippers", and maximum result number is 50
  search_keywords = "la clippers"
  max_results = 50

  #making connection to database rds with the following configurations
  USERNAME=''
  PASSWORD=''
  DB_NAME='stream'

  print 'connecting to rds instance'

  #connecting to MySQL database with above configurations
  conn = MySQLdb.connect(host='',
                       user=USERNAME,
                       passwd=PASSWORD,
                       db=DB_NAME,
                       port=3306,
                       use_unicode=True,
                       charset='utf8'
                       )

  print 'connected to rds'
  # get the cursor
  cursor = conn.cursor()

  # set the developer key, etc for Youtube API
  DEVELOPER_KEY = ""
  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # prepare for searching by Youtube API
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  complete_tag=''
  # Call the search.list method to retrieve results matching the specified
  # query term.
  if request.method == 'POST':
    print 'come to post'
    search_response_id = youtube.search().list(
      q=request.POST['search'],
      part="id,snippet",
      maxResults=max_results
    ).execute()

    # Add each result to the appropriate list, and then display the lists of
    # matching videos
    for search_result in search_response_id.get("items", []):
      if search_result["id"]["kind"] == "youtube#video":
        search_response_statistics = youtube.videos().list(
          part="statistics",
          id = search_result["id"]["videoId"]
        ).execute()

        # insert the video data from Youtube API into MySQL database 
        for search_result_statistics in search_response_statistics.get("items", []):
          cursor.execute("""INSERT INTO video_trend VALUES (%s,%s, %s,%s,%s,%s,%s)""",(search_result["id"]["videoId"], datetime.datetime.now(timezone('US/Eastern')), search_result["snippet"]["title"], search_result["snippet"]["publishedAt"],search_result_statistics["statistics"]["viewCount"], search_result_statistics["statistics"]["likeCount"], search_result_statistics["statistics"]["dislikeCount"] ))
          conn.commit()
          complete_tag = 'Complete!'
  # tell the administrator that this insertion is completed
  return render(request, 'search_trend.html', {'complete_tag':complete_tag})

def help(request):
  # link to the page of help
  return render(request, 'help.html')

def about(request):
  # link to the page of about
  return render(request, 'about.html')


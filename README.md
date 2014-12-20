video_processing-web
====================

Web part of video recommendation system using Django (Python), AWS MySQL database, and IBM InfoSphere Streams

Motivations:
1. Recommend Youtube Videos based on metadata analysis, including previous or current view count, etc;
2. Better recommendation with more options, including order of view count, and upload time, popularity etc;

Why we need stream processing:  
Process tuples like view count of a particular video at each acquired time like a stream to get the trend;
Do the processing part in a higher speed 

Features:
1. Youtube video basic search;
2. Hyperlinks to youtube.com for each particular video;
3. Video recommendation according to the recent view count trend, as a sign of popularity;
4. Video result reordering according to view count, trend, and upload time;

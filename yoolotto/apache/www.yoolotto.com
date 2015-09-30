Listen *:9876
<VirtualHost *:9876>
   ServerName 162.243.120.32:9876
   ServerAlias *.162.243.120.32:9876
   ServerAdmin admin@162.243.120.32:9876

   DocumentRoot /home/nikhil/yoolotto/

   Alias /robots.txt /home/nikhil/yoolotto/yoolotto/static/robots.txt
   Alias /favicon.ico /home/nikhil/yoolotto/yoolotto/static/favicon.ico
   Alias /static/ /home/nikhil/yoolotto/static/

   <Directory /home/nikhil/yoolotto/static>
       Options None
       Order deny,allow
       Allow from all
   </Directory>

   <Directory /home/nikhil/yoolotto/log/>
       Options None
       Order deny,allow
       Allow from all
   </Directory>

   WSGIScriptAlias / /home/nikhil/yoolotto/yoolotto/wsgi.py

   ErrorLog /home/nikhil/yoolotto/log/error.log
   CustomLog /home/nikhil/yoolotto/log/access.log combined

   <Directory /home/nikhil/yoolotto/apache>
      Order allow,deny
      Allow from all
   </Directory>

</VirtualHost>

echo-mod09ga
============

Simple Python script that will query NASA's ECHO Rest API using some simple command line parameters.
To keep it really simple the script only searches for MOD09GA products and it just prints the urls
to std-out.

The script generates a python list internally, so if you want to use that list in another program you can
but I mostly use it to pipe the output to a file.  Then I can take that file and use wget or curl.

Example Usage(s):

Fetch all MOD09GA products for tileID h11v03, save them to a file.  Then use wget to download them all.

    $> python mod09ga_urls.py h11v03 > h11v03-urls.txt
    $> wget -i h11v03-urls.txt

Fetch all MOD09GA products for tileID h09v05 after 2010 (using a start date of January 1, 2011),
save them.  Then use curl and xargs to download the list.

    $> python mod09ga_urls.py h09v05 -s 20110101 > h09v05-urls.txt
    $> cat h09v05-urls.txt | xargs -n1 curl -O

Fetch all MOD09GA hdfs for tile h08v05 between (and including) Feb. 1, 2007 to Dec. 16 2009. Wget them.

    $> python mod09ga_urls.py h08v05 -s 20070201 -e 20091216 > h08v05-urls.txt
    $> wget -i h08v05-urls.txt

More Info About ECHO
====================

API Docs:  https://api.echo.nasa.gov/catalog-rest/catalog-docs/

REST Catalog Search Guide: https://earthdata.nasa.gov/echo/controlled-documents/echo-partner-guides-documents#echo-rest-search-guide (download the PDF)

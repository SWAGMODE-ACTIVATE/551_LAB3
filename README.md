# 551_LAB3

the permit searching website works by allowing users to query the city of Calgarys public data API to see building permits around the city that were issued between certain ranges of dates that are inputted by the user. the application first brings users to a main page showing an empty map, where they are promted to enter in a date range to query. after the application makes sure the dates are valid, it searches the API and displayed all of the matching data points on the map for the user to view. Points are clustered for readibility using the github library leaflet.markercluster and can be clicked on to see a popup with all the relevant information about that point.

Files-
/static/pagestyle.css - this is the css stylesheet for all of the template pages

/static/Leaflet.markercluster-1.4.1 - this is the github library i used to create the clusted map icons (https://github.com/Leaflet/Leaflet.markercluster)

/templates/index.html - this is the initial page you see. it just a simple empty map of calgary with the date -range search input at the bottom of the page. if you enter in a daterange thats invalid, you are redirected here along with an error message.

/templates/search.html - looks and functions pretty much identical to index.html but this is the map that is filled in with all of the matching building permits.

the templates for the search page as well as the book page have logout and return buttons at the top of the page.

.gitattributes - idk what this is but it looks important

application.py - this is the main flask applicatoin that makes the whole thing work. it has 2 functions, one for the main page and one for the searching function. this is where the maps are created and filled, and where the API is queried for informatoin.

readme.md- this file

requirements.txt - all packages needed to run both .py programs

ENGO 551 - Adv. Topics on Geospatial Technologies Nick Kennedy 30145355

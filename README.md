# CS50's Finance
![Screenshot](https://user-images.githubusercontent.com/69594457/95256563-e4755a00-081a-11eb-80e6-298d8e56abca.png)

## Introduction

This webapp was part of the web-track exercise of Harvard's CS50 course, which you can learn more about at [Harvard's CS50](https://online-learning.harvard.edu/course/cs50-introduction-computer-science)

In this website there were several main functions:
- Allow users to 'buy' and 'sell' stocks
- Allow users to register an account and password via a form
- Ensure password and username checks and general security
- Allow users to quote up a stock's current price, check history of transactions
  
In addition I added more functionality to allow the user to change their password.

## Technology used

This webapp uses Python3, and Flask framework. The HTML styling was done with Bootstrap. [IEX API](https://iexcloud.io/) is also used to get stock values in real time with an api call and SQLite3 has been used to control the SQL database to store user information.

## Run

You will need [Python](https://www.python.org/downloads/) and [Flask](https://flask.palletsprojects.com/en/1.1.x/installation/) installed on your computer to run this application.

Start by installing [Python 3](https://www.python.org/downloads/).

Once you have Python, and cloned this repository, you can run the following commands:

To install pip, run:

`sudo apt install python3-pip`

To install Flask, run:

`sudo apt install python3-flask`

To install this project's dependecies, run:

`pip3 install -r requirements.txt`

Define the correct file as the default Flask application:

Unix Bash (Linux, Mac, etc.):

`export FLASK_APP=application.py`

Windows CMD:

`set FLASK_APP=application.py`

Windows PowerShell:

`$env:FLASK_APP = "application.py"`

Run Flask and you're good to go!

`flask run`

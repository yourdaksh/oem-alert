
print("start")
import sys
print("sys imported")
import os
print("os imported")
try:
    import requests
    print("requests imported")
except ImportError:
    print("requests failed")

try:
    from bs4 import BeautifulSoup
    print("bs4 imported")
except ImportError:
    print("bs4 failed")

try:
    print("Importing selenium...")
    from selenium import webdriver
    print("selenium imported")
except ImportError:
    print("selenium failed")

print("done")

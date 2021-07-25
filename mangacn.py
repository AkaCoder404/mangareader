# selenium deps
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# manga.py deps
import requests
import cloudscraper
import json
import os
import time
import argparse
import csv
from tempfile import NamedTemporaryFile
import shutil

from PIL import Image
from fpdf import FPDF

import schedule


# options
chromeOptions = Options()
chromeOptions.headless = True
chromeOptions.binary_locations="/usr/bin/google-chrome"

browser = webdriver.Chrome(executable_path="drivers/chromedriver", options=chromeOptions)

def download_img(r, file_name):
  start_time = time.time()
  with open(file_name, "wb") as f:
     for chunk in r.iter_content(chunk_size=1024):
          if chunk:
              f.write(chunk)
  print("下载时间", file_name, time.time() - start_time)

def download_manga(manga_url, manga_name):
  session = requests.Session()
  page_num = 1
  url = manga_url
  
  while True:
    browser.get(url)
    chapter_title = browser.title
    print("标题: %s" % chapter_title)

    # find img link
    image = browser.find_elements_by_css_selector("img")
    page = image[0].get_attribute("src")
    print("本页", page)

    # find next page link
    link = browser.find_elements_by_css_selector("a")
    next_page = link[-1].get_attribute("href")
    print("下页", next_page)

    # make request and download page
    r = session.get(page, stream=True)

    # if chapter folder doesn't exists yet
    if os.path.exists("mangacn/" + manga_name + "/" + chapter_title + "/") == False:
      os.mkdir("mangacn/" + manga_name + "/" + chapter_title + "/")

    # download image
    download_img(r, "mangacn/" + manga_name + "/" + chapter_title + "/" + str(page_num) + ".jpg")
    # go to next page
    page_num = page_num + 1
    url = next_page

    if url == "http://comic.ikkdm.com/exit/exit.htm":
      print("chapter finished")
      page_num = 0
      break

def manga_chapter_list(manga_url, manga_name):
  browser.get(manga_url)
  chapter_num = 1
  chapter_list = browser.find_elements_by_css_selector("dd")
  chapter_length = len(chapter_list)
  print(manga_name, "chapters", chapter_length)

  # if mangacn/manga_name doesn't exist
  if os.path.exists("mangacn/" + manga_name) == False:
    os.mkdir("mangacn/" + manga_name)

  # if csv doesn't exist for specific manga
  header = ["chapter_title", "chapter_link"]
  if os.path.exists("mangacn/" + manga_name + "/chapters.csv") == False:
    with open("mangacn/" + manga_name + "/chapters.csv", "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(header)

  with open("mangacn/" + manga_name + "/chapters.csv") as f:
    row_count = sum(1 for line in f)

  print("entries", row_count - 1)

  if row_count - 1 == chapter_length: 
    print("no new entries")
  else:
    print(chapter_length - (row_count - 1), "new entries") 
     # store new chapter entries in csv
    with open("mangacn/" + manga_name + "/chapters.csv", "a") as f:
      writer = csv.writer(f)
      for chapter in chapter_list[row_count - 1:]:
        chapter_link = chapter.find_elements_by_css_selector("a")[0].get_attribute("href")
        row = [chapter_num,chapter_link]
        writer.writerow(row)
        chapter_num = chapter_num + 1
      
  # iterate chapters one by one

  # start from latest downloaded
  latest_chapter_read = 0
  with open("mangacn/mangas.csv", "r", newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for read in reader: 
      if read[0] == manga_name:
        latest_chapter_read = int(read[2])

  print("latest chapter read", latest_chapter_read)


  manga_header = ["title", "link", "latest_chapter"]
  with open("mangacn/" + manga_name + "/chapters.csv", "r") as f:
    reader = csv.reader(f, delimiter=",")
    # skip headers
    next(reader)
    for i in range(0,latest_chapter_read):
      next(reader)
    # start downloading from the latest downloaded manga + 1
    for row in reader:
      download_manga(row[1], manga_name)
      # write to temp file and copy over
      tempfile = NamedTemporaryFile(mode='w',newline='', delete=False)
      # when finished downloading, update latest read manga
      with open("mangacn/mangas.csv", "r", newline="") as csvfile, tempfile:
        reader_csv = csv.DictReader(csvfile, fieldnames=manga_header)
        writer_csv = csv.DictWriter(tempfile, fieldnames=manga_header)
        for row_csv in reader_csv:
          if row_csv["title"] == str(manga_name):
            print("updating anime.csv for", manga_name)
            row_csv["title"] = str(manga_name)
            row_csv["link"] = str(row_csv["link"])
            row_csv["latest_chapter"] = row[0]
          row_csv = {"title": row_csv["title"], "link": row_csv["link"], "latest_chapter": row_csv["latest_chapter"]}
          writer_csv.writerow(row_csv)
        shutil.move(tempfile.name, "mangacn/mangas.csv") 
        
def update(t):
  """check for new update every day at update_time"""
  print(t)
  main()
       
def main():
  # update_time = "13.11"
  # schedule.every().day.at(update_time).do(update, "it is " + update_time + "... time to update manga")

  # while True:
  #   schedule.run_pending()
  #   time.sleep(30)

  # one piece

  # read mangacn/mangas.csv for mangas
  manga_list = []
  with open("mangacn/mangas.csv", "r") as f:
    reader = csv.reader(f, delimiter=",") 
    for row in reader:
      if row[0] == "title":
        continue
      title = row[0]
      link = row[1]
      latest_chapter = row[2]
      manga = {"title": title, "link" : link, "latest_chapter": latest_chapter}
      manga_list.append(manga)

  for manga in manga_list:
    manga_chapter_list(manga["link"], manga["title"])
    

  # base_url = "http://comic.ikkdm.com/comiclist/4/"
  # manga_name = ""
  # chapter_url = "http://comic.ikkdm.com/comiclist/4/90750/1.htm"
  # manga_chapter_list(base_url, manga_name)
  
if __name__ == "__main__":
  print("自动下载漫画")
  main()
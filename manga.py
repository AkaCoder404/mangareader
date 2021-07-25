# manga scrape on mangareader.site
# https://mangareader.site/

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

parser = argparse.ArgumentParser()
parser.add_argument("--anime", help="input anime link to update")
parser.add_argument("--delete", help="delete anime")
args = parser.parse_args()

# current directory
curr_dir = os.getcwd()

# print(args.anime)
# https://img.mghubcdn.com/file/imghub/boku-no-hero-academia/0/1.jpg

reading_list = ["chicha-koi-nikki","horimiya"]
url = "https://img.mghubcdn.com/file/imghub/"

def stich(sdir, name, chapter, page):
  pdf = FPDF()
  sdir = sdir
  # standard a4 paper
  w = 210 
  h = 297

  for i in range(1, page):
    fname = sdir + "%d.jpg" % i
    if os.path.exists(fname):
      if i == 1:
        # cover = Image.open(fname)
        # w,h = cover.size
        # w = 210
        # h = 297
        pdf = FPDF(unit = "pt", format = [w,h])
      image = fname 
      pdf.add_page()
      try:
        pdf.image(image, 0, 0, w, h)
      except:
        continue
    else: 
      print("file not found: ", fname)
    # print("processed %d" % i)

  # if mangas_pdf/manga path doesn't 
  if os.path.exists("mangas_pdf/" + name) == False:
    os.mkdir("mangas_pdf/" + name)

  pdf.output("mangas_pdf/" + name + "/" + "chapter " + chapter + ".pdf", "F")
  print("done stiching for chapter")

def download_img(r, file_name):
  start_time = time.time()
  with open(file_name, "wb") as f:
      for chunk in r.iter_content(chunk_size=1024):
          if chunk:
              f.write(chunk)
  print(file_name, time.time() - start_time)
  
def download_manga(manga, manga_url, start_ch, end_ch):
  # open session so we don't have to restablish connection each time
  session = requests.Session()
  chapter = start_ch
  max_chapter = end_ch
  page = 1

  
  header = ["anime", "chapter"]
  # make csv if doesn't exists
  if os.path.exists('anime.csv') == False:
    with open('anime.csv', 'w', newline="") as f:
      writer = csv.writer(f)
      writer.writerow(header)

  # track download of latest chapter
  with open("anime.csv", "r") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
      if row[0] == manga:
        chapter = int(row[1]) + 1 # continue download from next chapter
  
  while True: 
    # if already downloaded chapter
    if chapter > max_chapter: 
      chapter = chapter - 1
      break
    url =  manga_url + str(chapter) + "/" + str(page) + ".jpg"

    with session.get(url, stream=True) as r:
      # end of chapter
      if r.status_code == 404:
        print("end of chapter", chapter)
        # stich the jpgs to make pdf, stich it into mangas_pdf
        stich("mangas/" + manga + "/chapter " + str(chapter) + "/", manga, str(chapter), page)
        # go to next chapter and reset page
        chapter = chapter + 1
        page = 1
        continue
      
      # create folder
      if os.path.exists("mangas/" + manga + "/chapter " + str(chapter)) == False:
        if os.path.exists("mangas/" + manga) == False:
          os.mkdir("mangas/" + manga)
        os.mkdir("mangas/" + manga + "/chapter " + str(chapter))

      # write to jpg
      download_img(r, "mangas/" + manga + "/chapter " + str(chapter) + "/" + str(page) + ".jpg")   
    # next page
    page = page + 1

  # find and update csv based on download
  read = -1 # check if anime is already read
  with open('anime.csv', 'r', newline='') as f:
    reader = csv.reader(f, delimiter=',')
    count = 0
    for row in reader:
      # print(row)
      try: 
        if row[0] == manga:
          # print("row changed", row[0])
          read = count
          break
      except:
        print("error")
        break
      count = count + 1

  # write to temp file and copy over
  tempfile = NamedTemporaryFile(mode='w',newline='', delete=False)

  if read == -1:
    with open('anime.csv', 'a+', newline='') as f:
      writer = csv.writer(f)
      writer.writerow([manga, chapter])
  else: 
    with open('anime.csv', 'r', newline='') as csvfile, tempfile:
      reader = csv.DictReader(csvfile, fieldnames=header)
      writer = csv.DictWriter(tempfile, fieldnames=header)
      # writer.writerow(header)
      for row in reader:
        if row["anime"] == str(manga):
          print("updating anime.csv for", row['anime'])
          row["anime"], row["chapter"] = manga, chapter
        row = {"anime" : row["anime"], "chapter" : row["chapter"]}
        writer.writerow(row)
    shutil.move(tempfile.name, "anime.csv")


def update(t):
  """check for new update every day at update_time"""
  print(t)
  for entry in reading_list:
    print("sync", entry)
    manga_url = url + entry + "/"

    # if new anime and not in anime.csv
    is_exists = False
    with open("anime.csv", "r") as f:
      reader = csv.reader(f, delimiter=",")
      for row in reader:
        if row[0] == entry:
          is_exists = True
          break

    # append to csv
    if is_exists == False:
      with open("anime.csv", "a") as f:
        writer = csv.writer(f)
        # row = {"anime" : entry, "chapter" : "0"}
        row = [entry, "1"]
        writer.writerow(row)

    # while still more chapters 
    is_more_chapters = True
    while(is_more_chapters):
      # retrieve latest chapter in anime.csv
      next_chapter = 0
      next_page = 1
      with open("anime.csv", "r") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
          if row[0] == entry:
            next_chapter = int(row[1]) + 1 # continue download from next chapter

      print("next chapter ", next_chapter)
      # request next chapter, if 404, exit, if success, download new chapter and update csv
      with requests.get(manga_url + str(next_chapter) + "/" + str(next_page) + ".jpg", stream=True) as r:
        if r.status_code == 404:
          is_more_chapters = False
          print("no new chapter for", entry)
          break
        else: 
          print("new chapter", next_chapter)
          # mangadownload for next chapter
          # track time it takes to complete 
          start_time = time.time()
          download_manga(manga=entry, manga_url=manga_url, start_ch=1, end_ch=next_chapter)
          time.sleep(5)
          end_time = time.time()
          print("sync execution time", end_time - start_time)
  print("done updating for the day")


def main():
  update_time = "13:11"
  schedule.every().day.at(update_time).do(update, "it is " + update_time + "... time to update manga")

  while True:
    schedule.run_pending()
    time.sleep(30)

  # start_time = time.time()

  # # cycle through the reading list
  # # for entry in readinglist:
  # manga = reading_list[0] 
  # manga_url = url + manga + "/"
  # print("sync manga", manga)

  # download_manga(manga=manga, manga_url=manga_url, start_ch=1, end_ch=1)
  # end_time = time.time()
  # print("total execution time", end_time - start_time)

if __name__ == "__main__":
  main()

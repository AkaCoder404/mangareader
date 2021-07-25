# Manga Reading Scripts

This is a collection of manga reading scripts that allow you to download mangas from various manga reading websites. 

## manga.py

The first manga source uses mangareader.site. This site has wide selection of manga, and popular ones should be up to date. This source was easier to parse due to the way the images are stored


In order to add manga, simply add it to the 

'''
reading_list = []
'''

line and run the code. However, the names have to be exactly as the ones on mangareader.site， with "-" replaces spaces. For example, one piece would be placed as 

'''
reading_list = ['one-piece']
'''

then run 'python manga.py', and the images will be stored under manga and split into chapters. There is also mangapdf folder which stiches the images of each chapter together to create one pdf for each chapter.

The code was designed to run once a day at a specific 'update_time', checking for new chapters once a day'

## mangacn.py 

If you want to read chinese manga, use mangacn.py. The way the website stored the images made it so there was no way to easily iterate as done in manga.py, so selenium was used to parse for the image and the next image. Repeating until there were no more images for the chapter.

If you want to add a manga, add it to mangacn/mangas.csv, for example, for one piece, we do, 

title,link,latest_chapter
海贼王,http://comic.ikkdm.com/comiclist/4/,0

However, the link must contain the chapter list in order for it to work. Click the link to see what the chapter link's may look like.

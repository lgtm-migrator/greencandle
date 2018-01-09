#!/usr/bin/env python

import time
from selenium import webdriver
from pyvirtualdisplay import Display
import plotly.offline as py
import plotly.graph_objs as go


from PIL import Image
from resizeimage import resizeimage

def get_screenshot(filename=None):
    display = Display(visible=0, size=(640, 480))
    display.start()

    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)  # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', '/tmp')
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'image/png')

    driver = webdriver.Firefox(firefox_profile=profile)
    driver.get("file://{0}.html".format(filename))
    #driver.get("file:////home/temp-plot.html")
    #export_button = driver.find_element_by_xpath("//a[@data-title='Download plot as a png']")
    #export_button.click()
    driver.save_screenshot('{0}.png'.format(filename))
    time.sleep(10)
    driver.quit()
    display.stop()

def resize_screenshot(filename=None):
    with open('{0}.png'.format(filename), 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_width(image, 100)
            cover.save('{0}_resized.png'.format(filename), image.format)

def create_graph(df, pair):
    py.init_notebook_mode()
    trace = go.Candlestick(x=df.index,
                           open=df.open,
                           high=df.high,
                           low=df.low,
                           close=df.close)
    filename = "simple_candlestick_{0}".format(pair)
    py.plot([trace], filename='{}.html'.format(filename), auto_open=False)
    get_screenshot(filename)
    resize_screenshot(filename)

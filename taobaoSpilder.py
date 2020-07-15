from pyquery import PyQuery as pq
import pymongo
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, MoveTargetOutOfBoundsException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import quote
import time
import random

# 搜索关键字
keyword = 'ipad'
options = webdriver.ChromeOptions()
# 设置成开发者模式
options.add_experimental_option('excludeSwitches', ['enable-automation'])
# 账户密码
USERNAME = ''
PASSWORD = ''
# 禁用图片跟css样式
prefs = {"profile.managed_default_content_settings.images": 2,
         'permissions.default.stylesheet': 2}
options.add_experimental_option("prefs", prefs)
browser = webdriver.Chrome(options=options)


def login():
    '''通过账号模拟登陆'''
    url = 'https://s.taobao.com/search?q=' + quote(keyword)
    browser.get(url)
    time.sleep(random.uniform(1, 3))
    # 显示等待，并设置10S超时
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, '//input[@name="fm-login-id"]')))
    browser.find_element_by_xpath(
        '//input[@name="fm-login-id"]').send_keys(USERNAME)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, '//input[@name="fm-login-password"]')))
    browser.find_element_by_xpath(
        '//input[@name="fm-login-password"]').send_keys(PASSWORD)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//button[contains(@class,'password-login')]")))
    browser.find_element_by_xpath(
        "//button[contains(@class,'password-login')]").click()

    dragger = browser.find_element_by_id('nc_1_n1z')
    # 设置行为，模拟滑动窗口，将滑块滑至最右端，并捕获异常后：跳出循环
    action = ActionChains(browser)
    for _ in range(500):
        try:
            action.drag_and_drop_by_offset(dragger, 258, 0).perform()
        except MoveTargetOutOfBoundsException:
            break
        time.sleep(1)
    browser.find_element_by_xpath(
        "//button[contains(@class,'password-login')]").click()


def index_page(page):
    '''
    抓取页面
    '''
    print('正在爬取第', page, '页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(keyword)
        browser.get(url)
        time.sleep(random.uniform(1, 3))
        wait = WebDriverWait(browser, 10)
        # 当页面大于1时，进行页面跳转，跳转至page页
        if page > 1:
            input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#mainsrp-pager div.form> input')))
            submit = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#mainsrp-pager div.form> span.btn.J_Submit')))
            input.clear()
            input.send_keys(page)
            submit.click()
        # 加载到第N页时，页码显示激活状态，则成功跳转
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager li.item.active> span'), str(page)))
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.m-itemlist .items .item')))
        # 获取商品信息
        getproducts()
    except TimeoutException:
        print('TimeOut')


MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_COLLECTion = 'products'
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def save_to_mongo(product):
    '''
    将数据保存到Mongo
    '''
    try:
        if db[MONGO_COLLECTion].insert(product):
            print('成功存储到mongo')
    except Exception:
        print('保存失败')


def getproducts():
    '''
    提取商品信息
    '''
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('data-src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.locaiton').text()
        }
        print(product)
        save_to_mongo(product)


MAX_PAGE = 100


def main():
    '''遍历每一页'''
    for i in range(1, MAX_PAGE):
        index_page(i)


if __name__ == "__main__":
    login()
    main()

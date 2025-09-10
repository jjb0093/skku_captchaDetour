import shutil, random
from time import sleep

import cv2
import numpy as np
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://2captcha.com/demo/geetest-v4")

class GeeTestSolver_Slider:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    def exists(self):
        self.driver.switch_to.default_content()
        try:
            captcha = self.driver.find_element(By.CSS_SELECTOR, "div.geetest_box")
            style = captcha.get_attribute('style')

            if "display: none" in style:
                return False
            elif "display: block" in style:
                return True
            
        except NoSuchElementException:
            return False
        
    def download_images(self, url, name = 'slider'):
        response = requests.get(url, stream = True)
        with open(f"imgFiles/geeTest/{name}.png", 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        del response
        print("이미지 다운로드 완료")

    def compter(self):
        background = cv2.imread("imgFiles/geeTest/slider_background.png", 1)
        morceau = cv2.imread("imgFiles/geeTest/slider_morceau.png", 1)
        morceau = cv2.convertScaleAbs(morceau, alpha = 1.0, beta = -50)
        #morceau = 255 - morceau

        #cv2.imwrite("imgFiles/geeTest/slider_background_gray.png", background)
        cv2.imwrite("imgFiles/geeTest/slider_morceau_modified.png", morceau)

        result = cv2.matchTemplate(background, morceau, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        x = max_loc[0]

        return (x * (220 / background.shape[1]))

    def solver(self):
        print("geeTest 슬라이더형 해결 시작")
        action = ActionChains(self.driver)
        
        sleep(5)
        btn1 = WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "geetest_btn_click"))
        )
        btn1.click()
        sleep(5)

        while self.exists():
            print("캡챠 해결 시작")

            slider = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "geetest_btn")))
            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "geetest_refresh")))
            
            img_background = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "geetest_bg")))
            style = img_background.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            self.download_images(url, name = "slider_background")

            img_morceau = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "geetest_slice_bg")))
            style = img_morceau.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            self.download_images(url, name = "slider_morceau")

            result = self.compter()
            if(result > 220) or (result < 0): continue
            print(f"옮겨야 하는 정도 : {result} / 220")

            action.click_and_hold(slider).perform()
            while True:
                combien = random.randrange(1, 6) * 10
                if(result - combien <= 0):
                    action.move_by_offset(result, 0).perform()
                    break
                else:
                    action.move_by_offset(combien, 0).perform()
                    result -= combien
                sleep(random.uniform(0.1, 0.3))
            action.release().perform()

        print("캡챠 해결")

solver = GeeTestSolver_Slider(driver)
solver.solver()
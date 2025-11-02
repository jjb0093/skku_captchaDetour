import shutil, random
from time import sleep

import cv2
import numpy as np
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

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
        background_gray = cv2.imread("imgFiles/geeTest/slider_background.png", 0)
        background_edge = cv2.Canny(background_gray, 50, 150)

        #cv2.imwrite("imgFiles/geeTest/slider_background_edge.png", background_edge)

        morceau = cv2.imread("imgFiles/geeTest/slider_morceau.png", cv2.IMREAD_UNCHANGED)
        morceau_gray = cv2.imread("imgFiles/geeTest/slider_morceau.png", 0)

        alpha = morceau[:, :, 3]
        h, w = alpha.shape

        for i in range(h):
            for k in range(w):
                if(alpha[i][k] != 255):
                    morceau[i, k, 3] = 0
                    alpha[i, k] = 0

        x_bound, y_bound, w, h = cv2.boundingRect(alpha)
        #alpha_coupe = alpha[y_bound:y_bound+h, x_bound:x_bound+w]
        morceau_gray_coupe = morceau_gray[y_bound:y_bound+h, x_bound:x_bound+w]

        kernel = np.ones((3, 3), np.uint8)
        morceau_edge = cv2.Canny(morceau_gray_coupe, 50, 150)
        morceau_edge = cv2.dilate(morceau_edge, kernel, iterations = 1)
        morceau_mask = (morceau_edge > 0).astype(np.uint8) * 255

        #cv2.imwrite("imgFiles/geeTest/slider_morceau_edge.png", morceau_edge)

        '''
        methods = [
            {'name': 'TM_SQDIFF', 'method': cv2.TM_SQDIFF, 'loc': 'min'},
            {'name': 'TM_SQDIFF_NORMED', 'method': cv2.TM_SQDIFF_NORMED, 'loc': 'min'},
            {'name': 'TM_CCORR', 'method': cv2.TM_CCORR, 'loc': 'max'},
            {'name': 'TM_CCORR_NORMED', 'method': cv2.TM_CCORR_NORMED, 'loc': 'max'},
            {'name': 'TM_CCOEFF', 'method': cv2.TM_CCOEFF, 'loc': 'max'},
            {'name': 'TM_CCOEFF_NORMED', 'method': cv2.TM_CCOEFF_NORMED, 'loc': 'max'}
        ]

        for i in range(len(methods)):
            result = cv2.matchTemplate(background_edge, morceau_edge, methods[i]['method'], mask = morceau_mask)

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if(methods[i]['loc'] == 'max'):
                x, y = max_loc
            elif(methods[i]['loc'] == 'min'):
                x, y = min_loc

            background_copy = background_gray.copy()
            for j in range(morceau_gray_coupe.shape[0]):
                for k in range(morceau_gray_coupe.shape[1]):
                    background_copy[j + y, k + x] = morceau_gray_coupe[j, k]

            cv2.imwrite(f"imgFiles/geeTest/background_{methods[i]['name']}.png", background_copy)
        '''

        result = cv2.matchTemplate(background_edge, morceau_edge, cv2.TM_CCORR, mask = morceau_mask)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        x, y = max_loc

        for i in range(morceau_gray_coupe.shape[0]):
            for k in range(morceau_gray_coupe.shape[1]):
                background_gray[i + y, k + x] = morceau_gray_coupe[i, k]

        cv2.imwrite("imgFiles/geeTest/slider_background_fin.png", background_gray)

        return (x - x_bound)

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

            sleep(5)

            slider = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_btn")))
            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_refresh")))
            
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
            print(f"옮겨야 하는 정도 : {result} / 220")
            if(result > 220) or (result < 0):
                reload.click()
                continue

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

if __name__ == "__main__":
    driver = webdriver.Chrome()
    driver.get("https://2captcha.com/demo/geetest-v4")

    solver = GeeTestSolver_Slider(driver)
    solver.solver()

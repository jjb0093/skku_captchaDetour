import shutil, random, time

import cv2
import numpy as np
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

class GeeTestSlideSolver:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    def exists(self):
        try:
            captcha = self.driver.find_element(By.CSS_SELECTOR, "div.geetest_box_wrap")
            style = captcha.get_attribute('style')

            if "display: none" in style:
                return False
            elif "display: block" in style:
                return True
            
        except NoSuchElementException:
            return False
    
    def downloadImage(self, url, name):
        response = requests.get(url, stream = True)

        with open(f"images/geeTestSlide_{name}", 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        del response

    def compter(self):
        backgroundGray = cv2.imread("images/geeTestSlide_background.jpg", 0)
        backgroundEdge = cv2.Canny(backgroundGray, 50, 150)

        cv2.imwrite("images/geeTestSlide_backgroundEdge.jpg", backgroundEdge)

        morceau = cv2.imread("images/geeTestSlide_morceau.png", cv2.IMREAD_UNCHANGED)
        morceauGray = cv2.imread("images/geeTestSlide_morceau.png", 0)
        
        
        alpha = morceau[:, :, 3]
        h, w = alpha.shape

        for i in range(h):
            for k in range(w):
                if(alpha[i][k] != 255):
                    morceau[i, k, 3] = 0
                    alpha[i, k] = 0

        xBound, yBound, w, h = cv2.boundingRect(alpha)
        morceauGrayCoupe = morceauGray[yBound : yBound + h, xBound : xBound + w]

        kernel = np.ones((3, 3), np.uint8)
        morceauEdge = cv2.Canny(morceauGrayCoupe, 50, 150)
        morceauEdge = cv2.dilate(morceauEdge, kernel, iterations = 1)
        morceauMask = (morceauEdge > 0).astype(np.uint8) * 255

        cv2.imwrite("images/geeTestSlide_morceauEdge.png", morceauEdge)

        result = cv2.matchTemplate(backgroundEdge, morceauEdge, cv2.TM_CCORR, mask = morceauMask)

        _, _, _, maxLoc = cv2.minMaxLoc(result)
        x, y = maxLoc

        for i in range(morceauGrayCoupe.shape[0]):
            for k in range(morceauGrayCoupe.shape[1]):
                backgroundGray[i + y, k + x] = morceauGrayCoupe[i, k]

        return (x - xBound)
    
    def solver(self):
        action = ActionChains(self.driver)

        WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "geetest_btn_click"))
        ).click()


        time.sleep(1)
        while self.exists():
            slider = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "geetest_btn")))
            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_refresh")))
            
            imgBackground = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "geetest_bg")))
            style = imgBackground.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            self.downloadImage(url, "background.jpg")

            imgMorceau = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "geetest_slice_bg")))
            style = imgMorceau.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            self.downloadImage(url, "morceau.png")

            result = self.compter()

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
                time.sleep(random.uniform(0.1, 0.3))
            action.release().perform()

            time.sleep(1)
            tip = self.driver.find_element(By.CLASS_NAME, "geetest_tip")

            if "Verification Success" in tip.text:
                return True
            else:
                continue

if(__name__ == "__main__"):
    from seleniumwire import webdriver
    driver = webdriver.Chrome()
    solver = GeeTestSlideSolver(driver)

    driver.get("https://gt4.geetest.com/demov4/slide-float-en.html")
    print(solver.solver())
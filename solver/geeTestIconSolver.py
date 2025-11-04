import shutil, time, requests, base64

import cv2
import numpy as np

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options

import torch
from PIL import Image

from openai import OpenAI

class GeeTestIconSolver:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10
        self.client = OpenAI(api_key  = "#")

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

        with open(f"images/geeTestIcon_{name}", 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        del response

    def modifierIcons(self, num):
        img = cv2.imread(f"images/geeTestIcon_icon{num}.png", cv2.IMREAD_UNCHANGED)
        canny = cv2.Canny(img, 100, 200)

        #kernel = np.ones((2, 2), np.uint8)
        #canny = cv2.dilate(canny, kernel, iterations = 1)

        cv2.imwrite(f"images/geeTestIcon_icon{num}.png", canny)

    def modifierImage(self):
        img = cv2.imread("images/geeTestIcon_background.jpg")
        height, width = img.shape[:2]

        imgCopy = img.copy()

        step = 50
        for h in range(0, height + step, step):
            cv2.line(imgCopy, (0, h), (width, h), (0, 255, 0), 1)

        for w in range(0, width + step, step):
            cv2.line(imgCopy, (w, 0), (w, height), (0, 255, 0), 1)

        cellNum = 1
        for i in range(height // 50):
            for k in range(width // 50):
                (text_w, text_h), _ = cv2.getTextSize(str(cellNum), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                cv2.putText(
                    imgCopy, str(cellNum), (k * 50 + ((50 - text_w) // 2), i * 50 + ((50 + text_h) // 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA
                )

                cellNum += 1

        cv2.imwrite("images/geeTestIcon_backgroundGrid.jpg", imgCopy)

    def demanderExplanation(self, num):
        with open(f"images/geeTestIcon_icon{num}.png", 'rb') as f:
            img = base64.b64encode(f.read()).decode('utf-8')

        question = """
            Describe the icon in detail in three sentences. Focus on how the overall outline flows and connects, capturing the general shape and movement of its form, without mentioning internal elements or color.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                ]}
            ]
        )

        return response.choices[0].message.content

    def demanderResponse(self, explain):
        with open(f"images/geeTestIcon_backgroundGrid.jpg", 'rb') as f:
            img = base64.b64encode(f.read()).decode('utf-8')

        question = f"""
            This is an explanation of a specific icon : {explain}. Find it and return the number of the grid that contains that icon. 
            If multiple grids contain the icon, return only one that contains the center of the icon.
            Ensure that the result is only the number, with no extra text or formatting.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                ]}
            ]
        )

        return response.choices[0].message.content
    
    def demanderVerification(self, num, explain):
        img = cv2.imread(f"images/geeTestIcon_background.jpg")

        x_initial, y_initial = (((num - 1) % 6)) * 50 + 25, (((num - 1) // 6)) * 50 + 25
        if((x_initial - 75) < 0): x_range = [0, 150]
        elif((x_initial + 75) > 300): x_range = [150, 300]
        else: x_range = [x_initial - 75, x_initial + 75]

        if((y_initial - 75) < 0): y_range = [0, 150]
        elif((y_initial + 75) > 200): y_range = [50, 200]
        else: y_range = [y_initial - 75, y_initial + 75]

        imgCrop = img[y_range[0] : y_range[1], x_range[0] : x_range[1]]

        height, width = imgCrop.shape[:2]
        imgCopy = imgCrop.copy()

        step = 30
        for h in range(0, height + step, step):
            cv2.line(imgCopy, (0, h), (width, h), (0, 255, 0), 1)

        for w in range(0, width + step, step):
            cv2.line(imgCopy, (w, 0), (w, height), (0, 255, 0), 1)

        cellNum = 1
        for i in range(height // step):
            for k in range(width // step):
                cx, cy = k * step + (step / 2), i * step + (step / 2)
                bgColor = imgCrop[int(cy), int(cx)]
                b, g, r = [x / 255.0 for x in bgColor]

                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                if(lum < 0.5):
                    text_color = (255, 255, 255)
                else:
                    text_color = (0, 0, 0)

                (text_w, text_h), _ = cv2.getTextSize(str(cellNum), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.putText(
                    imgCopy, str(cellNum), (k * step + ((step - text_w) // 2), i * step + ((step + text_h) // 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1, cv2.LINE_AA
                )

                cellNum += 1

        cv2.imwrite(f"images/geeTestIcon_backgroundGrids.jpg", imgCopy)

        with open(f"images/geeTestIcon_backgroundGrids.jpg", 'rb') as f:
            img = base64.b64encode(f.read()).decode('utf-8')

        question = f"""
            This is an explanation of a specific icon : {explain}. Find it and return the number of the grid that contains that icon. 
            If multiple grids contain the icon, return only one that contains the center of the icon.
            Ensure that the result is only the number, with no extra text or formatting.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                ]}
            ]
        )

        grid = int(response.choices[0].message.content)
        x, y = (x_range[0] + step * ((grid - 1) % 5) + 15), (y_range[0] + step * ((grid - 1) // 5) + 15)

        return grid, x, y

    def solver(self):
        action = ActionChains(self.driver)

        WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "geetest_btn_click"))
        ).click()
        time.sleep(1)
        
        urlBefore = None
        while self.exists():
            '''
            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_refresh")))
            '''

            background = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_bg"))
            )
            style = background.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            if(urlBefore != None) and (urlBefore == url):
                continue

            urlBefore = url
            self.downloadImage(url, "background.jpg")
            self.modifierImage()

            icon = self.driver.find_element(By.CLASS_NAME, "geetest_ques_tips")
            imgs = icon.find_elements(By.TAG_NAME, "img")

            for i in range(len(imgs)):
                url = imgs[i].get_attribute("src")
                self.downloadImage(url, f"icon{i}.png")
                self.modifierIcons(i)

            result = []
            for i in range(len(imgs)):
                explain = self.demanderExplanation(i)
                grid = self.demanderResponse(explain)
                num, x, y = self.demanderVerification(int(grid), explain)
                print(i, x, y)
                result.append([x, y])

            for x_offset, y_offset in result:
                self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                var evt = new MouseEvent('click', {
                    clientX: rect.left + arguments[1],
                    clientY: rect.top + arguments[2],
                    bubbles: true,
                    cancelable: true
                });
                arguments[0].dispatchEvent(evt);
                """, background, x_offset, y_offset)
                time.sleep(1)

            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_submit"))
            ).click()
            time.sleep(1)

            tip = self.driver.find_element(By.CLASS_NAME, "geetest_tip")
            if "Verification Success" in tip.text:
                return True
            else:
                time.sleep(1)
                continue
            
if(__name__ == "__main__"):
    driver = webdriver.Chrome()

    driver.get("https://gt4.geetest.com/demov4/icon-popup-en.html")

    solver = GeeTestIconSolver(driver)
    solver.solver()

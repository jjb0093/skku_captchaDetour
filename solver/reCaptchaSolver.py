import re, shutil, random, os, time

import cv2
import numpy as np
import requests
from PIL import Image
from ultralytics import YOLO

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

class ReCaptchaSolver:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    def iframe(self, idx):
        self.driver.switch_to.default_content()
        if(idx == 1):
            iframe = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
        elif(idx == 2):
            iframe = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='bframe']"))
            )
        self.driver.switch_to.frame(iframe)

    def getTarget(self, titleWrapper):
        targetMap = {
            "bicycle": 1, "자전거": 1,
            "car": 2, "자동차": 2,
            "motorcycle": 3, "오토바이": 3,
            "bus": 5, "버스": 5,
            "boat": 8, "보트": 8,
            "traffic": 9, "신호등": 9,
            "hydrant": 10, "소화전": 10
        }

        target = WebDriverWait(titleWrapper, self.timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "strong"))
        )

        for key, value in targetMap.items():
            if(target.text in key): return value
        return -1
    
    def delay(self, mean, variance):
        maxTime = np.random.normal(mean, variance)
        delay = max(0.25, maxTime)
        time.sleep(delay)

    def getImgUrl(self):
        images = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@id='rc-imageselect-target']//img"))
        )

        url = []
        for img in images:
            src = img.get_attribute("src")
            url.append(src)

        return url

    def downloadImage(self, name, url):
        response = requests.get(url, stream = True)

        with open(f"images/{name}.jpg", 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        del response
    
    def solver_9(self, target, model):
        image = Image.open("images/tile_0.jpg")
        image = np.asarray(image)

        result = model.predict(image, task = "detect")
        cls, boxes = result[0].boxes.cls, result[0].boxes.data

        targetIndex, count = [], 0
        for num in cls:
            if num == target:
                targetIndex.append(count)
            count += 1

        answer = set()
        for i in targetIndex:
            targetBox = boxes[i]
            x1, y1, x2, y2 = map(int, targetBox[:4])
            xc = (x1 + x2) // 2
            yc = (y1 + y2) // 2

            h, w, _ = image.shape
            row = yc * 3 // h
            col = xc * 3 // w

            answer.add(int(row * 3 + col + 1))

        return list(answer)
    
    def solver_16(self, target, model):
        image = Image.open("images/tile_0.jpg")
        width = image.size[0]
        image = np.asarray(image)

        result = model.predict(source = image, task = "detect")
        cls, boxes = result[0].boxes.cls, result[0].boxes.data

        targetIndex, count = [], 0
        for num in cls:
            if num == target:
                targetIndex.append(count)
            count += 1

        answer = set()
        for i in targetIndex:
            targetBox = boxes[i]
            x1, y1, x4, y4 = map(int, targetBox[:4])
            x2, y2 = x4, y1
            x3, y3 = x1, y4
            xys = [x1, y1, x2, y2, x3, y3, x4, y4]

            for j in range(4):
                x = xys[j * 2]
                y = xys[j * 2 + 1]

                frontiere = np.linspace(0, width, 5)
                rows, cols = [], []
                for k in range(4):
                    for m in range(4):
                        if(frontiere[k] <= x < frontiere[k + 1]) and (frontiere[m] <= y < frontiere[m + 1]):
                            rows.append(m)
                            cols.append(k)

                for r in range(min(rows), max(rows) + 1):
                    for c in range(min(cols), max(cols) + 1):
                        answer.add(4 * r + c + 1)

        return sorted(list(answer))
    
    def exists(self):
        self.driver.switch_to.default_content()
        try:
            captcha = self.driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
            if(captcha.is_displayed()):
                self.iframe(1)

                checkBox = self.driver.find_element(By.ID, "recaptcha-anchor")
                if(checkBox.get_attribute("aria-checked") == "true"):
                    return False
                else: 
                    self.driver.switch_to.default_content()
                    return True
            
        except NoSuchElementException:
            return False
            
    def solver(self):
        self.iframe(1)
        WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='recaptcha-checkbox-border']"))
        ).click()

        baseDir = os.path.dirname(os.path.abspath(__file__))
        model = YOLO(f"{baseDir}/reCAPTCHAModel.onnx", task = "detect")

        while True:
            time.sleep(2)
            if(not self.exists()):
                return True
            self.iframe(2)

            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, 'recaptcha-reload-button'))
            )
            titleWrapper = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, 'rc-imageselect'))
            )

            target = self.getTarget(titleWrapper)
            if(target == -1):
                reload.click()
                continue
            
            if(titleWrapper.find_elements(By.CSS_SELECTOR, ".rc-imageselect-table-33")):
                count = 0
                while True:
                    if(not count):
                        imgUrl = self.getImgUrl()
                        baseUrl = imgUrl[0]
                        self.downloadImage("tile_0", imgUrl[0])
                    else:
                        time.sleep(3)
                        imgUrl = self.getImgUrl()

                        if(imgUrl[answer[0] - 1] == baseUrl) or (len(answer) == 0):
                            break
                        else:
                            image = np.array(Image.open("images/tile_0.jpg"))

                            for i in range(len(answer)):
                                self.downloadImage(f"tile_{answer[i]}", imgUrl[answer[i] - 1])

                                newImage = np.array(Image.open(f"images/tile_{answer[i]}.jpg"))
                                newImage = cv2.cvtColor(newImage, cv2.COLOR_RGB2BGR)
                                row, col = (answer[i] - 1) // 3, (answer[i] - 1) % 3

                                startRow, endRow = row * 100, (row + 1) * 100
                                startCol, endCol = col * 100, (col + 1) * 100

                                if(newImage.shape[0] == image.shape[0]):
                                    continue

                                image[startRow : endRow, startCol : endCol] = newImage
                                cv2.imwrite(f"images/tile_0.jpg", image)

                    answer = self.solver_9(target, model)
                    random.shuffle(answer)

                    if(len(answer) < 1):
                        if(not count):
                            reload.click()
                        break

                    baseUrl = imgUrl[answer[0] - 1]

                    WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((By.XPATH, '(//div[@id="rc-imageselect-target"]//td)[1]'))
                    )

                    for ans in answer:
                        WebDriverWait(self.driver, self.timeout).until(
                            EC.element_to_be_clickable((By.XPATH, f'(//div[@id="rc-imageselect-target"]//td)[{ans}]'))
                        ).click()
                        self.delay(2, 1)

                    count += 1

            elif(titleWrapper.find_elements(By.CSS_SELECTOR, ".rc-imageselect-table-44")):
                reload.click()
                continue
                imgUrl = self.getImgUrl()
                self.downloadImage("tile_0", imgUrl[0])

                answer = self.solver_16(target, model)
                random.shuffle(answer)

                if(len(answer) < 1):
                    reload.click()
                    continue

                WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, '(//div[@id="rc-imageselect-target"]//td)[1]'))
                )

                for ans in answer:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((By.XPATH, f'(//div[@id="rc-imageselect-target"]//td)[{ans}]'))
                    ).click()
                    self.delay(2, 1)

            verifyBtn = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
            )
            verifyBtn.click()

            polite = self.driver.find_element(By.CLASS_NAME, "rc-imageselect-error-select-more")
            if(not "display: none;" in polite.get_attribute("style")):
                reload.click()
                continue

            if(self.exists()):
                continue
            else:
                return True
            
if(__name__ == "__main__"):
    from seleniumwire import webdriver
    driver = webdriver.Chrome()
    solver = ReCaptchaSolver(driver)

    driver.get("https://2captcha.com/demo/recaptcha-v2")
    print(solver.solver())
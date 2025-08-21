import re, os, shutil, random
from time import sleep

import cv2
import numpy as np
import requests
from PIL import Image
from ultralytics import YOLO

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

class ImageRecaptchaSolver:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    def iframe(self, idx):
        self.driver.switch_to.default_content()
        if idx == 1:    # I'm not a robot 써 있는 iframe 탐색
            iframe1 = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@title='reCAPTCHA']")))
            self.driver.switch_to.frame(iframe1)
        elif idx == 2:  # 리캡챠 이미지가 있는 iframe 탐색
            iframe2 = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'bframe')]")))
            self.driver.switch_to.frame(iframe2)

    def get_target(self):
        target_map = {
            "bicycle": 1, "자전거": 1,
            "bus": 5, "버스": 5,
            "boat": 8, "보트": 8,
            "car": 2, "자동차": 2,
            "hydrant": 10, "소화전": 10,
            "motorcycle": 3, "오토바이": 3,
            "traffic": 9, "신호등": 9
        }

        target = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='rc-imageselect']//strong")))
        
        for term, value in target_map.items():
            if re.search(term, target.text): return value

        return (-1)
    
    def delay(self, mu, sigma):
        # mu : 평균 시간, sigma : 표준편차
        time = np.random.normal(mu, sigma)
        delay = max(0.1, time)
        sleep(delay)

    def get_imgUrl(self):
        images = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@id="rc-imageselect-target"]//img')))

        url = []
        for img in images:
            url.append(img.get_attribute("src"))

        return url

    def download_images(self, name, url):
        response = requests.get(url, stream = True)
        with open(f"v2_images/{name}.png", 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        del response
        print("이미지 다운로드 완료")

    def solver_square(self, target, model):
        # 4*4 타일 유형 리캡챠 해결 함수
        image = Image.open("v2_images/0.png")
        image = np.asarray(image)

        result = model.predict(source = image, task = "detect")
        boxes = result[0].boxes.data

        target_idx = []
        count = 0
        answer = set()

        for num in result[0].boxes.cls:
            if num == target:
                target_idx.append(count)
            count += 1

        for i in target_idx:
            target_box = boxes[i]
            print(target_box)
            x1, y1, x4, y4 = map(int, target_box[:4])
            x2, y2 = x4, y1
            x3, y3 = x1, y4
            xys = [x1, y1, x2, y2, x3, y3, x4, y4]

            sommet = []
            for j in range(4):
                x = xys[j * 2]
                y = xys[j * 2 + 1]

                frontiere = [0, 112.5, 225, 337.5, 450]
                for k in range(4):
                    for f in range(4):
                        if (frontiere[k] <= x < frontiere[k + 1]) and (frontiere[f] <= y < frontiere[f + 1]):
                            sommet.append(f * 4 + k + 1)

            rows, cols = zip(*[((s - 1) // 4, (s - 1) % 4) for s in sommet])

            for r in range(min(rows), max(rows) + 1):
                for c in range(min(cols), max(cols) + 1):
                    answer.add(4 * r + c + 1)

        return sorted(list(answer))
        
    def solver_selection(self, target, model, img_num = 0):
        # 3*3 타일 다회성 유형 리캡챠 해결 함수
        image = Image.open(f"v2_images/{img_num}.png")
        image = np.asarray(image)

        result = model.predict(image, task = "detect")

        target_idx = []
        count = 0
        for num in result[0].boxes.cls:
            if num == target: target_idx.append(count)
            count += 1

        answer = set()
        boxes = result[0].boxes.data
        for i in target_idx:
            target_box = boxes[i]
            x1, y1, x2, y2 = map(int, target_box[:4])

            xc = (x1 + x2) // 2
            yc = (y1 + y2) // 2

            h, w, _ = image.shape

            row = yc * 3 // h
            col = xc * 3 // w

            answer.add(int(row * 3 + col + 1))

        return list(answer)
    
    def exists(self):
        self.driver.switch_to.default_content()
        try:
            captcha = self.driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
            return captcha.is_displayed()
        except NoSuchElementException:
            return False
    
    def solver(self):
        print("리캡챠 해결 시작")

        self.iframe(1)
        WebDriverWait(self.driver, self.timeout).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='recaptcha-checkbox-border']"))).click()
        self.iframe(2)
        
        print("모델 로드")
        model = YOLO("RecaptchaV2-IA-Solver/model.onnx", task="detect")

        while True:
            try:
                while True:
                    sleep(2)
                    if(not self.exists()):
                        print("리캡챠 통과")
                        return True
                    else: self.iframe(2)

                    print("리캡챠 iframe 존재 여부 확인")
                    reload = WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((By.ID, 'recaptcha-reload-button')))
                    # reload -> 새로고침 버튼
                    title_wrapper = WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.ID, 'rc-imageselect')))
                    # title_wrapper -> 안내문 + 이미지 타일 포함 영역

                    target = self.get_target()
                    print("타겟 발견")

                    if target == -1:
                        self.delay(2, 1)
                        print("타겟 탐색되지 않아 재시도 ㄱㄱ")
                        reload.click()
                        continue
                    else:
                        print("리캡챠 유형 분석 시작")

                        if(title_wrapper.find_elements(By.CSS_SELECTOR, ".rc-imageselect-table-33")):
                            print("3x3 타일 유형의 리캡챠 탐지")

                            count = 0   # 반복인지 아닌지 확인용
                            while True:
                                print(f"{count + 1}번째 시도")

                                if(not count):
                                    img_url = self.get_imgUrl()
                                    self.download_images(0, img_url[0])

                                else:
                                    before_url = img_url
                                    img_url = self.get_imgUrl()
                                    
                                    if(before_url[answer[0] - 1] == img_url[answer[0] - 1]):
                                        print("이미지 변화 없음 - 단회성")
                                        break
                                    else:
                                        print("이미지 변화 있음 - 다회성")
                                        image = np.array(Image.open("v2_images/0.png"))
                                        for i in range(len(answer)):
                                            self.download_images(i + 1, img_url[answer[i] - 1])

                                            newImage = np.array(Image.open(f"v2_images/{i + 1}.png"))
                                            row, col = (answer[i] - 1) // 3, (answer[i] - 1) % 3

                                            start_row, end_row = row * 100, (row + 1) * 100
                                            start_col, end_col = col * 100, (col + 1) * 100

                                            image[start_row : end_row, start_col : end_col] = newImage
                                            cv2.imwrite("v2_images/0.png", image)

                                answer = self.solver_selection(target, model)
                                random.shuffle(answer)
                                print(f"{len(answer)}개의 답안 발견")

                                if(len(answer) < 1):
                                    print("답변이 너무 적어 재시도")
                                    break
                                
                                WebDriverWait(self.driver, self.timeout).until(
                                    EC.element_to_be_clickable((By.XPATH, '(//div[@id="rc-imageselect-target"]//td)[1]')))

                                print("답안 작성 ㄱㄱ")
                                for ans in answer:
                                    WebDriverWait(self.driver, self.timeout).until(
                                        EC.element_to_be_clickable((By.XPATH, f'(//div[@id="rc-imageselect-target"]//td)[{ans}]'))).click()
                                    self.delay(2, 1)

                                count += 1
                                sleep(2)

                        elif(title_wrapper.find_elements(By.CSS_SELECTOR, ".rc-imageselect-table-44")):
                            print("4x4 타일 유형의 리캡챠 탐지")

                            img_url = self.get_imgUrl()
                            self.download_images(0, img_url[0])

                            answer = self.solver_square(target, model)
                            random.shuffle(answer)
                            print(f"{len(answer)}개의 답안 발견")

                            if(len(answer) < 1):
                                print("답변이 너무 적어 재시도")
                                break

                            WebDriverWait(self.driver, self.timeout).until(
                                EC.element_to_be_clickable((By.XPATH, '(//div[@id="rc-imageselect-target"]//td)[1]')))

                            print("답안 작성 ㄱㄱ")
                            for ans in answer:
                                WebDriverWait(self.driver, self.timeout).until(
                                    EC.element_to_be_clickable((By.XPATH, f'(//div[@id="rc-imageselect-target"]//td)[{ans}]'))).click()
                                self.delay(2, 1)

                    verify_btn = WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
                    self.delay(2, 1)
                    verify_btn.click()

                    polite = self.driver.find_element(By.CLASS_NAME, "rc-imageselect-error-select-more")
                    if (not "display:none" in polite.get_attribute("style")):
                        reload.click()
                        continue

                    self.driver.switch_to.default_content()
                    sleep(1)
                    
                    if(self.exists()):
                        print("리캡챠 실패")
                        self.iframe(2)
                    else:
                        print("리캡챠 통과")
                        return True

            except Exception as e:
                print(e)
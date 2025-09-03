import re, shutil, random
from time import sleep

import numpy as np
import requests
from PIL import Image
import base64

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from openai import OpenAI

class ImageRecaptchaSolver_GPT:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10
        self.client = OpenAI(api_key  = "#")

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

    def solver_selection(self):
        print("GPT 돌리기~")

        with open("v2_images/screenshot.png", 'rb') as f:
            image = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "Your are an object detection assistant. Understand what is asked on the top instruction of the "
            "image. For Example if instruction says select all squares with motorcycle. There are 9 squares "
            "give number for each square 1 to 9. The numbers starts from top left to right. Then answer only "
            "with the square numbers like 1-3-5-6."
            "Understand the instruction and give me the highest probability squares as answer. Give only the correct square numbers."
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Please make a answer of this image"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}
                ]}
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        answer = response.choices[0].message.content
        print(f"RESPONSE : {answer}")
        return [int(x) for x in answer.split('-')]

    def solver_square(self):
        print("GPT 돌리기~")

        with open("v2_images/screenshot.png", 'rb') as f:
            image = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "Your are an object detection assistant. Understand what is asked on the top instruction of the "
            "image. For Example if instruction says select all squares with motorcycle. There are 16 squares "
            "give number for each square 1 to 16. The numbers starts from top left to right. Then answer only "
            "with the square numbers like 1-3-5-6."
            "Understand the instruction and give me the highest probability squares as answer. Give only the correct square numbers."
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Please make a answer of this image"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}
                ]}
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        answer = response.choices[0].message.content
        print(f"RESPONSE : {answer}")
        return [int(x) for x in answer.split('-')]

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

                    print("리캡챠 유형 분석 시작")

                    if(title_wrapper.find_elements(By.CSS_SELECTOR, ".rc-imageselect-table-33")):
                        print("3x3 타일 유형의 리캡챠 탐지")

                        count = 0   # 반복인지 아닌지 확인용
                        while True:
                            print(f"{count + 1}번째 시도")

                            if(not count):
                                title_wrapper.screenshot('v2_images/screenshot.png')
                                img_url = self.get_imgUrl()

                            else:
                                before_url = img_url
                                img_url = self.get_imgUrl()
                                
                                if(before_url[answer[0] - 1] == img_url[answer[0] - 1]):
                                    print("이미지 변화 없음 - 단회성")
                                    break
                                else:
                                    print("이미지 변화 있음 - 다회성")
                                    title_wrapper.screenshot('v2_images/screenshot.png')

                            answer = self.solver_selection()
                            random.shuffle(answer)
                            print(f"{len(answer)}개의 답안 발견")

                            if(len(answer) < 1):
                                print("답변이 너무 적어 재시도")
                                reload.click()
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

                        title_wrapper.screenshot('v2_images/screenshot.png')

                        answer = self.solver_square()
                        random.shuffle(answer)
                        print(f"{len(answer)}개의 답안 발견")

                        if(len(answer) < 1):
                            print("답변이 너무 적어 재시도")
                            reload.click()
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
                        #self.iframe(2)
                    else:
                        print("리캡챠 통과")
                        return True

            except Exception as e:
                print(e)

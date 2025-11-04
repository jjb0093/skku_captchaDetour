import shutil, random, time
from time import sleep

import cv2
import numpy as np
import requests, base64

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options

import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer

#from openai import OpenAI

class GeeTestSolver_Icon_Gpt:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10
        #self.client = OpenAI(api_key  = "#")

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
        
    def capture_div(self, type, name, load):
        if(type == 'class'):
            div = self.driver.find_element(By.CLASS_NAME, name)
        elif(type == 'id'):
            div = self.driver.find_element(By.ID, name)

        if(div.screenshot(f"imgFiles/geeTest/{load}")):
            return True
        else: return False

    def download_images(self, url, load):
        response = requests.get(url, stream = True)
        with open(f"imgFiles/geeTest/{load}", 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        del response

    def modifier_icons(self, num):
        img = cv2.imread(f"imgFiles/geeTest/icon_{num}.png", cv2.IMREAD_UNCHANGED)
        
        bgr = img[:, :, :3]
        alpha = img[:, :, 3] if img.shape[2] == 4 else np.ones(bgr.shape[:2], dtype=np.uint8) * 255

        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha_f = alpha[:, :, np.newaxis] / 255.0
        blended = (bgr * alpha_f + white_bg * (1 - alpha_f)).astype(np.uint8)

        # 엣지 검출 (Canny)
        edges = cv2.Canny(blended, 200, 300)

        # 엣지 확장 (dilate)
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        # 확장된 엣지를 마스크로 사용 → 나머지는 흰색 배경
        mask = cv2.merge([dilated, dilated, dilated])
        result = np.where(mask > 0, blended, 255)  # 엣지 부분만 남기고 나머지는 흰색

        # RGB 변환 (혹시 BGR일 경우)
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

        # 결과 저장
        cv2.imwrite(f"imgFiles/geeTest/icon_{num}_white.png", result_rgb)

    def modifier_images(self):
        img = cv2.imread("imgFiles/geeTest/icon_background.png")
        height, width = img.shape[0:2]

        #img_copy = cv2.Canny(img, 300, 400)
        #img_copy = cv2.cvtColor(img_copy, cv2.COLOR_GRAY2BGR)
        img_copy = img.copy()

        step = 50
        for h in range(0, height + step, step):
            cv2.line(img_copy, (0, h), (width, h), (0, 255, 0), 1)

        for w in range(0, width + step, step):
            cv2.line(img_copy, (w, 0), (w, height), (0, 255, 0), 1)

        cell_num = 1
        for i in range(height // 50):
            for k in range(width // 50):
                (text_w, text_h), baseline = cv2.getTextSize(str(cell_num), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                cv2.putText(
                    img_copy, str(cell_num), (k * 50 + ((50 - text_w) // 2), i * 50 + ((50 + text_h) // 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA
                )

                cell_num += 1

        img_full = cv2.imread("imgFiles/geeTest/iconCaptcha.png")
        img_full[60 : 60 + height, 20 : 20 + width] = img_copy

        cv2.imwrite("imgFiles/geeTest/icon_background_line.png", img_copy)
        cv2.imwrite("imgFiles/geeTest/iconCaptcha_line.png", img_full)

    def demander_LLM_pour_Obj(self):
        image = Image.open("imgFiles/geeTest/iconCaptcha.png").convert('RGB')

        enable_thinking=False # If `enable_thinking=True`, the thinking mode is enabled.
        stream=True # If `stream=True`, the answer is string

        question = """
            Follow the instruction above.
            Find the icons that are illustrated on the top right,
            Find each icons from the image below, and explain specifically with their features like color, shape, etc., keeping the order of the instruction.
            OUTPUT must be in this exact format : 'explanation of the first icon / second icon / third icon'. 
            Please include '/' between those explanations.
            Do not include numbering, labels, or line breaks.
        """

        msgs = [{'role': 'user', 'content': [image, question]}]

        answer = model.chat(
            msgs=msgs,
            tokenizer=tokenizer,
            enable_thinking=enable_thinking,
            stream=True
        )

        generated_text = ""
        for new_text in answer:
            generated_text += new_text

        print(generated_text)
        result = generated_text.split('/')

        return result
    
    def demander_LLM_pour_Explanation(self, num):
        image = Image.open(f"imgFiles/geeTest/icon_{num}_white.png").convert('RGBA')

        enable_thinking=False
        stream = True

        question = """
            Describe the icon in detail in three sentences. Focus on how the overall outline flows and connects, capturing the general shape and movement of its form, without mentioning internal elements or color.
        """

        msgs = [{'role': 'user', 'content': [image, question]}]

        answer = model.chat(
            msgs=msgs,
            tokenizer=tokenizer,
            enable_thinking=enable_thinking,
            stream=True
        )

        generated_text = ""
        for new_text in answer:
            generated_text += new_text

        return generated_text

    def demander_LLM_pour_Reponses(self, icon):
        image = Image.open("imgFiles/geeTest/icon_background_line.png").convert('RGB')

        enable_thinking=False # If `enable_thinking=True`, the thinking mode is enabled.
        stream=True # If `stream=True`, the answer is string

        question = f"""
            This is an explanation of a specific icon : {icon}. Find it and return the number of the grid that contains that icon. 
            If multiple grids contain the icon, return only one that contains the center of the icon.
            Ensure that the result is only the number, with no extra text or formatting.
        """

        msgs = [{'role': 'user', 'content': [image, question]}]

        answer = model.chat(
            msgs=msgs,
            tokenizer=tokenizer,
            enable_thinking=enable_thinking,
            stream=True
        )

        generated_text = ""
        for new_text in answer:
            generated_text += new_text

        return generated_text

    def demander_LLM_Test(self, num):
        image = Image.open("imgFiles/geeTest/iconCaptcha.png").convert('RGB')

        enable_thinking=False # If `enable_thinking=True`, the thinking mode is enabled.
        stream=True # If `stream=True`, the answer is string

        if(num == 1): text = "first"
        elif(num == 2): text = "second"
        else: text = "third"

        question = f"""
            Look carefully at the instruction text at the top of the image.
            You must identify the three icons shown there, in the **exact same order** as they appear in that instruction area (left to right).
            Then, find the {text} icon from the image below, and eturn the number of the grid that contains that icon. 
            If multiple grids contain the icon, return only one that contains the center of the icon.
            Ensure that the result is only the number, with no extra text or formatting.
        """

        msgs = [{'role': 'user', 'content': [image, question]}]

        answer = model.chat(
            msgs=msgs,
            tokenizer=tokenizer,
            enable_thinking=enable_thinking,
            stream=True
        )

        generated_text = ""
        for new_text in answer:
            generated_text += new_text

        result = generated_text.split('/')

        return result
    
    def demanader_LLM_pour_Verification(self, num, icon):
        image = cv2.imread("imgFiles/geeTest/icon_background.png")
        num = int(num)

        x_initial, y_initial = (((num - 1) % 6)) * 50 + 25, (((num - 1) // 6)) * 50 + 25
        if((x_initial - 75) < 0): x_range = [0, 150]
        elif((x_initial + 75) > 300): x_range = [150, 300]
        else: x_range = [x_initial - 75, x_initial + 75]

        if((y_initial - 75) < 0): y_range = [0, 150]
        elif((y_initial + 75) > 200): y_range = [50, 200]
        else: y_range = [y_initial - 75, y_initial + 75]

        img_crop = image[y_range[0] : y_range[1], x_range[0] : x_range[1]]

        height, width = img_crop.shape[:2]
        img_copy = img_crop.copy()

        step = 30
        for h in range(0, height + step, step):
            cv2.line(img_copy, (0, h), (width, h), (0, 255, 0), 1)

        for w in range(0, width + step, step):
            cv2.line(img_copy, (w, 0), (w, height), (0, 255, 0), 1)

        cell_num = 1
        for i in range(height // step):
            for k in range(width // step):
                cx, cy = k * 30 + 15, i * 30 + 15
                bg_color = img_crop[cy, cx]
                b, g, r = [x / 255.0 for x in bg_color]
                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                if(lum < 0.5):
                    text_color = (255, 255, 255)
                else:
                    text_color = (0, 0, 0)

                (text_w, text_h), baseline = cv2.getTextSize(str(cell_num), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.putText(
                    img_copy, str(cell_num), (k * step + ((step - text_w) // 2), i * step + ((step + text_h) // 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1, cv2.LINE_AA
                )

                cell_num += 1

        cv2.imwrite(f"imgFiles/geeTest/icon_crop_line_{num}.png", img_copy)
        image = Image.fromarray(cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB))

        enable_thinking=False # If `enable_thinking=True`, the thinking mode is enabled.
        stream=True # If `stream=True`, the answer is string

        question = f"""
            This is an explanation of a specific icon : {icon}. Find it and return the number of the grid that contains that icon. 
            If multiple grids contain the icon, return only one that contains the center of the icon.
            Ensure that the result is only the number, with no extra text or formatting.
        """

        msgs = [{'role': 'user', 'content': [image, question]}]

        answer = model.chat(
            msgs=msgs,
            tokenizer=tokenizer,
            enable_thinking=enable_thinking,
            stream=True
        )

        generated_text = ""
        for new_text in answer:
            generated_text += new_text

        grid = int(generated_text)
        x, y = (x_range[0] + step * ((grid - 1) % 5) + 15), (y_range[0] + step * ((grid - 1) // 5) + 15)

        return grid, x, y

    def getDistance(self, pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def solver(self, t):
        print("geeTest 아이콘 유형 해결 시작")
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

            reload = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_refresh")))
            verify = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_submit")))
            
            img_background = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_bg"))
            )
            img_x, img_y = img_background.size['width'], img_background.size['height']
            style = img_background.get_attribute("style")
            url = style.split('(')[1].split(')')[0].replace('"', '')

            iconDiv = self.driver.find_element(By.CLASS_NAME, "geetest_ques_tips")
            imgs = iconDiv.find_elements(By.TAG_NAME, "img")

            for i in range(len(imgs)):
                icon_url = imgs[i].get_attribute("src")
                self.download_images(icon_url, f"icon_{i}.png")
                self.modifier_icons(i)

            start = time.time()
            explanation = []
            for i in range(len(imgs)):
                explanation.append(self.demander_LLM_pour_Explanation(i))

            self.download_images(url, "icon_background.png")

            self.capture_div("class", "geetest_box", "iconCaptcha.png")
            
            self.modifier_images()

            result = []
            for i in range(3):
                grid = self.demander_LLM_pour_Reponses(explanation[i])
                num, x, y = self.demanader_LLM_pour_Verification(grid, explanation[i])
                print(f"설명 : {explanation[i]} / 그리드 : {grid} / 검증 결과 : {num} / 좌표 : ({x}, {y})")
                result.append([x, y])

            finish = time.time()
            referenceTime = finish - start

            '''
            for i in range(len(result)):
                action.move_to_element_with_offset(img_background, result[i][0], result[i][1]).click().perform()
                sleep(1)
            '''

            # result에 들어있는 div 내부 좌표 클릭
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
                """, img_background, x_offset, y_offset)

                sleep(1)

            verify.click()
            self.driver.save_screenshot(f"imgFiles/screenshot_{t}.png")

            sleep(2)

            tip = self.driver.find_element(By.CLASS_NAME, "geetest_tip")
            if "Verification Success" in tip.text:
                print("성공")
                return True, referenceTime
            else:
                print("실패")
                return False, referenceTime

            
if(__name__ == "__main__"):
    torch.manual_seed(100)

    model_id = "openbmb/MiniCPM-V-4_5-int4"

    # 토크나이저 로드
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    # 모델 로드 (4bit 양자화 버전)
    model = AutoModel.from_pretrained(
        model_id,
        trust_remote_code=True,
        load_in_4bit=True,   # 핵심 부분!
        device_map={"": "cuda:1"}    # GPU 있으면 자동 할당, 없으면 CPU
    ).eval()

    options = Options()
    options.add_argument("--headless")  # GUI 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options = options)

    success = 0
    referenceTimes = []
    workTimes = []
    for i in range(10):
        driver.get("https://gt4.geetest.com/demov4/icon-popup-en.html")

        wstart = time.time()
        solver = GeeTestSolver_Icon_Gpt(driver)
        result, reftime = solver.solver(i+11)
        wfinish = time.time()

        if(result):
            success += 1
            referenceTimes.append(reftime)
            workTimes.append(wfinish - wstart)

        print(f"{success}번 성공 / {i + 1}번째 시도 중")
        if(len(referenceTimes) > 0):
            print(f"평균 추론 시간 : {sum(referenceTimes) / len(referenceTimes)}")

print(f"총 50번의 시도 중 통과한 횟수 : {success}")
print(f"평균 추론 시간 : {sum(referenceTimes) / len(referenceTimes)}")
print(f"평균 수행 시간 : {sum(workTimes) / len(workTimes)}")
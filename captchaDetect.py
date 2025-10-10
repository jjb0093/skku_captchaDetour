from seleniumwire import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import time, re

from openai import OpenAI

class CaptchaDetect:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10
        self.client = OpenAI(api_key = "#")

    def detectType(self):
        responseUrl = self.getNetwork()
        htmlInfo = self.getHtml()
        
        result = self.classifier(responseUrl, htmlInfo)
        return result

    def getNetwork(self):
        responseUrl = []

        for request in self.driver.requests:
            response = request.response
            if(response):
                status = getattr(response, "status_code", None)
                #content_type = response.headers.get("Content=Type") or response.headers.get("content=type")
                if(status == 200): responseUrl.append(request.url)

        return responseUrl

    def getHtml(self):
        self.driver.switch_to.default_content()
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
        except:
            pass

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        iframes = [iframe.get("src", "") for iframe in soup.find_all("iframe")]
        scripts = [script.get("src", "") for script in soup.find_all("script")]
        siteKeys = re.findall(r'data-sitekey=["\'](.*?)["\']', html)

        return {
            "iframes": iframes,
            "scripts": scripts,
            "siteKeys": siteKeys
        }
    
    def classifier(self, urls, htmls):

        prompt = "Here's the list of networks, iframes, scripts, and sitekeys. Analyze those infos and print me out the name of provider and the type of specific captcha. Do not explain anything else except the result."
        prompt += f" Networks: {urls}"
        prompt += f" Iframes: {htmls["iframes"]}"
        prompt += f" Scripts: {htmls["scripts"]}"
        prompt += f" SiteKeys: {htmls["siteKeys"]}"

        systemPrompt = """
            You are a CAPTCHA identification expert.
            You must determine WHICH CAPTCHA PROVIDER is being used on a website 
            (e.g., Google reCAPTCHA, hCaptcha, Cloudflare Turnstile), 
            NOT the solving service (like 2Captcha or AntiCaptcha).
            Return the result as 'providerName-captchaType', for example:
            - google-recaptchaV2
            - google-recaptchaV3
            - hcaptcha-enterprise
            - cloudflare-turnstile
            If you are uncertain, return 'unknown-unknown'. Do not include explanations.
        """

        response = self.client.chat.completions.create(
            model = "gpt-4",
            messages = [
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.5,
        )
        answer = response.choices[0].message.content

        return answer

reCaptchaTestLink = [
    ['2Captcha_reCaptchav2', 'https://2captcha.com/demo/recaptcha-v2'],
    ['google_reCaptchav2', 'https://www.google.com/recaptcha/api2/demo'],
    ['nopecha_reCaptchav2', 'https://nopecha.com/demo/recaptcha'],
    ['nextCaptcha_reCaptchav2', 'https://nextcaptcha.com/demo/recaptcha_v2'],
    ['salesForce_reCaptchav2', 'https://comfortgroup.my.site.com/resource/1683234966000/recaptchaV2'],
    ['myVarian_reCaptchav2', 'https://www.myvarian.com/apex/Mv_Recaptcha'],
    ['capMonster_reCaptchav2', 'https://capmonster.cloud/en/demo/recaptcha-v2'],
    ['ahpra_reCaptchav2', 'https://portal.ahpra.gov.au/resource/1741233813000/reCaptchaV2']
]

captchaTestLink = [
    ['google-reCaptchav2', 'https://nopecha.com/demo/recaptcha'],
    ['google-reCaptchav3', 'https://nopecha.com/captcha/recaptcha#v3'],
    ['hCaptcha', 'https://nopecha.com/demo/hcaptcha'],
    ['leminCaptcha', 'https://nopecha.com/captcha/lemincaptcha'],
    ['cloudFlare-turnstile', 'https://nopecha.com/captcha/turnstile'],
    ['geeTest-puzzle', 'https://gt4.geetest.com/demov4/slide-float-en.html'],
    ['geeTest-slider', 'https://gt4.geetest.com/demov4/slide-popup-en.html'],
    ['geeTest-image', 'https://gt4.geetest.com/demov4/nine-popup-en.html'],
    ['geeTest-iconCrush', 'https://gt4.geetest.com/demov4/match-popup-en.html'],
]

if __name__ == "__main__":
    driver = webdriver.Chrome()
    captchaDetector = CaptchaDetect(driver)

    results = {}
    for i in range(len(captchaTestLink)):
        driver.get(captchaTestLink[i][1])
        time.sleep(1)

        detect = captchaDetector.detectType()
        print(f"{captchaTestLink[i][0]} -> {detect}")
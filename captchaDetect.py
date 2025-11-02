from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class captchaDetect:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    def getHtml(self):
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "div"))
        )
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        divs = self.driver.find_elements(By.TAG_NAME, "div")

        return iframes, divs
    
    def getNetwork(self):
        self.driver.requests.clear()
        responseUrl = set()

        for request in self.driver.requests:
            response = request.response
            if(response):
                status = getattr(response, "status_code", None)
                if(status == 200): responseUrl.add(request.url)

        return list(responseUrl)
    
    def detectCaptcha(self):
        iframes, divs = self.getHtml()

        while True:
            for iframe in iframes:
                titles = iframe.get_attribute("title")
                if "reCAPTCHA" in titles:
                    return "reCAPTCHA"
            
            for div in divs:
                classes = div.get_attribute("class")
                if "geetest" in classes:
                    responseUrl = self.getNetwork()

                    for resUrl in responseUrl:
                        if "slide" in resUrl:
                            return "GeeTest_Slide"
                        elif "icon" in resUrl:
                            return "GeeTest_Icon"
            
            return None
from time import sleep

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class CloudFlareSolver:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 5
        
    def exists(self):
        try:
            captcha = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1[class='zone-name-title h1']"))
            )
            print("CloudFlare 캡챠 발견")
            return captcha.is_displayed()
        except TimeoutException:
            return False
        
    def solveCaptcha(self):
        count = 0

        while True:
            with open('cloudFlareCookie.txt', 'r') as f:
                clearance = f.read().strip()

            if(clearance != '') and (count == 0):
                print("저장된 쿠키값 있음")
                cookie = {
                    'name': 'cf_clearance',
                    'value': clearance
                }
                self.driver.add_cookie(cookie)
                self.driver.refresh()

                sleep(2)

                if(not self.exists()):
                    print("캡챠 해결 성공")
                    return True
                else:
                    print("캡챠 해결 실패 -> 기존 쿠키값 삭제 후 재시도")
                    count += 1
                    with open('cloudFlareCookie.txt', 'w') as f:
                        f.write('')
                    continue

            else:
                print("저장된 쿠키값 없음")
                while True:
                    if(not self.exists()):
                        print("캡챠 해결")
                        sleep(2)

                        clearance_cookie = self.driver.get_cookie('cf_clearance')

                        if(clearance_cookie):
                            print("cf_clearance 발급 성공~")
                            with open('cloudFlareCookie.txt', 'w') as f:
                                f.write(clearance_cookie['value'])
                        else:
                            print("얼라리 해결은 했지만 쿠키값 없음")
                        return True
                    else:
                        sleep(2)
                        continue

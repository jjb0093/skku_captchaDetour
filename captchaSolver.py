from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

from captchaDetect import captchaDetect
from solver.reCaptchaSolver import ReCaptchaSolver
from solver.geeTestSlideSolver import GeeTestSlideSolver
from solver.geeTestIconSolver import GeeTestIconSolver

class captchaSolver:
    def __init__(self, driver):
        self.driver = driver

    def solver(self):
        captcha = {
            "reCAPTCHA": ReCaptchaSolver,
            "GeeTest_Slide": GeeTestSlideSolver,
            "GeeTest_Icon": GeeTestIconSolver
        }

        detectResult = captchaDetect(self.driver).detectCaptcha()
        if(detectResult in captcha.keys()):
            solverModule = captcha[detectResult](self.driver)

            if(solverModule.solver()): return True
            else: return False
        else:
            return None

if(__name__ == "__main__"):
    test = [
        'https://gt4.geetest.com/demov4/slide-float-en.html',
        'https://2captcha.com/demo/recaptcha-v2',
        'https://gt4.geetest.com/demov4/icon-popup-en.html'
    ]

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options = options)
    
    for i in range(len(test)):
        driver.get(test[i])

        solver = captchaSolver(driver)
        print(solver.solver())

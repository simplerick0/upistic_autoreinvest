from PIL import Image
from selenium import webdriver
from twocaptcha import TwoCaptcha

import argparse
import getpass
import shutil
import time

try:
    from secrets import captcha_api_key, up_pass
except ImportError:
    print("No configuration detected. Creating default secrets.py to update")
    shutil.copy("sample-secrets.py", "secrets.py")
    print("Please update secrets.py")
    exit(1)

CAPTCHA_FILENAME = "captcha.png"
SUPPORTED_TOKENS = [
    "btc",
    "eth",
    "eth_bep20",
    "ltc",
    "doge",
    "bch",
    "usdt",
    "usdt_trc20",
    "usdt_bep20",
    "dash",
    "trx",
    "usdc",
    "usdc_bep20",
    "busd_bep20",
    "xrp",
    "bnb",
    "zec",
    "xmr",
    "xlm",
    "eos_bep20",
    "ada_bep20",
    "pm",
    "sol",
    "dot_bep20",
    "link_bep20",
    "shib",
    "shib_bep20",
    "beam",
    "waves",
    "xvg",
    "vlx",
    "dai",
    "babydoge",
]

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", required=True, help="UPistic username")
parser.add_argument(
    "-t",
    "--token",
    choices=SUPPORTED_TOKENS,
    required=True,
    help="Token name as used by UPistic. (i.e. btc, eth, eth_dep20, ...)",
)
args = parser.parse_args()

print(f"Logging in as {args.user}")
if not up_pass:
    print("No UPistic password provided, please update up_pass in secrets.py")
    exit(1)

if not captcha_api_key:
    print("No 2Captcha API key provided, please update captcha_api_key in secrets.py")
    exit(1)

browser = webdriver.Firefox()
browser.get("https://upistic.com/login")
browser.find_element_by_xpath("/html/body/div/div/div/form/div[1]/input").send_keys(args.user)
browser.find_element_by_xpath("/html/body/div/div/div/form/div[2]/input").send_keys(up_pass)

captcha_input = browser.find_element_by_xpath("/html/body/div/div/div/form/div[4]/input")
captcha_image = browser.find_element_by_xpath("/html/body/div/div/div/form/div[3]/img")
captcha_location = captcha_image.location
captcha_size = captcha_image.size
browser.save_screenshot(CAPTCHA_FILENAME)
x = captcha_location['x']
y = captcha_location['y']
height = captcha_location['y'] + captcha_size['height']
width = captcha_location['x'] + captcha_size['width']
img = Image.open(CAPTCHA_FILENAME)
img = img.crop((int(x), int(y), int(width), int(height)))
img.save(CAPTCHA_FILENAME)
print(f"Saved captcha to upload to 2Captcha as {CAPTCHA_FILENAME}")

solver = TwoCaptcha(captcha_api_key)
print(f"Using 2Captcha Solver. Account balance: {solver.balance()}")

captcha_answer = ""
try:
    captcha_answer = solver.normal(CAPTCHA_FILENAME, numeric=1, min_len=6, max_len=6)
except ValidationException as e:
    # Invalid parameters
    print(e)
    browser.close()
    exit(1)
except NetworkException as e:
    # Network error
    print(e)
    browser.close()
    exit(1)
except ApiException as e:
    # API responded with error
    print(e)
    browser.close()
    exit(1)
except TimeoutException as e:
    # captcha solve timed out
    print(e)
    browser.close()
    exit(1)

print(f"Solved captcha. Code={captcha_answer['code']}. Remaining balance: {solver.balance()}")
captcha_input.send_keys(captcha_answer['code'])

print("Clicking Login button")
browser.find_element_by_xpath("/html/body/div/div/div/form/div[5]/button").click()

print(browser.current_url)
if browser.current_url != None and "login_otp" in browser.current_url:
    print("UPistic is requesting MFA code")
    mfa_code = getpass.getpass("UPistic MFA Code: ")

    browser.find_element_by_xpath("/html/body/div/div/div/form/div[1]/input").send_keys(mfa_code)
    browser.find_element_by_xpath("/html/body/div/div/div/form/div[2]/button").click()
elif "login" in browser.current_url:
    print("Login failed")
    browser.close()
    exit(1)
else:
    print(browser.current_url)
    print("MFA is not enabled, continuing")

print(f"Reinvesting available balance for {args.token}")
browser.get(f"https://upistic.com/enter?ps={args.token}")

bal = browser.find_element_by_xpath('//*[@id="balance"]').text
print(f"Token [{args.token}] available balance: {bal}")

browser.find_element_by_xpath("/html/body/div[1]/div[2]/div[2]/form/div/div/div[2]/div[1]/div[2]/input").send_keys(bal)

print("Clicking Create order button")
browser.find_element_by_xpath("/html/body/div[1]/div[2]/div[2]/form/div/div/div[2]/div[2]/button").click()
time.sleep(1) # quick hack, seems like selenium looks for the notif before the page finishes loading on occasion

notifications = browser.find_element_by_class_name("wrpnotif")
notif = notifications.find_element_by_xpath(".//div[2]").text
print(f"Got notification: {notif}")
if "Minimum" in notif:
    print("Failed to reinvest, insufficient available balance")
elif "successfully" in notif:
    print(f"Successfully reinvested {args.token} balance of {bal}")
else:
    print("Unknown notification")

browser.close()

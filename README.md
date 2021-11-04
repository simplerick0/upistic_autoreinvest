Automation Tool for Reinvesting an Account at UPistic.com

Includes Captcha support via 2Captcha

NOTE: If your account has Two-Factor Authentication enabled, the script will prompt for your code 
(thus breaking automation).

Requirements:
* `firefox`
* `pip3 install -r requirements.txt`
* Install: `https://github.com/mozilla/geckodriver/releases`

Run:
* `python3 reinvest.py -u <username> -t <token>`
  * ex. `python3 reinvest.py -u ilovelamp -t eth`
  * This will reinvest your available Ethereum balance into your account

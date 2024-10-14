from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_new_ip():
    """Fetch a new IP address from the API."""
    try:
        response = requests.get("https://api.myip.com")
        if response.status_code == 200:
            return response.json()['ip']
    except Exception as e:
        print(f"Error while getting new IP: {e}")
        return None


def login_facebook(account):
    """Log in to Facebook using provided account credentials."""

    # Set up Selenium options
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")  # Enable incognito mode
    options.add_argument("--disable-cache")  # Disable cache
    options.add_argument("--disable-application-cache")  # Disable application cache
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.facebook.com")

    try:
        # Wait for cookie consent
        time.sleep(1)

        # Attempt to accept cookies
        try:
            cookie_accept_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept All Cookies']"))
            )
            cookie_accept_button.click()
        except Exception:
            pass  # Ignore if cookie button is not found

        # Fill in email and password fields
        email_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_elem.send_keys(account["login"])

        password_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "pass"))
        )
        password_elem.send_keys(account["password"])

        # Click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "login"))
        )
        time.sleep(2)  # Wait for the button to be visible
        driver.execute_script("arguments[0].click();", login_button)  # Click using JavaScript

        # Wait for the page to load
        time.sleep(3)

        # Check for unsuccessful login
        try:
            error_message = driver.find_elements(By.XPATH, "//div[@class='_9ay7']")
            yes_continue_button = driver.find_elements(By.XPATH, "//button[text()='Yes, Continue']")
            login_as_message = driver.find_elements(By.XPATH, "//span[contains(text(), 'Log in as')]")
            facebook_message = driver.find_elements(By.XPATH, "//span[contains(text(), 'facebook')]")

            if error_message or yes_continue_button or login_as_message or facebook_message:
                print(f"Login failed for {account['login']}: Incorrect email or password.")
                return None

            # Record selected cookies upon successful login
            selected_cookies = {}
            all_cookies = driver.get_cookies()
            for cookie in all_cookies:
                if cookie['name'] in ['datr', 'sb', 'm_pixel_ratio', 'wd', 'c_user', 'fr', 'xs']:
                    selected_cookies[cookie['name']] = cookie['value']

            # Format the cookies in the desired order
            ordered_cookies = [
                f"datr={selected_cookies.get('datr', '')}",
                f"sb={selected_cookies.get('sb', '')}",
                f"m_pixel_ratio={selected_cookies.get('m_pixel_ratio', '')}",
                f"wd={selected_cookies.get('wd', '')}",
                f"c_user={selected_cookies.get('c_user', '')}",
                f"fr={selected_cookies.get('fr', '')}",
                f"xs={selected_cookies.get('xs', '')}"
            ]
            account["cookies"] = "; ".join(ordered_cookies).strip("; ")
            print(f"Successfully logged in: {account['login']}")
            return account

        except Exception as e:
            print(f"Error during login for {account['login']}: {e}")
            return None

    finally:
        driver.quit()  # Close the browser


def main():
    """Main function to manage the login process."""

    # Read account data from the JSON file
    with open('accounts.json') as f:
        accounts = json.load(f)

    successful_logins = []

    for account in accounts:
        # Change IP before login
        new_ip = get_new_ip()
        if new_ip:
            print("IP successfully changed")

        # Attempt to log in to Facebook
        result = login_facebook(account)
        if result:
            successful_logins.append({
                "login": account["login"],
                "password": account["password"],
                "proxy": account.get("proxy", "No proxy provided"),  # Add proxy from accounts.json
                "cookies": result["cookies"]  # Use formatted cookies
            })

    # Save successful logins to a JSON file
    with open('successful_logins.json', 'w') as f:
        json.dump(successful_logins, f, indent=4)

    # Output message indicating the process completion
    print("Login process completed. Check 'successful_logins.json' for results.")


if __name__ == "__main__":
    main()

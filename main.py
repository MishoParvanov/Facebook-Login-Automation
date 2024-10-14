from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def change_ip():
    """Change IP address using the provided API."""
    try:
        response = requests.get(
            "https://api.ltesocks.io/v2/port/reset/395bc511ccd51db8de4b778aa5c011560f8abd6a75e48e33a80ce4911f039576"
        )
        if response.status_code == 202:
            print("IP address successfully changed.")
            return True  # Return True if IP change is successful
        else:
            print(f"Failed to change IP address. Status code: {response.status_code}")
            return False  # Return False if IP change fails
    except Exception as e:
        print(f"Error while changing IP: {e}")
        return False  # Return False if there's an exception


def login_facebook(account):
    """Log in to Facebook using provided account credentials."""
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")  # Open browser in incognito mode
    options.add_argument("--disable-cache")  # Disable caching
    options.add_argument("--disable-application-cache")  # Disable application cache
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
        "like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )  # Set user agent

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://www.facebook.com")  # Navigate to Facebook

    try:
        time.sleep(1)  # Wait for the page to load

        # Attempt to accept cookies
        try:
            cookie_accept_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept All Cookies']"))
            )
            cookie_accept_button.click()
        except Exception:
            pass  # Ignore if no button is found

        # Fill in email and password
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
        time.sleep(2)  # Wait for the button to be clickable
        driver.execute_script("arguments[0].click();", login_button)  # Click the login button

        time.sleep(3)  # Wait for the login process to complete

        # Check for login success or failure
        try:
            error_message = driver.find_elements(By.XPATH, "//div[@class='_9ay7']")
            yes_continue_button = driver.find_elements(By.XPATH, "//button[text()='Yes, Continue']")
            login_as_message = driver.find_elements(By.XPATH, "//span[contains(text(), 'Log in as')]")
            facebook_message = driver.find_elements(By.XPATH, "//span[contains(text(), 'facebook')]")

            if error_message or yes_continue_button or login_as_message or facebook_message:
                print(f"Login failed for {account['login']}: Incorrect email or password.")
                return None  # Return None if login fails

            # Collect cookies
            selected_cookies = {}
            all_cookies = driver.get_cookies()
            for cookie in all_cookies:
                if cookie['name'] in ['datr', 'sb', 'm_pixel_ratio', 'wd', 'c_user', 'fr', 'xs']:
                    selected_cookies[cookie['name']] = cookie['value']

            # Order cookies for the output
            ordered_cookies = [
                f"datr={selected_cookies.get('datr', '')}",
                f"sb={selected_cookies.get('sb', '')}",
                f"m_pixel_ratio={selected_cookies.get('m_pixel_ratio', '')}",
                f"wd={selected_cookies.get('wd', '')}",
                f"c_user={selected_cookies.get('c_user', '')}",
                f"fr={selected_cookies.get('fr', '')}",
                f"xs={selected_cookies.get('xs', '')}"
            ]
            account["cookies"] = "; ".join(ordered_cookies).strip("; ")  # Store cookies in the account

            # Record the actual proxy used
            account["proxy"] = driver.command_executor._url  # Get the actual proxy used
            print(f"Successfully logged in: {account['login']}")
            return account  # Return account with cookies and proxy

        except Exception as e:
            print(f"Error during login for {account['login']}: {e}")
            return None  # Return None if an error occurs

    finally:
        driver.quit()  # Ensure the driver quits after use


def main():
    """Main function to manage the login process."""
    # Check if IP change was successful
    if not change_ip():
        print("Exiting program due to IP change failure.")
        return

    # Load accounts from the JSON file
    with open('accounts.json') as f:
        accounts = json.load(f)

    successful_logins = []  # List to hold successful logins

    # Iterate through accounts and attempt to log in
    for account in accounts:
        result = login_facebook(account)
        if result:  # If login is successful
            successful_logins.append({
                "login": account["login"],
                "password": account["password"],
                "proxy": result["proxy"],  # Use actual proxy from successful login
                "cookies": result["cookies"]
            })

    # Save successful logins to JSON file
    with open('successful_logins.json', 'w') as f:
        json.dump(successful_logins, f, indent=4)

    print("Login process completed. Check 'successful_logins.json' for results.")


if __name__ == "__main__":
    main()  # Run the main function

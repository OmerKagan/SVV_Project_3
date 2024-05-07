import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CustomTestRunner(unittest.TextTestRunner):
    def run(self, test):
        result = super().run(test)
        if result.wasSuccessful():
            print("All test cases are passed.")


class TestLoginPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize the WebDriver
        cls.driver = webdriver.Chrome()
        cls.driver.get("http://127.0.0.1:5000/login")

    @classmethod
    def tearDownClass(cls):
        # Close the WebDriver after all tests are completed
        cls.driver.quit()

    def test_login_successful_redirect(self):
        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")

        email_input.send_keys("user1@login.com")
        password_input.send_keys("password1")

        login_button.click()

        WebDriverWait(self.driver, 10).until(EC.url_to_be("http://127.0.0.1:5000/entry-page"))
        self.assertEqual(self.driver.current_url, "http://127.0.0.1:5000/entry-page", "User login unsuccessful")

        logout_link = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "logout-link"))
        )
        logout_link.click()

    def test_login_incorrect_credentials(self):
        email_input = self.driver.find_element(By.NAME, "email")
        password_input = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")

        email_input.send_keys("invalid_user@login.com")
        password_input.send_keys("invalid_password")

        login_button.click()

        error_message = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "alertContainer"))
        )
        self.assertIn("Invalid email or password!", error_message.text, "Error message not displayed for invalid credentials")

    def test_login_empty_credentials(self):
        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")

        login_button.click()

        error_message = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "alertContainer"))
        )
        self.assertIn("Empty email or password!", error_message.text, "Error message not displayed for empty input")

    def test_login_with_google(self):
        google_login_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login with Google')]"))
        )

        google_login_button.click()

        WebDriverWait(self.driver, 10).until(EC.url_contains("accounts.google.com"))
        self.assertIn("accounts.google.com", self.driver.current_url, "Google Authentication Page not opened")


class TestNearestSeaDistance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize the WebDriver
        cls.driver = webdriver.Chrome()
        cls.driver.get("http://127.0.0.1:5000/sea")

    @classmethod
    def tearDownClass(cls):
        # Close the WebDriver after all tests are completed
        cls.driver.quit()

    def test_gps_coordinates_retrieved(self):
        location_button = self.driver.find_element(By.CLASS_NAME, "location-button")
        location_button.click()

        location_info_element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "location-info"))
        )

        self.assertNotEqual(location_info_element.text, "", "GPS coordinates not retrieved")

    def test_distance_to_nearest_sea(self):
        location_button = self.driver.find_element(By.CLASS_NAME, "location-button")
        location_button.click()

        nearest_sea_element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "nearest_sea"))
        )
        distance_to_sea_element = self.driver.find_element(By.ID, "distance_to_sea")

        nearest_sea = nearest_sea_element.text
        distance_to_sea_text = distance_to_sea_element.text
        distance_value = float(distance_to_sea_text.split()[0])  # Extract distance value as float

        self.assertNotEqual(nearest_sea, "", "Nearest sea name not displayed")

        self.assertTrue(distance_value >= 0, "Invalid distance value displayed")


class TestSunCoreDistance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize the WebDriver
        cls.driver = webdriver.Chrome()
        cls.driver.get("http://127.0.0.1:5000/sun")

    @classmethod
    def tearDownClass(cls):
        # Close the WebDriver after all tests are completed
        cls.driver.quit()

    def test_gps_or_manual_coordinates(self):
        location_button = self.driver.find_element(By.CLASS_NAME, "location-button")
        location_button.click()

        location_info_element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "location-info"))
        )

        self.assertNotEqual(location_info_element.text, "", "GPS coordinates not retrieved")

        latitude_input = self.driver.find_element(By.ID, "latitude-input")
        longitude_input = self.driver.find_element(By.ID, "longitude-input")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "form#manual-location-form button[type='submit']")

        latitude_input.send_keys("37.7749")
        longitude_input.send_keys("-122.4194")
        submit_button.click()

        distance_to_sun_element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "distance_to_sun"))
        )

        self.assertNotEqual(distance_to_sun_element.text, "", "Distance to Sun's core not calculated")

    def test_distance_to_suns_core(self):
        test_coordinates = [
            (40.7128, -74.0060),  # New York City
            (51.5074, -0.1278),    # London
            (48.8566, 2.3522)      # Paris
        ]

        for latitude, longitude in test_coordinates:
            latitude_input = self.driver.find_element(By.ID, "latitude-input")
            longitude_input = self.driver.find_element(By.ID, "longitude-input")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "form#manual-location-form button[type='submit']")

            latitude_input.clear()
            latitude_input.send_keys(str(latitude))

            longitude_input.clear()
            longitude_input.send_keys(str(longitude))

            submit_button.click()

            distance_to_sun_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "distance_to_sun"))
            )

            self.assertNotEqual(distance_to_sun_element.text, "", "Distance to Sun's core not calculated")
            distance_value = float(distance_to_sun_element.text.split()[0])
            self.assertTrue(distance_value >= 0, "Invalid distance value displayed")

if __name__ == '__main__':
    test_login = unittest.TestLoader().loadTestsFromTestCase(TestLoginPage)
    test_sea = unittest.TestLoader().loadTestsFromTestCase(TestNearestSeaDistance)
    test_sun = unittest.TestLoader().loadTestsFromTestCase(TestSunCoreDistance)

    runner = CustomTestRunner()

    runner.run(test_login)
    runner.run(test_sea)
    runner.run(test_sun)
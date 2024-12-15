from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random

class InstagramBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()
        self.followed_count = 0
        self.max_follows = 200

    def login(self):
        try:
            self.driver.get('https://www.instagram.com/')

            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_input = self.driver.find_element(By.NAME, "password")

            username_input.send_keys(self.username)
            password_input.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            time.sleep(3)
            login_button.click()

            time.sleep(5)
            return True
        except Exception as e:
            print(f"ログインエラー: {str(e)}")
            return False

    def check_profile_criteria(self, bio):
        criteria = ['23s', '23m', '23p', '23a', '23h']
        return any(c in bio.lower() for c in criteria)

    def process_followers(self, target_profile):
        try:
            # まずプロフィールページに遷移
            self.driver.get(f'https://www.instagram.com/{target_profile}/')

            # フォロワーリンクを探してクリック
            followers_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.x5n08af.x9n4tj2._a6hd"))
            )
            followers_link.click()

            #  # フォロー状態を確認
            # try:
            #     follow_button = WebDriverWait(self.driver, 5).until(
            #         EC.presence_of_element_located((By.CSS_SELECTOR, "button._acan._acap._acas"))
            #     )
            #     if follow_button.text not in ["フォロー", "Follow"]:
            #         print(f"{target_profile}はすでにフォロー済みです")
            #         return
            # except Exception as e:
            #     print(f"フォロー状態の確認に失敗: {str(e)}")
            #     return

            # フォロワーリストのダイアログを取得
            followers_dialog = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )

            last_height = self.driver.execute_script("return arguments[0].scrollHeight", followers_dialog)
            processed_hrefs = set()

            while self.followed_count < self.max_follows:
                # フォロワーの要素を取得
                follower_links = followers_dialog.find_elements(By.CSS_SELECTOR, "a[role='link']")
                
                for link in follower_links:
                    if self.followed_count >= self.max_follows:
                        return

                    try:
                        href = link.get_attribute('href')
                        if not href or href in processed_hrefs:
                            continue

                        processed_hrefs.add(href)
                        
                        # 新しいタブでプロフィールを開く
                        self.driver.execute_script("window.open('');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.get(href)

                        try:
                            # フォローボタンの状態を確認
                            follow_button = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "button._acan._acap._acas"))
                            )
                            
                            # フォローボタンのテキストが"フォロー"または"Follow"の場合のみ処理を続行
                            if follow_button.text in ["フォロー", "Follow"]:
                                # プロフィールのbioを取得
                                bio = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "._aa_c"))
                                ).text

                                if self.check_profile_criteria(bio):
                                    follow_button.click()
                                    self.followed_count += 1
                                    print(f"フォロー完了: {self.followed_count}人目 - {href}")
                            else:
                                print(f"すでにフォロー済み: {href}")

                        except Exception as e:
                            print(f"プロフィール処理エラー: {str(e)}")

                        # タブを閉じて元のタブに戻る
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

                    except Exception as e:
                        print(f"フォロワー処理エラー: {str(e)}")
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                        continue

                # スクロール
                self.driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight;',
                    followers_dialog
                )
                time.sleep(2)

                new_height = self.driver.execute_script("return arguments[0].scrollHeight", followers_dialog)
                if new_height == last_height:
                    break
                last_height = new_height

        except Exception as e:
            print(f"全体的なエラー: {str(e)}")

    def close_browser(self):
        self.driver.quit()

def main():
    bot = InstagramBot('@engineering_takumi', 'kusaka0914')
    
    try:
        if bot.login():
            target_profile = 'hori_hitoo'  # 対象のプロフィール名
            bot.process_followers(target_profile)
            print(f"合計フォロー数: {bot.followed_count}")
    finally:
        bot.close_browser()

if __name__ == "__main__":
    main()
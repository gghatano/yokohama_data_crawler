from selenium.webdriver.common.by import By
import time
import pandas as pd
from datetime import datetime
import re
from selenium import webdriver


# Chromeドライバーの設定
## ヘッドレスモードを有効化
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument("--headless")  # 必須: ヘッドレスモード
chrome_options.add_argument("--no-sandbox")  # サーバー環境用
chrome_options.add_argument("--disable-dev-shm-usage")  # 共有メモリの問題回避
chrome_options.add_argument("--disable-gpu")  # GPU無効化（古い環境向け）
chrome_options.add_argument("--window-size=1920x1080")  # ウィンドウサイズ指定（省略可）

## ChromeServiceの作成とログ設定
from selenium.webdriver.chrome.service import Service
current_date = datetime.now().strftime("%Y%m%d")
service = Service(log_path="./log/"+current_date+"_selenium.log")
# おわり


## ドライバーの初期化
driver = webdriver.Chrome(service=service, options=chrome_options)

# ページにアクセス
url = "https://nsddd.com/web/735498669426/proposalrequest/list/view?init"
driver.get(url)

# すべてのページからデータを収集
all_data = []

# ページ巡回
while True:
    # 表の行データ取得
    rows = driver.find_elements(By.TAG_NAME, "tr")

    # データを抽出
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        col_text = [col.text.strip().replace("\u2003", "") for col in cols]
        if any(col_text):  # 空でない行だけを追加
            all_data.append(col_text)

    # 次ページボタンの検出とクリック
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a[data-dt-idx='next']")

        # 無効なボタン検出 (`aria-disabled="true"` も確認)
        if "disabled" in next_button.get_attribute("class") or next_button.get_attribute("aria-disabled") == "true":
            print("最後のページに到達しました。")
            break
        
        # 次のページへ進む
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(3)  # ページ読み込み待機時間
    except Exception as e:
        print(f"エラー: {e}")
        break

# 募集期間の解析関数
def parse_period(period_text):
    match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2})～(\d{4}/\d{2}/\d{2} \d{2}:\d{2})(.*)", period_text)
    if match:
        start_date, end_date, status = match.groups()
        return start_date, end_date, status.strip()
    return None, None, None

# データフレームの作成
parsed_data = []
for row in all_data:
    start_date, end_date, status = parse_period(row[2])
    parsed_data.append([row[0], row[1], start_date, end_date, status, row[3]])

df = pd.DataFrame(parsed_data, columns=['部局名', '提案名', '募集開始', '募集終了', '募集状態', '公開日'])

# CSVファイルへの保存
file_name = f"{current_date}_横浜市提案募集.csv"
df.to_csv("./data/"+file_name, index=False, encoding='utf-8-sig')

print(f"ファイル {file_name} を作成しました。")

# ブラウザを閉じる
driver.quit()


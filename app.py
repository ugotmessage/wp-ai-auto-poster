import os, re, json, random, time, requests, logging
from urllib.parse import quote
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# === 環境變數 ===
WP_URL        = os.getenv("WP_URL")
WP_USER       = os.getenv("WP_USER")
WP_PASS       = os.getenv("WP_APP_PASS")
BRAND         = os.getenv("BRAND_NAME", "品牌名稱")
SITE_NAME     = os.getenv("SITE_NAME", "example.com")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID  = os.getenv("GOOGLE_CSE_ID")
GENAI_MODEL    = os.getenv("GENAI_MODEL", "gemini-2.5-flash")
CATEGORY_ID    = int(os.getenv("CATEGORY_ID", "0"))

KEYWORDS  = [k.strip() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()]
TAGS_BASE = [t.strip() for t in os.getenv("TAGS", "").split(",") if t.strip()]
POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "1"))

# === SEO 設定 ===
SEO_BRAND_SUFFIX = os.getenv("SEO_BRAND_SUFFIX", "｜健康誌")
DEFAULT_SEO_KEYWORDS = [k.strip() for k in os.getenv("DEFAULT_SEO_KEYWORDS", "").split(",") if k.strip()]

# === 測試模式 ===
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

USED_FILE = "used_refs.json"
LOG_FILE = "wp_article_generator.log"
TEST_OUTPUT_DIR = "test_output"

# === Google API URLs ===
GENAI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GENAI_MODEL}:generateContent"
CSE_URL   = "https://www.googleapis.com/customsearch/v1"

# === 日誌設定 ===
def setup_logging():
    """設定日誌記錄"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()  # 同時輸出到控制台
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ---------------------------------------------------------------
# SEO 解析工具
# ---------------------------------------------------------------
def parse_gemini_output(text):
    """解析 Gemini 輸出，提取 SEO metadata 和文章內容"""
    try:
        # 提取 SEO 標題
        seo_title = extract_between(text, "SEO_TITLE:", "SEO_DESC:")
        if not seo_title:
            seo_title = extract_after(text, "SEO_TITLE:")
        
        # 提取 SEO 描述
        seo_desc = extract_between(text, "SEO_DESC:", "SEO_KEYWORD:")
        if not seo_desc:
            seo_desc = extract_after(text, "SEO_DESC:")
        
        # 提取 SEO 關鍵字
        seo_keyword = extract_between(text, "SEO_KEYWORD:", "ARTICLE:")
        if not seo_keyword:
            seo_keyword = extract_after(text, "SEO_KEYWORD:")
        
        # 提取文章內容
        article = extract_after(text, "ARTICLE:")
        
        # 清理文字
        seo_title = seo_title.strip() if seo_title else ""
        seo_desc = seo_desc.strip() if seo_desc else ""
        seo_keyword = seo_keyword.strip() if seo_keyword else ""
        article = article.strip() if article else ""
        
        # 強制移除所有連結
        article = remove_all_links(article)
        
        logger.info(f"解析 SEO 資料 - 標題: {seo_title[:50]}..., 描述: {seo_desc[:50]}..., 關鍵字: {seo_keyword}")
        
        return seo_title, seo_desc, seo_keyword, article
        
    except Exception as e:
        logger.error(f"解析 Gemini 輸出失敗: {e}")
        return "", "", "", ""

def extract_between(text, start_marker, end_marker):
    """提取兩個標記之間的文字"""
    try:
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        start_idx += len(start_marker)
        
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return text[start_idx:].strip()
        
        return text[start_idx:end_idx].strip()
    except:
        return ""

def extract_after(text, marker):
    """提取標記之後的文字"""
    try:
        idx = text.find(marker)
        if idx == -1:
            return ""
        return text[idx + len(marker):].strip()
    except:
        return ""

def remove_all_links(text):
    """移除所有 HTML 連結標籤、參考資料區塊和 URL"""
    # 移除所有 <a> 標籤及其內容
    text = re.sub(r'<a\s+[^>]*>.*?</a>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除參考資料區塊
    text = re.sub(r'<h[23]>\s*參考資料</h[23]>.*?</ul>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h[23]>\s*資料來源</h[23]>.*?</ul>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h[23]>\s*參考連結</h[23]>.*?</ul>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除帶協議的 URL（http:// 或 https://）
    text = re.sub(r'https?://[^\s<>"{}|\\^`\[\]]+', '', text)
    
    # 移除純文字網址（xxx.com、xxx.org、xxx.info、xxx.net 等）
    # 只匹配常見的頂級域名，避免誤刪
    text = re.sub(r'\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\.(?:com|org|net|info|edu|gov|io|co|tech|app|site|online|store|shop|htapp)\b', '', text, flags=re.IGNORECASE)
    
    return text

# ---------------------------------------------------------------
# 工具
# ---------------------------------------------------------------
def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\-一-龥]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:90]

def load_used_refs():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, "r") as f:
            return json.load(f).get("used_urls", [])
    return []

def save_used_refs(urls):
    with open(USED_FILE, "w") as f:
        json.dump({"used_urls": urls}, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------
# Google Custom Search：取得新參考連結
# ---------------------------------------------------------------
def get_reference_links(keyword, used_list, num_results=5):
    """搜尋 Google Custom Search 取得參考連結"""
    logger.info(f"搜尋參考連結，關鍵字: {keyword}")
    
    params = {
        "q": keyword,
        "cx": GOOGLE_CSE_ID,
        "key": GOOGLE_API_KEY,
        "num": num_results,
        "hl": "zh-TW"
    }
    
    try:
        r = requests.get(CSE_URL, params=params, timeout=20)
        
        if r.status_code != 200:
            logger.error(f"Google Custom Search API 請求失敗，狀態碼: {r.status_code}")
            logger.error(f"回應內容: {r.text}")
            return []
            
        response_data = r.json()
        items = response_data.get("items", [])
        
        logger.info(f"找到 {len(items)} 個搜尋結果")
        
        new_links = []
        for item in items:
            link = item.get("link")
            if link and link not in used_list:
                new_links.append(link)
                logger.debug(f"新增參考連結: {link}")
            elif link in used_list:
                logger.debug(f"跳過已使用的連結: {link}")
                
        logger.info(f"篩選後得到 {len(new_links)} 個新連結")
        return new_links[:2]
        
    except requests.exceptions.Timeout:
        logger.error("Google Custom Search API 請求超時")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Custom Search API 請求失敗: {e}")
        return []
    except Exception as e:
        logger.error(f"搜尋參考連結時發生未知錯誤: {e}")
        return []

# ---------------------------------------------------------------
# Gemini 產文
# ---------------------------------------------------------------
def gemini_generate_article(keyword, brand, site_name):
    """使用 Gemini AI 生成文章，包含詳細的錯誤處理和日誌記錄"""
    logger.info(f"開始生成文章，關鍵字: {keyword}")
    
    prompt = f"""
主題：{keyword}

請生成以下四個部分（繁體中文）：
1. SEO 標題（70 字內）
2. SEO 描述（150 字內）
3. 焦點關鍵字（1~3 個）
4. 文章內容（HTML 格式）

條件：
- 文章開頭或結尾自然出現一次品牌「{brand}」與站名「{site_name}」
- HTML格式，含<h2>/<h3>/<p>段落
- **嚴格禁止**：不使用任何 <a href> 連結標籤
- **嚴格禁止**：不使用任何 <h3>參考資料</h3> 或 <h2>參考資料</h2> 區塊
- **嚴格禁止**：不使用任何 <ul><li> 連結列表
- **嚴格禁止**：不使用任何外部 URL 連結
- **嚴格禁止**：不使用任何來源註釋或參考註解
- 文章內容應為純粹的獨立的知識分享，僅使用 <p>, <h2>, <h3>, <strong>, <em> 等基本標籤

輸出格式如下：
---
SEO_TITLE: [SEO 標題，70字內，必須以「{SEO_BRAND_SUFFIX}」結尾]
SEO_DESC: [SEO 描述，150字內，吸引點擊]
SEO_KEYWORD: [焦點關鍵字，1-3個，用逗號分隔]
---
ARTICLE:
[文章內容，HTML格式，800-1200字，純粹的知識分享內容，嚴格禁止任何連結或參考資料]
"""
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-goog-api-key": GOOGLE_API_KEY
    }
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        logger.info(f"發送請求到 Gemini API，URL: {GENAI_URL}")
        r = requests.post(GENAI_URL, headers=headers, json=body, timeout=120)
        
        # 檢查 HTTP 狀態碼
        if r.status_code != 200:
            logger.error(f"Gemini API 請求失敗，狀態碼: {r.status_code}")
            logger.error(f"回應內容: {r.text}")
            return None
            
        response_data = r.json()
        logger.info("Gemini API 請求成功")
        
        # 檢查回應結構
        if "candidates" not in response_data or not response_data["candidates"]:
            logger.error(f"Gemini API 回應格式異常: {response_data}")
            return None
            
        candidate = response_data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"]:
            logger.error(f"Gemini API 候選回應格式異常: {candidate}")
            return None
            
        text = candidate["content"]["parts"][0]["text"]
        logger.info(f"收到 Gemini 回應，長度: {len(text)} 字元")
        
    except UnicodeEncodeError as e:
        logger.error(f"編碼錯誤: {e}")
        logger.error(f"檢查環境變數是否包含非 ASCII 字元")
        logger.error(f"BRAND: {repr(brand)}")
        logger.error(f"SITE_NAME: {repr(site_name)}")
        logger.error(f"KEYWORD: {repr(keyword)}")
        return None
    except requests.exceptions.Timeout:
        logger.error("Gemini API 請求超時")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API 請求失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini API 請求發生未知錯誤: {e}")
        return None

    # 使用新的解析器處理 Gemini 回應
    try:
        # 清理 markdown 程式碼區塊標記
        cleaned_text = text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]  # 移除 ```json
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]   # 移除 ```
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]  # 移除結尾的 ```
        
        cleaned_text = cleaned_text.strip()
        logger.info(f"清理後的文字長度: {len(cleaned_text)} 字元")
        
        # 使用新的解析器
        seo_title, seo_desc, seo_keyword, article = parse_gemini_output(cleaned_text)
        
        # 驗證必要欄位
        if not seo_title or not article:
            logger.error(f"Gemini 回應缺少必要欄位 - 標題: {bool(seo_title)}, 內容: {bool(article)}")
            logger.error(f"原始回應: {cleaned_text[:500]}...")
            return None
            
        # 檢查內容品質
        if len(article) < 100:
            logger.warning(f"生成內容過短: {len(article)} 字元")
        
        # 如果 SEO 描述為空，使用預設
        if not seo_desc:
            seo_desc = f"{keyword} 健康懶人包 - {SEO_BRAND_SUFFIX}"
            logger.warning("使用預設 SEO 描述")
        
        # 如果 SEO 關鍵字為空，使用預設
        if not seo_keyword:
            seo_keyword = ",".join(DEFAULT_SEO_KEYWORDS[:3])
            logger.warning("使用預設 SEO 關鍵字")
        
        # 驗證和修正 SEO 標題
        if not seo_title.endswith(SEO_BRAND_SUFFIX):
            seo_title = f"{seo_title}{SEO_BRAND_SUFFIX}"
            logger.info(f"已為標題加入品牌後綴: {seo_title}")
        
        # 組合文章內容
        content_html = assemble_html(article, brand, site_name, TAGS_BASE)
        
        # 建立回傳物件
        obj = {
            "seo_title": seo_title,
            "meta_desc": seo_desc,
            "content": content_html,
            "tags": DEFAULT_SEO_KEYWORDS,
            "focus_keyword": seo_keyword
        }
            
        logger.info(f"文章生成成功 - 標題: {seo_title[:50]}...")
        
    except Exception as e:
        logger.error(f"處理 Gemini 回應時發生錯誤: {e}")
        logger.error(f"原始回應: {text[:500]}...")
        return None

    return obj

# ---------------------------------------------------------------
# WordPress 工具
# ---------------------------------------------------------------
def get_wp_tags():
    """從 WordPress 獲取現有標籤列表"""
    try:
        tags_url = WP_URL.replace('/posts', '/tags')
        logger.info(f"獲取 WordPress 標籤列表: {tags_url}")
        
        r = requests.get(tags_url, auth=(WP_USER, WP_PASS), timeout=15)
        
        if r.status_code == 200:
            tags_data = r.json()
            tags = [tag['name'] for tag in tags_data if tag.get('name')]
            logger.info(f"成功獲取 {len(tags)} 個 WordPress 標籤: {tags[:5]}...")
            return tags
        else:
            logger.warning(f"獲取 WordPress 標籤失敗，狀態碼: {r.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        logger.error("獲取 WordPress 標籤超時")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"獲取 WordPress 標籤失敗: {e}")
        return []
    except Exception as e:
        logger.error(f"獲取 WordPress 標籤時發生未知錯誤: {e}")
        return []

def wp_post_exists_by_slug(slug):
    search_url = WP_URL + f"?search={quote(slug)}&per_page=3"
    r = requests.get(search_url, auth=(WP_USER, WP_PASS), timeout=15)
    if r.status_code != 200:
        return False
    for item in r.json():
        if item.get("slug") == slug:
            return True
    return False

def safe_publish_to_wp(title, content_html, meta_desc, slug, focus_keyword=""):
    """安全發送文章至 WordPress，偵測 Yoast 欄位封鎖後自動重試"""
    logger.info(f"準備發佈文章到 WordPress: {title}")
    
    # 建立基本 payload
    payload = {
        "title": title,
        "content": content_html,
        "status": "publish",
        "slug": slug,
        "excerpt": meta_desc[:150]
    }
    
    # 加入分類
    if CATEGORY_ID > 0:
        payload["categories"] = [CATEGORY_ID]
        logger.info(f"指定分類 ID: {CATEGORY_ID}")
    
    # 加入 Yoast SEO meta 欄位
    meta_fields = {
        "_yoast_wpseo_title": title,
        "_yoast_wpseo_metadesc": meta_desc
    }
    
    if focus_keyword:
        meta_fields["_yoast_wpseo_focuskw"] = focus_keyword
    
    payload["meta"] = meta_fields
    
    try:
        logger.info("嘗試發送包含 Yoast SEO meta 欄位的文章...")
        r = requests.post(WP_URL, auth=(WP_USER, WP_PASS), json=payload, timeout=60)
        
        # 檢查是否為 403 錯誤且與 meta 欄位相關
        if r.status_code == 403 and ("meta" in r.text.lower() or "forbidden" in r.text.lower()):
            logger.warning("⚠️ Yoast SEO 欄位未開啟，跳過 meta 欄位重新發送...")
            
            # 移除 meta 欄位重新發送
            payload.pop("meta", None)
            r = requests.post(WP_URL, auth=(WP_USER, WP_PASS), json=payload, timeout=60)
            
            if r.status_code == 201:
                logger.info(f"✅ WordPress 發佈成功（無 meta 欄位）: {title}")
                logger.info(f"文章 URL: {r.json().get('link', 'N/A')}")
                return r.json()
            else:
                logger.error(f"❌ WordPress 發佈失敗（無 meta 欄位），狀態碼: {r.status_code}")
                logger.error(f"錯誤回應: {r.text}")
                return None
        
        elif r.status_code == 201:
            logger.info(f"✅ WordPress 發佈成功（含 meta 欄位）: {title}")
            logger.info(f"文章 URL: {r.json().get('link', 'N/A')}")
            return r.json()
        
        else:
            logger.error(f"❌ WordPress 發佈失敗，狀態碼: {r.status_code}")
            logger.error(f"錯誤回應: {r.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("WordPress API 請求超時")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"WordPress API 請求失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"發佈到 WordPress 時發生未知錯誤: {e}")
        return None

def wp_publish(title, content_html, meta_desc, slug):
    """向後相容的發佈函數"""
    return safe_publish_to_wp(title, content_html, meta_desc, slug)

# ---------------------------------------------------------------
# HTML 組合
# ---------------------------------------------------------------
def assemble_html(content_html, brand, site_name, tags):
    """組合文章 HTML，只加入標籤和品牌簽名"""
    
    tag_block = ""
    if tags:
        tag_block = "<p><em>標籤：</em>" + "、".join(tags) + "</p>"

    sig = f"<p style='color:#666;'>本文由 <strong>{brand}</strong> 提供，更多健康補充知識請見：<strong>{site_name}</strong></p>"
    
    # 組合完整的 HTML
    full_html = content_html + tag_block + sig
    
    # 最後一次移除所有可能的網址（包括簽名中的）
    full_html = remove_all_links(full_html)
    
    return full_html

# ---------------------------------------------------------------
# 測試模式工具
# ---------------------------------------------------------------
def check_for_links(html_content):
    """檢查 HTML 內容是否包含連結"""
    link_patterns = [
        (r'<a\s+[^>]*>.*?</a>', 'a 標籤'),
        (r'https?://[^\s<>"{}|\\^`\[\]]+', 'URL 連結'),
        (r'\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\.(?:com|org|net|info|edu|gov|io|co|tech|app|site|online|store|shop|htapp)\b', '純文字網址'),
        (r'<h[23]>\s*參考資料</h[23]>', '參考資料標題'),
        (r'<h[23]>\s*資料來源</h[23]>', '資料來源標題'),
        (r'<h[23]>\s*參考連結</h[23]>', '參考連結標題'),
    ]
    
    found = []
    for pattern, description in link_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            found.append((description, matches))
    
    return found

def save_test_output(keyword, obj):
    """保存測試輸出到本地文件"""
    if not os.path.exists(TEST_OUTPUT_DIR):
        os.makedirs(TEST_OUTPUT_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{TEST_OUTPUT_DIR}/test_{timestamp}_{keyword}.txt"
    
    # 檢查是否有連結
    links_found = check_for_links(obj["content"])
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"關鍵字: {keyword}\n")
        f.write(f"=" * 80 + "\n\n")
        
        f.write(f"SEO 標題: {obj['seo_title']}\n")
        f.write(f"SEO 描述: {obj['meta_desc']}\n")
        f.write(f"焦點關鍵字: {obj.get('focus_keyword', '')}\n")
        f.write(f"=" * 80 + "\n\n")
        
        if links_found:
            f.write("⚠️ 發現連結！\n")
            for desc, matches in links_found:
                f.write(f"  - {desc}: {len(matches)} 個\n")
                for match in matches[:3]:  # 只顯示前3個
                    f.write(f"    {match}\n")
            f.write(f"=" * 80 + "\n\n")
        else:
            f.write("✅ 沒有發現任何連結\n")
            f.write(f"=" * 80 + "\n\n")
        
        f.write("文章內容:\n")
        f.write(obj["content"])
    
    logger.info(f"測試輸出已保存到: {filename}")
    if links_found:
        logger.warning(f"⚠️ 發現連結: {links_found}")
    else:
        logger.info("✅ 文章內容乾淨，沒有任何連結")
    
    return filename

# ---------------------------------------------------------------
# 環境變數檢查
# ---------------------------------------------------------------
def check_env_vars():
    """檢查環境變數是否包含非 ASCII 字元"""
    env_vars = {
        "WP_URL": WP_URL,
        "WP_USER": WP_USER, 
        "WP_PASS": WP_PASS,
        "BRAND_NAME": BRAND,
        "SITE_NAME": SITE_NAME,
        "GOOGLE_API_KEY": GOOGLE_API_KEY,
        "GOOGLE_CSE_ID": GOOGLE_CSE_ID,
        "GENAI_MODEL": GENAI_MODEL
    }
    
    for name, value in env_vars.items():
        if value and not value.isascii():
            logger.warning(f"環境變數 {name} 包含非 ASCII 字元: {repr(value)}")
            logger.warning(f"這可能導致 HTTP 請求失敗")

# ---------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------
def main():
    """主程式流程，包含完整的錯誤處理和日誌記錄"""
    logger.info("=== WordPress 文章自動生成器開始執行 ===")
    
    if TEST_MODE:
        logger.info("🧪 測試模式已啟用 - 文章將保存到本地文件，不會推送到 WordPress")
    
    # 檢查環境變數
    check_env_vars()
    
    # 智能選擇關鍵字來源
    logger.info("🔍 檢查關鍵字來源...")
    
    wp_tags = []
    if not TEST_MODE:
        # 只在非測試模式下嘗試連接 WordPress
        wp_tags = get_wp_tags()
    
    if wp_tags:
        # 使用 WordPress 標籤作為關鍵字
        keywords_to_use = wp_tags
        logger.info(f"✅ 使用 WordPress 標籤作為關鍵字 ({len(keywords_to_use)} 個)")
    else:
        # 使用環境變數中的關鍵字
        keywords_to_use = KEYWORDS
        logger.info(f"✅ 使用環境變數關鍵字 ({len(keywords_to_use)} 個)")
    
    if not keywords_to_use:
        logger.error("❌ 沒有可用的關鍵字，程式結束")
        return
    
    random.shuffle(keywords_to_use)
    
    success_count = 0
    failure_count = 0
    
    for keyword in keywords_to_use[:POSTS_PER_DAY]:
        logger.info(f"開始處理主題: {keyword}")
        
        try:
            # 生成文章
            obj = gemini_generate_article(keyword, BRAND, SITE_NAME)
            
            # 檢查生成是否成功
            if obj is None:
                logger.error(f"文章生成失敗，跳過關鍵字: {keyword}")
                failure_count += 1
                continue
                
            # 驗證生成內容
            if not obj.get("seo_title") or not obj.get("content"):
                logger.error(f"生成內容不完整，跳過關鍵字: {keyword}")
                logger.error(f"生成物件: {obj}")
                failure_count += 1
                continue

            # 準備發佈內容
            seo_title = obj["seo_title"].strip()
            meta_desc = obj["meta_desc"].strip()
            content_html = obj["content"]  # 已經包含完整的文章內容
            focus_keyword = obj.get("focus_keyword", "")

            # 檢查標題是否過短
            if len(seo_title) < 10:
                logger.warning(f"標題過短: {seo_title}")

            # 測試模式：保存到本地文件
            if TEST_MODE:
                logger.info("🧪 測試模式：保存到本地文件")
                save_test_output(keyword, obj)
                success_count += 1
                logger.info(f"✅ 測試完成: {keyword}")
                continue
            
            # 生成唯一 slug
            slug = slugify(seo_title)
            tries = 0
            while wp_post_exists_by_slug(slug) and tries < 5:
                tries += 1
                slug = f"{slug}-{tries}"

            # 發佈到 WordPress（使用新的安全發佈函數）
            logger.info(f"準備發佈文章: {seo_title}")
            result = safe_publish_to_wp(
                seo_title, 
                content_html, 
                meta_desc, 
                slug, 
                focus_keyword
            )
            
            if result:
                success_count += 1
                logger.info(f"✅ 成功處理關鍵字: {keyword}")
            else:
                failure_count += 1
                logger.error(f"❌ 發佈失敗，跳過關鍵字: {keyword}")
                continue
            
        except Exception as e:
            logger.error(f"處理關鍵字 {keyword} 時發生錯誤: {e}")
            failure_count += 1
            
        # 等待一下再處理下一個
        time.sleep(5)
    
    # 總結報告
    logger.info(f"=== 執行完成 ===")
    logger.info(f"成功: {success_count} 篇")
    logger.info(f"失敗: {failure_count} 篇")
    
    if failure_count > 0:
        logger.warning(f"有 {failure_count} 個關鍵字處理失敗，請檢查日誌檔案: {LOG_FILE}")

if __name__ == "__main__":
    main()

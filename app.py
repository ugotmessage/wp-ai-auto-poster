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

USED_FILE = "used_refs.json"
LOG_FILE = "wp_article_generator.log"

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
def gemini_generate_article(keyword, brand, site_name, refs):
    """使用 Gemini AI 生成文章，包含詳細的錯誤處理和日誌記錄"""
    logger.info(f"開始生成文章，關鍵字: {keyword}")
    
    refs_text = "\n".join(f"- {r}" for r in refs) if refs else "（無特定參考連結）"
    prompt = f"""
請以生活化保健專欄風格撰寫一篇約800～1200字的文章。
主題：「{keyword}」
條件：
- 文章開頭或結尾自然出現一次品牌「{brand}」與站名「{site_name}」
- HTML格式，含<h2>/<h3>/<p>段落。
- 在文末附上參考資料清單：
{refs_text}

輸出格式（純JSON）：
{{
  "seo_title": "...",
  "meta_desc": "...",
  "content": "...",      # HTML
  "tags": ["...", "..."],
  "references": [{refs_text}]
}}
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

    # 嘗試剖析 JSON
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
        logger.info(f"清理後的 JSON 長度: {len(cleaned_text)} 字元")
        
        obj = json.loads(cleaned_text)
        logger.info("成功解析 Gemini 回應 JSON")
        
        # 驗證必要欄位
        required_fields = ["seo_title", "meta_desc", "content"]
        missing_fields = [field for field in required_fields if not obj.get(field)]
        
        if missing_fields:
            logger.error(f"Gemini 回應缺少必要欄位: {missing_fields}")
            logger.error(f"完整回應: {obj}")
            return None
            
        # 檢查內容品質
        if len(obj.get("content", "")) < 100:
            logger.warning(f"生成內容過短: {len(obj.get('content', ''))} 字元")
            
        logger.info(f"文章生成成功 - 標題: {obj.get('seo_title', 'N/A')}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失敗: {e}")
        logger.error(f"原始回應: {text[:500]}...")
        return None
    except Exception as e:
        logger.error(f"處理 Gemini 回應時發生錯誤: {e}")
        return None

    # 過濾重複連結
    obj["references"] = [r for r in obj.get("references", []) if r.startswith("http")]
    return obj

# ---------------------------------------------------------------
# WordPress 工具
# ---------------------------------------------------------------
def wp_post_exists_by_slug(slug):
    search_url = WP_URL + f"?search={quote(slug)}&per_page=3"
    r = requests.get(search_url, auth=(WP_USER, WP_PASS), timeout=15)
    if r.status_code != 200:
        return False
    for item in r.json():
        if item.get("slug") == slug:
            return True
    return False

def wp_publish(title, content_html, meta_desc, slug):
    """發佈文章到 WordPress"""
    logger.info(f"準備發佈文章到 WordPress: {title}")
    
    payload = {
        "title": title,
        "content": content_html,
        "status": "publish",
        "slug": slug,
        "excerpt": meta_desc[:150],
        "meta": {
            "_yoast_wpseo_title": title,
            "_yoast_wpseo_metadesc": meta_desc
        }
    }
    if CATEGORY_ID > 0:
        payload["categories"] = [CATEGORY_ID]
        logger.info(f"指定分類 ID: {CATEGORY_ID}")

    try:
        r = requests.post(WP_URL, auth=(WP_USER, WP_PASS), json=payload, timeout=60)
        
        if r.status_code == 201:
            logger.info(f"✅ WordPress 發佈成功: {title}")
            logger.info(f"文章 URL: {r.json().get('link', 'N/A')}")
        else:
            logger.error(f"❌ WordPress 發佈失敗，狀態碼: {r.status_code}")
            logger.error(f"錯誤回應: {r.text}")
            
    except requests.exceptions.Timeout:
        logger.error("WordPress API 請求超時")
    except requests.exceptions.RequestException as e:
        logger.error(f"WordPress API 請求失敗: {e}")
    except Exception as e:
        logger.error(f"發佈到 WordPress 時發生未知錯誤: {e}")

# ---------------------------------------------------------------
# HTML 組合
# ---------------------------------------------------------------
def assemble_html(content_html, refs, brand, site_name, tags):
    ref_block = ""
    if refs:
        lis = "".join(f'<li><a href="{r}" target="_blank" rel="nofollow noopener">{r}</a></li>' for r in refs)
        ref_block = f"<hr><h3>參考資料</h3><ul>{lis}</ul>"

    tag_block = ""
    if tags:
        tag_block = "<p><em>標籤：</em>" + "、".join(tags) + "</p>"

    sig = f"<p style='color:#666;'>本文由 <strong>{brand}</strong> 提供，更多健康補充知識請見：<strong>{site_name}</strong></p>"
    return content_html + ref_block + tag_block + sig

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
    
    # 檢查環境變數
    check_env_vars()
    
    used_refs = load_used_refs()
    random.shuffle(KEYWORDS)
    
    success_count = 0
    failure_count = 0
    
    for keyword in KEYWORDS[:POSTS_PER_DAY]:
        logger.info(f"開始處理主題: {keyword}")
        
        try:
            # 搜尋參考連結
            refs = get_reference_links(keyword, used_refs)
            if not refs:
                logger.warning(f"沒找到新連結，改用空參考")
            else:
                used_refs.extend(refs)
                save_used_refs(used_refs)
                logger.info(f"找到 {len(refs)} 個新參考連結")

            # 生成文章
            obj = gemini_generate_article(keyword, BRAND, SITE_NAME, refs)
            
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
            content_html = assemble_html(obj["content"], obj["references"], BRAND, SITE_NAME, TAGS_BASE + obj["tags"])

            # 檢查標題是否過短
            if len(seo_title) < 10:
                logger.warning(f"標題過短: {seo_title}")

            # 生成唯一 slug
            slug = slugify(seo_title)
            tries = 0
            while wp_post_exists_by_slug(slug) and tries < 5:
                tries += 1
                slug = f"{slug}-{tries}"

            # 發佈到 WordPress
            logger.info(f"準備發佈文章: {seo_title}")
            wp_publish(seo_title, content_html, meta_desc, slug)
            success_count += 1
            
            logger.info(f"✅ 成功處理關鍵字: {keyword}")
            
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

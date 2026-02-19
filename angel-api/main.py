from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
import os
import secrets
import httpx
import time
from datetime import datetime, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")

KEY_FILE = "apikeys.json"
ADMIN_PASSWORD = "angelneedapi"

# -------------------------
# 🔥 WEBS
# -------------------------

# API WEB (FREE USERS)
FREE_WEB = "https://abysstest1-phi.vercel.app/api/bypass?url={url}"

# NORMAL WEBSITE (PAID USERS)
PAID_WEB_2 = "https://bypassunlock.com"

# Luarmor wrapper
LUARMOR_PREFIX = "https://ads.luarmor.net/get_key?for="
WRAP_LINK = "http://camper.pythonanywhere.com/redirect?to={}"

# -------------------------
# UTILITIES
# -------------------------

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_duration(text):
    number = int(text[:-1])
    unit = text[-1]

    if unit == "d":
        return timedelta(days=number)
    elif unit == "h":
        return timedelta(hours=number)
    elif unit == "m":
        return timedelta(minutes=number)
    else:
        return timedelta(days=int(text))

def validate_key(key):
    keys = load_keys()
    if key not in keys:
        return None

    expire = datetime.strptime(keys[key]["expires"], "%Y-%m-%d %H:%M:%S")
    if datetime.utcnow() > expire:
        del keys[key]
        save_keys(keys)
        return None

    return keys[key]

# -------------------------
# ADMIN LOGIN
# -------------------------

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        res = RedirectResponse("/panel", status_code=302)
        res.set_cookie("admin", "true")
        return res
    return RedirectResponse("/", status_code=302)

# -------------------------
# PANEL
# -------------------------

@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request):
    if request.cookies.get("admin") != "true":
        return RedirectResponse("/")
    keys = load_keys()
    return templates.TemplateResponse("panel.html", {"request": request, "keys": keys})

@app.post("/generate")
def generate(request: Request, duration: str = Form(...), key_type: str = Form(...)):
    if request.cookies.get("admin") != "true":
        return RedirectResponse("/")

    keys = load_keys()
    new_key = secrets.token_hex(16)

    expire_time = datetime.utcnow() + parse_duration(duration)

    keys[new_key] = {
        "type": key_type,
        "expires": expire_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    save_keys(keys)
    return RedirectResponse("/panel", status_code=302)

@app.get("/revoke/{key}")
def revoke(key: str, request: Request):
    if request.cookies.get("admin") != "true":
        return RedirectResponse("/")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return RedirectResponse("/panel", status_code=302)

# -------------------------
# BYPASS API
# -------------------------

@app.get("/api/bypass")
async def bypass(url: str, apikey: str):

    start = time.time()

    key_data = validate_key(apikey)
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid or expired key")

    result = None
    used_web = None

    async with httpx.AsyncClient(timeout=20) as client:

        # FREE API WEB
        try:
            r = await client.get(FREE_WEB.format(url=url))
            if r.status_code == 200:
                data = r.json()
                if "result" in data:
                    result = data["result"]
                    used_web = "free-api"
        except:
            pass

    # 🔥 If paid and API failed → send to website
    if key_data["type"] == "paid" and not result:
        result = f"{PAID_WEB_2}?url={url}"
        used_web = "paid-website"

    if not result:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "failed to bypass"}
        )

    # 🔥 Wrap Luarmor links
    if result.startswith(LUARMOR_PREFIX):
        result = WRAP_LINK.format(result)

    end = time.time()
    time_taken = f"{round(end - start, 3)}s"

    return {
        "status": "success",
        "action": "bypass-url",
        "result": result,
        "key_type": key_data["type"],
        "used_web": used_web,
        "time_taken": time_taken
    }

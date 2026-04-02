import time
from typing import Literal, List, Dict, Any

from openai import OpenAI
import instructor
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------
# 1. CONNECT TO vLLM
# ---------------------------------------------------------
client = instructor.patch(
    OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy",
    )
)

# ---------------------------------------------------------
# 2. STRUCTURED ACTION MODEL
# ---------------------------------------------------------
class BrowserAction(BaseModel):
    action: Literal["click", "type", "navigate", "finish"]
    selector: str | None = None
    text: str | None = None
    url: str | None = None

# ---------------------------------------------------------
# 3. STABLE SELECTOR BUILDER (S1)
# ---------------------------------------------------------
def build_stable_selector(el) -> str:
    for attr in ["id", "name", "role", "type", "aria-label", "placeholder"]:
        val = el.get_attribute(attr)
        if val:
            if attr == "id":
                return f"#{val}"
            return f"[{attr}='{val}']"

    href = el.get_attribute("href")
    if href:
        return f"a[href='{href}']"

    text = el.inner_text().strip()
    if text:
        safe = text.replace('"', "'")[:40]
        tag = el.evaluate("e => e.tagName.toLowerCase()")
        return f"{tag}:has-text(\"{safe}\")"

    return el.evaluate("e => e.tagName.toLowerCase()")

# ---------------------------------------------------------
# 4. INPUT RANKING
# ---------------------------------------------------------
def rank_input(el) -> int:
    score = 0
    if el.get_attribute("type") == "search": score += 5
    if el.get_attribute("role") == "searchbox": score += 5
    if el.get_attribute("name") == "q": score += 4
    if el.get_attribute("id") == "sb_form_q": score += 4
    if el.get_attribute("placeholder"): score += 2
    if el.get_attribute("aria-label"): score += 2
    return score

# ---------------------------------------------------------
# 5. DOM WALKER (D2-A + S1 + R1 + LOW TOKEN)
# ---------------------------------------------------------
def extract_actions(page) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []

    # CLICKABLE ELEMENTS
    clickable = page.locator(
        "a, button, [role='button'], [onclick], [tabindex], "
        "input[type='submit'], input[type='button']"
    ).all()

    for el in clickable:
        try:
            if not el.is_visible(): continue
            href = el.get_attribute("href")
            if href and "bing.com/ck/a" in href: continue
            text = el.inner_text().strip()
            if not text: continue

            actions.append({
                "type": "click",
                "selector": build_stable_selector(el),
                "text": text[:40],
                "description": ""
            })
        except:
            continue

    # INPUT FIELDS
    inputs = page.locator(
        "input, textarea, [role='searchbox'], input[type='search'], "
        "input[aria-label], input[placeholder]"
    ).all()

    try:
        inputs_sorted = sorted(inputs, key=rank_input, reverse=True)
    except:
        inputs_sorted = inputs

    for el in inputs_sorted:
        try:
            if not el.is_visible(): continue
            actions.append({
                "type": "type",
                "selector": build_stable_selector(el),
                "text": "",
                "description": ""
            })
        except:
            continue

    # NAVIGATION LINKS
    links = page.locator("a[href]").all()
    for el in links:
        try:
            if not el.is_visible(): continue
            href = el.get_attribute("href")
            if not href: continue
            if "bing.com/ck/a" in href: continue
            text = el.inner_text().strip()
            if not text: continue

            actions.append({
                "type": "navigate",
                "url": href,
                "text": text[:40],
                "description": ""
            })
        except:
            continue

    # R1: BING RESULT TITLES
    for el in page.locator("h2").all():
        try:
            if not el.is_visible(): continue
            text = el.inner_text().strip()
            if not text or len(text) > 40: continue
            safe = text.replace('"', "'")
            selector = f"h2:has-text(\"{safe}\")"

            actions.append({
                "type": "click",
                "selector": selector,
                "text": safe,
                "description": ""
            })
        except:
            continue

    return actions[:40]  # HARD LIMIT

# ---------------------------------------------------------
# 6. SAFE PLAYWRIGHT HELPERS
# ---------------------------------------------------------
def safe_click(page, selector):
    try:
        loc = page.locator(selector)
        if loc.count() == 0:
            print(f"[WARN] No element for selector: {selector}")
            return False
        loc.first.click()
        return True
    except Exception as e:
        print(f"[ERROR] click failed: {e}")
        return False

def safe_type(page, selector, text):
    try:
        loc = page.locator(selector)
        if loc.count() == 0:
            print(f"[WARN] No element for selector: {selector}")
            return False
        loc.first.fill(text or "")
        return True
    except Exception as e:
        print(f"[ERROR] type failed: {e}")
        return False

# ---------------------------------------------------------
# 7. DECISION FUNCTION (LOW TOKEN PROMPT)
# ---------------------------------------------------------
def decide_action(task, actions, visible_text):
    prompt = f"""
Task: {task}

Visible text:
{visible_text}

Valid actions:
{actions}

Rules:
- Use only selectors/URLs from the list.
- Prefer search boxes, search buttons, and result titles.
- If nothing helps, return action="finish".

Return a JSON object matching BrowserAction.
"""

    return client.chat.completions.create(
        model="microsoft/Phi-4-mini-instruct",
        response_model=BrowserAction,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

# ---------------------------------------------------------
# 8. MAIN AGENT LOOP
# ---------------------------------------------------------
def run_agent(start_url, task, max_steps=20):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(start_url)

        for step in range(max_steps):
            time.sleep(1)

            actions = extract_actions(page)
            visible_text = page.inner_text("body")[:800]  # HARD LIMIT

            action = decide_action(task, actions, visible_text)
            print(f"[STEP {step}] {action}")

            if action.action == "click":
                safe_click(page, action.selector)
            elif action.action == "type":
                safe_type(page, action.selector, action.text)
            elif action.action == "navigate":
                page.goto(action.url)
            elif action.action == "finish":
                print("[DONE]")
                break

        browser.close()

# ---------------------------------------------------------
# 9. RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    run_agent(
        start_url="https://www.bing.com",
        task="Search for machine learning and open the first result.",
    )

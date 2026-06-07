"""
XPath Collector — собирает интерактивные элементы со страницы через Playwright.
Использование: python collect_xpath.py --url URL [--scope all|buttons|inputs|links]
"""
 
import argparse
import sys
from playwright.sync_api import sync_playwright
 
SELECTOR_MAP = {
    "buttons": [
        "button",
        "[role='button']",
        "input[type='button']",
        "input[type='submit']",
        "input[type='reset']",
    ],
    "inputs": [
        "input:not([type='button']):not([type='submit']):not([type='reset']):not([type='hidden'])",
        "textarea",
        "select",
    ],
    "links": ["a[href]"],
    "checkboxes": ["input[type='checkbox']", "input[type='radio']"],
}
 
PRIORITY_ATTRS = ["data-pointer", "data-testid", "data-qa", "data-cy", "id", "name", "aria-label"]
 
 
def best_xpath(tag, attrs, text):
    """Построить XPath по приоритету атрибутов."""
    for attr in PRIORITY_ATTRS:
        val = attrs.get(attr, "").strip()
        if val:
            return f'//*[@{attr}="{val}"]', attr
 
    # Текст кнопки / ссылки
    if tag in ("button", "a") and text:
        clean = text.strip()
        if clean and len(clean) < 50:
            return f'//{tag}[normalize-space()="{clean}"]', "text"
 
    # Fallback: тег + type + class (хрупкий)
    parts = [f"//{tag}"]
    conditions = []
    t = attrs.get("type", "").strip()
    if t:
        conditions.append(f'@type="{t}"')
    c = attrs.get("class", "").strip()
    if c:
        first_class = c.split()[0]
        conditions.append(f'contains(@class,"{first_class}")')
    if conditions:
        parts.append(f'[{" and ".join(conditions)}]')
    return "".join(parts), "fragile"
 
 
def make_const_name(tag, attrs, text, index, used_names):
    """Сгенерировать имя константы в UPPER_SNAKE_CASE."""
    # Приоритет: data-pointer > data-testid > id > name > aria-label > text
    for attr in ["data-pointer", "data-testid", "data-qa", "data-cy", "id", "name", "aria-label"]:
        val = attrs.get(attr, "").strip()
        if val:
            name = val.upper().replace("-", "_").replace(" ", "_").replace("/", "_")
            name = "".join(c for c in name if c.isalnum() or c == "_")
            break
    else:
        clean_text = (text or "").strip()[:20]
        if clean_text:
            name = clean_text.upper().replace(" ", "_")
            name = "".join(c for c in name if c.isalnum() or c == "_")
        else:
            name = f"{tag.upper()}_{index}"
 
    # Убедиться что имя уникальное
    base = name
    counter = 2
    while name in used_names:
        name = f"{base}_{counter}"
        counter += 1
    used_names.add(name)
    return name
 
 
def make_description(tag, attrs, text):
    """Краткое описание элемента на английском."""
    label = attrs.get("aria-label") or attrs.get("placeholder") or attrs.get("title") or text or ""
    label = label.strip()[:40]
 
    tag_desc = {
        "button": "button",
        "a": "link",
        "input": f"{attrs.get('type', 'text')} input",
        "textarea": "textarea",
        "select": "dropdown",
    }.get(tag, tag)
 
    return f"{label} {tag_desc}".strip() if label else tag_desc
 
 
def collect(url, scope="all", headless=True, auth_callback=None):
    results = {"buttons": [], "inputs": [], "links": [], "other": []}
    used_names = set()
 
    selectors = []
    if scope == "all":
        for v in SELECTOR_MAP.values():
            selectors.extend(v)
    else:
        selectors = SELECTOR_MAP.get(scope, [])
 
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
 
        if auth_callback:
            auth_callback(page)
        else:
            page.goto(url, wait_until="networkidle", timeout=30000)
 
        # Дождаться загрузки
        page.wait_for_load_state("networkidle", timeout=15000)
 
        for selector in selectors:
            elements = page.query_selector_all(selector)
            for i, el in enumerate(elements):
                try:
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    attrs = el.evaluate("""e => {
                        const result = {};
                        for (const attr of e.attributes) {
                            result[attr.name] = attr.value;
                        }
                        return result;
                    }""")
                    text = (el.inner_text() or "").strip()[:60]
 
                    # Пропустить скрытые элементы
                    visible = el.is_visible()
                    if not visible:
                        continue
 
                    xpath, source = best_xpath(tag, attrs, text)
                    const_name = make_const_name(tag, attrs, text, i, used_names)
                    description = make_description(tag, attrs, text)
                    fragile = source == "fragile"
 
                    entry = {
                        "name": const_name,
                        "xpath": xpath,
                        "description": description,
                        "fragile": fragile,
                    }
 
                    if tag in ("button",) or attrs.get("role") == "button":
                        results["buttons"].append(entry)
                    elif tag in ("input", "textarea", "select"):
                        results["inputs"].append(entry)
                    elif tag == "a":
                        results["links"].append(entry)
                    else:
                        results["other"].append(entry)
 
                except Exception:
                    continue
 
        browser.close()
    return results
 
 
def print_results(results):
    for group, items in results.items():
        if not items:
            continue
        print(f"\n# {group.capitalize()}")
        for item in items:
            prefix = "# ⚠️ нет стабильного атрибута, может сломаться при изменении вёрстки\n" if item["fragile"] else ""
            print(f"{prefix}{item['name']} = (\"locator\", '{item['xpath']}', \"{item['description']}\")")
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect XPath locators from a page")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--scope", default="all", choices=["all", "buttons", "inputs", "links"],
                        help="Which elements to collect")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()
 
    results = collect(
        url=args.url,
        scope=args.scope,
        headless=not args.no_headless,
    )
    print_results(results)

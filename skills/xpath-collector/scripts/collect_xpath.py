"""
XPath Collector — собирает интерактивные элементы со страницы через Playwright.
Использование: python collect_xpath.py --url URL [--scope all|buttons|inputs|links] [--headless]
По умолчанию браузер открывается визуально (headed) с замедлением 500ms — видно каждое действие.
"""

import argparse
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


def collect(url, scope="all", headless=False, slow_mo=500, auth_callback=None):
    results = {"buttons": [], "inputs": [], "links": [], "other": []}
    used_names = set()

    selectors = []
    if scope == "all":
        for v in SELECTOR_MAP.values():
            selectors.extend(v)
    else:
        selectors = SELECTOR_MAP.get(scope, [])

    with sync_playwright() as p:
        # headed + slow_mo по умолчанию — видно каждое действие
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo if not headless else 0
        )
        context = browser.new_context()
        page = context.new_page()

        if auth_callback:
            auth_callback(page)
        else:
            page.goto(url, wait_until="networkidle", timeout=30000)

        page.wait_for_load_state("networkidle", timeout=15000)

        print(f"🔍 Собираю локаторы: {page.url}")

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

                    if not el.is_visible():
                        continue

                    # Подсветить элемент в браузере перед сбором
                    try:
                        el.evaluate("""e => {
                            e.style.outline = '2px solid red';
                            setTimeout(() => e.style.outline = '', 400);
                        }""")
                    except Exception:
                        pass

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

                    if tag == "button" or attrs.get("role") == "button":
                        results["buttons"].append(entry)
                    elif tag in ("input", "textarea", "select"):
                        results["inputs"].append(entry)
                    elif tag == "a":
                        results["links"].append(entry)
                    else:
                        results["other"].append(entry)

                except Exception:
                    continue

        print("✅ Сбор завершён")
        browser.close()
    return results


def print_results(results):
    total = sum(len(v) for v in results.values())
    print(f"\n# Найдено элементов: {total}\n")
    for group, items in results.items():
        if not items:
            continue
        print(f"# {group.capitalize()}")
        for item in items:
            if item["fragile"]:
                print(f"# ⚠️ нет стабильного атрибута, может сломаться при изменении вёрстки")
            print(f'{item["name"]} = ("locator", \'{item["xpath"]}\", "{item["description"]}")')
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect XPath locators from a page")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--scope", default="all", choices=["all", "buttons", "inputs", "links"],
                        help="Which elements to collect (default: all)")
    parser.add_argument("--headless", action="store_true",
                        help="Run without UI (by default browser opens visually)")
    parser.add_argument("--slow-mo", type=int, default=500,
                        help="Delay between actions in ms (default: 500)")
    args = parser.parse_args()

    results = collect(
        url=args.url,
        scope=args.scope,
        headless=args.headless,
        slow_mo=args.slow_mo,
    )
    print_results(results)

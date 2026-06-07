---
name: xpath-collector
description: >
  Use this skill to collect XPath locators from a web page using Playwright in CLI (Claude Code).
  Trigger whenever the user says "собери локаторы", "найди локаторы", "собери XPath", "сгенерируй локаторы",
  "xpath для страницы", "локаторы для автотестов", or asks to collect/generate locators for any page or set of elements.
  Use this skill even if the user just points at a page and says "собери всё" or names specific elements like "кнопки", "инпуты", "ссылки".
---

# XPath Collector — сбор локаторов через Playwright (CLI)

Ты собираешь XPath-локаторы со страницы через Playwright и выводишь их в чат в формате, готовом для использования в тестах.

---

## Шаг 1 — Определи параметры

Перед запуском уточни (если не указано):
- **URL страницы** — обязательно
- **Нужна ли авторизация** — если да, собери credentials у пользователя
- **Scope сбора** — по умолчанию все интерактивные элементы; если пользователь уточнил ("только кнопки") — только они

---

## Шаг 2 — Установи Playwright (если не установлен)

```bash
pip install playwright --break-system-packages
playwright install chromium
```

---

## Шаг 3 — Запусти скрипт сбора

Используй `bash_tool` для запуска скрипта из `scripts/collect_xpath.py`:

```bash
python scripts/collect_xpath.py --url URL [--scope all|buttons|inputs|links] [--headless] [--slow-mo 500]
```

**По умолчанию** браузер открывается визуально (headed) с задержкой 500ms — каждый найденный элемент подсвечивается красной рамкой прямо в браузере.

Флаги:
- `--headless` — запустить без UI (фоновый режим)
- `--slow-mo N` — изменить задержку в мс (например `--slow-mo 800` для более медленного просмотра)

Читай скрипт: `scripts/collect_xpath.py`

---

## Шаг 4 — Приоритет атрибутов для XPath

При построении локаторов соблюдай порядок (от лучшего к худшему):

1. `data-pointer` → `//*[@data-pointer="value"]`
2. `data-testid` / `data-qa` / `data-cy`
3. `id`
4. `name`
5. `aria-label`
6. Текст элемента → `//button[normalize-space()='Текст']`
7. `type` + `class` — только если ничего лучше нет

**Избегай:** локаторов только на `class` или позиции (`[1]`, `[2]`).

---

## Шаг 5 — Выведи результат

Формат каждого локатора:
```python
ИМЯ_КОНСТАНТЫ = ("locator", '//xpath', "Описание элемента на английском")
```

Пример:
```python
# Buttons
SEND_BTN = ("locator", '//*[@data-pointer="send_button"]', "Send asset button")
MAX_BTN = ("locator", '//button[normalize-space()="Max"]', "Max amount button")

# Inputs
AMOUNT_INPUT = ("locator", '//input[@data-testid="amount-input"]', "Amount input field")
ADDRESS_INPUT = ("locator", '//input[@name="address"]', "Wallet address input")

# ⚠️ нет стабильного атрибута, может сломаться при изменении вёрстки
CANCEL_BTN = ("locator", '//button[contains(@class,"btn-secondary")]', "Cancel button")
```

Группируй по типу: Buttons / Inputs / Links / Other.
Хрупкие локаторы помечай `# ⚠️`.

---

## Крипто-специфика

На страницах криптокошелька обращай особое внимание на:
- Кнопки Send / Receive / Confirm / Cancel / Max
- Инпуты для суммы и адреса кошелька
- Элементы выбора валютной пары
- Статусы транзакций (pending / confirmed / failed)
- Кнопки Copy (адрес, сумма)
- Элементы биржи (пары, котировки, кнопки торговли)

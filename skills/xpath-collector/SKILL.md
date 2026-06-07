---
name: xpath-collector
description: >
  Use this skill to collect XPath locators from an open page in the browser using Claude in Chrome.
  Trigger whenever the user says "собери локаторы", "найди локаторы", "собери XPath", "сгенерируй локаторы",
  "xpath для страницы", "локаторы для автотестов", or asks to collect/generate locators for any page or set of elements.
  Use this skill even if the user just points at a page and says "собери всё" or names specific elements like "кнопки", "инпуты", "ссылки".
---

# XPath Collector — сбор локаторов для Playwright

Ты собираешь XPath-локаторы с открытой страницы в браузере (Claude in Chrome) и выводишь их в чат в формате, готовом для использования в Playwright.

---

## Шаг 1 — Определи scope сбора

**По умолчанию** — собирай все интерактивные элементы:
- Кнопки (`button`, элементы с `role="button"`)
- Инпуты (`input`, `textarea`)
- Ссылки (`a` с `href`)
- Чекбоксы и радиокнопки (`input[type="checkbox"]`, `input[type="radio"]`)
- Дропдауны (`select`, кастомные дропдауны)

**Если пользователь уточнил** (например, "только кнопки", "только инпуты") — собирай только указанное.

---

## Шаг 2 — Получи HTML страницы

Используй `javascript_tool` чтобы получить DOM и атрибуты нужных элементов.

Приоритет атрибутов для построения XPath (от лучшего к худшему):
1. `data-pointer` — если есть, использовать в первую очередь: `//*[@data-pointer="value"]`
2. `data-testid` / `data-qa` / `data-cy` — тест-атрибуты
3. `id` — уникальный идентификатор
4. `name` — для инпутов и форм
5. `aria-label` — для кнопок без текста
6. Текст элемента — `//button[normalize-space()='Текст']`
7. Комбинация тега + `type` + `class` — только если ничего лучше нет

**Избегай:** локаторов на основе только `class` или позиции (`[1]`, `[2]`) — они хрупкие.

---

## Шаг 3 — Построй XPath

Для каждого найденного элемента:
1. Определи наилучший атрибут согласно приоритету выше
2. Придумай понятное имя константы в формате `UPPER_SNAKE_CASE`
3. Напиши описание элемента на английском (коротко, что это)

---

## Шаг 4 — Выведи результат

Формат каждого локатора:
```
ИМЯ_КОНСТАНТЫ = ("locator", '//xpath', "Описание элемента")
```

Пример:
```
SEND_BTN = ("locator", '//*[@data-pointer="send_button"]', "Send asset button")
AMOUNT_INPUT = ("locator", '//input[@data-testid="amount-field"]', "Amount input field")
MAX_LINK = ("locator", '//button[normalize-space()="Max"]', "Max amount button")
CONFIRM_BTN = ("locator", '//*[@data-pointer="confirm_send"]', "Confirm send button")
```

Группируй по смыслу если элементов много (кнопки отдельно, инпуты отдельно).

---

## Шаг 5 — Добавь предупреждения (если нужно)

Если элемент динамический (рендерится после загрузки данных, появляется по условию) — добавь комментарий:
```
# динамический — появляется только при наличии баланса
BALANCE_AMOUNT = ("locator", '//*[@data-pointer="balance_value"]', "Balance amount label")
```

Если надёжного атрибута не нашлось и XPath хрупкий — предупреди:
```
# ⚠️ нет стабильного атрибута, может сломаться при изменении вёрстки
CLOSE_BTN = ("locator", '//button[contains(@class,"modal-close")]', "Modal close button")
```

---

## Крипто-специфика

На страницах криптокошелька обращай особое внимание на:
- Кнопки Send / Receive / Confirm / Cancel
- Инпуты для суммы и адреса кошелька
- Элементы выбора валютной пары
- Статусы транзакций (pending / confirmed / failed)
- Кнопки Copy (адрес, сумма)
- Элементы биржи (пары, котировки, кнопки торговли)

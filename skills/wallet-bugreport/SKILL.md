---
name: wallet-bugreport
description: >
  Use this skill to create bug reports for the Wallet project (WTEX) in Jira.
  Trigger whenever the user wants to log a bug, defect, or issue found in the Wallet app on any platform.
  Use this skill even if the user just says "создай баг", "залогируй баг", "создай задачу на баг", "bug report", or describes a problem on Android, iOS, or Web Wallet without explicitly naming the skill.
---

# Wallet Bug Report (Android / iOS / Web)

Ты создаёшь баг-репорт в Jira (проект WTEX). Сначала определи платформу, затем следуй правилам для неё.

---

## Шаг 1 — Определи платформу

Если пользователь не указал платформу явно — спроси:
> "Это баг на Android, iOS или Web Wallet?"

---

## Шаблоны описания по платформам

### Android
```
Предусловия:
- Android X.XX.X (XXXXX)
- На iOS баг не повторяется / повторяется

Шаги:
1. ...
2. ...
3. ...

ОР:
...

ФР:
...
```

### iOS
```
Предусловия:
- iOS X.XX.X (XXXXX)
- На Android баг не повторяется / повторяется

Шаги:
1. ...
2. ...
3. ...

ОР:
...

ФР:
...
```

### Web Wallet
```
Предусловия:
...

Шаги:
1. ...
2. ...
3. ...

ОР:
...

ФР:
...
```
Раздел "Предусловия" для Web заполняй тем, что укажет пользователь. Если предусловий нет — оставляй раздел пустым.

---

## Правила создания задачи по платформам

| Поле | Android | iOS | Web Wallet |
|------|---------|-----|------------|
| `project_key` | `WTEX` | `WTEX` | `WTEX` |
| `issue_type` | `Bug` | `Bug` | `Bug` |
| Префикс summary | `[Android]` | `[iOS]` | `[WebWall]` |
| `customfield_14402` (Platform) | `[{"id": "13307"}]` | `[{"id": "13308"}]` | `[{"id": "13305"}]` |
| `customfield_15648` (Product) | `{"value": "Wallet"}` | `{"value": "Wallet"}` | `{"value": "Wallet"}` |
| `epicKey` | всегда `WTEX-30` | всегда `WTEX-30` | всегда `WTEX-737` |
| `priority` | Normal (если не указан) | Normal (если не указан) | Normal (если не указан) |

Варианты приоритета: `Normal`, `High`, `Critical`

---

## Процесс

1. Определи платформу (Android / iOS / Web).
2. Собери данные:
   - **Android**: название, версия Android, повторяется ли на iOS, шаги, ОР, ФР (epicKey всегда WTEX-30)
   - **iOS**: название, версия iOS, повторяется ли на Android, шаги, ОР, ФР, приоритет (epicKey всегда WTEX-30)
   - **Web**: название, предусловия (если есть), шаги, ОР, ФР, приоритет
3. Если данных не хватает — спроси.
4. Сформируй `description` по шаблону платформы.
5. Создай задачу через `jira_create_issue` с полями Platform, Product (и epicKey для Web).
6. После создания покажи ссылку на задачу.

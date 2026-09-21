import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_PATH = os.path.join(BASE_DIR, "messages.txt")
RESULTS_PATH = os.path.join(BASE_DIR, "messages_out.txt")

SPRAVKA = "справка"
ZHALOBA = "жалоба"
DRUG = "другое"

STRONG_COMPLAINT_MARKERS = (
    "не работает", "не работают", "не работал", "не работала", "не работало",
    "не включается", "не включают", "не включён", "не включен",
    "не открывается", "не открыть", "не загружается", "не грузится",
    "не приходит", "не пришла", "не пришел", "не пришли", "не приехал", "не приехала",
    "не поступил", "не поступили", "не поступает",
    "не получил", "не получила", "не получили", "не получается",
    "не подали", "не приняли", "не вернул", "не вернули", "не проходит",
    "пропал", "пропала", "пропало", "пропали", "пропадает",
    "сломал", "сломался", "сломалась", "сломались", "поломк", "поломал",
    "неисправн", "очеред", "холодн", "жарко", "душно", "грязн", "грязь",
    "жалоб", "претенз", "недовол", "неудовлетвор",
    "плох", "отвратител", "ужасн", "кошмар", "ужас",
    "медленно", "медленн", "тормозит", "зависает", "вылетает",
    "ошибк", "ошиблись", "ошибочн", "неверн", "неправильн",
    "не хватает", "не хватило",
    "нет денег", "нет средств", "нет стипендии", "нет зарплаты", "нет выплат",
    "нет света", "нет воды", "нет интернета", "нет связи", "нет wi-fi",
    "нет wifi", "нет отопления", "почему нет", "деньги не", "не пришли деньги",
    "не дали", "не выдали", "не выплатил", "не начислили", "не зачислили",
    "задержал", "задержк", "задерживают",
    "украл", "украли", "обман", "мошенн", "обманули",
    "не отвечают", "не отвечает", "игнорир", "молчат",
    "долго не", "ждал уже", "ждала уже", "третий день", "второй день",
    "не меняли", "не починили", "не убрали", "не убирают",
    "воняет", "вонь", "запах", "шумит", "шумно", "громко",
    "течет", "течёт", "протекает", "капает",
    "не греет", "не горит", "не светит", "перегорел",
    "разбит", "треснут", "царапин", "дефект", "брак",
    "не могу", "не можем", "невозможно", "никак не",
    "не пускают", "не пускает", "заблокирован", "нет доступа",
    "не сохраняется", "перебои", "сбой", "сбои", "отключили", "отключён", "отключен",
    "потерял", "потеряла", "пропустил", "опоздал",
    "грубо", "хамств", "нахамил",
    "дорого", "завышен", "переплат", "списали",
    "не соответствует", "некачественн",
    "жалу", "сколько можно", "надоел",
)

WEAK_COMPLAINT_MARKERS = (
    "проблем", "сложност", "неудобн", "недостат", "недостаточно",
    "не нравится", "раздража", "неприятн", "разочаров", "беспокоит",
    "нарекани", "сомнительн", "странн", "мешает",
)

INFO_LEAD_MARKERS = (
    "как", "каким образом", "где", "куда", "откуда", "когда", "во сколько",
    "в какое время", "до скольки", "сколько", "какой", "какая", "какое",
    "какие", "каких", "можно ли", "возможно ли", "есть ли", "имеется ли",
    "подскажи", "подскажите", "скажите", "уточнить", "уточните",
    "расскажите", "объясните", "поясните", "интересует", "хочу узнать",
    "хочу уточнить", "хотел бы узнать", "что нужно", "что требуется",
    "какие документы", "какие условия", "где взять", "где найти",
    "где получить", "где находится", "действует ли", "проконсультируйте",
)

INFO_TOPIC_MARKERS = (
    "справк", "документ", "адрес", "контакт", "телефон", "номер",
    "график", "расписание", "режим работы", "часы работы", "время работы",
    "стоимост", "цена", "прайс", "тариф", "сколько стоит", "информаци",
    "условия", "требования", "правила", "сроки", "срок", "варианты",
    "помощь", "поддержка", "парковк", "расположен", "находится",
    "как получить", "как оформить", "как подать", "как записаться",
    "как включить", "как открыть", "как попасть", "как добраться",
    "как найти", "как пользоваться", "как оплатить", "как заказать",
    "как проверить", "как узнать", "нужен", "нужна", "нужно", "нужны",
    "требуется", "надо ли", "возможно", "можно",
)

DRAFTS = {
    SPRAVKA: (
        "Здравствуйте! Эту информацию можно получить в учебном отделе "
        "(каб. 101, пн–пт с 9:00 до 17:00) или через портал студента. "
        "Напишите, если нужны подробности или список документов."
    ),
    ZHALOBA: (
        "Здравствуйте! Спасибо, что сообщили о проблеме. Мы передали "
        "обращение в ответственный отдел и разберёмся в ближайшее время. "
        "Приносим извинения за неудобства."
    ),
    DRUG: (
        "Здравствуйте! Ваше обращение принято. Подскажите, пожалуйста, "
        "удобные дату и время для консультации, — мы подтвердим запись."
    ),
}


def dedupe(markers):
    return [m for m in markers if not any(m != o and m in o for o in markers)]


def score(text):
    lower = text.lower()
    strong = dedupe([m for m in STRONG_COMPLAINT_MARKERS if m in lower])
    weak = dedupe([m for m in WEAK_COMPLAINT_MARKERS if m in lower])
    lead = dedupe([m for m in INFO_LEAD_MARKERS if m in lower])
    topic = dedupe([m for m in INFO_TOPIC_MARKERS if m in lower])
    complaint = 3 * len(strong) + len(weak)
    info = 2 * len(lead) + len(topic)
    return complaint, info, strong + weak, lead + topic


def classify(text):
    complaint, info, _, _ = score(text)
    if complaint == 0 and info == 0:
        return DRUG
    return ZHALOBA if complaint >= info else SPRAVKA


def classify_with_llm(messages):
    base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    if not key:
        raise RuntimeError("LLM_API_KEY не задан")

    numbered = "\n".join(f"{i}. {msg}" for i, msg in enumerate(messages))
    prompt = (
        'Классифицируй каждое обращение по категориям: "справка", "жалоба", "другое". '
        "Напиши короткий черновик ответа на русском (1–2 предложения). "
        'Верни строго JSON вида {"0": {"category": "...", "answer": "..."}, "1": {...}}. '
        "Никакого другого текста.\n\n"
        + numbered
    )
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content[content.find("{"): content.rfind("}") + 1])
    return [
        (parsed[str(i)]["category"], parsed[str(i)]["answer"])
        for i in range(len(messages))
    ]


def render_entry(message, category, answer):
    return f"{message} | {category} | {answer}"


def main():
    parser = argparse.ArgumentParser(description="Классификатор обращений")
    parser.add_argument("--llm", action="store_true", help="классификация одним вызовом LLM")
    parser.add_argument("--file", default=MESSAGES_PATH, help="путь к файлу с обращениями")
    parser.add_argument("--out", default=RESULTS_PATH, help="путь к файлу с результатами")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Ошибка: входной файл не найден: {args.file}", file=sys.stderr)
        print("Создайте messages.txt рядом со скриптом и повторите запуск.", file=sys.stderr)
        sys.exit(1)

    with open(args.file, encoding="utf-8-sig") as fh:
        messages = [line.strip() for line in fh.read().splitlines() if line.strip()]

    if not messages:
        print(f"Ошибка: файл {args.file} пустой — нечего классифицировать.", file=sys.stderr)
        sys.exit(1)

    if args.llm:
        try:
            results = classify_with_llm(messages)
        except Exception as exc:
            print(f"LLM недоступен ({exc}). Использую правила.", file=sys.stderr)
            results = [(classify(m), DRAFTS[classify(m)]) for m in messages]
    else:
        results = [(classify(m), DRAFTS[classify(m)]) for m in messages]

    rendered = [
        render_entry(message, category, answer)
        for message, (category, answer) in zip(messages, results)
    ]

    try:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rendered) + "\n")
    except OSError as exc:
        print(f"Ошибка записи в {args.out}: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n".join(rendered))
    print()
    print(f"Обращений обработано: {len(messages)}")
    print(f"Результат сохранён: {os.path.abspath(args.out)}")
    print(f"Входной файл {os.path.abspath(args.file)} не изменён.")


if __name__ == "__main__":
    main()
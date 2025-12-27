from flask import Flask, render_template, request
import sqlite3
import spacy
import re
from datetime import date, timedelta
import calendar
from difflib import get_close_matches

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")


def get_items():
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT item_name FROM transactions")
    items = cur.fetchall()
    conn.close()
    return items

def ai_extract_filters(user_input):
    """
    Extract filters intelligently from user input.
    Supports customer_id, transaction_type, item_name, date, month_range.
    """
    if not user_input:
        return {}

    user_input = user_input.lower()
    filters = {}
    today = date.today()

    # 1️⃣ Customer ID (C001, C123 etc.)
    match = re.search(r"c\d{3}", user_input)
    if match:
        filters["customer_id"] = match.group().upper()

    # 2️⃣ Transaction type synonyms
    if any(word in user_input for word in ["sale", "sold", "selling"]):
        filters["transaction_type"] = "SALE"
    elif any(word in user_input for word in ["purchase", "bought", "buy"]):
        filters["transaction_type"] = "PURCHASE"

    # 3️⃣ Fuzzy item name matching
    item_list = [item["item_name"] for item in get_items()]
    matches = get_close_matches(user_input, [i.lower() for i in item_list], n=1, cutoff=0.6)
    if matches:
        filters["item_name"] = next((i for i in item_list if i.lower() == matches[0]), None)

    # 4️⃣ Dates / Month detection
    if "today" in user_input:
        filters["date"] = today.strftime("%Y-%m-%d")
    elif "yesterday" in user_input:
        filters["date"] = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "last week" in user_input:
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        filters["month_range"] = (start, today.strftime("%Y-%m-%d"))
    elif "this month" in user_input:
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime("%Y-%m-%d")
        filters["month_range"] = (start, end)
    elif "last month" in user_input:
        first_day_this_month = today.replace(day=1)
        last_month_last_day = first_day_this_month - timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)
        filters["month_range"] = (last_month_first_day.strftime("%Y-%m-%d"), last_month_last_day.strftime("%Y-%m-%d"))
    else:
        # Check for month names
        months = {calendar.month_name[i].lower(): i for i in range(1, 13)}
        for month_name, month_num in months.items():
            if month_name in user_input:
                year = today.year
                if month_num > today.month:
                    year -= 1
                start = date(year, month_num, 1)
                end = date(year, month_num, calendar.monthrange(year, month_num)[1])
                filters["month_range"] = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                break

    return filters


# -----------------------------
# Normal database query
def query_db(filters):
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    for key, value in filters.items():
        if key == "month_range":
            query += " AND date BETWEEN ? AND ?"
            params.extend(value)
        elif key == "date":
            query += " AND date = ?"
            params.append(value)
        else:
            query += f" AND {key} = ?"
            params.append(value)

    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


# -----------------------------
# Sales summary query
def get_sales_summary(filters):
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT item_name,
               SUM(quantity) AS total_quantity,
               SUM(total_amount) AS total_sales
        FROM transactions
        WHERE transaction_type = 'SALE'
    """
    params = []

    if filters.get("date"):
        query += " AND date = ?"
        params.append(filters["date"])

    if filters.get("month_range"):
        query += " AND date BETWEEN ? AND ?"
        params.extend(filters["month_range"])

    query += " GROUP BY item_name ORDER BY total_sales DESC"

    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    summary = []
    items = get_items()  # dropdown for manual filter

    if request.method == "POST":
        # 1️⃣ AI query input
        user_query = request.form.get("ai_query", "")

        # 2️⃣ Manual filters
        manual_filters = {
            "customer_id": request.form.get("customer_id"),
            "item_name": request.form.get("item_name"),
            "transaction_type": request.form.get("transaction_type"),
            "date": request.form.get("date")
        }
        manual_filters = {k: v for k, v in manual_filters.items() if v}

        # 3️⃣ AI filters
        ai_filters = ai_extract_filters(user_query)

        # 4️⃣ Merge filters: manual filters take priority
        filters = manual_filters.copy()
        for k, v in ai_filters.items():
            if k not in filters:
                filters[k] = v

        # Debug prints (optional)
        print("User query:", user_query)
        print("Manual filters:", manual_filters)
        print("AI filters:", ai_filters)
        print("Combined filters:", filters)

        # 5️⃣ Decide whether to show summary or normal query
        if "today" in user_query.lower() or "this month" in user_query.lower() or "last month" in user_query.lower() \
                or any(month in user_query.lower() for month in calendar.month_name if month):
            summary = get_sales_summary(filters)
        else:
            data = query_db(filters)

    return render_template("index.html", data=data, summary=summary, items=items)


if __name__ == "__main__":
    app.run(debug=True)

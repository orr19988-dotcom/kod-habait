# -*- coding: utf-8 -*-
"""
בונה מדריך אורח לכל נכס מתוך תבנית אחת.

    py build.py              בודק את כל הנכסים ובונה אותם
    py build.py --check      בודק בלבד, בלי לכתוב קבצים
    py build.py --selftest   מוודא שהבדיקה תופסת קובץ פגום

לכל properties/<id>.json נוצרים:
    g/<id>/index.html    מדריך האורח
    a/<id>/index.html    יעד ה‑QR (הפניה למדריך)

ה‑QR מצביע תמיד ל‑a/<id>/ — כך אפשר להחליף את היעד בלי להדפיס מחדש.
הסכימה מתועדת ב‑SCHEMA.md.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS_DIR = os.path.join(HERE, "properties")
TEMPLATE = os.path.join(HERE, "template.html")
PLACEHOLDER = "__PROPERTY_DATA__"

# שדות חובה. הנקודה מציינת קינון: "wifi.pass" הוא data["wifi"]["pass"].
REQUIRED = [
    "id",
    "name.he",
    "wifi.ssid",
    "wifi.pass",
    "checkin.from",
    "checkin.to",
    "host.whatsapp",
]

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
URL_RE = re.compile(r"^https?://", re.I)


def dig(data, path):
    """מחזיר את הערך בנתיב מנוקד, או None אם משהו בדרך חסר."""
    cur = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def validate(data, filename):
    """מחזיר רשימת שגיאות. רשימה ריקה = הקובץ תקין."""
    errors = []

    for path in REQUIRED:
        value = dig(data, path)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append("חסר שדה חובה '%s'" % path)

    pid = data.get("id")
    if isinstance(pid, str) and pid and not ID_RE.match(pid):
        errors.append("השדה 'id' חייב להיות אותיות אנגליות קטנות, ספרות ומקפים בלבד (התקבל: '%s')" % pid)

    expected_id = os.path.splitext(os.path.basename(filename))[0]
    if isinstance(pid, str) and pid and pid != expected_id:
        errors.append("השדה 'id' הוא '%s' אבל שם הקובץ הוא '%s' — הם חייבים להיות זהים" % (pid, expected_id))

    phone = dig(data, "host.whatsapp")
    if isinstance(phone, str) and phone and not phone.isdigit():
        errors.append("השדה 'host.whatsapp' חייב ספרות בלבד, בלי + ובלי מקפים (התקבל: '%s')" % phone)

    for path in ("parking.nav", "review.url"):
        url = dig(data, path)
        if url is not None and not URL_RE.match(str(url)):
            errors.append("השדה '%s' חייב להתחיל ב‑http:// או https:// (התקבל: '%s')" % (path, url))

    emergency = data.get("emergency")
    if isinstance(emergency, list):
        for i, item in enumerate(emergency):
            if not isinstance(item, dict) or not str(item.get("tel", "")).strip():
                errors.append("ב'emergency' פריט מספר %d חסר שדה 'tel'" % (i + 1))

    for key in ("rules", "devices", "emergency", "tips"):
        if key in data and not isinstance(data[key], list):
            errors.append("השדה '%s' חייב להיות רשימה" % key)

    return errors


def load_properties():
    """קורא את כל קבצי הנכסים. מחזיר (רשימת נכסים תקינים, רשימת שגיאות)."""
    if not os.path.isdir(PROPS_DIR):
        return [], ["התיקייה properties/ לא קיימת"]

    names = sorted(f for f in os.listdir(PROPS_DIR) if f.endswith(".json"))
    if not names:
        return [], ["אין אף קובץ נכס בתיקייה properties/"]

    good, problems = [], []
    for name in names:
        path = os.path.join(PROPS_DIR, name)
        try:
            # utf-8-sig סובל גם קובץ עם BOM וגם בלעדיו. עורכים בווינדוס
            # מוסיפים BOM בשקט, ובלי זה הבנייה נופלת עם הודעה לא מובנת.
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except ValueError as e:
            problems.append("properties/%s: הקובץ אינו JSON תקין — %s" % (name, e))
            continue

        errors = validate(data, name)
        if errors:
            for e in errors:
                problems.append("properties/%s: %s" % (name, e))
        else:
            good.append(data)

    return good, problems


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


REDIRECT = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">

<!-- ==========================================================
     היעד — זו השורה היחידה שמשנים כשרוצים להפנות למקום אחר.
     ה‑QR שהודפס לא משתנה לעולם. רק השורה הזו.
     ========================================================== -->
<meta http-equiv="refresh" content="0; url=../../g/{pid}/">
<!-- ========================================================== -->

<title>רגע אחד…</title>
<style>
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       background:#f5f6f8;color:#131820;
       font:16px/1.6 system-ui,-apple-system,"Segoe UI",Arial,sans-serif;text-align:center}}
  @media (prefers-color-scheme:dark){{ body{{background:#0f1318;color:#e9edf2}} }}
  .box{{padding:24px}}
  a{{color:#0e6d51;font-weight:700}}
  @media (prefers-color-scheme:dark){{ a{{color:#3fb392}} }}
</style>
</head>
<body>
  <div class="box">
    <p>פותחים את מדריך האורח…</p>
    <p><a id="go" href="#">לחצו כאן אם לא נפתח אוטומטית</a></p>
  </div>
<script>
(function(){{
  var m = document.querySelector('meta[http-equiv="refresh"]');
  var url = m ? m.getAttribute("content").split(/url=/i)[1] : "";
  if (url) document.getElementById("go").setAttribute("href", url.trim());
}})();
</script>
</body>
</html>
"""


STICKER = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>מדבקה — {name}</title>
<style>
@page {{ size: 90mm 90mm; margin: 0; }}
*{{box-sizing:border-box}}
body{{margin:0;background:#e9ecf0;font-family:system-ui,"Segoe UI",Arial,sans-serif}}
.sticker{{
  width:90mm; height:90mm; background:#fff; color:#000; padding:6mm;
  display:flex; flex-direction:column; align-items:center; justify-content:space-between;
  text-align:center; margin:24px auto; box-shadow:0 2px 12px rgba(0,0,0,.18);
}}
.he{{ font-size:6mm; font-weight:800; line-height:1.2; }}
.en{{ font-size:4.2mm; font-weight:600; line-height:1.2; direction:ltr; }}
.qrbox{{ padding:2mm; background:#fff; }}
.qrbox img{{ display:block; width:46mm; height:46mm; }}
.action{{ font-size:4.6mm; font-weight:700; letter-spacing:.02em; }}
.action span{{ direction:ltr; display:inline-block; }}
.brand{{ font-size:3mm; color:#555; letter-spacing:.06em; }}
.howto{{ max-width:520px; margin:24px auto; padding:16px 20px; background:#fff;
        border-radius:12px; font-size:14px; line-height:1.6; color:#222 }}
.howto h2{{ margin:0 0 8px; font-size:15px }}
@media print{{ body{{background:#fff}} .sticker{{margin:0;box-shadow:none}} .howto{{display:none}} }}
</style>
</head>
<body>
<div class="sticker">
  <div class="he">Wi‑Fi, שעות כניסה, חניה</div>
  <div class="qrbox"><img src="../qr/{pid}.svg" alt="QR"></div>
  <div class="action">סרקו · <span>Scan</span></div>
  <div class="en">Wi‑Fi, check-in times, parking</div>
  <div class="brand">קוד הבית</div>
</div>
<div class="howto">
  <h2>{name}</h2>
  <ol>
    <li>Ctrl+P בדפדפן.</li>
    <li>ביעד לבחור <b>Save as PDF</b>.</li>
    <li>גודל נייר 90×90 מ״מ, שוליים <b>None</b>.</li>
    <li>לכבות Headers and footers.</li>
    <li>להדפיס על ויניל <b>מט, לא מבריק</b> — בוהק מונע סריקה.</li>
  </ol>
  <p><b>חובה אחרי ההדפסה:</b> לסרוק את המדבקה המודפסת עצמה, לא את המסך.</p>
  <p>אם התמונה לא מופיעה — צריך להריץ קודם:<br>
     <code>py make-qr.py --all &lt;כתובת הבסיס&gt;</code></p>
</div>
</body>
</html>
"""


def build(properties):
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()
    if PLACEHOLDER not in template:
        raise SystemExit("template.html לא מכיל את הסימון %s" % PLACEHOLDER)

    for data in properties:
        pid = data["id"]
        name = data.get("name", {}).get("he", pid)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        write(os.path.join(HERE, "g", pid, "index.html"), template.replace(PLACEHOLDER, payload))
        write(os.path.join(HERE, "a", pid, "index.html"), REDIRECT.format(pid=pid))
        write(os.path.join(HERE, "stickers", pid + ".html"), STICKER.format(pid=pid, name=name))
        print("  נבנה: g/%s/  ·  a/%s/  ·  stickers/%s.html" % (pid, pid, pid))


def selftest():
    """מוודא שהוולידציה באמת תופסת קובץ פגום ולא רק אומרת שהכול בסדר."""
    broken = {"id": "x", "name": {"he": "בלי סיסמה"},
              "wifi": {"ssid": "net"},
              "checkin": {"from": "15:00", "to": "11:00"},
              "host": {"whatsapp": "972500000000"}}
    errs = validate(broken, "x.json")
    assert any("wifi.pass" in e for e in errs), "הוולידציה לא תפסה שדה חובה חסר"

    bad_phone = json.loads(json.dumps(broken))
    bad_phone["wifi"]["pass"] = "abc"
    bad_phone["host"]["whatsapp"] = "+972-50-000-0000"
    errs = validate(bad_phone, "x.json")
    assert any("host.whatsapp" in e for e in errs), "הוולידציה לא תפסה טלפון עם תווים"

    bad_id = json.loads(json.dumps(broken))
    bad_id["wifi"]["pass"] = "abc"
    bad_id["id"] = "Red View"
    errs = validate(bad_id, "Red View.json")
    assert any("'id'" in e for e in errs), "הוולידציה לא תפסה id לא חוקי"

    ok = json.loads(json.dumps(broken))
    ok["wifi"]["pass"] = "abc"
    assert validate(ok, "x.json") == [], "הוולידציה נכשלה על קובץ תקין"

    print("בדיקה עצמית עברה ✓")
    return 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()

    properties, problems = load_properties()

    if problems:
        print("נמצאו בעיות:\n")
        for p in problems:
            print("  ✗ " + p)
        print("\nלא נבנה כלום. תקן את הקבצים ותריץ שוב.")
        return 1

    print("נבדקו %d נכסים, כולם תקינים." % len(properties))
    if "--check" in args:
        return 0

    build(properties)
    print("\nהכול נבנה. אל תערוך את הקבצים ב‑g/ וב‑a/ ידנית — הם נכתבים מחדש בכל בנייה.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

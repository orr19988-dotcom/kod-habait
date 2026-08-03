# -*- coding: utf-8 -*-
"""
יוצר QR ברזולוציה גבוהה מכל כתובת. רץ מקומית, בלי אינטרנט, בלי חשבון, בלי עלות.

שימוש:
    py make-qr.py https://user.github.io/kod-habait/a/demo
    py make-qr.py https://user.github.io/kod-habait/a/demo red-view

נוצרים שני קבצים:
    <שם>.svg  — להדפסה. וקטורי, אפשר להגדיל לכל גודל בלי לאבד איכות.
    <שם>.png  — לשליחה בוואטסאפ או להצגה במסך.

בדיקה עצמית:
    py make-qr.py --selftest
"""
import os
import sys
import re
import tempfile

import segno

# ponytail: תיקון שגיאות ברמה H — עד 30% מה‑QR יכול להיות מלוכלך, שרוט או מכוסה
# והסריקה עדיין תעבוד. מדבקה בדירת נופש סופגת שמש, מים ואצבעות, אז זה שווה את
# הצפיפות הנוספת. אם היעד ארוך מאוד וה‑QR יוצא צפוף מדי להדפסה — לרדת ל‑"q" (25%).
ERROR_LEVEL = "h"

SVG_SCALE = 10   # וקטורי, המספר משפיע רק על גודל הבסיס בקובץ
PNG_SCALE = 20   # פיקסלים לכל מודול. 20 נותן קובץ נוח לוואטסאפ ולהדפסה קטנה
BORDER = 4       # שוליים לבנים. מתחת ל‑4 מודולים סורקים מתחילים להתקשות


def add_viewbox(svg_path):
    """
    segno כותב SVG עם width/height בלבד, בלי viewBox.
    בלי viewBox דפדפן לא מקטין את התוכן כשנותנים ל‑<img> גודל אחר — ה‑QR יוצא חתוך.
    זה בדיוק מה שקורה בקובץ המדבקה, שמציג אותו ב‑50 מ"מ.
    """
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()
    if "viewBox" in svg:
        return
    m = re.search(r'<svg[^>]*?width="(\d+)"\s+height="(\d+)"', svg)
    if not m:
        return
    svg = svg.replace("<svg", '<svg viewBox="0 0 %s %s"' % (m.group(1), m.group(2)), 1)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)


def build(url, name):
    """יוצר SVG ו‑PNG. מחזיר (נתיב svg, נתיב png, מספר מודולים בצלע)."""
    qr = segno.make(url, error=ERROR_LEVEL)
    svg_path = name + ".svg"
    png_path = name + ".png"
    qr.save(svg_path, scale=SVG_SCALE, border=BORDER)
    add_viewbox(svg_path)
    qr.save(png_path, scale=PNG_SCALE, border=BORDER)
    modules = qr.symbol_size(scale=1, border=0)[0]
    return svg_path, png_path, modules


def selftest():
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        svg, png, modules = build("https://example.com/a/demo", base)
        assert os.path.getsize(svg) > 200, "קובץ ה‑SVG יצא ריק"
        assert os.path.getsize(png) > 200, "קובץ ה‑PNG יצא ריק"
        assert modules >= 21, "מטריצת ה‑QR קטנה מדי"
        with open(svg, "r", encoding="utf-8") as f:
            head = f.read(400)
        assert "<svg" in head, "ה‑SVG לא נראה כמו SVG"
        assert "viewBox" in head, "חסר viewBox — ה‑QR ייחתך כשמקטינים אותו במדבקה"
    print("בדיקה עצמית עברה ✓")
    return 0


def build_all(base):
    """יוצר QR לכל נכס ב-properties/. הקבצים נשמרים בתיקייה qr/."""
    import json

    here = os.path.dirname(os.path.abspath(__file__))
    props = os.path.join(here, "properties")
    out = os.path.join(here, "qr")
    os.makedirs(out, exist_ok=True)

    base = base.rstrip("/")
    names = sorted(f for f in os.listdir(props) if f.endswith(".json"))
    if not names:
        print("אין נכסים בתיקייה properties/")
        return 1

    for name in names:
        with open(os.path.join(props, name), "r", encoding="utf-8-sig") as f:
            pid = json.load(f)["id"]
        url = "%s/a/%s/" % (base, pid)
        svg, png, modules = build(url, os.path.join(out, pid))
        print("%-14s %s  (%dx%d)" % (pid, url, modules, modules))

    print("\nנוצרו %d קודים בתיקייה qr/" % len(names))
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--all":
        if len(args) < 2:
            print("שימוש: py make-qr.py --all https://user.github.io/kod-habait")
            return 1
        return build_all(args[1].strip())

    url = args[0].strip()
    name = args[1].strip() if len(args) > 1 else "qr"

    if not url.lower().startswith(("http://", "https://")):
        print("שגיאה: הכתובת חייבת להתחיל ב‑http:// או ב‑https://")
        print("כתובת file:// לא תעבוד בטלפון — היא מצביעה על הדיסק של המחשב הזה.")
        return 1

    svg, png, modules = build(url, name)
    min_cm = max(3.0, round(modules * 0.05, 1))   # ~0.5 מ"מ למודול, מינימום מעשי 3 ס"מ

    print("היעד:      " + url)
    print("נוצרו:     " + svg + "  |  " + png)
    print("מודולים:   " + str(modules) + "x" + str(modules))
    print("להדפסה:    לפחות " + str(min_cm) + " ס\"מ על " + str(min_cm) + " ס\"מ.")
    print("           כלל אצבע: הצלע צריכה להיות בערך עשירית ממרחק הסריקה.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

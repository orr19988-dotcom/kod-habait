# -*- coding: utf-8 -*-
"""
גיבוי שבועי של מה שבאמת חשוב: קבצי הנכסים והתבנית.

    py backup.py            גיבוי לתיקיית ברירת המחדל
    py backup.py <תיקייה>   גיבוי למקום אחר (כונן חיצוני, OneDrive)
    py backup.py --selftest בדיקה עצמית

שומר 8 גרסאות אחורה ומוחק ישנות.
אם הגיבוי נכשל — נוצר קובץ בולט על שולחן העבודה. זו ההתראה.

למה בכלל צריך את זה אם הכול בגיט:
    גיט בגיטהאב הוא הגיבוי הראשי. זה הגיבוי השני, במקום אחר לגמרי,
    למקרה שהחשבון ננעל או שנמחק משהו בטעות ונדחף.
"""
import datetime
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DEST = os.path.join(os.path.expanduser("~"), "Documents", "kod-habait-backups")
ALERT_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "הגיבוי-נכשל-לבדוק.txt")
KEEP = 8

# רק מה שלא ניתן לשחזר. g/, a/, stickers/ ו-qr/ נוצרים מחדש בפקודה אחת.
SOURCES = ["properties", "template.html", "build.py", "make-qr.py", "SCHEMA.md", "README.md"]


def make_backup(src_root, dest_dir):
    """יוצר קובץ zip מתוארך. מחזיר את הנתיב."""
    os.makedirs(dest_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(dest_dir, "kod-habait_%s.zip" % stamp)

    added = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for item in SOURCES:
            full = os.path.join(src_root, item)
            if os.path.isdir(full):
                for root, _dirs, files in os.walk(full):
                    for name in files:
                        f = os.path.join(root, name)
                        z.write(f, os.path.relpath(f, src_root))
                        added += 1
            elif os.path.isfile(full):
                z.write(full, item)
                added += 1

    if added == 0:
        os.remove(path)
        raise RuntimeError("לא נמצא שום קובץ לגיבוי — בדוק שאתה מריץ מתוך תיקיית הפרויקט")
    return path, added


def prune(dest_dir):
    """משאיר את KEEP הגיבויים האחרונים ומוחק את השאר."""
    zips = sorted(f for f in os.listdir(dest_dir)
                  if f.startswith("kod-habait_") and f.endswith(".zip"))
    removed = 0
    for old in zips[:-KEEP]:
        os.remove(os.path.join(dest_dir, old))
        removed += 1
    return len(zips) - removed, removed


def alert(message):
    """ההתראה: קובץ בולט על שולחן העבודה. בלי שירות ובלי עלות."""
    try:
        with open(ALERT_FILE, "w", encoding="utf-8") as f:
            f.write("הגיבוי של קוד הבית נכשל.\n\n")
            f.write("מתי: %s\n\n" % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
            f.write("מה קרה:\n%s\n\n" % message)
            f.write("מה לעשות: להריץ py backup.py ידנית ולראות את השגיאה.\n")
    except Exception:
        pass


def clear_alert():
    if os.path.exists(ALERT_FILE):
        try:
            os.remove(ALERT_FILE)
        except Exception:
            pass


def selftest():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "src")
        os.makedirs(os.path.join(src, "properties"))
        with open(os.path.join(src, "properties", "a.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        with open(os.path.join(src, "template.html"), "w", encoding="utf-8") as f:
            f.write("<html></html>")

        dest = os.path.join(d, "out")
        path, added = make_backup(src, dest)
        assert os.path.exists(path), "קובץ הגיבוי לא נוצר"
        assert added == 2, "מספר הקבצים שגובו שגוי: %d" % added
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        assert any("properties" in n for n in names), "תיקיית הנכסים לא נכנסה לגיבוי"

        # מוודא שהניקוי באמת משאיר רק KEEP
        for i in range(KEEP + 3):
            shutil.copy(path, os.path.join(dest, "kod-habait_2020-01-%02d_0000.zip" % (i + 1)))
        kept, removed = prune(dest)
        assert kept == KEEP, "הניקוי השאיר %d גרסאות במקום %d" % (kept, KEEP)
        assert removed > 0, "הניקוי לא מחק כלום"

        empty = os.path.join(d, "empty")
        os.makedirs(empty)
        try:
            make_backup(empty, dest)
            raise AssertionError("גיבוי מתיקייה ריקה היה אמור להיכשל")
        except RuntimeError:
            pass

    print("בדיקה עצמית עברה ✓")
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        return selftest()

    dest = args[0] if args else DEFAULT_DEST
    try:
        path, added = make_backup(HERE, dest)
        kept, removed = prune(dest)
        clear_alert()
        print("גובו %d קבצים" % added)
        print("נשמר: %s" % path)
        print("גרסאות שמורות: %d  (נמחקו ישנות: %d)" % (kept, removed))
        return 0
    except Exception as e:
        alert(str(e))
        print("הגיבוי נכשל: %s" % e)
        print("נוצרה התראה על שולחן העבודה.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

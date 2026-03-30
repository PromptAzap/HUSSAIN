"""
setup.py — سكريبت الإعداد الأولي لمشروع HUSSAIN
===================================================
يتحقق من توفر جميع الملفات الضرورية ويرشدك لتنزيلها،
ثم يبني فهرس TF-IDF إذا لم يكن موجوداً.

الاستخدام:
    python setup.py
"""

import os
import sys
import subprocess

# =========================================================
# روابط التنزيل — يُرجى تحديثها بالروابط الصحيحة
# =========================================================
DRIVE_LINKS = {
    "lectures_db.sqlite": {
        "url": "https://drive.google.com/uc?export=download&id=1fbK37yxz5yGibDwp6hk_X0Mx8QLA8_6U",
        "description": "قاعدة بيانات الدروس والفقرات",
        "size": "~17.6 MB"
    },
    "quran_roots_dual_v2.sqlite": {
        "url": "https://drive.google.com/uc?export=download&id=1tqqcj6v4DDLfVv7nXEmsit2IyD2XeHXg",
        "description": "قاعدة بيانات القرآن الكريم والجذور اللغوية",
        "size": "~15.2 MB"
    }
}

# =========================================================
# ألوان للطرفية (Terminal Colors)
# =========================================================
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def print_header():
    print(f"""
{BOLD}{BLUE}
╔══════════════════════════════════════════════════════╗
║     🔬 HUSSAIN Knowledge Engine — Project Setup     ║
║         منظومة معرفية — إعداد المشروع               ║
╚══════════════════════════════════════════════════════╝
{RESET}""")

def check_databases():
    """التحقق من وجود قواعد البيانات وإرشاد المستخدم لتنزيلها"""
    print(f"{BOLD}[1] التحقق من قواعد البيانات...{RESET}")
    all_ok = True

    for filename, info in DRIVE_LINKS.items():
        if os.path.exists(filename):
            size_bytes = os.path.getsize(filename)
            size_mb = round(size_bytes / (1024 * 1024), 1)
            print(f"  {GREEN}✅ {filename}{RESET} ({size_mb} MB) — موجود")
        else:
            all_ok = False
            print(f"  {RED}❌ {filename}{RESET} — غير موجود!")
            print(f"     الوصف: {info['description']} ({info['size']})")
            print(f"     {YELLOW}📥 رابط التنزيل: {info['url']}{RESET}")
            print(f"     ضع الملف في نفس مجلد هذا السكريبت.")
            print()

    return all_ok

def check_tfidf_index():
    """التحقق من فهرس TF-IDF أو بنائه تلقائياً"""
    print(f"\n{BOLD}[2] التحقق من فهرس TF-IDF...{RESET}")

    if os.path.exists("lectures_tfidf.npy"):
        size_bytes = os.path.getsize("lectures_tfidf.npy")
        size_gb = round(size_bytes / (1024 ** 3), 2)
        print(f"  {GREEN}✅ lectures_tfidf.npy{RESET} ({size_gb} GB) — موجود")
        return True

    print(f"  {YELLOW}⚠️  فهرس TF-IDF غير موجود — سيتم بناؤه الآن...{RESET}")
    print(f"  (قد يستغرق ذلك من 5 إلى 15 دقيقة حسب حجم البيانات)\n")

    if not os.path.exists("lectures_db.sqlite"):
        print(f"  {RED}❌ تعذّر بناء الفهرس: lectures_db.sqlite غير موجود{RESET}")
        print(f"     الرجاء تنزيل قاعدة البيانات أولاً.")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "lectures_indexer.py"],
            check=True
        )
        if os.path.exists("lectures_tfidf.npy"):
            print(f"\n  {GREEN}✅ تم بناء الفهرس بنجاح!{RESET}")
            return True
        else:
            print(f"\n  {RED}❌ فشل بناء الفهرس — يُرجى تشغيل: python lectures_indexer.py{RESET}")
            return False
    except subprocess.CalledProcessError:
        print(f"\n  {RED}❌ حدث خطأ أثناء الفهرسة. تشغيل يدوي: python lectures_indexer.py{RESET}")
        return False

def check_python_packages():
    """التحقق من تثبيت الحزم المطلوبة"""
    print(f"\n{BOLD}[3] التحقق من الحزم المطلوبة...{RESET}")
    required = ["numpy", "sentence_transformers", "chromadb"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
            print(f"  {GREEN}✅ {pkg}{RESET}")
        except ImportError:
            missing.append(pkg)
            print(f"  {RED}❌ {pkg} — غير مثبت{RESET}")

    if missing:
        print(f"\n  {YELLOW}لتثبيت الحزم الناقصة:{RESET}")
        print(f"  pip install -r requirements.txt")
        return False
    return True

def print_summary(db_ok, index_ok, pkg_ok):
    print(f"\n{BOLD}{'='*54}")
    print("📊 ملخص الإعداد")
    print(f"{'='*54}{RESET}")

    items = [
        ("قواعد البيانات", db_ok),
        ("فهرس TF-IDF", index_ok),
        ("الحزم المطلوبة", pkg_ok),
    ]

    for label, status in items:
        icon = f"{GREEN}✅" if status else f"{RED}❌"
        print(f"  {icon} {label}{RESET}")

    if all([db_ok, index_ok, pkg_ok]):
        print(f"\n{GREEN}{BOLD}🎉 المشروع جاهز للتشغيل!{RESET}")
        print(f"\n  ▶️  لتشغيل محرك البحث:")
        print(f"     python hybrid_search.py")
        print(f"\n  🔍 للبحث عن درس:")
        print(f"     python lectures_query.py")
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  أكمل الخطوات الناقصة ثم أعد تشغيل setup.py{RESET}")

if __name__ == "__main__":
    print_header()
    db_ok = check_databases()
    pkg_ok = check_python_packages()
    index_ok = check_tfidf_index() if db_ok else False
    print_summary(db_ok, index_ok, pkg_ok)

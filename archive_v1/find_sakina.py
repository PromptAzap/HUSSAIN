import json
with open('مفاهيم سلسلة دروس معرفة الله.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
def search(obj):
    if isinstance(obj, dict):
        if 'حالة من الطمأنينة والأمن' in obj.get('definition', ''):
            print(f"{obj.get('lesson_concept_id')} | {obj.get('concept_name')}")
        for v in obj.values(): search(v)
    elif isinstance(obj, list):
        for i in obj: search(i)
search(data)

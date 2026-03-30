import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
for file in os.listdir('.'):
    if not file.endswith('.json') or file == 'concept_ayah_mapping.json':
        continue
    with open(file, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    def find(obj):
        if isinstance(obj, dict):
            if obj.get('lesson_concept_id') in ['W001', 'C312', 'C504', 'I005']:
                print(f"{obj.get('lesson_concept_id')}: {obj.get('concept_name')}")
            for k, v in obj.items(): find(v)
        elif isinstance(obj, list):
            for i in obj: find(i)
    find(data)

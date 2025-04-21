#Function to handle SQl queries
def sqlQuery(select, groupingAttributes, predicate, havingVar):
    return f"""
from collections import defaultdict
import re

def normalize_having_clause(having):
    if not having:
        return ''
    return re.sub(r'(?<!\\w)(\\d+?_(sum|avg|min|max|count)_[\\w]+)', r'agg_\\1', having)

select = "{select}"
groupingAttributes = "{groupingAttributes}"
predicate = "{predicate}"
havingVar = "{havingVar}"

select_fields = [s.strip() for s in select.split(',') if s.strip()]
grouping_attributes = [g.strip() for g in groupingAttributes.split(',') if g.strip()]

if predicate:
    predicate_expr = ' and '.join(predicate.split(','))
    filtered = []
    for t in relation:
        try:
            if eval(predicate_expr, {{}}, t):
            filtered.append(t)
        except:
            continue
else:
    filtered = relation


grouped = defaultdict(list)
for t in filtered:
    key = tuple(t[attr] for attr in grouping_attributes)
    grouped[key].append(t)

result = []
for group_key, tuples in grouped.items():
    aggregates = defaultdict(lambda: 0)
    count_tracker = defaultdict(int)
    row = {{grouping_attributes[i]: val for i, val in enumerate(group_key)}}

    for t in tuples:
        for field in select_fields:
            match = re.match(r"(sum|avg|min|max|count)_(\\w+)", field)
            if not match:
                continue
            func, attr = match.groups()
            key = f"{{func}}_{{attr}}"

            if func == 'sum':
                aggregates[key] += t[attr]
            elif func == 'count':
                aggregates[key] += 1
            elif func == 'avg':
                aggregates[key] += t[attr]
                count_tracker[key] += 1
            elif func == 'min':
                aggregates[key] = min(t[attr], aggregates[key]) if key in aggregates else t[attr]
            elif func == 'max':
                aggregates[key] = max(t[attr], aggregates[key]) if key in aggregates else t[attr]

for key in count_tracker:
    aggregates[key] = aggregates[key] / count_tracker[key] if count_tracker[key] else 0


    context = {{**row, **{{f'agg_{{k}}': v for k, v in aggregates.items()}}}}
    having_pass     
    if havingVar:
        try:
            having_pass = eval(normalize_having_clause(havingVar), {{}} , context)
        except Exception as e:
            print("Error:", e)
            having_pass = False

    if having_pass:
        context.update(aggregates)
        result.append(context)

print("SQL Results:")
for r in result:
    print(', '.join(str(r.get(f.strip(), '')) for f in select_fields))
"""

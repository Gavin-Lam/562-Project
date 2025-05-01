#Function to handle SQl queries
def sqlQuery(select, groupingAttributes, predicate, havingVar, fVector):
    return f"""
    from collections import defaultdict
    import re

    cols = [desc[0] for desc in cur.description]
    relation = [dict(zip(cols, row)) for row in cur.fetchall()]

    select = "{select}"
    groupingAttributes = "{groupingAttributes}"
    predicate = "{predicate}".strip()
    havingVar = "{havingVar}".strip()

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
                prefix, func, attr = match.groups()
                key = f"{{prefix or ''}}{{func}}_{{attr}}"

                try:
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
                
                except:
                    continue

        for k, v in aggregates.items():
            if k.startswith('avg_') or "_avg_" in k:
                row[k] = v / count_tracker[k] if count_tracker[k] > 0 else 0
            else:
                row[k] = v
        
        try:
            if not havingVar or eval(havingVar, {{}}, row):
                result.append(row)
        except:
            continue

                
    for r in result:
        print(', '.join(str(r.get(f.strip(), '')) for f in select_fields))
    """

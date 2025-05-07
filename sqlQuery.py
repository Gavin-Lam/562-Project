#Function to handle SQl queries
def sqlQuery(select, groupingAttributes, predicate, havingVar, fVector):
    return f"""
    relation = cur.fetchall()

    selectAttributes = [s.strip() for s in "{select}".split(',') if s.strip()]
    groupingAttributes = [g.strip() for g in "{groupingAttributes}".split(',') if g.strip()]
    predicate = "{predicate}".strip()
    havingCondition = [h.strip() for h in "{havingVar}".split(' ') if h.strip()]
    fVect = [f.strip() for f in "{fVector}".split(',') if f.strip()]


    MF_Struct = {{}}

    for row in relation:
        key = ''
        value = {{}}
        for attr in groupingAttributes:
            key += f"{{str(row[attr])}},"
        key = key[:-1]
        

        if predicate:
            pred_pass = True
            for pred in predicate.split(','):
                lhs, rhs = pred.split('=')
                lhs = lhs.strip()
                rhs = rhs.strip()
                rhs = rhs.replace('"', '')
                rhs = rhs.replace("'", '')  
                try:
                    if str(row[lhs]) != rhs:
                        pred_pass = False
                        break
                except KeyError:
                    pred_pass = False
                    break
            if not pred_pass:
                continue

        if key not in MF_Struct:
        
            for groupAttr in groupingAttributes:
                colVal = row[groupAttr]
                if colVal is not None:
                    value[groupAttr] = colVal

            for fVectAttr in fVect:
                parts = fVectAttr.split('_')
                func = parts[0]
                tableCol = '_'.join(parts[1:])
                if func == 'avg':
                    value[fVectAttr] = {{'sum': row[tableCol], 'count': 1, 'avg': row[tableCol]}}
                elif func == 'count':
                    value[fVectAttr] = 1
                else:
                    value[fVectAttr] = row[tableCol]

            MF_Struct[key] = value
        else:
            for fVectAttr in fVect:
                parts = fVectAttr.split('_')
                func = parts[0]
                tableCol = '_'.join(parts[1:])
                if func == 'sum':
                    MF_Struct[key][fVectAttr] += int(row[tableCol])
                elif func == 'avg':
                    newSum = MF_Struct[key][fVectAttr]['sum'] + int(row[tableCol])
                    newCount = MF_Struct[key][fVectAttr]['count'] + 1
                    MF_Struct[key][fVectAttr] = {{
                        'sum': newSum,
                        'count': newCount,
                        'avg': newSum / newCount
                    }}
                elif func == 'count':
                    MF_Struct[key][fVectAttr] += 1
                elif func == 'min':
                    if row[tableCol] < MF_Struct[key][fVectAttr]:
                        MF_Struct[key][fVectAttr] = int(row[tableCol])
                elif func == 'max':
                    if row[tableCol] > MF_Struct[key][fVectAttr]:
                        MF_Struct[key][fVectAttr] = int(row[tableCol])

    table_data = []    
    for key, data in MF_Struct.items():
        evalString = ''
        if havingCondition:
            for token in havingCondition:
                if token not in ['>', '<', '==', '<=', '>=', 'and', 'or', 'not', '*', '/', '+', '-']:
                    try:
                        int(token)
                        evalString += token
                    except:
                        if '_' in token and token.split('_')[0] == 'avg':
                            evalString += str(data[token]['avg'])
                        else:
                            evalString += str(data[token])
                else:
                    evalString += f' {{token}} '

            if not eval(evalString.replace('=', '==')):
                continue

            row_info = {{}}
            for val in selectAttributes:
                if '_' in val and val.split('_')[0] == 'avg':
                    row_info[val] = str(data[val]['avg'])
                else:
                    row_info[val] = str(data[val])
            table_data.append(row_info)
        else:
            row_info = {{}}
            for val in selectAttributes:
                if '_' in val and val.split('_')[0] == 'avg':
                    row_info[val] = str(data[val]['avg'])
                else:
                    row_info[val] = str(data[val])
            table_data.append(row_info)
    """

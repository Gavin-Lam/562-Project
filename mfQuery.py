def MFQuery(select, groupingVarAmt, groupingAttributes, fVector, predicate, havingVar):
    return f"""

    #Grab the database
    relation = cur.fetchall()

    selectAttributes = [s.strip() for s in "{select}".split(',') if s.strip()]
    groupingAttributes = [g.strip() for g in "{groupingAttributes}".split(',') if g.strip()]
    predicate = [p.strip() for p in "{predicate}".split(',') if p.strip()]
    havingCondition = [h.strip() for h in "{havingVar}".split(',') if h.strip()]
    fVect = [f.strip() for f in "{fVector}".split(',') if f.strip()]
    groupingVarCount = {groupingVarAmt} 

    # Initialize the MF_Struct dictionary
    MF_Struct = {{}}

    # Split the predicates into a list of lists
    pList = [p.strip().split(' ') for p in predicate]

    # Initialize MF_Struct with the grouping attributes and aggregate functions
    for i in range(int(groupingVarCount) + 1):
        if i == 0:
            for row in relation:
                key = ','.join(str(row[attr]) for attr in groupingAttributes)
                if key not in MF_Struct:
                    value = {{attr: row[attr] for attr in groupingAttributes}}
                    for fAttr in fVect:
                        parts = fAttr.split('_')
                        if parts[1] == 'avg':
                            value[fAttr] = {{'sum': 0, 'count': 0, 'avg': 0}}
                        elif parts[1] == 'min':
                            value[fAttr] = float('inf')
                        else:
                            value[fAttr] = 0
                    MF_Struct[key] = value

        # For each aggregate function in fVect, check if it belongs to the current grouping variable
        # and apply the aggregate function to the relation
        else:
            for aggregate in fVect:
                aggParts = aggregate.split('_')
                if int(aggParts[0]) != i:
                    continue
                aggFunc, aggCol = aggParts[1], aggParts[2]

                for row in relation:
                    key = ','.join(str(row[attr]) for attr in groupingAttributes)

                    evalString = predicate[i - 1]
                    for token in pList[i - 1]:
                        if '.' in token and token.split('.')[0] == str(i):
                            attr = token.split('.')[1]
                            val = row[attr]
                            evalString = evalString.replace(token, repr(val))
                    
                    if eval(evalString.replace('=', '==')):
                        if aggFunc == 'sum':
                            MF_Struct[key][aggregate] += int(row[aggCol])
                        elif aggFunc == 'avg':
                            prev = MF_Struct[key][aggregate]
                            new_sum = prev['sum'] + int(row[aggCol])
                            new_count = prev['count'] + 1
                            MF_Struct[key][aggregate] = {{
                                'sum': new_sum,
                                'count': new_count,
                                'avg': new_sum / new_count
                            }}
                        elif aggFunc == 'min':
                            MF_Struct[key][aggregate] = min(MF_Struct[key][aggregate], int(row[aggCol]))
                        elif aggFunc == 'max':
                            MF_Struct[key][aggregate] = max(MF_Struct[key][aggregate], int(row[aggCol]))
                        elif aggFunc == 'count':
                            MF_Struct[key][aggregate] += 1

    # Evaluates the having conditions and creates the table data based on the results
    # If there are no having conditions, it will just create the table data based on the MF_Struct
    table_data = []    
    for key, data in MF_Struct.items():
        evalString = ''
        if havingCondition:
            counter = len(havingCondition) - 1
            for condition in havingCondition:
                for token in condition.split(' '):
                    if token not in ['>', '<', '==', '<=', '>=', 'and', 'or', 'not', '*', '/', '+', '-']:
                        try:
                            int(token)
                            evalString += token
                        except:
                            if '_' in token and token.split('_')[1] == 'avg':
                                evalString += str(data[token]['avg'])
                            else:
                                evalString += str(data[token])
                    else:
                        evalString += f' {{token}} '
                if counter > 0:
                    evalString += ' and '
                    counter -= 1
            if not eval(evalString.replace('=', '==')):
                continue

            row_info = {{}}
            for val in selectAttributes:
                if '_' in val and val.split('_')[1] == 'avg':
                    row_info[val] = str(data[val]['avg'])
                else:
                    row_info[val] = str(data[val])
            table_data.append(row_info)
        else:
            row_info = {{}}
            for val in selectAttributes:
                if '_' in val and val.split('_')[1] == 'avg':
                    row_info[val] = str(data[val]['avg'])
                else:
                    row_info[val] = str(data[val])
            table_data.append(row_info)
    """
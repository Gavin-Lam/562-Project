def EMFQuery(select, groupingVarAmt, groupingAttributes, fVector, predicate, havingVar):
    return f"""
    from collections import defaultdict
    import re

    def update_eval_string(evalString, string, value):
        #Helper function to replace a string in evalString with its corresponding value.
        #If value is number, it will be converted to string
        #If value is string, it will be wrapped in quotes.
        try:
            if isinstance(value, (int, float)):
                return evalString.replace(string, str(value))
            else:
                return evalString.replace(string, f"'{{value}}'")
        except:
            return evalString.replace(string, f"'{{value}}'")

    relation = cur.fetchall()
    selectAttributes = [s.strip() for s in "{select}".split(',') if s.strip()]
    groupingAttributes = [g.strip() for g in "{groupingAttributes}".split(',') if g.strip()]
    predicate = [p.strip() for p in "{predicate}".split(',') if p.strip()]
    havingCondition = [h.strip() for h in "{havingVar}".split(' ') if h.strip()]
    fVect = [f.strip() for f in "{fVector}".split(',') if f.strip()]
    groupingVarCount = {groupingVarAmt}

    print("Grouping Attributes: ", groupingAttributes)

    # Initialize the MF_Struct dictionary
    MF_Struct = {{}}

    # Split the predicates into a list of lists
    pList = [p.strip().split(' ') for p in predicate]

    print(pList)

    for i in range(groupingVarCount + 1):  # Use groupingVarCount as an integer
        if i == 0:
            for row in relation:
                key = ','.join(str(row[attr]) for attr in groupingAttributes)

                if key not in MF_Struct:
                    value = {{attr: row[attr] for attr in groupingAttributes}}
                    for fAttr in fVect:
                        parts = fAttr.split('_')
                        # avg needs to be initialized separately because it needs a sum and count
                        # min needs to be initialized to infinity so that it can be compared with the first value
                        if parts[1] == 'avg':
                            value[fAttr] = {{'sum': 0, 'count': 0, 'avg': 0}}
                        elif parts[1] == 'min':
                            value[fAttr] = float('inf')
                        else:
                            value[fAttr] = 0
                    MF_Struct[key] = value
        else:
            for aggregate in fVect:
                aggParts = aggregate.split('_')
                aggFunc, aggCol = aggParts[1], aggParts[2]

                if int(aggParts[0]) != i:
                    continue

                for row in relation:
                    for key in MF_Struct.keys():
                        if aggFunc == 'sum':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                stringParts = string.split('.')
                                if len(stringParts) > 1 and stringParts[0] == str(i):
                                    rowVal = row[stringParts[1]]
                                    evalString = update_eval_string(evalString, string, rowVal)
                                elif string in groupingAttributes:
                                    rowVal = MF_Struct[key][string]
                                    evalString = update_eval_string(evalString, string, rowVal)
                            if eval(evalString.replace('=', '==')):
                                sum = int(row[aggCol])
                                MF_Struct[key][aggregate] += sum
                        elif aggFunc == 'avg':
                            sum = MF_Struct[key][aggregate]['sum']
                            count = MF_Struct[key][aggregate]['count']
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                stringParts = string.split('.')
                                if len(stringParts) > 1 and stringParts[0] == str(i):
                                    rowVal = row[stringParts[1]]
                                    evalString = update_eval_string(evalString, string, rowVal)
                                elif string in groupingAttributes:
                                    rowVal = MF_Struct[key][string]
                                    evalString = update_eval_string(evalString, string, rowVal)
                            if eval(evalString.replace('=', '==')):
                                sum += int(row[aggCol])
                                count += 1
                                if count != 0:
                                    MF_Struct[key][aggregate] = {{'sum': sum, 'count': count, 'avg': (sum/count)}}
                        elif aggFunc == 'min':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                stringParts = string.split('.')
                                if len(stringParts) > 1 and stringParts[0] == str(i):
                                    rowVal = row[stringParts[1]]
                                    evalString = update_eval_string(evalString, string, rowVal)
                                elif string in groupingAttributes:
                                    rowVal = MF_Struct[key][string]
                                    evalString = update_eval_string(evalString, string, rowVal)
                            if eval(evalString.replace('=', '==')):
                                min = int(MF_Struct[key][aggregate])
                                if int(row[aggCol]) < min:
                                    MF_Struct[key][aggregate] = row[aggCol]
                        elif aggFunc == 'max':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                stringParts = string.split('.')
                                if len(stringParts) > 1 and stringParts[0] == str(i):
                                    rowVal = row[stringParts[1]]
                                    evalString = update_eval_string(evalString, string, rowVal)
                                elif string in groupingAttributes:
                                    rowVal = MF_Struct[key][string]
                                    evalString = update_eval_string(evalString, string, rowVal)
                            if eval(evalString.replace('=', '==')):
                                max = int(MF_Struct[key][aggregate])
                                if int(row[aggCol]) > max:
                                    MF_Struct[key][aggregate] = row[aggCol]
                        elif aggFunc == 'count':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                stringParts = string.split('.')
                                if len(stringParts) > 1 and stringParts[0] == str(i):
                                    rowVal = row[stringParts[1]]
                                    evalString = update_eval_string(evalString, string, rowVal)
                                elif string in groupingAttributes:
                                    rowVal = MF_Struct[key][string]
                                    evalString = update_eval_string(evalString, string, rowVal)
                            if eval(evalString.replace('=', '==')):
                                MF_Struct[key][aggregate] += 1


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
                        if '_' in token and token.split('_')[1] == 'avg':
                            evalString += str(data[token]['avg'])
                        else:
                            evalString += str(data[token])
                else:
                    evalString += f' {{token}} '

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
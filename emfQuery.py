def EMFQuery(select, groupingVarAmt, groupingAttributes, fVector, predicate, havingVar):
    return f"""
    from collections import defaultdict
    import re

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

    # Split the predicates into a list of lists for easier processing
    pList = [p.strip().split(' ') for p in predicate]

    print(pList)

    for i in range(groupingVarCount + 1):  # Use groupingVarCount as an integer
        # 0th pass of the algorithm, where each row of the MF Struct is initialized for every unique group based on the grouping variables.
        # Each row in the MF struct also has its columns initialized appropriately based on the aggregates in the F-Vect
        if i == 0:
            for row in relation:
                key = ','.join(str(row[attr]) for attr in groupingAttributes)

                # Check if the key already exists in MF_Struct
                # If not, create a new entry with the initial values
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
            # Begin n passes for each of the n grouping variables
            for aggregate in fVect:
                aggParts = aggregate.split('_')
                aggFunc, aggCol = aggParts[0], aggParts[1]
                # Check to make sure the aggregate function is being called on the grouping variable you are currently on (i)
                # Also loop through every key in the MF_Struct to update every row of the MF_Struct the predicate statments apply to(1.state = state and 1.cust = cust vs 1.state = state)
                if int(aggParts[0]) != i:
                    continue

                for row in relation:
                    for key in MF_Struct.keys():
                        if aggFunc == 'sum':
                            evalString = predicate[i-1]
                            # Creates a string to be run with the eval() method by replacing grouping variables with their actual values
                            # Since it's an EMF query, it must also check if the string is a grouping variable and replace that with the actual value from the table row as well
                            for string in pList[i-1]:
                                if len(string.split('.')) > 1 and string.split('.')[0] == str(i):
                                    rowVal = row[string.split('.')[1]]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"{{rowVal}}")
                                elif string in groupingAttributes.split(','):
                                    rowVal = MF_Struct[key][string]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                            # If evalString is true, update the sum
                            if eval(evalString.replace('=', '==')):
                                sum = int(row[aggCol])
                                MF_Struct[key][aggregate] += sum
                        elif aggFunc == 'avg':
                            sum = MF_Struct[key][aggregate]['sum']
                            count = MF_Struct[key][aggregate]['count']
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                if len(string.split('.')) > 1 and string.split('.')[0] == str(i):
                                    rowVal = row[string.split('.')[1]]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                                elif string in groupingAttributes.split(','):
                                    rowVal = MF_Struct[key][string]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                            # If evalString is true and count isn't 0, update the avg
                            if eval(evalString.replace('=', '==')):
                                sum += int(row[aggCol])
                                count += 1
                                if count != 0:
                                    MF_Struct[key][aggregate] = {{'sum': sum, 'count': count, 'avg': (sum/count)}}
                        elif aggFunc == 'min':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                
                                if len(string.split('.')) > 1 and string.split('.')[0] == str(i):
                                    rowVal = row[string.split('.')[1]]
                                    
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                                elif string in groupingAttributes.split(','):
                                    rowVal = MF_Struct[key][string]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                            # If evalString is true, update the min
                            if eval(evalString.replace('=', '==')):
                                min = int(MF_Struct[key][aggregate])
                                if int(row[aggCol]) < min:
                                    MF_Struct[key][aggregate] = row[aggCol]
                        elif aggFunc == 'max':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                if len(string.split('.')) > 1 and string.split('.')[0] == str(i):
                                    rowVal = row[string.split('.')[1]]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                                elif string in groupingAttributes.split(','):
                                    rowVal = MF_Struct[key][string]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                            # If evalString is true, update the max
                            if eval(evalString.replace('=', '==')):
                                max = int(MF_Struct[key][aggregate])
                                if int(row[aggCol]) > max:
                                    MF_Struct[key][aggregate] = row[aggCol]
                        elif aggFunc == 'count':
                            evalString = predicate[i-1]
                            for string in pList[i-1]:
                                if len(string.split('.')) > 1 and string.split('.')[0] == str(i):
                                    rowVal = row[string.split('.')[1]]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                                elif string in groupingAttributes.split(','):
                                    rowVal = MF_Struct[key][string]
                                    try:
                                        int(rowVal)
                                        evalString = evalString.replace(string, str(rowVal))
                                    except:
                                        evalString = evalString.replace(string, f"'{{rowVal}}'")
                            # If evalString is true, increment the count
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
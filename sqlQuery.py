#Function to handle SQl queries
def sqlQuery(select, groupingAttributes, predicate, havingVar):
    sql_parts = []

    sql_parts.append(f"SELECT [select]")
    sql_parts.append("FROM sales")

    if predicate:
        clean_predicate = ' AND '.join(pred.strip() for pred in predicate.split(',') if pred.strip())
        sql_parts.append(f"WHERE {clean_predicate}")
    
    if groupingAttributes:
        group_by = ', '.join(attr.strip() for attr in groupingAttributes.split(',') if attr.strip())
        if group_by:
            sql_parts.append(f"GROUP BY {group_by}")
    
    if havingVar:
        sql_parts.append(f"HAVING {havingVar}")
    
    formatted_sql = '\n'.join(sql_parts)
    print("SQL Query:\n")
    print(formatted_sql)
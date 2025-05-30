import subprocess
from sqlQuery import sqlQuery
from mfQuery import MFQuery
from emfQuery import EMFQuery


def main():
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a 
    file (e.g. _generated.py) and then run.
    """

    file = input("Enter file name to read off of or enter nothing to pick your own variables")
    select = ""
    groupingVarAmt = ""
    groupingAttributes = ""
    fVector = ""
    predicate = ""
    havingVar = ""

    if file != "":
        with open(file) as f:
            text = f.read().split('\n')

        text = [line.strip() for line in text]

        i = 0

        while i < len(text):
            if(text[i] == 'SELECT ATTRIBUTE(S):'):
                i += 1
                select = text[i].strip()
                i += 1
            elif(text[i] == 'NUMBER OF GROUPING VARIABLES(N)'):
                i += 1
                groupingVarAmt = text[i].strip()
                i += 1 
            elif(text[i] == 'GROUPING ATTRIBUTES(V)'):  
                i += 1
                groupingAttributes = text[i].strip()
                i += 1
            elif(text[i] == 'F-VECT([F])'):
                i += 1
                fVector = text[i].strip()
                i += 1
            elif(text[i] == 'SELECT CONDITION-VECT([C])'):
                i += 1
                predicate = text[i].strip()
                i += 1
            elif(text[i] == 'HAVING_CONDITION(G)'):
                i += 1
                havingVar = text[i].strip()
                i += 1
            else:
                predicate += "," + text[i].strip()
                i += 1
            #select condition vect isn't all in a single line meanwhile all the other are so 
            #if we hit something that isn't one of the lines
            #we can assume it is the rest of the predicates (in a file)
            
    else:
        select = input("Input each select attribute separated by a comma: ").strip()
        groupingVarAmt = input("Input the number of grouping variables: ").strip()
        groupingAttributes = input("Input the grouping attributes separated by a comma if more than one: ").strip()
        fVector = input("Input the list of aggregate functions each separated by a comma: ").strip()
        predicate = input("Input each predicate separated by a comma and having a space after each comma: ").strip()
        havingVar = input("Input each having condition separated by spaces with AND or OR: ").strip().lower()
            
    check = 1

    if groupingVarAmt == '0':
        check = 0
        print("Using SQL Query")
        body = sqlQuery(select, groupingAttributes, predicate, havingVar, fVector)

    for pred in predicate.split(','):
        if (check):
            for attribute in pred.split(' '):
                if (attribute in groupingAttributes.split(',')):
                    check = 0
                    print("Using EMF Query")
                    body = EMFQuery(select, groupingVarAmt, groupingAttributes, fVector, predicate, havingVar)   
                    break
        else:
            break

        
    if (check):
        print("Using MF Query")
        body = MFQuery(select, groupingVarAmt, groupingAttributes, fVector, predicate, havingVar)     

    body = f"""
    {body}
    """

    # Note: The f allows formatting with variables.
    #       Also, note the indentation is preserved.
    tmp = f"""
import os
import psycopg2
import psycopg2.extras
import tabulate
from dotenv import load_dotenv


# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py

def query():
    load_dotenv()

    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DBNAME')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales")

    
    _global = []

    {body}
    
    return tabulate.tabulate(table_data,
                        headers="keys", tablefmt="psql")

def main():
    print(query())
    
if "__main__" == __name__:
    main()
    """

    # Write the generated code to a file
    open("_generated.py", "w").write(tmp)
    # Execute the generated code
    # subprocess.run(["python", "_generated.py"])


if "__main__" == __name__:
    main()

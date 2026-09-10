from app.database import get_connection

from app.models import LabTest

def get_active_lab_tests() ->list[LabTest]:
    
    query="""
    Select test_code,test_name,specimen_type, turnaround_hours from
    lab_tests where active= TRUE order by test_name;
    
    """
    
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute (query)
            rows= cursor.fetchall()
    lab_tests=[]
    
    
    for row in rows:
        lab_tests.append(
        
        LabTest(
            test_code= row[0],
            test_name=row[1],
            specimen_type=row[2],
            turnaround_hours=row[3],
        )
        )
        
    return lab_tests
        


def get_lab_test_by_code(test_code: str) -> LabTest | None:
    query =""" Select test_code,test_name,specimen_type, turnaround_hours from
    lab_tests where test_code = %s and active= TRUE ;
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query,(test_code,))
            row = cursor.fetchone()
            
    if row is None:
        return None
    
    return LabTest(
                test_code= row[0],
                test_name=row[1],
                specimen_type=row[2],
                turnaround_hours=row[3],
            )
            

def search_lab_test(search_text: str) -> LabTest | None:
    query = """
        SELECT
            lt.test_code,
            lt.test_name,
            lt.specimen_type,
            lt.turnaround_hours
        FROM lab_tests AS lt
        LEFT JOIN test_aliases AS ta
            ON ta.lab_test_id = lt.lab_test_id
        WHERE lt.active = TRUE
        AND (
                LOWER(lt.test_code) = LOWER(%s)
            OR LOWER(lt.test_name) = LOWER(%s)
            OR LOWER(ta.alias_name) = LOWER(%s)
        )
        LIMIT 1;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    search_text,
                    search_text,
                    search_text,
                ),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return LabTest(
        test_code=row[0],
        test_name=row[1],
        specimen_type=row[2],
        turnaround_hours=row[3],
    )

    
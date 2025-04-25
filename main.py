import psycopg2
import json
import dicttoxml

def connect_db():
    conn = psycopg2.connect(
        dbname="university",
        user="bogda",
        password="INSQL",
        host="localhost",
        port="5432"
    )
    return conn

def load_rooms(file_path, conn):
    with open(file_path, 'r') as file:
        rooms_data = json.load(file)
        cursor = conn.cursor()
        for room in rooms_data:
            cursor.execute("INSERT INTO rooms (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;",
                           (room['id'], room['name']))
        conn.commit()

def load_students(file_path, conn):
    with open(file_path, 'r') as file:
        students_data = json.load(file)
        cursor = conn.cursor()
        for student in students_data:
            cursor.execute("SELECT id FROM rooms WHERE id = %s;", (student['room'],))
            room_id = cursor.fetchone()
            if room_id:
                cursor.execute("INSERT INTO students (id, name, birthday, sex, room_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;",
                               (student['id'], student['name'], student['birthday'], student['sex'], room_id[0]))
        conn.commit()



def get_room_student_counts(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.name, COUNT(*) AS student_count
        FROM rooms r
        JOIN students s ON s.room_id = r.id
        GROUP BY r.name
    """)
    return [{'room': row[0], 'count': row[1]} for row in cursor.fetchall()]

def get_top5_youngest_avg_age(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, AVG(EXTRACT(YEAR FROM AGE(s.birthday))) AS avg_age
        FROM students s
        JOIN rooms r ON s.room_id = r.id
        GROUP BY r.id
        ORDER BY avg_age
        LIMIT 5
    """)
    return [{'room_id': row[0], 'avg_age': float(row[1])} for row in cursor.fetchall()]

def get_top5_largest_age_diff(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id,
               MAX(EXTRACT(YEAR FROM AGE(s.birthday))) -
               MIN(EXTRACT(YEAR FROM AGE(s.birthday))) AS age_diff
        FROM students s
        JOIN rooms r ON s.room_id = r.id
        GROUP BY r.id
        ORDER BY age_diff DESC
        LIMIT 5
    """)
    return [{'room_id': row[0], 'age_diff': float(row[1])} for row in cursor.fetchall()]

def get_mixed_gender_rooms(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id
        FROM rooms r
        JOIN students s ON s.room_id = r.id
        GROUP BY r.id
        HAVING COUNT(CASE WHEN sex = 'M' THEN 1 END) > 0
           AND COUNT(CASE WHEN sex = 'F' THEN 1 END) > 0
    """)
    return [{'room_id': row[0]} for row in cursor.fetchall()]

def export_results(data, format='json', filename='output'):
    if format == 'json':
        with open(f'{filename}.json', 'w') as f:
            json.dump(data, f, indent=4)
    elif format == 'xml':
        xml = dicttoxml.dicttoxml(data)
        with open(f'{filename}.xml', 'wb') as f:
            f.write(xml)

def main():
    conn = connect_db()

    result_1 = get_room_student_counts(conn)
    result_2 = get_top5_youngest_avg_age(conn)
    result_3 = get_top5_largest_age_diff(conn)
    result_4 = get_mixed_gender_rooms(conn)

    export_results(result_1, format='json', filename='room_student_counts')
    export_results(result_2, format='json', filename='youngest_avg_age')
    export_results(result_3, format='json', filename='largest_age_diff')
    export_results(result_4, format='json', filename='mixed_gender_rooms')

    conn.close()

if __name__ == "__main__":
    main()

import pymysql

# MySQL 연결
connection = pymysql.connect(host='172.31.8.56', port=3306, user='purple', password='Palove26!', db='readingcenter')
cursor = connection.cursor()

try:
    # 외래 키 제약 해제
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    
    # 데이터 삭제
    # cursor.execute("DELETE FROM table_name;")
    
    # 데이터 다시 삽입
    # ... (데이터 다시 삽입 작업)
    
    # 외래 키 제약 복원
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    
    # 커밋
    connection.commit()
except Exception as e:
    # 에러 발생 시 롤백
    connection.rollback()
    print(f"Error: {e}")
finally:
    # 연결 종료
    cursor.close()
    connection.close()

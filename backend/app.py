from flask import Flask, jsonify, request
import mysql.connector
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='student_dev',      
            password='123456',       
            database='EcommerceDB'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối DB: {err}")
        return None

def rows_to_dict(cursor, rows):
    if not rows: return []
    columns = [column[0] for column in cursor.description]
    results = []
    for row in rows:
        results.append(dict(zip(columns, row)))
    return results

# --- API 1: Lấy danh sách sản phẩm ---
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Không thể kết nối Database.'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                Product_ID as id, 
                Name as name, 
                Original_Price as originalPrice, 
                StockQuantity as stock,
                Description as description
            FROM Product
            ORDER BY Product_ID DESC -- Sắp xếp để thấy SP mới nhất lên đầu
        """)
        rows = cursor.fetchall()
        products = rows_to_dict(cursor, rows)
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/reports/high-revenue', methods=['GET'])
def get_high_revenue_report():
    year = request.args.get('year', 2025)
    min_revenue = request.args.get('min_revenue', 0)
    
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connect failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("CALL sp_GetHighRevenueShops(%s, %s)", (year, float(min_revenue)))
        
        rows = cursor.fetchall()
        report_data = rows_to_dict(cursor, rows)
        
        # Dọn dẹp result set (nếu có)
        while cursor.nextset(): pass
        
        return jsonify(report_data)
    except Exception as e:
        print("Lỗi Report:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connect failed'}), 500

    try:
        cursor = conn.cursor()
        
        # 1. Không cần random ID nữa
        create_at = datetime.now().strftime('%Y-%m-%d') 
        shop_id = 1 

        # 2. Gọi SP Insert (Chỉ còn 6 tham số, bỏ p_id)
        cursor.execute("CALL sp_InsertProduct(%s, %s, %s, %s, %s, %s)", (
            int(data['stock']),
            create_at,
            data.get('description', ''),
            data['name'],
            float(data['originalPrice']),
            shop_id
        ))
        
        # 3. Lấy ID tự động tăng
        new_row = cursor.fetchone()
        if new_row:
            new_id = new_row[0]
        else:
            new_id = None

        # 4. QUAN TRỌNG: Dọn sạch các result set còn lại để tránh lỗi "Commands out of sync"
        while cursor.nextset():
            pass

        conn.commit()
        return jsonify({'message': 'Thêm thành công!', 'new_id': new_id}), 201
    except Exception as e:
        print("Lỗi Insert:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("CALL sp_DeleteProduct(%s)", (id,))
        conn.commit()
        return jsonify({'message': 'Xóa thành công!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        shop_id = 1 
        
        cursor.execute("CALL sp_UpdateProduct(%s, %s, %s, %s, %s, %s)", (
            id,
            int(data['stock']),
            data.get('description', ''),
            data['name'],
            float(data['originalPrice']),
            shop_id
        ))
        conn.commit()
        return jsonify({'message': 'Cập nhật thành công!'}), 200
    except Exception as e:
        print("Lỗi Update:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# --- API 6: Tìm kiếm (SEARCH via SP) ---
@app.route('/api/products/search', methods=['GET'])
def search_products():
    keyword = request.args.get('keyword', '')
    max_price = request.args.get('max_price', 2000000000)
    
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("CALL sp_SearchProducts(%s, %s)", (keyword, int(max_price)))
        rows = cursor.fetchall()
        
        products = []
        if rows:
            columns = [col[0] for col in cursor.description]
            for row in rows:
                item = dict(zip(columns, row))
                products.append({
                    'id': item['Product_ID'],
                    'name': item['ProductName'],
                    'originalPrice': item['OriginalPrice'],
                    'stock': item['StockQuantity'],
                    'description': item['Description']
                })
        
        # Dọn dẹp result set cho chắc chắn
        while cursor.nextset(): pass

        return jsonify(products)
    except Exception as e:
        print("Lỗi Search:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
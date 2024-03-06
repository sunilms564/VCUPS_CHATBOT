
import mysql.connector

# Establish database connection
cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="vcups_database"
)

# Function to call the MySQL stored procedure and insert an order item
def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # Calling the stored procedure with parameterized query
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        # Committing the changes
        cnx.commit()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        cnx.rollback()
        return -1

    finally:
        if 'cursor' in locals():
            cursor.close()

# Function to insert a record into the order_tracking table
def insert_order_tracking(order_id, status):
    try:
        cursor = cnx.cursor()

        # Inserting the record into the order_tracking table with parameterized query
        insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
        cursor.execute(insert_query, (order_id, status))

        # Committing the changes
        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error inserting order tracking: {err}")
        cnx.rollback()

    finally:
        if 'cursor' in locals():
            cursor.close()

# Function to get the next available order_id
def get_next_order_id():
    try:
        cursor = cnx.cursor()

        # Executing the SQL query to get the next available order_id
        query = "SELECT MAX(order_id) FROM orders"
        cursor.execute(query)

        # Fetching the result
        result = cursor.fetchone()[0]

        # Returning the next available order_id
        return result + 1 if result else 1

    except mysql.connector.Error as err:
        print(f"Error fetching next order id: {err}")
        return None

    finally:
        if 'cursor' in locals():
            cursor.close()

# Function to fetch the order status from the order_tracking table
def get_order_status(order_id):
    try:
        cursor = cnx.cursor()

        # Executing the SQL query to fetch the order status
        query = "SELECT status FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))

        # Fetching the result
        result = cursor.fetchone()

        # Returning the order status
        return result[0] if result else None

    except mysql.connector.Error as err:
        print(f"Error fetching order status: {err}")
        return None

    finally:
        if 'cursor' in locals():
            cursor.close()

# Close database connection
cnx.close()

if __name__ == "__main__":
    print(get_next_order_id())

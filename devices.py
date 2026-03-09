from db import get_connection
from nvd_service import search_vulnerabilities

# This function adds a new device to the database
def add_device(user_id, manufacturer, model):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insert the new device into the database
        cursor.execute(
            "INSERT INTO devices (user_id, manufacturer, model) VALUES (%s, %s, %s)",
            (user_id, manufacturer, model)
        )
        conn.commit()

        # Get the ID of the newly added device
        device_id = cursor.lastrowid
        return True, device_id

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        cursor.close()
        conn.close()


# This function gets all devices for a specific user
def get_user_devices(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get all devices belonging to this user
        cursor.execute(
            "SELECT id, manufacturer, model, created_at FROM devices WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        devices = cursor.fetchall()

        # Convert to a list of dictionaries for easy use
        result = []
        for d in devices:
            result.append({
                "id": d[0],
                "manufacturer": d[1],
                "model": d[2],
                "created_at": d[3]
            })
        return result

    except Exception as e:
        return []

    finally:
        cursor.close()
        conn.close()


# This function deletes a device and all its vulnerabilities
def delete_device(device_id, user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Make sure the device belongs to this user before deleting
        cursor.execute(
            "DELETE FROM devices WHERE id = %s AND user_id = %s",
            (device_id, user_id)
        )
        conn.commit()
        return True, "Device deleted successfully."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        cursor.close()
        conn.close()


# This function scans a device for vulnerabilities
# and saves the results to the database
def scan_device(device_id, manufacturer, model):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # First delete any old vulnerability results for this device
        cursor.execute(
            "DELETE FROM vulnerabilities WHERE device_id = %s",
            (device_id,)
        )

        # Search the NVD API for vulnerabilities
        vulnerabilities = search_vulnerabilities(manufacturer, model)

        # Save each vulnerability to the database
        for v in vulnerabilities:
            cursor.execute(
                """INSERT INTO vulnerabilities 
                (device_id, cve_id, description, severity, plain_summary, recommendation) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (device_id, v["cve_id"], v["description"],
                 v["severity"], v["plain_summary"], v["recommendation"])
            )

        conn.commit()
        return True, vulnerabilities

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        cursor.close()
        conn.close()


# This function gets all saved vulnerabilities for a device
def get_device_vulnerabilities(device_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT cve_id, description, severity, plain_summary, recommendation 
            FROM vulnerabilities WHERE device_id = %s 
            ORDER BY FIELD(severity, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')""",
            (device_id,)
        )
        rows = cursor.fetchall()

        # Convert to a list of dictionaries
        result = []
        for r in rows:
            result.append({
                "cve_id": r[0],
                "description": r[1],
                "severity": r[2],
                "plain_summary": r[3],
                "recommendation": r[4]
            })
        return result

    except Exception as e:
        return []

    finally:
        cursor.close()
        conn.close()
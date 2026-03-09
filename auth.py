import bcrypt
from db import get_connection

# This function converts a plain password into a secure bcrypt hash
def hash_password(password):
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed

# This function checks if a plain password matches a stored hash
def check_password(password, hashed):
    password_bytes = password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed)

# This function registers a new user in the database
# All users registered through the app are normal users
# Admin accounts can only be created directly in the database
def register_user(username, email, password):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "Username already exists. Please choose another one."

        # Check if the email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "Email already registered. Please use another email."

        # Hash the password using bcrypt before saving
        hashed = hash_password(password)

        # Insert the new user — always as a normal user (is_admin = FALSE)
        cursor.execute(
            "INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, FALSE)",
            (username, email, hashed)
        )
        conn.commit()
        return True, "Registration successful! Please log in."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function checks if the username and password are correct
def login_user(username, password):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the user record by username
        cursor.execute(
            "SELECT id, username, password, is_admin FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()

        if user:
            # Check if the password matches the stored hash
            if check_password(password, user[2]):
                return True, {
                    "id": user[0],
                    "username": user[1],
                    "is_admin": bool(user[3])
                }
            else:
                return False, "Invalid username or password."
        else:
            return False, "Invalid username or password."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function deletes a user account
# Survey data remains in the database linked only to participant number
# This protects research data while respecting GDPR right to erasure
def delete_account(user_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Set user_id to NULL in sus_results before deleting
        # This keeps the survey data but removes the link to the user
        cursor.execute(
            "UPDATE sus_results SET user_id = NULL WHERE user_id = %s",
            (user_id,)
        )

        # Now delete the user account
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return True, "Your account has been deleted. Thank you for participating."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function gets all users (for admin use only)
def get_all_users():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()

        result = []
        for u in users:
            result.append({
                "id": u[0],
                "username": u[1],
                "email": u[2],
                "is_admin": bool(u[3]),
                "created_at": u[4]
            })
        return result

    except Exception as e:
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function promotes a user to admin
def make_admin(user_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET is_admin = TRUE WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        return True, "User has been promoted to admin."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function demotes an admin back to a normal user
def remove_admin(user_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET is_admin = FALSE WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        return True, "User has been demoted to normal user."

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function checks if a user has already submitted the survey
def has_submitted_survey(user_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM sus_results WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchone() is not None

    except Exception as e:
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# This function gets the next available participant number
def get_next_participant_number():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(participant_number) FROM sus_results")
        result = cursor.fetchone()

        if result[0] is None:
            return 1
        else:
            return result[0] + 1

    except Exception as e:
        return 1

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
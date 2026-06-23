import requests
import random
import sys

base_url = "http://127.0.0.1:8000"

def get_csrf():
    s = requests.Session()
    r = s.get(f"{base_url}/csrf-token")
    csrf_token = r.json()["csrf_token"]
    return {"csrf_token": csrf_token}, csrf_token

def register_and_login(username, email, password):
    c, csrf = get_csrf()
    r = requests.post(f"{base_url}/supabase/register", json={"username": username, "email": email, "password": password}, cookies=c, headers={"X-CSRF-Token": csrf})
    if r.status_code != 201:
        print(f"Failed to register {username}: {r.status_code} {r.text}")
        sys.exit(1)
        
    r2 = requests.post(f"{base_url}/supabase/login", data={"grant_type": "password", "username": email, "password": password}, cookies=c, headers={"X-CSRF-Token": csrf})
    if r2.status_code != 200:
        print(f"Failed to login {username}: {r2.status_code} {r2.text}")
        sys.exit(1)
    
    return c, csrf, r2.json()["access_token"]

u_a = f"usera_{random.randint(10000, 99999)}"
u_b = f"userb_{random.randint(10000, 99999)}"

c_a, csrf_a, token_a = register_and_login(u_a, f"{u_a}@example.com", "password123")
c_b, csrf_b, token_b = register_and_login(u_b, f"{u_b}@example.com", "password123")

# User A creates meetup
m1 = requests.post(f"{base_url}/meetups", json={"title": "Meetup A", "description": "Desc", "location": "Loc", "max_attendees": 10}, headers={"Authorization": f"Bearer {token_a}", "X-CSRF-Token": csrf_a}, cookies=c_a)
meetup_id = m1.json()["id"]
print("Meetup created by User A:", meetup_id)

# User B updates meetup
print("\nUser B trying to update User A's meetup:")
r_upd = requests.put(f"{base_url}/meetups/{meetup_id}", json={"title": "Hacked", "description": "Hacked", "location": "Loc", "max_attendees": 15}, headers={"Authorization": f"Bearer {token_b}", "X-CSRF-Token": csrf_b}, cookies=c_b)
print("Status:", r_upd.status_code)
print("Response:", r_upd.text)

# User B deletes meetup
print("\nUser B trying to delete User A's meetup:")
r_del = requests.delete(f"{base_url}/meetups/{meetup_id}", headers={"Authorization": f"Bearer {token_b}", "X-CSRF-Token": csrf_b}, cookies=c_b)
print("Status:", r_del.status_code)
print("Response:", r_del.text)


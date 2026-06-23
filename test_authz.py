import requests

base_url = "http://127.0.0.1:8000"

def get_csrf():
    s = requests.Session()
    r = s.get(f"{base_url}/csrf-token")
    return s.cookies, r.json()["csrf_token"]

c_a, csrf_a = get_csrf()
r1 = requests.post(f"{base_url}/supabase/register", json={"username": "usera", "email": "usera@example.com", "password": "password123"}, cookies=c_a, headers={"X-CSRF-Token": csrf_a})
print("Reg A:", r1.status_code, r1.text)

r2 = requests.post(f"{base_url}/supabase/login", data={"grant_type": "password", "username": "usera@example.com", "password": "password123"}, cookies=c_a, headers={"X-CSRF-Token": csrf_a})
print("Log A:", r2.status_code)
token_a = r2.json()["access_token"]

m1 = requests.post(f"{base_url}/meetups", json={"title": "Meetup", "description": "Desc", "location": "Loc", "max_attendees": 10}, headers={"Authorization": f"Bearer {token_a}", "X-CSRF-Token": csrf_a}, cookies=c_a)
meetup_id = m1.json()["id"]

c_b, csrf_b = get_csrf()
r3 = requests.post(f"{base_url}/supabase/register", json={"username": "userb", "email": "userb@example.com", "password": "password123"}, cookies=c_b, headers={"X-CSRF-Token": csrf_b})
print("Reg B:", r3.status_code, r3.text)

r4 = requests.post(f"{base_url}/supabase/login", data={"grant_type": "password", "username": "userb@example.com", "password": "password123"}, cookies=c_b, headers={"X-CSRF-Token": csrf_b})
token_b = r4.json()["access_token"]

print("User B updating:")
r5 = requests.put(f"{base_url}/meetups/{meetup_id}", json={"title": "Hacked", "description": "Hacked", "location": "Loc", "max_attendees": 15}, headers={"Authorization": f"Bearer {token_b}", "X-CSRF-Token": csrf_b}, cookies=c_b)
print(r5.status_code, r5.text)

print("User B deleting:")
r6 = requests.delete(f"{base_url}/meetups/{meetup_id}", headers={"Authorization": f"Bearer {token_b}", "X-CSRF-Token": csrf_b}, cookies=c_b)
print(r6.status_code, r6.text)


#!/bin/bash

echo -e "\n=== FETCH CSRF TOKEN ==="
CSRF_RESP=$(curl -s -c cookies.txt http://127.0.0.1:8000/csrf-token)
CSRF_TOKEN=$(echo $CSRF_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('csrf_token', ''))")

USER_A_EMAIL="usera_${RANDOM}@example.com"
USER_A_PASS="password123"
USER_A_NAME="usera_${RANDOM}"

USER_B_EMAIL="userb_${RANDOM}@example.com"
USER_B_PASS="password123"
USER_B_NAME="userb_${RANDOM}"

echo -e "\n=== REGISTER USER A ==="
curl -s -c cookies_a.txt -X POST http://127.0.0.1:8000/supabase/register \
  -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"username\": \"$USER_A_NAME\", \"email\": \"$USER_A_EMAIL\", \"password\": \"$USER_A_PASS\"}"

echo -e "\n=== LOGIN USER A ==="
LOGIN_A=$(curl -s -c cookies_a.txt -X POST http://127.0.0.1:8000/supabase/login \
  -H "Content-Type: application/x-www-form-urlencoded" -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "grant_type=password&username=${USER_A_EMAIL/@/%40}&password=$USER_A_PASS")
echo "LOGIN_A: $LOGIN_A"
TOKEN_A=$(echo $LOGIN_A | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo -e "\n=== CREATE MEETUP (USER A) ==="
MEETUP_RESP=$(curl -s -c cookies_a.txt -X POST http://127.0.0.1:8000/meetups \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies_a.txt \
  -d '{"title": "Terminal Meetup", "description": "Testing from terminal", "location": "CLI", "max_attendees": 10}')
echo "MEETUP_RESP: $MEETUP_RESP"
MEETUP_ID=$(echo $MEETUP_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo "Created Meetup ID: $MEETUP_ID"

echo -e "\n=== REGISTER USER B ==="
# IMPORTANT: use fresh cookies_b.txt so we don't mix sessions!
CSRF_RESP_B=$(curl -s -c cookies_b.txt http://127.0.0.1:8000/csrf-token)
CSRF_TOKEN_B=$(echo $CSRF_RESP_B | python3 -c "import sys, json; print(json.load(sys.stdin).get('csrf_token', ''))")

curl -s -c cookies_b.txt -X POST http://127.0.0.1:8000/supabase/register \
  -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF_TOKEN_B" -b cookies_b.txt \
  -d "{\"username\": \"$USER_B_NAME\", \"email\": \"$USER_B_EMAIL\", \"password\": \"$USER_B_PASS\"}"

echo -e "\n=== LOGIN USER B ==="
LOGIN_B=$(curl -s -c cookies_b.txt -X POST http://127.0.0.1:8000/supabase/login \
  -H "Content-Type: application/x-www-form-urlencoded" -H "X-CSRF-Token: $CSRF_TOKEN_B" -b cookies_b.txt \
  -d "grant_type=password&username=${USER_B_EMAIL/@/%40}&password=$USER_B_PASS")
echo "LOGIN_B: $LOGIN_B"
TOKEN_B=$(echo $LOGIN_B | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo -e "\n=== AUTHZ TEST: USER B UPDATES MEETUP ==="
curl -s -X PUT http://127.0.0.1:8000/meetups/$MEETUP_ID \
  -H "Authorization: Bearer $TOKEN_B" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF_TOKEN_B" -b cookies_b.txt \
  -d '{"title": "Hacked Meetup", "description": "I hacked this", "location": "CLI", "max_attendees": 15}'

echo -e "\n\n=== AUTHZ TEST: USER B DELETES MEETUP ==="
curl -s -X DELETE http://127.0.0.1:8000/meetups/$MEETUP_ID \
  -H "Authorization: Bearer $TOKEN_B" -H "X-CSRF-Token: $CSRF_TOKEN_B" -b cookies_b.txt

echo -e "\n\nFinished authz tests."

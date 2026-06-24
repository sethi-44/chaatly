#!/bin/bash

echo -e "\n=== FETCH CSRF TOKEN ==="
CSRF_RESP=$(curl -s -c cookies.txt http://127.0.0.1:8000/csrf-token)
CSRF_TOKEN=$(echo $CSRF_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('csrf_token', ''))")
echo "CSRF_TOKEN: $CSRF_TOKEN"

USER_EMAIL="testuser_${RANDOM}@example.com"
USER_EMAIL_ENC=${USER_EMAIL/@/%40}
USER_PASS="password123"
RANDOM_USERNAME="user_${RANDOM}"

echo -e "\n=== REGISTER ==="
REG_RESP=$(curl -s -X POST http://127.0.0.1:8000/supabase/register \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"username\": \"$RANDOM_USERNAME\", \"email\": \"$USER_EMAIL\", \"password\": \"$USER_PASS\"}")
echo $REG_RESP

echo -e "\n=== LOGIN ==="
LOGIN_RESP=$(curl -s -X POST http://127.0.0.1:8000/supabase/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "grant_type=password&username=$USER_EMAIL_ENC&password=$USER_PASS")
echo $LOGIN_RESP

ACCESS_TOKEN=$(echo $LOGIN_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
REFRESH_TOKEN=$(echo $LOGIN_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('refresh_token', ''))")

echo -e "\n=== /ME ==="
curl -s -X GET http://127.0.0.1:8000/supabase/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -b cookies.txt

echo -e "\n\n=== CREATE MEETUP ==="
MEETUP_RESP=$(curl -s -X POST http://127.0.0.1:8000/meetups \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d '{"title": "Terminal Meetup", "description": "Testing from terminal", "location": "CLI", "max_attendees": 10}')
echo $MEETUP_RESP
MEETUP_ID=$(echo $MEETUP_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

echo -e "\n=== UPDATE MEETUP ==="
curl -s -X PUT http://127.0.0.1:8000/meetups/$MEETUP_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d '{"title": "Updated Terminal Meetup", "description": "Still testing from terminal", "location": "CLI", "max_attendees": 15}'

echo -e "\n\n=== JOIN MEETUP ==="
USER2_EMAIL="user2_${RANDOM}@example.com"
REG2_RESP=$(curl -s -X POST http://127.0.0.1:8000/supabase/register \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"username\": \"user2\", \"email\": \"$USER2_EMAIL\", \"password\": \"$USER_PASS\"}")
ACCESS_TOKEN2=$(echo $REG2_RESP | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

curl -s -X POST http://127.0.0.1:8000/meetups/$MEETUP_ID/join \
  -H "Authorization: Bearer $ACCESS_TOKEN2" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt

echo -e "\n\n=== LEAVE MEETUP ==="
curl -s -X POST http://127.0.0.1:8000/meetups/$MEETUP_ID/leave \
  -H "Authorization: Bearer $ACCESS_TOKEN2" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt

echo -e "\n\n=== DELETE MEETUP ==="
curl -s -X DELETE http://127.0.0.1:8000/meetups/$MEETUP_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt

echo -e "\n\n=== REFRESH ==="
REFRESH_RESP=$(curl -s -X POST http://127.0.0.1:8000/supabase/refresh \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")
echo $REFRESH_RESP

echo -e "\n\n=== PASSWORD RESET (Request) ==="
curl -s -X POST http://127.0.0.1:8000/supabase/request-password-reset \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"email\": \"$USER_EMAIL\"}"

echo -e "\n\n=== LOGOUT ==="
curl -s -X POST http://127.0.0.1:8000/supabase/logout \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -b cookies.txt \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"

echo -e "\n\nFinished tests."

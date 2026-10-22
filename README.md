# PortSwigger Lab Login Exercise

This educational Python script is for the PortSwigger Web Security Academy lab on username enumeration via different responses. It first tests candidate usernames with a fixed dummy password, then tests candidate passwords for a username whose response indicates it may exist.

## Requirements

- Python 3
- The `requests` package (`python3 -m pip install requests`)
- An active, authorized PortSwigger Web Security Academy lab
- The lab's candidate username and password lists, saved as `usernames.txt` and `passwords.txt` in this directory

## Run in the lab

1. In `find_uname_pass.py`, set `LAB_URL` to the origin URL of your active lab (for example, `https://<your-lab-id>.web-security-academy.net`). Do not include `/login`.
2. Put the candidate lists in `usernames.txt` and `passwords.txt`.
3. Run `python3 find_uname_pass.py`.

The script loads the lab page to establish a session, posts to `/login`, and checks the response text and redirect to identify likely matches. The wordlist files in this repository are examples; use the candidate lists provided for the lab.

## Security scope and checks

Use this credential-guessing exercise only on your own active PortSwigger Web Security Academy lab. Do not point it at real users, production systems, or any service without explicit authorization.

Before sending login attempts, the script checks that `LAB_URL` uses HTTPS and that its hostname ends in `.web-security-academy.net`. This is a basic scope guard, not proof that a lab is active or that you have authorization. The script also uses a short delay between attempts and stops if the server responds with HTTP 429; do not bypass rate limits.

The script prints a candidate username and password when its response checks indicate a match. Keep all activity and any results confined to the authorized lab.
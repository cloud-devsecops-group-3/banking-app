# banking-app — EastWest Bank (mock)

Flask banking app for the QR payment prototype. Handles account
selection, payment confirmation, and settlement — and owns QR generation
entirely, per the security design agreed with the ecommerce team (see
"Why transaction_id, not raw amounts" below).

## Setup

```bash
cp .env.example .env   # fill in DB_HOST, DB_USER, DB_PASSWORD, SECRET_KEY
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py           # :5001, creates tables + seeds demo accounts automatically
```

No separate migration step needed — `app.py` calls `db.create_all()` and
seeds demo accounts on every startup; both are safe to run repeatedly.
`seed.py` can still be run standalone (`python seed.py`) if you just want
to re-seed without starting the server.

## Run with Docker

```bash
docker compose up --build
```

Starts MySQL + this app together (see `docker-compose.yml`). The app is
on `:5001`; MySQL's `3306` is mapped to the host for local DB-client
convenience only — drop that mapping when this merges into the shared
Dev VM's compose file, since port 3306 must never be reachable outside
the VM (SSH tunnel instead, per the Dev VM guide).

## The contract with the ecommerce app

```
POST /api/payment-requests   (server-to-server, ecommerce -> bank)
Body: {
  "order_id": "...",
  "amount": "23.48",
  "merchant_account": "pageturn-books",
  "callback_url": "http://shop.<ip>.nip.io/api/payment/callback",
  "return_url": "http://shop.<ip>.nip.io/order/<order_id>"   (optional)
}
Response: {
  "transaction_id": "txn-...",
  "qr_url": "http://bank.<ip>.nip.io/qr/txn-....png"
}
```

After the customer pays or the payment fails, this app calls
`callback_url` with:

```json
{ "order_id": "...", "status": "PAID", "transaction_id": "txn-..." }
```

## Why transaction_id, not raw amounts

Earlier versions of this flow put `order_id`/`amount`/`merchant` directly
in the payment URL or hidden form fields. That meant a user could edit
the URL or form before submitting and authorize a different amount than
the order actually costs — the bank had no independent record of what
the "real" transaction was.

Now: `POST /api/payment-requests` creates a `PaymentRequest` row FIRST,
with the amount coming from the ecommerce app's own trusted checkout
(never from anything this app receives from a browser). Every later
step — account selection, confirm, settlement — looks that row up by
`transaction_id` and re-reads amount/merchant from it. Nothing the
customer's browser sends can change how much money moves.

## Routes

| Route | Method | Purpose |
|---|---|---|
| `/` , `/dashboard` | GET | Read-only balance dashboard |
| `/health` | GET | Liveness probe, `{"status": "ok"}` |
| `/api/payment-requests` | POST | Called by the ecommerce app at checkout |
| `/qr/<transaction_id>.png` | GET | QR image, generated on demand |
| `/pay/<transaction_id>` | GET | Account selection page |
| `/pay/<transaction_id>` | POST | Confirm-payment summary page |
| `/pay/<transaction_id>/confirm` | POST | Settles the payment, fires the webhook |
| `/complete` | GET | Success page (reads from session) |
| `/qr`, `/qr-scanner` | GET | Manual demo/testing tools, not part of the real integration |

## Data model

- `Account` — consumer and merchant balances
- `PaymentRequest` — one per checkout attempt; the authoritative record
  of amount/merchant/status for a `transaction_id`
- `Transaction` — one per **settled** payment (append-only ledger entry)

## Environment variables

| Var | Purpose |
|---|---|
| `SECRET_KEY` | Signs the session cookie used between confirm and the complete page |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL connection |
| `PORT` | Local `python app.py` port (Docker always uses 5001) |

## What's still open

- No login/auth gate yet — anyone who opens a `/pay/<transaction_id>`
  link can pick any consumer account. Worth adding before this goes
  further than a class prototype.
- `_notify_ecommerce()` is best-effort: if the ecommerce app is
  unreachable when we try to call back, the payment has still settled
  on our side, and we don't retry. The ecommerce order stays `PENDING`
  in that case — visible and safe, but not self-healing. A retry queue
  would be the real fix, out of scope for this MVP.

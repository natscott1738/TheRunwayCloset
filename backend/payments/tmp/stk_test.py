# /tmp/stk_test.py
import base64, time, json, requests

ACCESS_TOKEN = "QchLSEyqqwVyGWvutAORpn5nvlA5"
BUSINESS_SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
PARTY_MSISDN = "254791529449"
CALLBACK = "https://your-public-callback.ngrok.io/payments/mpesa/callback"

ts = time.strftime("%Y%m%d%H%M%S")
password = base64.b64encode(f"{BUSINESS_SHORTCODE}{PASSKEY}{ts}".encode()).decode()

payload = {
  "BusinessShortCode": BUSINESS_SHORTCODE,
  "Password": password,
  "Timestamp": ts,
  "TransactionType": "CustomerPayBillOnline",
  "Amount": 10,
  "PartyA": PARTY_MSISDN,
  "PartyB": BUSINESS_SHORTCODE,
  "PhoneNumber": PARTY_MSISDN,
  "CallBackURL": CALLBACK,
  "AccountReference": "TEST123",
  "TransactionDesc": "Test STK push"
}

print("Payload:", json.dumps(payload, indent=2))
r = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                  headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
                  json=payload,
                  timeout=30)
print("HTTP", r.status_code)
print(r.text)

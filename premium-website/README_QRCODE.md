# QR CODE SETUP

## How to Generate Ko-fi QR Code:

1. **Get Your Ko-fi Membership Link**
   - Go to your Ko-fi dashboard
   - Navigate to Memberships section
   - Copy your membership page URL (e.g., https://ko-fi.com/yourname/membership)

2. **Generate QR Code**
   
   **Option A: Online QR Generator**
   - Visit: https://www.qr-code-generator.com/
   - Select "URL" type
   - Paste your Ko-fi membership link
   - Customize colors (optional):
     - Foreground: #6366f1 (match website theme)
     - Background: white
   - Download as PNG (recommended size: 500x500px)
   - Save as `qrcode.png`

   **Option B: Python Script**
   ```python
   import qrcode
   
   # Your Ko-fi membership URL
   kofi_url = "https://ko-fi.com/yourname/membership"
   
   # Generate QR code
   qr = qrcode.QRCode(
       version=1,
       error_correction=qrcode.constants.ERROR_CORRECT_H,
       box_size=10,
       border=4,
   )
   qr.add_data(kofi_url)
   qr.make(fit=True)
   
   # Create image
   img = qr.make_image(fill_color="#6366f1", back_color="white")
   img.save("qrcode.png")
   ```

3. **Place QR Code**
   - Save the generated `qrcode.png` in the `premium-website/` folder
   - The website will automatically display it when users click purchase

4. **Test QR Code**
   - Open website
   - Click "Select Basic" or "Select Pro"
   - Verify QR code displays correctly
   - Scan with phone to test it opens Ko-fi

## Ko-fi Membership Tier Setup:

Create two membership tiers on Ko-fi:

### Tier 1: Constellation | Basic
- **Price**: $1.99/month
- **Name**: Constellation | Basic
- **Description**: 
  ```
  100k coins/month
  150 luck potions/month
  +250% permanent luck
  2x coins & exp
  Permanent auto-roll
  
  ⚠️ IMPORTANT: Include your Telegram ID in the message!
  Format: telegram_id: YOUR_ID_HERE
  ```

### Tier 2: Constellation | Pro
- **Price**: $3.99/month
- **Name**: Constellation | Pro
- **Description**:
  ```
  200k coins/month (2x Basic!)
  300 luck potions/month (2x Basic!)
  +500% permanent luck (2x Basic!)
  2x coins & exp
  3 Exclusive Lights (get 2 random)
  30% shop discount
  Light preview access
  
  ⚠️ IMPORTANT: Include your Telegram ID in the message!
  Format: telegram_id: YOUR_ID_HERE
  ```

## Webhook Setup:

1. **Configure Ko-fi Webhook**
   - Go to Ko-fi Settings > Webhooks
   - Add webhook URL: `https://your-server.com/kofi-webhook`
   - Enable for: Subscriptions
   - Save webhook verification token

2. **Deploy Webhook Server**
   ```bash
   pip install flask
   python kofi_webhook.py
   ```

3. **Test Webhook**
   - Use Ko-fi's webhook test feature
   - Verify 200 response
   - Check logs for data parsing

## Security Notes:

- QR code is public (safe to share)
- Webhook endpoint should use HTTPS
- Verify webhook signatures (if Ko-fi provides)
- Log all webhook data for debugging
- Return 200 even on errors to avoid retries

## File Location:

```
premium-website/
├── index.html
├── style.css
├── script.js
├── qrcode.png          ← Place your QR code here
└── README_QRCODE.md    ← This file
```

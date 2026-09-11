# 🌟 Constellation Premium Website

Official premium subscription website for Constellation RNG Bot.

## 🚀 Features

- **Space-themed Design** - Beautiful cosmic interface with animated stars
- **Responsive Layout** - Works on all devices (desktop, tablet, mobile)
- **Interactive Elements** - Smooth animations and transitions
- **Premium Tiers** - Basic and Pro subscription options
- **Purchase Modal** - Built-in purchase form (ready for payment integration)
- **Easter Egg** - Konami code surprise! (↑↑↓↓←→←→BA)

## 📁 Files

```
premium-website/
├── index.html      # Main HTML structure
├── style.css       # All styling and animations
├── script.js       # Interactive functionality
└── README.md       # This file
```

## 🎨 Design Elements

### Color Scheme
- Primary: `#6366f1` (Indigo)
- Secondary: `#8b5cf6` (Purple)
- Accent: `#ec4899` (Pink)
- Background: `#0a0a1a` (Dark Space)
- Gold: `#ffd700` (Premium highlight)

### Fonts
- **Orbitron** - Headers and titles (space-tech feel)
- **Space Grotesk** - Body text (modern and readable)

### Animations
- ✨ Animated starfield background (3 layers)
- 🪐 Floating planet with rotation
- 💫 Glitch effect on hero title
- 🌟 Pulsing tier badges
- ⭐ Glow effects on exclusive lights
- 🚀 Smooth scroll and hover effects

## 🔧 Setup Instructions

### 1. Quick Start (No Server Needed)
Simply open `index.html` in your browser to view the website locally.

### 2. Using a Local Server (Recommended)

**With Python:**
```bash
cd premium-website
python -m http.server 8000
```
Then visit: `http://localhost:8000`

**With Node.js:**
```bash
cd premium-website
npx http-server
```

**With VS Code:**
Install "Live Server" extension and right-click `index.html` → "Open with Live Server"

### 3. Deploy to Web

**Option A: Netlify (Easiest)**
1. Create account at [netlify.com](https://netlify.com)
2. Drag and drop the `premium-website` folder
3. Your site is live instantly!
4. Get a free subdomain: `yoursite.netlify.app`

**Option B: GitHub Pages**
1. Create a GitHub repository
2. Upload files to the repo
3. Go to Settings → Pages
4. Select branch and save
5. Your site will be at: `username.github.io/repo-name`

**Option C: Custom Domain**
1. Purchase domain (constellation-premium.space recommended)
2. Use any hosting provider (Netlify, Vercel, Cloudflare Pages)
3. Connect your domain following provider instructions

## 💳 Payment Integration

The website includes a purchase modal with a form. To integrate real payments:

### Stripe Integration
```javascript
// In script.js, replace handlePurchase function:
async function handlePurchase(event, tier) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    // Call your backend
    const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tier: tier,
            telegram_id: formData.get('telegram_id'),
            email: formData.get('email')
        })
    });
    
    const { sessionId } = await response.json();
    
    // Redirect to Stripe Checkout
    const stripe = Stripe('your_publishable_key');
    await stripe.redirectToCheckout({ sessionId });
}
```

### PayPal Integration
```javascript
// Add PayPal SDK to index.html:
<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID"></script>

// Then in script.js:
paypal.Buttons({
    createOrder: function(data, actions) {
        return actions.order.create({
            purchase_units: [{
                amount: { value: tier === 'basic' ? '1.99' : '3.99' }
            }]
        });
    },
    onApprove: function(data, actions) {
        return actions.order.capture().then(function(details) {
            // Send details to your server for premium activation
            activatePremium(details);
        });
    }
}).render('#paypal-button-container');
```

## 🔗 Update Links

Before deploying, update these placeholder links in `index.html`:

```html
<!-- Line ~15: Bot username -->
<a href="https://t.me/YourBotUsername">

<!-- Line ~XXX: Admin contact -->
<a href="https://t.me/YourAdminUsername">

<!-- Line ~XXX: Support group -->
<a href="#">Support Group</a>

<!-- Line ~XXX: Updates channel -->
<a href="#">Updates Channel</a>
```

## 🎯 Customization

### Change Prices
Edit in `index.html`:
```html
<!-- Line ~180 for Basic -->
<span class="amount">1.99</span>

<!-- Line ~220 for Pro -->
<span class="amount">3.99</span>
```

### Change Features
Edit the `<ul class="tier-features">` sections in `index.html`.

### Change Colors
Edit CSS variables in `style.css`:
```css
:root {
    --primary-color: #6366f1;    /* Change to your color */
    --secondary-color: #8b5cf6;  /* Change to your color */
    /* etc... */
}
```

## 🎮 Easter Egg

Try the Konami code on the website:
```
↑ ↑ ↓ ↓ ← → ← → B A
```
Shooting stars appear and a secret message shows! 🌠

## 📱 Responsive Breakpoints

- **Desktop**: 1200px+
- **Tablet**: 768px - 1199px
- **Mobile**: < 768px

All sections adapt beautifully to any screen size!

## 🐛 Troubleshooting

### Stars not animating?
- Check if CSS is loaded properly
- Try refreshing the page
- Clear browser cache

### Modal not appearing?
- Check JavaScript console for errors
- Ensure script.js is loaded
- Try in a different browser

### Payment integration not working?
- Check API keys are correct
- Verify backend server is running
- Check CORS settings
- Look at network tab in DevTools

## 📊 Analytics (Optional)

Add Google Analytics by adding this before `</head>` in `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## 🔒 Security Notes

- Never expose payment API keys in frontend code
- Always process payments through a secure backend
- Use HTTPS for production (most hosts provide free SSL)
- Validate all user input on the server side
- Store Telegram IDs securely and privately

## 📞 Support

For issues with the website:
1. Check browser console for errors
2. Verify all files are uploaded correctly
3. Test on different browsers
4. Check responsive design on mobile

## 🎨 Credits

- **Fonts**: Google Fonts (Orbitron, Space Grotesk)
- **Design**: Custom space-themed interface
- **Animations**: Pure CSS (no external libraries)
- **Icons**: Emoji (universal support)

## 📄 License

This website is part of the Constellation RNG Bot project.
Customize freely for your bot!

---

**Made with 💜 for the Constellation community**

Enjoy your beautiful premium website! 🚀✨

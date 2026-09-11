// ===============================================
// CONSTELLATION PREMIUM - JAVASCRIPT
// ===============================================

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(10, 10, 26, 0.95)';
    } else {
        navbar.style.background = 'rgba(10, 10, 26, 0.8)';
    }
});

// Purchase Modal Functions
function openPurchase(tier) {
    const modal = document.getElementById('purchaseModal');
    const content = document.getElementById('modalContent');
    
    // Get user ID from URL parameter or localStorage
    // Users should access this page with ?user_id=123456789
    const urlParams = new URLSearchParams(window.location.search);
    let user_id = urlParams.get('user_id');
    
    // If no URL parameter, try localStorage
    if (!user_id) {
        user_id = localStorage.getItem('telegram_user_id');
    }
    
    // If still no user_id, prompt user to enter it
    if (!user_id) {
        user_id = prompt('Please enter your Telegram User ID\n(You can find it by sending /start to the bot):');
        if (user_id) {
            localStorage.setItem('telegram_user_id', user_id);
        } else {
            alert('Telegram User ID is required to purchase premium!');
            return;
        }
    }
    
    let tierName, tierPrice, tierFeatures;
    
    if (tier === 'basic') {
        tierName = 'Constellation | Basic';
        tierPrice = '$1.99/month';
        tierFeatures = `
            <ul class="modal-features">
                <li>✅ <strong>100,000 Monthly Coins</strong></li>
                <li>✅ <strong>150 Luck Potions/month</strong></li>
                <li>✅ <strong>+250% Permanent Luck Boost</strong></li>
                <li>✅ <strong>2x Coins & EXP Multiplier</strong></li>
                <li>✅ <strong>Permanent Auto-Roll</strong> (Always ON!)</li>
                <li>✅ Special Premium Title</li>
                <li>✅ Priority Support</li>
            </ul>
        `;
    } else {
        tierName = 'Constellation | Pro';
        tierPrice = '$3.99/month';
        tierFeatures = `
            <ul class="modal-features">
                <li>✅ <strong>200,000 Monthly Coins</strong> (2x Basic)</li>
                <li>✅ <strong>300 Luck Potions/month</strong> (2x Basic)</li>
                <li>✅ <strong>+500% Permanent Luck Boost</strong> (2x Basic)</li>
                <li>✅ <strong>2x Coins & EXP Multiplier</strong></li>
                <li>✅ <strong>Permanent Auto-Roll</strong> (Always ON!)</li>
                <li>✅ <strong>3 Exclusive Lights</strong> (Get 2 Random):</li>
                <li style="padding-left: 20px;">🌆 Cybernight, 🎸 O'Sound, 🎻 Remembrance</li>
                <li>✅ <strong>15% Drop During Heaven Approach</strong> ✨👼</li>
                <li>✅ <strong>New Light Preview Access</strong> 🔮</li>
                <li>✅ <strong>30% Shop Discount</strong> 💸</li>
                <li>✅ Elite Premium Title</li>
                <li>✅ Premium Support + Feature Suggestions</li>
            </ul>
        `;
    }
    
    content.innerHTML = `
        <div class="modal-header">
            <h3 class="modal-tier-name">${tierName}</h3>
            <p class="modal-tier-price">${tierPrice}</p>
        </div>
        ${tierFeatures}
        <div class="modal-form">
            <h4>🎯 How to Purchase</h4>
            <div class="purchase-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h5>Scan QR Code</h5>
                        <p>Use your phone camera or Ko-fi app to scan the QR code below</p>
                        <div class="qr-code-container">
                            <img src="qrcode.png" alt="Ko-fi QR Code" class="qr-code">
                            <p class="qr-note">Ko-fi Premium Subscription</p>
                        </div>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h5>Select ${tierName} Tier</h5>
                        <p>Choose the correct membership tier on Ko-fi</p>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h5>Enter Your Telegram ID</h5>
                        <p><strong>IMPORTANT:</strong> Include this in your message:</p>
                        <div class="telegram-id-box">
                            <code>telegram_id: ${user_id}</code>
                            <button onclick="copyTelegramId('${user_id}')" class="btn-copy">📋 Copy</button>
                        </div>
                        <small>⚠️ Without your Telegram ID, we can't activate your premium!</small>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-content">
                        <h5>Complete Payment</h5>
                        <p>Follow Ko-fi's secure checkout process</p>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">5</div>
                    <div class="step-content">
                        <h5>Get Instant Activation</h5>
                        <p>Your premium will activate automatically and you'll receive a Telegram notification!</p>
                    </div>
                </div>
            </div>
            <div class="payment-info">
                <h4>💳 Payment Info</h4>
                <ul>
                    <li>✅ Secure payment via Ko-fi</li>
                    <li>✅ Credit/Debit cards accepted</li>
                    <li>✅ PayPal supported</li>
                    <li>✅ Instant activation</li>
                    <li>✅ Auto-renewal (can cancel anytime)</li>
                </ul>
            </div>
        </div>
        <p class="modal-note">* Premium activates instantly after payment. You'll receive rewards immediately via Telegram bot.</p>
    `;
    
    modal.style.display = 'block';
    
    // Gift toggle
    document.getElementById('gift').addEventListener('change', function() {
        document.getElementById('giftSection').style.display = this.checked ? 'block' : 'none';
    });
}

function closePurchase() {
    document.getElementById('purchaseModal').style.display = 'none';
}

function copyTelegramId(userId) {
    const text = `telegram_id: ${userId}`;
    navigator.clipboard.writeText(text).then(() => {
        alert('✅ Telegram ID copied! Paste this in your Ko-fi message.');
    }).catch(err => {
        alert('Failed to copy. Please copy manually: telegram_id: ' + userId);
    });
}

function handlePurchase(event, tier) {
    // This function is no longer used since we use QR code
    // Kept for backwards compatibility
    event.preventDefault();
    alert('Please scan the QR code to complete your purchase via Ko-fi!');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('purchaseModal');
    if (event.target === modal) {
        closePurchase();
    }
}

// Animated counter for stats (if you want to add stats section)
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        element.textContent = Math.floor(start).toLocaleString();
        
        if (start >= target) {
            element.textContent = target.toLocaleString();
            clearInterval(timer);
        }
    }, 16);
}

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all feature cards, tier cards, etc.
document.addEventListener('DOMContentLoaded', () => {
    const elementsToAnimate = document.querySelectorAll('.feature-card, .tier-card, .light-card, .faq-item');
    
    elementsToAnimate.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Add parallax effect to stars only
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const stars = document.querySelector('.stars');
    const stars2 = document.querySelector('.stars2');
    const stars3 = document.querySelector('.stars3');
    
    if (stars && stars2 && stars3) {
        stars.style.transform = `translateY(-${scrolled * 0.1}px)`;
        stars2.style.transform = `translateY(-${scrolled * 0.15}px)`;
        stars3.style.transform = `translateY(-${scrolled * 0.2}px)`;
    }
});

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-10);
    
    if (konamiCode.join(',') === konamiSequence.join(',')) {
        activateEasterEgg();
    }
});

function activateEasterEgg() {
    // Create shooting stars
    for (let i = 0; i < 20; i++) {
        setTimeout(() => {
            createShootingStar();
        }, i * 200);
    }
    
    // Show secret message
    const message = document.createElement('div');
    message.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        padding: 2rem 3rem;
        border-radius: 20px;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.5rem;
        z-index: 9999;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.6);
        animation: fadeIn 0.5s;
    `;
    message.textContent = '🌟 Secret Unlocked! You found the Constellation! 🌟';
    document.body.appendChild(message);
    
    setTimeout(() => {
        message.remove();
    }, 3000);
}

function createShootingStar() {
    const star = document.createElement('div');
    star.style.cssText = `
        position: fixed;
        top: ${Math.random() * 50}%;
        left: ${Math.random() * 100}%;
        width: 2px;
        height: 2px;
        background: white;
        border-radius: 50%;
        box-shadow: 0 0 10px white;
        animation: shootingStar 1s linear;
        pointer-events: none;
        z-index: 9998;
    `;
    
    document.body.appendChild(star);
    
    setTimeout(() => {
        star.remove();
    }, 1000);
}

// Add CSS for shooting star animation
const style = document.createElement('style');
style.textContent = `
    @keyframes shootingStar {
        0% {
            transform: translate(0, 0);
            opacity: 1;
        }
        100% {
            transform: translate(300px, 300px);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    }
    
    .modal-features {
        list-style: none;
        text-align: left;
        margin: 2rem 0;
    }
    
    .modal-features li {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(99, 102, 241, 0.1);
    }
    
    .modal-form {
        margin-top: 2rem;
        text-align: left;
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 0.5rem;
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .form-group input,
    .form-group select {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        background: var(--bg-dark);
        color: var(--text-primary);
        font-size: 1rem;
    }
    
    .form-group input:focus,
    .form-group select:focus {
        outline: none;
        border-color: var(--primary-color);
    }
    
    .form-group small {
        display: block;
        margin-top: 0.25rem;
        color: var(--text-secondary);
        font-size: 0.875rem;
    }
    
    .form-group.checkbox {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .form-group.checkbox input {
        width: auto;
    }
    
    .btn-purchase {
        width: 100%;
        margin-top: 1rem;
    }
    
    .modal-note {
        margin-top: 1.5rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-align: center;
    }
    
    .modal-tier-name {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .modal-tier-price {
        font-size: 1.5rem;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .gift-section {
        background: rgba(99, 102, 241, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
`;
document.head.appendChild(style);

console.log('🌟 Constellation Premium - Loaded successfully!');
console.log('💡 Try the Konami code for a surprise! (↑↑↓↓←→←→BA)');

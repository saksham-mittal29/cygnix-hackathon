/**
 * LandingPage.js
 * ──────────────
 * Full-screen dark ambient splash screen inspired by the Nest Learning Thermostat.
 * Shows a circular thermostat dial with live temperature, time, and Cygnix branding.
 * Clicking anywhere triggers a GSAP morph-out animation and reveals the main app.
 */

export function renderLandingPage(onEnter) {
  const landing = document.createElement("div");
  landing.className = "landing-page";
  landing.id = "landing-page";

  // Get current time
  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true });
  const dateStr = now.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" });

  landing.innerHTML = `
    <div class="landing-ambient-bg">
      <div class="landing-glow-orb landing-glow-1"></div>
      <div class="landing-glow-orb landing-glow-2"></div>
      <div class="landing-glow-orb landing-glow-3"></div>
    </div>

    <div class="landing-content" id="landing-content">
      <!-- Thermostat Dial -->
      <div class="landing-dial" id="landing-dial">
        <svg class="landing-dial-svg" viewBox="0 0 300 300">
          <!-- Outer Ring -->
          <circle cx="150" cy="150" r="140" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="2"/>
          
          <!-- Tick Marks -->
          ${generateTickMarks()}
          
          <!-- Temperature Arc (animated) -->
          <circle 
            cx="150" cy="150" r="120" 
            fill="none" 
            stroke="url(#dialGradient)" 
            stroke-width="4"
            stroke-dasharray="754"
            stroke-dashoffset="377"
            stroke-linecap="round"
            transform="rotate(-90 150 150)"
            class="landing-arc"
            id="landing-arc"
          />
          
          <!-- Inner Glass Circle -->
          <circle cx="150" cy="150" r="105" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
          
          <!-- Gradient Definition -->
          <defs>
            <linearGradient id="dialGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#3b82f6"/>
              <stop offset="50%" stop-color="#06b6d4"/>
              <stop offset="100%" stop-color="#10b981"/>
            </linearGradient>
            <radialGradient id="innerGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="rgba(59,130,246,0.15)"/>
              <stop offset="100%" stop-color="rgba(0,0,0,0)"/>
            </radialGradient>
          </defs>
          
          <!-- Inner Glow -->
          <circle cx="150" cy="150" r="100" fill="url(#innerGlow)"/>
        </svg>

        <!-- Temperature Display (overlaid on center) -->
        <div class="landing-temp-display">
          <div class="landing-temp-value" id="landing-temp-value">72</div>
          <div class="landing-temp-unit">°F</div>
        </div>

        <!-- Status Ring Text -->
        <div class="landing-dial-status">
          <span class="landing-status-dot"></span>
          <span>COOLING</span>
        </div>
      </div>

      <!-- Info Below Dial -->
      <div class="landing-info">
        <div class="landing-time">${timeStr}</div>
        <div class="landing-date">${dateStr}</div>
      </div>

      <!-- Branding -->
      <div class="landing-brand">
        <div class="landing-brand-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="28" height="28">
            <circle cx="12" cy="12" r="5" stroke="#3b82f6" stroke-width="2" stroke-dasharray="16 16"/>
            <path d="M3 15h18" stroke="rgba(255,255,255,0.7)" stroke-width="2" stroke-linecap="round"/>
            <path d="M7 19h10" stroke="rgba(255,255,255,0.3)" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="landing-brand-name">Cygnix</span>
        <span class="landing-brand-tagline">AI Climate Intelligence</span>
      </div>

      <!-- CTA -->
      <div class="landing-cta" id="landing-cta">
        <div class="landing-cta-pulse"></div>
        <span>Click anywhere to enter</span>
      </div>
    </div>
  `;

  // Entrance animation
  setTimeout(() => {
    if (typeof gsap !== "undefined") {
      const tl = gsap.timeline();
      tl.from("#landing-dial", { scale: 0.5, opacity: 0, duration: 1.2, ease: "elastic.out(1, 0.6)" })
        .from(".landing-info", { y: 30, opacity: 0, duration: 0.6, ease: "power2.out" }, "-=0.5")
        .from(".landing-brand", { y: 20, opacity: 0, duration: 0.5, ease: "power2.out" }, "-=0.3")
        .from("#landing-cta", { opacity: 0, duration: 0.8, ease: "power2.out" }, "-=0.2");

      // Animate the arc
      gsap.to("#landing-arc", {
        strokeDashoffset: 200,
        duration: 2,
        ease: "power2.out",
        delay: 0.5
      });

      // Subtle floating animation on the dial
      gsap.to("#landing-dial", {
        y: -8,
        duration: 3,
        ease: "sine.inOut",
        yoyo: true,
        repeat: -1
      });
    }
  }, 50);

  // Click to enter
  landing.addEventListener("click", () => {
    if (typeof gsap !== "undefined") {
      const tl = gsap.timeline({
        onComplete: () => {
          landing.remove();
          onEnter();
        }
      });

      tl.to("#landing-cta", { opacity: 0, duration: 0.2 })
        .to(".landing-info, .landing-brand", { opacity: 0, y: -20, duration: 0.3, stagger: 0.05 }, "-=0.1")
        .to("#landing-dial", { scale: 15, opacity: 0, duration: 0.8, ease: "power3.in" }, "-=0.1")
        .to(".landing-page", { opacity: 0, duration: 0.3 }, "-=0.3");
    } else {
      landing.remove();
      onEnter();
    }
  });

  return landing;
}

function generateTickMarks() {
  let marks = "";
  for (let i = 0; i < 60; i++) {
    const angle = (i * 6) - 90;
    const isMajor = i % 5 === 0;
    const r1 = isMajor ? 130 : 133;
    const r2 = 137;
    const rad = (angle * Math.PI) / 180;
    const x1 = 150 + r1 * Math.cos(rad);
    const y1 = 150 + r1 * Math.sin(rad);
    const x2 = 150 + r2 * Math.cos(rad);
    const y2 = 150 + r2 * Math.sin(rad);
    const opacity = isMajor ? 0.4 : 0.15;
    const width = isMajor ? 1.5 : 0.8;
    marks += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="rgba(255,255,255,${opacity})" stroke-width="${width}"/>`;
  }
  return marks;
}

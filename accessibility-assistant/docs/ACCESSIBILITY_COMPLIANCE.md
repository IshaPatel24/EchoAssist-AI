# VoiceForge — Accessibility Compliance Document

## Overview
VoiceForge is built accessibility-first, following WCAG 2.1 AA guidelines.

## WCAG 2.1 AA Compliance

### Perceivable
- 1.1.1 Non-text Content: All UI icons have aria-label or aria-hidden attributes
- 1.3.1 Info and Relationships: Semantic HTML with ARIA roles (main, banner, region, log)
- 1.4.3 Contrast (Minimum): Normal mode meets AA; High contrast mode exceeds AAA
- 1.4.4 Resize Text: CSS variables allow font scaling to 200%

### Operable
- 2.1.1 Keyboard: Full keyboard navigation
- 2.4.1 Bypass Blocks: Skip link provided
- 2.4.7 Focus Visible: 3px accent-colored focus outline

### Understandable
- 3.1.1 Language of Page: lang="en" set on HTML element
- 3.3.2 Labels or Instructions: All form fields have labels

### Robust
- 4.1.2 Name, Role, Value: ARIA attributes used correctly
- 4.1.3 Status Messages: aria-live="polite" on status areas

## Voice-First Accessibility Features

| Feature | Implementation |
|---------|---------------|
| Screen reader mode | Stores in Qdrant; auto-generates TTS for all responses |
| Large text | CSS variable system: medium / large / x-large |
| High contrast | Dark high-contrast theme via data-contrast attribute |
| Keyboard navigation | All controls reachable and operable via keyboard |
| Reduce motion | Respects prefers-reduced-motion + manual toggle |
| Voice-only mode | Entire app usable without mouse or keyboard |
| Audio feedback | TTS via ElevenLabs or gTTS for all agent responses |
| Session persistence | Qdrant stores preferences across sessions |

## Disability Use Cases

### Visual Impairments
- Screen reader compatible (tested with NVDA + Chrome)
- High contrast mode for low vision
- Large text modes
- Audio readback of all generated documents

### Motor Impairments
- Voice-only interaction — zero mouse/keyboard required
- Large click targets (80px mic button)
- Keyboard navigation fallback

### Cognitive Disabilities
- Simple, clear language
- Step-by-step guided workflows
- Persistent memory via Qdrant
- Status messages clearly communicated

## Testing
Tested with: NVDA + Chrome, VoiceOver + Safari, keyboard-only, 400% zoom

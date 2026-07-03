{
  "product": {
    "name": "iProd OS / MemoGraph OS",
    "design_intent": "Premium personal command center (AI-first second brain). Calm, ordered, decisive. Dark-mode-first glassmorphism bento dashboard. Not a to-do list; not a chat app.",
    "audience": "Multipotential entrepreneurs / founders / knowledge workers who want a calm, high-end operating system for ideas, projects, tasks, areas, and decisions.",
    "brand_attributes": [
      "calm authority",
      "precision",
      "quiet luxury",
      "high-performance",
      "trustworthy",
      "AI-native but not gimmicky"
    ]
  },

  "inspiration_fusion": {
    "layout_principle": "Bento grid command center (Raycast/Notion Calendar-like compartmentalization) with strict hierarchy: tile size = priority.",
    "interaction_principle": "Linear/Superhuman-like speed + keyboard-first affordances + subtle glow focus states.",
    "material_principle": "Dark glassmorphism: frosted surfaces, hairline borders, inner highlights, deep shadows; gradients only as large, mild background accents (<=20% viewport).",
    "references": {
      "search_terms_used": [
        "premium dark glassmorphism productivity dashboard bento grid",
        "dark mode glassmorphism color palette deep navy graphite teal sage"
      ],
      "notes": [
        "Use bento tiles with consistent padding and strong typographic hierarchy.",
        "Glass surfaces must keep WCAG contrast; increase surface opacity behind dense text.",
        "Avoid purple/pink gradients; keep accents teal/sage/ice-cyan with restrained glow."
      ]
    }
  },

  "typography": {
    "font_pairing": {
      "display": {
        "name": "Space Grotesk",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "H1/H2, tile titles, key numbers"
      },
      "body": {
        "name": "Inter",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "Body, labels, UI copy (bilingual-friendly)"
      },
      "mono": {
        "name": "JetBrains Mono",
        "fallback": "ui-monospace, SFMono-Regular",
        "usage": "Scores, timestamps, formulas, small metrics"
      }
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "tile_title": "text-sm font-medium tracking-tight",
      "kpi_number": "text-2xl md:text-3xl font-semibold tracking-tight",
      "body": "text-sm md:text-base leading-relaxed",
      "caption": "text-xs text-muted-foreground"
    },
    "bilingual_rules": [
      "Prefer 2-line clamps for titles: use Tailwind line-clamp-2 on tile headings.",
      "Avoid fixed widths for buttons; use px-3/px-4 and whitespace-nowrap only for short labels.",
      "Use icon+label patterns; allow label wrap on mobile."
    ]
  },

  "color_system": {
    "mode": "dark-default",
    "palette_name": "Nebula Sage (Deep Navy + Graphite Teal + Sage)",
    "semantic_tokens_hsl_for_shadcn": {
      "note": "These map to shadcn's HSL tokens in index.css. Keep dark as the primary experience.",
      "dark": {
        "background": "215 62% 10%",
        "foreground": "210 33% 96%",
        "card": "215 55% 12%",
        "card-foreground": "210 33% 96%",
        "popover": "215 55% 12%",
        "popover-foreground": "210 33% 96%",
        "primary": "190 34% 42%",
        "primary-foreground": "210 33% 98%",
        "secondary": "215 28% 18%",
        "secondary-foreground": "210 33% 96%",
        "muted": "215 22% 18%",
        "muted-foreground": "215 15% 70%",
        "accent": "170 14% 60%",
        "accent-foreground": "215 62% 10%",
        "destructive": "0 62% 42%",
        "destructive-foreground": "210 33% 96%",
        "border": "215 22% 22%",
        "input": "215 22% 22%",
        "ring": "190 34% 52%"
      }
    },
    "hex_reference": {
      "bg_primary": "#0A192A",
      "bg_secondary": "#1C242E",
      "text_primary": "#E6EDF3",
      "text_muted": "#94A3B8",
      "accent_primary": "#4A7B8C",
      "accent_secondary": "#8FA6A0",
      "danger": "#B84A4A",
      "warning": "#C7A24A",
      "success": "#4A8C6E"
    },
    "gradients_allowed": {
      "hero_backdrop_only": {
        "css": "radial-gradient(900px circle at 20% 10%, rgba(74,123,140,0.18), transparent 55%), radial-gradient(700px circle at 80% 20%, rgba(143,166,160,0.12), transparent 60%)",
        "rule": "Use only as page background decoration; keep under 20% perceived coverage; never behind dense text blocks."
      }
    },
    "state_colors": {
      "focus_glow": "rgba(74,123,140,0.22)",
      "hover_glow": "rgba(143,166,160,0.14)",
      "divider": "rgba(230,237,243,0.08)"
    }
  },

  "design_tokens": {
    "css_custom_properties": {
      "note": "Add these to /frontend/src/index.css under :root and .dark. Use for consistent glass + motion.",
      "glass": {
        "--glass-bg": "rgba(20, 34, 53, 0.22)",
        "--glass-bg-strong": "rgba(20, 34, 53, 0.34)",
        "--glass-border": "rgba(230, 237, 243, 0.10)",
        "--glass-border-strong": "rgba(74, 123, 140, 0.22)",
        "--glass-blur": "16px",
        "--glass-shadow": "0 18px 50px rgba(0,0,0,0.45)",
        "--glass-shadow-soft": "0 10px 30px rgba(0,0,0,0.35)",
        "--glass-inner-highlight": "inset 0 1px 0 rgba(255,255,255,0.06)"
      },
      "radius": {
        "--radius-card": "18px",
        "--radius-control": "12px",
        "--radius-chip": "999px"
      },
      "spacing": {
        "--space-1": "4px",
        "--space-2": "8px",
        "--space-3": "12px",
        "--space-4": "16px",
        "--space-5": "20px",
        "--space-6": "24px",
        "--space-8": "32px"
      },
      "motion": {
        "--ease-out": "cubic-bezier(0.16, 1, 0.3, 1)",
        "--ease-in": "cubic-bezier(0.7, 0, 0.84, 0)",
        "--dur-1": "120ms",
        "--dur-2": "180ms",
        "--dur-3": "260ms"
      }
    },
    "tailwind_utilities_recipes": {
      "app_background": "bg-background text-foreground [background-image:var(--app-bg)]",
      "glass_card": "rounded-[var(--radius-card)] bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)] border border-[var(--glass-border)] shadow-[var(--glass-shadow-soft)] [box-shadow:var(--glass-shadow-soft)] [--tw-backdrop-blur:blur(var(--glass-blur))]",
      "glass_card_strong": "rounded-[var(--radius-card)] bg-[var(--glass-bg-strong)] backdrop-blur-[var(--glass-blur)] border border-[var(--glass-border-strong)] shadow-[var(--glass-shadow)] [box-shadow:var(--glass-shadow)]",
      "hairline_divider": "border-t border-white/10",
      "focus_ring": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-0",
      "hover_lift": "transition-[background-color,box-shadow,border-color,opacity] duration-200 hover:shadow-[0_18px_50px_rgba(0,0,0,0.55)] hover:border-white/15",
      "press": "active:scale-[0.99]"
    }
  },

  "layout": {
    "grid_system": {
      "desktop": "12 columns, gap-4 (16px), max content width 1280–1440, outer padding px-6",
      "tablet": "6 columns, gap-3 (12px), px-4",
      "mobile": "4 columns, gap-3 (12px), px-4",
      "bento_rule": "Tile size communicates priority. Only 1 hero tile per screen. Avoid more than 2 dense tables per viewport."
    },
    "shell": {
      "sidebar": {
        "width": "w-[264px] (desktop), collapsible to icon rail w-[72px]",
        "style": "glass sidebar with stronger opacity; active item has subtle teal glow + left indicator",
        "nav_items": [
          "Dashboard",
          "Inbox",
          "Projects",
          "Next Actions",
          "Areas",
          "Incubator",
          "Reviews",
          "Settings"
        ]
      },
      "header": {
        "height": "h-14",
        "contents": "Search (Command), Quick Add, Focus Mode toggle, Language toggle, Profile",
        "behavior": "Sticky on scroll with slight opacity increase + blur"
      }
    },
    "dashboard_bento_map": {
      "hero_tile": "Focus of the Day + Top 3 priorities (spans 6–8 cols desktop)",
      "support_tiles": [
        "Today’s Next Actions (4–6 cols)",
        "Active Projects (4 cols)",
        "Inbox Unprocessed Count (2 cols)",
        "Weekly Review Reminder (2–4 cols)",
        "Areas Summary (4 cols)",
        "Incubated Ideas (2–4 cols)"
      ]
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/command.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/slider.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/switch.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/calendar.jsx",
        "/app/frontend/src/components/ui/sonner.jsx"
      ]
    },
    "recipes": {
      "bento_card": {
        "base": "glass_card hover_lift",
        "padding": "p-4 md:p-5",
        "header": "flex items-start justify-between gap-3",
        "title": "text-sm font-medium text-foreground/90",
        "subtitle": "text-xs text-muted-foreground",
        "footer": "mt-4 flex items-center justify-between"
      },
      "priority_score": {
        "visual": "Use Progress + mono number. Show formula tooltip: Urgency×Impact×StrategicAlignment÷MentalCost.",
        "classes": "flex items-center gap-3",
        "progress": "h-2 bg-white/10 [&>div]:bg-[hsl(var(--primary))]",
        "badge": "font-mono text-xs px-2 py-1 rounded-md bg-white/5 border border-white/10"
      },
      "task_chip": {
        "shape": "pill",
        "classes": "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs bg-white/5 border border-white/10 text-foreground/85",
        "variants": {
          "deep_work": "border-[rgba(74,123,140,0.35)] bg-[rgba(74,123,140,0.10)]",
          "light_work": "border-white/10 bg-white/5",
          "quick_admin": "border-[rgba(199,162,74,0.35)] bg-[rgba(199,162,74,0.10)]",
          "review": "border-[rgba(143,166,160,0.35)] bg-[rgba(143,166,160,0.10)]"
        }
      },
      "ai_suggestion_panel": {
        "container": "glass_card_strong p-4",
        "header": "flex items-center justify-between",
        "tone": "Feels like an analyst panel: concise bullets, confidence meter, suggested action buttons.",
        "confidence": "Use Progress h-1.5 with muted track; label in mono xs.",
        "cta_buttons": "Primary: teal; Secondary: ghost with border."
      },
      "quick_capture_modal": {
        "component": "Dialog",
        "layout": "Two tabs: Text / Voice. Voice shows waveform placeholder + transcription area.",
        "glass": "Use glass_card_strong for modal content; keep backdrop dim (bg-black/60).",
        "inputs": "Use Input/Textarea with bg-white/5 border-white/10; focus ring teal.",
        "actions": "Primary Save, Secondary 'Send to Inbox'."
      },
      "inbox_processing_drawer": {
        "component": "Drawer or Sheet (right side)",
        "layout": "Left: inbox list; Right drawer: selected note + AI suggestions + convert buttons.",
        "convert_actions": [
          "Convert to Project",
          "Convert to Next Action",
          "Send to Incubator",
          "Assign Area"
        ]
      },
      "weekly_review_box": {
        "tone": "Executive summary: stuck, urgent, time sinks, conflicts, recommendations.",
        "layout": "Accordion sections with short bullets; each section has a 'Resolve now' CTA.",
        "component": "Accordion + Card"
      },
      "empty_states": {
        "rule": "Never show blank glass. Provide a calm prompt + one primary action.",
        "copy_style": "Short, decisive. Bilingual-friendly.",
        "skeleton": "Use Skeleton with rounded-xl and subtle shimmer (opacity only)."
      }
    }
  },

  "motion": {
    "library": "Framer Motion",
    "principles": [
      "Soft lift on hover (shadow + border), not big scale.",
      "Entrance: fade+slide 6–10px with ease-out.",
      "Respect prefers-reduced-motion.",
      "No universal transitions; only transition background-color, border-color, box-shadow, opacity."
    ],
    "microinteractions": {
      "bento_hover": "onHover: shadow deepens + border brightens + subtle glow",
      "button_press": "active scale 0.99 + opacity 0.95",
      "drawer_open": "spring, stiffness 380, damping 34",
      "focus_mode": "toggle animates a soft vignette overlay (opacity only)"
    }
  },

  "accessibility": {
    "contrast": [
      "On glass surfaces, if text contrast drops, increase glass opacity to --glass-bg-strong.",
      "Use visible focus rings on all controls (ring token)."
    ],
    "keyboard": [
      "Command palette (shadcn Command) must be fully keyboard navigable.",
      "Provide shortcuts hints in tooltips (e.g., ⌘K / Ctrl+K)."
    ],
    "reduced_motion": "Wrap motion components with prefers-reduced-motion checks; disable parallax and springy transitions."
  },

  "testing_attributes": {
    "rule": "All interactive and key informational elements MUST include data-testid in kebab-case.",
    "examples": [
      "data-testid=\"sidebar-nav-dashboard\"",
      "data-testid=\"header-global-search\"",
      "data-testid=\"quick-capture-open-button\"",
      "data-testid=\"quick-capture-save-button\"",
      "data-testid=\"inbox-item\"",
      "data-testid=\"inbox-process-drawer\"",
      "data-testid=\"ai-suggestion-convert-to-project\"",
      "data-testid=\"project-card\"",
      "data-testid=\"priority-score-value\"",
      "data-testid=\"language-toggle\""
    ]
  },

  "image_urls": {
    "note": "Image provider tool unavailable in this environment. Use CSS noise + gradients instead of photos for premium calm.",
    "background_textures": [
      {
        "category": "noise-overlay",
        "description": "CSS-only subtle grain overlay for depth (preferred over images).",
        "url": "CSS_ONLY"
      }
    ],
    "illustrations": [
      {
        "category": "empty-state",
        "description": "Use Lottie abstract minimal line animations (self-host later).",
        "url": "PLACEHOLDER_LOTTIE"
      }
    ]
  },

  "extra_libraries": {
    "recommended": [
      {
        "name": "framer-motion",
        "why": "Microinteractions + drawer/modal transitions + bento entrance animations",
        "install": "npm i framer-motion",
        "usage": "Use motion.div for tiles; AnimatePresence for drawers/modals"
      },
      {
        "name": "recharts",
        "why": "Priority score mini charts, weekly review trends (lightweight, readable)",
        "install": "npm i recharts",
        "usage": "Use AreaChart with low-opacity fill; avoid gradients on small charts"
      }
    ]
  },

  "instructions_to_main_agent": [
    "Remove CRA default App.css centering patterns; do not center the whole app container.",
    "Set dark mode by default by applying class 'dark' on <html> or <body> at app bootstrap.",
    "Update /frontend/src/index.css tokens to match Nebula Sage palette; keep shadcn HSL structure.",
    "Implement an AppShell: glass sidebar + sticky header + main bento grid content.",
    "Use shadcn Card as base but override with glass recipes (bg opacity + backdrop-blur + hairline borders).",
    "Ensure every button/input/nav item has data-testid.",
    "Bilingual: avoid fixed widths; use truncation + tooltips for long labels; test Italian strings.",
    "Gradients: only as background decoration; never on small elements; never purple/pink combos."
  ],

  "general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}

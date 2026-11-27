"""CivicStack UI layer: dark/light design system, HTML components and answer-report rendering.

Pure Python (no Streamlit import) so it can be tested on its own. app.py calls these and does the
Streamlit layout. Nothing here touches the pipeline, the retriever or the data.
"""
from __future__ import annotations

import html
import re
from collections import OrderedDict

# ----------------------------------------------------------------------------- constants
TIER_LABEL = {1: "Tier 1 · Official", 2: "Tier 2 · Practitioner", 3: "Tier 3 · Reported experience"}

EXAMPLES = [
    "What documents are needed to register a Private Limited company?",
    "What is the minimum number of directors for a Private Limited company?",
    "What is the fee for filing the DIR-3 KYC Web form?",
    "How long can a reserved company name be extended and at what fee?",
]

_ICONS = {
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
    "scale": '<path d="M12 3v18M6 21h12M5 7h14"/><path d="M5 7l-3 7a3 3 0 0 0 6 0zM19 7l-3 7a3 3 0 0 0 6 0z"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>',
    "stack": '<path d="M12 2l9 4.5-9 4.5-9-4.5z"/><path d="M3 11.5l9 4.5 9-4.5"/><path d="M3 16.5l9 4.5 9-4.5"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    "ext": '<path d="M7 17L17 7M9 7h8v8"/>',
}


def icon(name: str, size: int = 20) -> str:
    return (f'<svg class="cs-ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_ICONS[name]}</svg>')


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


# ----------------------------------------------------------------------------- design system (CSS)
_DARK = """
--bg:#070B16; --bg2:#0D1426; --surface:rgba(255,255,255,.045); --surface2:rgba(255,255,255,.08);
--border:rgba(148,163,184,.16); --border2:rgba(148,163,184,.32);
--ink:#E8EDF7; --muted:#97A3BA; --faint:#6B7792;
--accent:#2DD4BF; --accent2:#3B82F6; --on-accent:#04141B;
--grad:linear-gradient(135deg,#2DD4BF 0%,#3B82F6 100%);
--shadow:0 12px 40px rgba(0,0,0,.38); --glow:0 0 0 1px rgba(45,212,191,.45),0 10px 34px rgba(45,212,191,.22);
--input:rgba(255,255,255,.05); --code:rgba(255,255,255,.06);
--t1:#34D399; --t1bg:rgba(52,211,153,.13); --t2:#FBBF24; --t2bg:rgba(251,191,36,.13); --t3:#60A5FA; --t3bg:rgba(96,165,250,.14);
--warn:#FBBF24; --warnbg:rgba(251,191,36,.10); --bad:#F87171; --badbg:rgba(248,113,113,.10);
--fx:radial-gradient(900px 520px at 8% -8%,rgba(45,212,191,.17),transparent 60%),radial-gradient(820px 520px at 96% 2%,rgba(59,130,246,.20),transparent 58%),radial-gradient(700px 500px at 50% 110%,rgba(99,102,241,.10),transparent 60%);
color-scheme:dark;
"""
_LIGHT = """
--bg:#F3F6FC; --bg2:#FFFFFF; --surface:rgba(255,255,255,.82); --surface2:rgba(15,23,42,.045);
--border:rgba(15,23,42,.10); --border2:rgba(15,23,42,.22);
--ink:#0F172A; --muted:#475569; --faint:#7A869B;
--accent:#0D9488; --accent2:#2563EB; --on-accent:#FFFFFF;
--grad:linear-gradient(135deg,#0D9488 0%,#2563EB 100%);
--shadow:0 10px 34px rgba(15,23,42,.08); --glow:0 0 0 1px rgba(13,148,136,.45),0 10px 30px rgba(13,148,136,.20);
--input:#FFFFFF; --code:rgba(15,23,42,.06);
--t1:#047857; --t1bg:rgba(4,120,87,.10); --t2:#A16207; --t2bg:rgba(202,138,4,.14); --t3:#1D4ED8; --t3bg:rgba(37,99,235,.10);
--warn:#A16207; --warnbg:rgba(202,138,4,.10); --bad:#B91C1C; --badbg:rgba(185,28,28,.08);
--fx:radial-gradient(900px 520px at 8% -8%,rgba(13,148,136,.13),transparent 60%),radial-gradient(820px 520px at 96% 2%,rgba(37,99,235,.13),transparent 58%);
color-scheme:light;
"""

_STATIC_CSS = """

html, body, .stApp, [class*="st-"], button, input, textarea{font-family:'Inter',-apple-system,'Segoe UI',Roboto,Arial,sans-serif;}
.stApp{background:var(--fx), var(--bg); background-attachment:fixed; color:var(--ink); transition:background-color .35s ease,color .35s ease;}
[data-testid="stAppViewContainer"], [data-testid="stMain"]{background:transparent;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer{visibility:hidden;}
.block-container{max-width:1120px; padding-top:1.1rem; padding-bottom:3rem;}
::selection{background:rgba(45,212,191,.35);}
*{scrollbar-width:thin; scrollbar-color:var(--border2) transparent;}
a{color:var(--accent);}
:focus-visible{outline:2px solid var(--accent); outline-offset:2px;}

:where([data-testid="stMarkdownContainer"]) :where(p,li,td,th,h1,h2,h3,h4,h5,h6,strong,em){color:var(--ink);}
:where([data-testid="stMarkdownContainer"]) code{background:var(--code); color:var(--ink);}
:where([data-testid="stCaptionContainer"], .stCaption, small){color:var(--muted) !important;}
[data-testid="stWidgetLabel"] p, label p{color:var(--ink) !important;}
h3{font-size:1.2rem !important; font-weight:700 !important; letter-spacing:-.01em;}

/* ---------- navigation (tabs as a glass pill bar) ---------- */
[data-testid="stTabs"] [role="tablist"]{gap:4px; background:var(--surface); border:1px solid var(--border); border-radius:16px;
  padding:5px; width:fit-content; max-width:100%; overflow-x:auto; backdrop-filter:blur(12px); box-shadow:var(--shadow);}
[data-testid="stTabs"] button[role="tab"]{border-radius:11px; padding:8px 16px; font-weight:600; font-size:.92rem; color:var(--muted);
  transition:background .2s, color .2s, transform .15s; height:auto;}
[data-testid="stTabs"] button[role="tab"] p{color:inherit !important; font-weight:600;}
[data-testid="stTabs"] button[role="tab"]:hover{color:var(--ink); background:var(--surface2);}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:var(--on-accent); background:var(--grad); box-shadow:var(--glow);}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"]{display:none;}
[data-testid="stTabs"] [role="tabpanel"]{animation:csUp .5s cubic-bezier(.2,.8,.2,1) both; padding-top:1.1rem;}

/* ---------- inputs & buttons ---------- */
.stTextArea textarea, .stTextInput input{background:var(--input) !important; color:var(--ink) !important; border:1px solid var(--border2) !important;
  border-radius:16px !important; font-size:1.02rem !important; padding:14px 16px !important; backdrop-filter:blur(10px);
  transition:border-color .2s, box-shadow .2s, background .3s;}
.stTextArea textarea::placeholder, .stTextInput input::placeholder{color:var(--faint) !important; opacity:1;}
.stTextArea textarea:focus, .stTextInput input:focus{border-color:var(--accent) !important; box-shadow:0 0 0 4px rgba(45,212,191,.16), var(--glow) !important;}
.stTextArea [data-baseweb="textarea"], .stTextInput [data-baseweb="input"], .stTextArea [data-baseweb="base-input"], .stTextInput [data-baseweb="base-input"]{background:transparent !important; border:none !important;}
.stButton > button{border-radius:12px; font-weight:600; padding:.55rem 1.05rem; background:var(--surface); color:var(--ink);
  border:1px solid var(--border2); transition:transform .15s ease, box-shadow .2s ease, border-color .2s, background .2s; backdrop-filter:blur(10px);}
.stButton > button p{color:inherit !important; font-weight:600;}
.stButton > button:hover{transform:translateY(-1px); border-color:var(--accent); background:var(--surface2); box-shadow:var(--glow);}
.stButton > button:active{transform:translateY(0) scale(.985);}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"]{background:var(--grad); color:var(--on-accent); border:none;
  box-shadow:0 8px 26px rgba(45,212,191,.28); font-weight:700; letter-spacing:.01em;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover{filter:brightness(1.07); box-shadow:var(--glow); background:var(--grad);}
[data-testid="stToggle"] label p{color:var(--muted) !important; font-size:.85rem; font-weight:500;}
[data-testid="stExpander"]{background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:14px !important; backdrop-filter:blur(10px);}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p{color:var(--ink) !important; font-weight:600;}
[data-testid="stExpander"] summary:hover{color:var(--accent) !important;}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--surface); border-color:var(--border) !important; border-radius:18px; backdrop-filter:blur(10px);}

/* ---------- motion ---------- */
@keyframes csUp{from{opacity:0; transform:translateY(14px);} to{opacity:1; transform:none;}}
@keyframes csFade{from{opacity:0;} to{opacity:1;}}
@keyframes csFloat{0%,100%{transform:translate(0,0) scale(1);} 50%{transform:translate(26px,18px) scale(1.08);}}
@keyframes csGrow{from{width:0;}}
@keyframes csShimmer{0%{background-position:-420px 0;} 100%{background-position:420px 0;}}
@keyframes csStage{0%,24%{opacity:1; transform:translateX(4px);} 25%,100%{opacity:.38; transform:none;}}
@keyframes csPulse{0%,100%{box-shadow:0 0 0 0 rgba(45,212,191,.5);} 50%{box-shadow:0 0 0 9px rgba(45,212,191,0);}}
@keyframes csSpin{to{transform:rotate(360deg);}}
.cs-reveal{animation:csUp .55s cubic-bezier(.2,.8,.2,1) both;}
.cs-d1{animation-delay:.06s;} .cs-d2{animation-delay:.12s;} .cs-d3{animation-delay:.18s;} .cs-d4{animation-delay:.24s;} .cs-d5{animation-delay:.3s;}

/* ---------- top bar & hero ---------- */
.cs-top{display:flex; align-items:center; gap:12px; padding:6px 2px 14px 2px;}
.cs-mark{width:38px; height:38px; border-radius:11px; background:var(--grad); color:var(--on-accent); display:flex; align-items:center; justify-content:center; box-shadow:var(--glow);}
.cs-brand{font-weight:800; font-size:1.18rem; letter-spacing:-.02em; color:var(--ink);}
.cs-brand small{font-weight:500; color:var(--muted); font-size:.74rem; margin-left:8px; letter-spacing:0; padding:2px 8px; border:1px solid var(--border2); border-radius:99px;}

.cs-hero{position:relative; overflow:hidden; border:1px solid var(--border); border-radius:26px; padding:clamp(26px,5vw,54px);
  background:var(--surface); backdrop-filter:blur(16px); box-shadow:var(--shadow); animation:csUp .6s cubic-bezier(.2,.8,.2,1) both; margin-bottom:14px;}
.cs-hero.compact{padding:18px 24px; border-radius:20px;}
.cs-orb{position:absolute; border-radius:50%; filter:blur(64px); pointer-events:none; animation:csFloat 15s ease-in-out infinite;}
.cs-orb.a{width:300px; height:300px; background:var(--accent); top:-110px; left:-70px; opacity:.26;}
.cs-orb.b{width:340px; height:340px; background:var(--accent2); right:-110px; bottom:-150px; opacity:.26; animation-delay:-7s;}
.cs-hero-in{position:relative; z-index:1;}
.cs-eyebrow{display:inline-flex; align-items:center; gap:8px; font-size:.78rem; font-weight:600; color:var(--accent); background:var(--t1bg);
  border:1px solid var(--border); padding:5px 12px; border-radius:99px; letter-spacing:.02em;}
.cs-eyebrow i{width:7px; height:7px; border-radius:50%; background:var(--accent); animation:csPulse 2s infinite;}
.stApp .cs-hero h1{font-size:clamp(2.05rem,5.2vw,3.55rem) !important; font-weight:800 !important; letter-spacing:-.035em !important; line-height:1.04 !important;
  margin:16px 0 14px 0 !important; padding:0 !important; color:var(--ink) !important; max-width:15em;}
.stApp .cs-hero.compact h1{font-size:1.5rem !important; margin:8px 0 4px 0 !important;}
.cs-grad{background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent !important; -webkit-text-fill-color:transparent;}
.stApp .cs-hero p{color:var(--muted) !important; font-size:clamp(.98rem,1.6vw,1.12rem); line-height:1.6; max-width:40rem; margin:0 !important;}

.cs-quota{display:inline-flex; align-items:center; gap:10px; font-size:.82rem; color:var(--muted); padding:8px 4px;}
.cs-dots{display:inline-flex; gap:5px;}
.cs-dots i{width:9px; height:9px; border-radius:50%; background:var(--surface2); border:1px solid var(--border2);}
.cs-dots i.on{background:var(--grad); border-color:transparent;}
.cs-label{font-size:.72rem; font-weight:700; color:var(--faint); text-transform:uppercase; letter-spacing:.09em; margin:.7rem 0 .25rem 0;}

/* ---------- cards & grids ---------- */
.cs-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; margin:8px 0 14px 0;}
.cs-card{position:relative; background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:20px; backdrop-filter:blur(12px);
  transition:transform .2s ease, border-color .2s, box-shadow .25s; box-shadow:var(--shadow);}
.cs-card:hover{transform:translateY(-3px); border-color:var(--border2); box-shadow:var(--glow);}
.cs-card .cs-ci{width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;
  background:var(--t1bg); color:var(--accent); border:1px solid var(--border);}
.stApp .cs-card h4{margin:0 0 6px 0 !important; padding:0 !important; font-size:1.02rem !important; font-weight:700 !important; color:var(--ink) !important;}
.stApp .cs-card p{margin:0 !important; color:var(--muted) !important; font-size:.9rem; line-height:1.6;}
.cs-step-n{font-family:'JetBrains Mono',monospace; font-size:.8rem; font-weight:600; color:var(--accent); margin-bottom:10px; display:block;}
.cs-stat{background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:16px 18px; backdrop-filter:blur(12px); box-shadow:var(--shadow);
  transition:transform .2s, border-color .2s;}
.cs-stat:hover{transform:translateY(-2px); border-color:var(--border2);}
.cs-stat b{display:block; font-size:1.8rem; font-weight:800; letter-spacing:-.02em; line-height:1.1; background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;}
.cs-stat span{font-size:.8rem; color:var(--muted);}
.cs-ico{flex:none;}

.cs-badge{display:inline-block; font-size:.7rem; font-weight:700; padding:2px 9px; border-radius:99px; white-space:nowrap; letter-spacing:.01em;}
.cs-badge.t1{background:var(--t1bg); color:var(--t1);} .cs-badge.t2{background:var(--t2bg); color:var(--t2);} .cs-badge.t3{background:var(--t3bg); color:var(--t3);}
.cs-pill{display:inline-flex; align-items:center; gap:6px; font-size:.76rem; font-weight:600; padding:4px 11px; border-radius:99px; background:var(--surface2); color:var(--muted); border:1px solid var(--border);}
.cs-pill.ok{background:var(--t1bg); color:var(--t1);} .cs-pill.warn{background:var(--warnbg); color:var(--warn);} .cs-pill.info{background:var(--t3bg); color:var(--t3);}
.cs-vs{display:inline-block; font-size:.76rem; font-weight:700; padding:5px 12px; border-radius:10px; margin-bottom:10px;}
.cs-vs.v1{background:var(--surface2); color:var(--muted); border:1px solid var(--border);} .cs-vs.v4{background:var(--grad); color:var(--on-accent);}

/* ---------- loading ---------- */
.cs-loading{background:var(--surface); border:1px solid var(--border2); border-radius:20px; padding:22px; backdrop-filter:blur(14px); box-shadow:var(--glow); animation:csFade .3s both;}
.cs-load-head{display:flex; align-items:center; gap:12px; font-weight:700; color:var(--ink); margin-bottom:14px;}
.cs-spin{width:22px; height:22px; border-radius:50%; border:3px solid var(--border2); border-top-color:var(--accent); animation:csSpin .9s linear infinite;}
.cs-stage{display:flex; align-items:center; gap:10px; padding:7px 0; font-size:.92rem; color:var(--muted); opacity:.38; animation:csStage 12s infinite; animation-delay:calc(var(--i) * 3s);}
.cs-stage i{width:8px; height:8px; border-radius:50%; background:var(--accent);}
.cs-skel{height:12px; border-radius:8px; margin-top:10px; background:linear-gradient(90deg,var(--surface2) 25%,var(--border2) 37%,var(--surface2) 63%); background-size:840px 100%; animation:csShimmer 1.6s infinite linear;}

/* ---------- answer report ---------- */
.cs-report{background:var(--surface); border:1px solid var(--border); border-radius:22px; padding:clamp(18px,3vw,30px); backdrop-filter:blur(14px); box-shadow:var(--shadow); margin:10px 0 14px 0;}
.cs-report-head{display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-bottom:16px;}
.cs-rtitle{font-size:.74rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); display:flex; align-items:center; gap:8px;}
.cs-key{position:relative; border-radius:16px; padding:18px 20px 18px 24px; background:linear-gradient(135deg,rgba(45,212,191,.12),rgba(59,130,246,.10)); border:1px solid var(--border2); margin-bottom:18px;}
.cs-key::before{content:""; position:absolute; left:0; top:12px; bottom:12px; width:4px; border-radius:4px; background:var(--grad);}
.cs-key-label{font-size:.7rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); margin-bottom:6px;}
.cs-key-body{font-size:1.1rem; line-height:1.6; font-weight:500; color:var(--ink);}
.cs-key-body p{margin:0 !important; color:var(--ink) !important;}
.cs-sec{font-size:.72rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--faint); margin:18px 0 8px 0;}
.cs-body{color:var(--ink); line-height:1.7; font-size:.98rem;}
.cs-body p{margin:0 0 10px 0 !important; color:var(--ink) !important;}
.cs-body ul, .cs-body ol{margin:6px 0 10px 0; padding-left:1.15rem;}
.cs-body li{margin:7px 0; padding-left:2px; color:var(--ink) !important; line-height:1.65;}
.cs-body li::marker{color:var(--accent);}
.cs-body strong, .cs-key-body strong{color:var(--ink); font-weight:700; background:linear-gradient(transparent 62%,rgba(45,212,191,.22) 0);}
.cs-body h5{margin:14px 0 6px 0; font-size:1rem; color:var(--ink);}
.cs-cite{display:inline-block; font-family:'JetBrains Mono',monospace; font-size:.68rem; font-weight:600; padding:1px 7px; margin:0 1px; border-radius:7px; vertical-align:2px;
  background:var(--t3bg); color:var(--t3); border:1px solid var(--border); cursor:help; transition:background .15s, transform .15s;}
.cs-cite:hover{background:var(--accent); color:var(--on-accent); transform:translateY(-1px);}
.cs-cite-note{font-size:.74rem; color:var(--faint); margin-left:3px;}
.cs-trust{display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin-top:20px; padding-top:18px; border-top:1px solid var(--border);}
.cs-ti{display:flex; gap:11px; align-items:flex-start; padding:11px 12px; border-radius:13px; background:var(--surface2); border:1px solid var(--border);}
.cs-ti .cs-ico{margin-top:1px;} .cs-ti.ok .cs-ico{color:var(--t1);} .cs-ti.warn .cs-ico{color:var(--warn);} .cs-ti.info .cs-ico{color:var(--t3);}
.cs-ti b{display:block; font-size:.84rem; color:var(--ink); font-weight:700;} .cs-ti span{font-size:.76rem; color:var(--muted); line-height:1.4;}
.cs-disc{margin-top:14px; font-size:.76rem; color:var(--faint); line-height:1.5;}
.cs-notice{display:flex; gap:12px; align-items:flex-start; border-radius:16px; padding:16px 18px; border:1px solid var(--border2); background:var(--surface); backdrop-filter:blur(12px); margin:10px 0 14px 0;}
.cs-notice.warn{background:var(--warnbg); border-color:rgba(251,191,36,.35);} .cs-notice.warn .cs-ico{color:var(--warn);}
.cs-notice.err{background:var(--badbg); border-color:rgba(248,113,113,.35);} .cs-notice.err .cs-ico{color:var(--bad);}
.cs-notice.info .cs-ico{color:var(--accent);}
.cs-notice b{display:block; color:var(--ink); font-size:.95rem; margin-bottom:2px;} .cs-notice div{color:var(--muted); font-size:.9rem; line-height:1.55;}

/* ---------- source panels (native <details>) ---------- */
.cs-srcs-title{display:flex; align-items:center; gap:10px; margin:18px 0 8px 0; font-weight:700; color:var(--ink); font-size:.98rem;}
details.cs-src{background:var(--surface); border:1px solid var(--border); border-radius:14px; margin-bottom:9px; backdrop-filter:blur(10px); transition:border-color .2s, box-shadow .25s; animation:csUp .5s both;}
details.cs-src:hover{border-color:var(--border2);} details.cs-src[open]{border-color:var(--accent); box-shadow:var(--glow);}
details.cs-src summary{list-style:none; cursor:pointer; display:flex; align-items:center; gap:12px; padding:12px 14px;}
details.cs-src summary::-webkit-details-marker{display:none;}
details.cs-src summary::after{content:"+"; margin-left:auto; font-size:1.2rem; color:var(--muted);}
details.cs-src[open] summary::after{content:"\\2212"; color:var(--accent);}
.cs-sid{font-family:'JetBrains Mono',monospace; font-size:.74rem; font-weight:700; padding:3px 8px; border-radius:8px; background:var(--surface2); color:var(--ink); border:1px solid var(--border);}
.cs-sname{font-size:.92rem; font-weight:600; color:var(--ink); line-height:1.35; word-break:break-word;}
.cs-smeta{font-size:.76rem; color:var(--muted); margin-top:3px; display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
.cs-sbody{border-top:1px dashed var(--border); margin:0 14px; padding:12px 0 14px 0;}
.cs-excerpt{font-size:.84rem; line-height:1.65; color:var(--muted); background:var(--code); border-radius:10px; padding:11px 13px; max-height:190px; overflow:auto; word-break:break-word;}
.cs-slink{display:inline-flex; gap:6px; align-items:center; margin-top:9px; font-size:.82rem; font-weight:600; color:var(--accent); text-decoration:none;}
.cs-slink:hover{text-decoration:underline;}
.cs-trace{display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 10px 0;}
.cs-kv{font-size:.78rem; background:var(--surface2); border:1px solid var(--border); border-radius:9px; padding:5px 10px; color:var(--ink);} .cs-kv i{font-style:normal; color:var(--faint); margin-right:6px;}
pre.cs-json{font-family:'JetBrains Mono',monospace; font-size:.74rem; line-height:1.55; color:var(--muted); background:var(--code); border-radius:12px; padding:12px 14px; overflow:auto; max-height:320px; white-space:pre-wrap; word-break:break-word;}

/* ---------- compare strip, dashboard ---------- */
.cs-delta{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin:6px 0 14px 0;}
.cs-delta .cs-stat b{font-size:1.15rem;} .cs-delta .cs-stat em{font-style:normal; font-size:.72rem; color:var(--faint); display:block; margin-top:2px;}
.cs-dash{display:grid; grid-template-columns:1.5fr 1fr; gap:14px; margin:8px 0 14px 0;} @media (max-width:820px){.cs-dash{grid-template-columns:1fr;}}
.cs-barrow{margin:12px 0;} .cs-barlab{display:flex; justify-content:space-between; font-size:.84rem; color:var(--muted); margin-bottom:6px;} .cs-barlab b{color:var(--ink);}
.cs-bar{height:11px; border-radius:99px; background:var(--surface2); overflow:hidden;}
.cs-bar > i{display:block; height:100%; width:var(--w); border-radius:inherit; background:var(--grad); animation:csGrow 1.1s cubic-bezier(.2,.8,.2,1) both;}
.cs-bar.v1 > i{background:linear-gradient(90deg,#64748B,#94A3B8);} .cs-bar.sm{height:7px;}
.cs-donut{width:132px; height:132px; border-radius:50%; margin:6px auto 12px auto; display:grid; place-items:center; background:conic-gradient(var(--accent) calc(var(--p) * 1%), var(--surface2) 0);}
.cs-donut > div{width:98px; height:98px; border-radius:50%; background:var(--bg2); display:grid; place-items:center; text-align:center; font-weight:800; font-size:1.35rem; color:var(--ink); line-height:1.1;}
.cs-donut small{display:block; font-size:.66rem; font-weight:600; color:var(--muted);}
.cs-scroll{overflow-x:auto; border-radius:16px; border:1px solid var(--border); background:var(--surface); backdrop-filter:blur(12px);}
table.cs-tbl{width:100%; border-collapse:collapse; min-width:640px;}
.cs-tbl th{font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; color:var(--faint); text-align:left; padding:12px 14px; border-bottom:1px solid var(--border); font-weight:700;}
.cs-tbl td{padding:11px 14px; border-bottom:1px solid var(--border); font-size:.86rem; color:var(--ink); vertical-align:middle;}
.cs-tbl tr:last-child td{border-bottom:none;} .cs-tbl tbody tr{transition:background .15s;} .cs-tbl tbody tr:hover{background:var(--surface2);}
.cs-tbl .qid{font-family:'JetBrains Mono',monospace; font-weight:700; color:var(--accent);} .cs-tbl .qtxt{color:var(--muted); max-width:340px;}
.cs-chip{font-size:.7rem; padding:2px 9px; border-radius:99px; background:var(--surface2); color:var(--muted); border:1px solid var(--border); white-space:nowrap;}
.cs-pass{font-weight:700; font-size:.78rem;} .cs-pass.y{color:var(--t1);} .cs-pass.n{color:var(--bad);}
.cs-pipe{display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px;}
.cs-foot{color:var(--faint); font-size:.78rem; margin-top:2.2rem; padding-top:14px; border-top:1px solid var(--border); text-align:center;}


/* ---------- fixes for real Streamlit rendering ---------- */
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{display:none !important; background:transparent !important;}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"], [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p{
  color:var(--on-accent) !important; background:var(--grad) !important; box-shadow:var(--glow);}
[data-testid="stTabs"] button[role="tab"]{border-bottom:none !important;}
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], .stDeployButton, [data-testid="stStatusWidget"]{display:none !important;}
.stButton > button{height:auto; min-height:2.6rem; white-space:normal; text-align:left;}
.stButton > button p{white-space:normal !important; text-align:left; line-height:1.4;}
.stButton > button[kind="primary"] p, .stButton > button[data-testid="stBaseButton-primary"] p{text-align:center;}
.cs-grid.stats{grid-template-columns:repeat(4,1fr);}
@media (max-width:820px){.cs-grid.stats{grid-template-columns:repeat(2,1fr);}}
.cs-card, .cs-stat, .cs-report, .cs-hero, .cs-src, .cs-scroll, .cs-key, .cs-ti, .cs-notice, .cs-loading, .cs-chip, .cs-pill, .cs-kv,
.stTextArea textarea, .stTextInput input, .stButton > button, [data-testid="stExpander"], [data-testid="stTabs"] [role="tablist"]{
  transition:background-color .35s ease, color .35s ease, border-color .35s ease, box-shadow .25s ease, transform .2s ease;}

@media (max-width:768px){
  .block-container{padding-left:.9rem; padding-right:.9rem; padding-top:.7rem;}
  .cs-hero{border-radius:20px;} .cs-key-body{font-size:1rem;}
  [data-testid="stTabs"] button[role="tab"]{padding:7px 11px; font-size:.84rem;}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important; transition:none !important;}}
"""


def theme_css(dark: bool = True) -> str:
    """Server-side vars as the base, plus a pure-CSS switch driven by the toggle itself (instant, no rerun needed)."""
    tg = '[data-testid="stToggle"] input'
    return ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap">'
            f"<style>:root{{{_DARK if dark else _LIGHT}}}"
            f".stApp:has({tg}:not(:checked)){{{_LIGHT}}}"
            f".stApp:has({tg}:checked){{{_DARK}}}"
            f"{_STATIC_CSS}</style>")


# ----------------------------------------------------------------------------- small helpers
def tier_badge(tier) -> str:
    try:
        t = int(tier)
    except (TypeError, ValueError):
        t = 0
    return f'<span class="cs-badge t{t if t in (1, 2, 3) else 2}">{esc(TIER_LABEL.get(t, "Unrated"))}</span>'


def cited_ids(answer: str) -> list[str]:
    seen: "OrderedDict[str, None]" = OrderedDict()
    for bracket in re.findall(r"\[([^\]]*)\]", answer or ""):
        for sid in re.findall(r"\bS\d+\b", bracket):
            seen.setdefault(sid, None)
    return list(seen)


def split_sources(out: dict) -> tuple[list[dict], list[dict]]:
    srcs = out.get("sources") or []
    ids = cited_ids(out.get("answer", ""))
    cited = sorted([s for s in srcs if s.get("id") in ids], key=lambda s: ids.index(s["id"]))
    other = [s for s in srcs if s.get("id") not in ids]
    return cited, other


def grouped_other_sources(other: list[dict]) -> list[dict]:
    groups: "OrderedDict[str, dict]" = OrderedDict()
    for s in other:
        g = groups.setdefault(s.get("name", ""), {**s, "n": 0, "ids": []})
        g["n"] += 1
        g["ids"].append(s.get("id"))
    return list(groups.values())


def context_excerpts(ctx: str, limit: int = 480) -> dict:
    """Map S1.. to the start of the retrieved passage (parsed from the pipeline's context string)."""
    out = {}
    for block in re.split(r"\n\n(?=\[S\d+\] Tier )", ctx or ""):
        m = re.match(r"\[(S\d+)\] [^\n]*\n(.*)", block, re.S)
        if m:
            txt = re.sub(r"\s+", " ", m.group(2)).strip()
            out[m.group(1)] = txt[:limit] + ("…" if len(txt) > limit else "")
    return out


def answer_kind(out: dict) -> tuple[str, str]:
    ans = (out.get("answer") or "").strip()
    if out.get("sources"):
        n = len(split_sources(out)[0]) or len(out["sources"])
        return "grounded", f"Grounded in {n} cited source{'s' if n != 1 else ''}"
    if ans.startswith("To give a useful comparison"):
        return "clarify", "Needs one more detail"
    if "could not find reported experience" in ans:
        return "limited", "No supporting source found"
    if ans.startswith("I can only give general information"):
        return "refusal", "Out of scope"
    return "plain", "No sources used"


# ----------------------------------------------------------------------------- markdown -> html (small subset)
def _inline(text: str, names: dict) -> str:
    t = esc(text)

    def cite(m):
        body = m.group(1)
        ids = re.findall(r"\bS\d+\b", body)
        rest = re.sub(r"\bS\d+\b", "", body).strip(" ,;")
        chips = "".join(f'<span class="cs-cite" title="{esc(names.get(i, i))}">{i}</span>' for i in ids)
        return chips + (f'<span class="cs-cite-note">{rest}</span>' if rest else "")

    t = re.sub(r"\[(S\d+[^\]]*)\]", cite, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])_(.+?)_(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def md_to_html(text: str, names: dict | None = None) -> str:
    names = names or {}
    out, items, kind = [], [], None

    def flush():
        nonlocal items, kind
        if items:
            tag = "ol" if kind == "ol" else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{i}</li>" for i in items) + f"</{tag}>")
        items, kind = [], None

    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            flush()
            continue
        mb = re.match(r"^[*\-•]\s+(.*)", s)
        mn = re.match(r"^\d+[.)]\s+(.*)", s)
        mh = re.match(r"^#{1,6}\s+(.*)", s)
        if mb:
            if kind != "ul":
                flush(); kind = "ul"
            items.append(_inline(mb.group(1), names))
        elif mn:
            if kind != "ol":
                flush(); kind = "ol"
            items.append(_inline(mn.group(1), names))
        elif mh:
            flush(); out.append(f"<h5>{_inline(mh.group(1), names)}</h5>")
        else:
            flush(); out.append(f"<p>{_inline(s, names)}</p>")
    flush()
    return "".join(out)


_SEC = re.compile(r"\*\*\s*(Short answer|Details|Reported experience(?:\s*\(if any\))?|Sources)\s*:?\s*\*\*\s*:?", re.I)


def parse_report(answer: str):
    """Split a V4 answer into sections. Returns None when the answer is not in the structured format."""
    ans = answer or ""
    if not re.search(r"\*\*\s*Short answer", ans, re.I):
        return None
    disc = ""
    m = re.search(r"_Information only[^\n]*_", ans)
    if m:
        disc = m.group(0).strip("_ ")
        ans = ans.replace(m.group(0), "")
    parts = _SEC.split(ans)
    secs = {}
    for i in range(1, len(parts) - 1, 2):
        key = parts[i].strip().lower().split(" (")[0]
        secs[key] = parts[i + 1].strip()
    if not secs.get("short answer"):
        return None
    return {"short": secs.get("short answer", ""), "details": secs.get("details", ""),
            "experience": secs.get("reported experience", ""), "disclaimer": disc}


# ----------------------------------------------------------------------------- page components
def topbar_html() -> str:
    return (f'<div class="cs-top"><div class="cs-mark">{icon("stack", 22)}</div>'
            '<div class="cs-brand">CivicStack<small>RAG assistant · India</small></div></div>')


def hero_html(compact: bool = False) -> str:
    if compact:
        return ('<div class="cs-hero compact"><div class="cs-hero-in">'
                '<span class="cs-eyebrow"><i></i>Source-grounded · Verified · Cited</span>'
                '<h1>Ask about company registration in India</h1></div></div>')
    return (
        '<div class="cs-hero"><div class="cs-orb a"></div><div class="cs-orb b"></div><div class="cs-hero-in">'
        '<span class="cs-eyebrow"><i></i>Source-grounded · Verified · Cited</span>'
        '<h1>Company registration in India, <span class="cs-grad">answered with receipts.</span></h1>'
        "<p>Ask in plain English. CivicStack searches official Acts, Rules and Gazette notifications, writes a short cited answer, "
        "and checks every claim against its source before you see it.</p></div></div>")


FEATURES = [
    ("shield", "Official sources first", "Tier 1 Acts, Rules and notifications outrank blogs, so fees and timelines come from the law, not hearsay."),
    ("check", "Every claim verified", "A separate verifier pass checks each statement against its cited passage and drops what the sources do not support."),
    ("layers", "Hybrid retrieval", "Dense embeddings and BM25 keyword search, merged and tier-weighted, find the right section even for everyday wording."),
    ("scale", "Honest about limits", "Out-of-scope or advice-seeking questions are refused, and gaps in the sources are stated instead of guessed."),
]


def features_html() -> str:
    cards = "".join(
        f'<div class="cs-card cs-reveal cs-d{i}"><div class="cs-ci">{icon(ic, 20)}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></div>'
        for i, (ic, t, d) in enumerate(FEATURES, 1))
    return f'<div class="cs-grid">{cards}</div>'


def stats_html(items: list[tuple[str, str]]) -> str:
    cells = "".join(f'<div class="cs-stat cs-reveal cs-d{min(i, 5)}"><b>{esc(v)}</b><span>{esc(k)}</span></div>'
                    for i, (k, v) in enumerate(items, 1))
    return f'<div class="cs-grid stats">{cells}</div>'


def quota_html(used: int, total: int) -> str:
    dots = "".join(f'<i class="{"on" if i < used else ""}"></i>' for i in range(total))
    return f'<div class="cs-quota"><span class="cs-dots">{dots}</span>{used} of {total} live questions used</div>'


def label_html(text: str) -> str:
    return f'<div class="cs-label">{esc(text)}</div>'


def alert_html(kind: str, title: str, text: str) -> str:
    ic = {"warn": "alert", "err": "alert", "info": "lock"}.get(kind, "lock")
    return f'<div class="cs-notice {kind} cs-reveal">{icon(ic, 20)}<div><b>{esc(title)}</b><div>{esc(text)}</div></div></div>'


def loading_html(stages=("Understanding the question", "Searching official sources", "Drafting a cited answer", "Verifying every claim")) -> str:
    rows = "".join(f'<div class="cs-stage" style="--i:{i}"><i></i>{esc(s)}</div>' for i, s in enumerate(stages))
    return (f'<div class="cs-loading"><div class="cs-load-head"><div class="cs-spin"></div>Working on it…</div>{rows}'
            '<div class="cs-skel" style="width:92%"></div><div class="cs-skel" style="width:78%"></div><div class="cs-skel" style="width:55%"></div></div>')


def vs_tag_html(version: str) -> str:
    return ('<span class="cs-vs v1">V1 · Model only, no retrieval</span>' if version == "v1"
            else '<span class="cs-vs v4">V4 · CivicStack pipeline</span>')


# ----------------------------------------------------------------------------- answer rendering
def _verified(trace: dict):
    claims = (trace or {}).get("verifier_claims") or []
    if not claims:
        return None
    ok = sum(1 for c in claims if isinstance(c, dict) and c.get("supported") is True)
    return ok, len(claims)


def trust_html(out: dict) -> str:
    cited, _ = split_sources(out)
    if not cited:
        return ""
    tiers = [int(s.get("tier", 0) or 0) for s in cited]
    items = []
    if all(t == 1 for t in tiers):
        items.append(("ok", "shield", "Official sources only", f"All {len(cited)} cited sources are Tier 1 (Acts, Rules, notifications)."))
    elif 1 in tiers:
        items.append(("info", "layers", "Official + practitioner", "Backed by Tier 1 text; practitioner sources add process detail."))
    else:
        items.append(("warn", "alert", "No official source cited", "Only practitioner sources back this. Verify on the MCA portal."))
    v = _verified(out.get("trace", {}))
    if v:
        items.append(("ok" if v[0] == v[1] else "warn", "check", "Claim check", f"{v[0]} of {v[1]} claims supported by the cited text."))
    dates = sorted({str(s.get("date")) for s in cited if s.get("date")})
    if dates:
        items.append(("info", "clock", "Sources as of", dates[-1] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"))
    return '<div class="cs-trust">' + "".join(
        f'<div class="cs-ti {k}">{icon(ic, 18)}<div><b>{esc(t)}</b><span>{esc(d)}</span></div></div>' for k, ic, t, d in items) + "</div>"


def report_html(out: dict, title: str = "Research brief") -> str | None:
    """Premium 'research brief' for a structured V4 answer, or None to fall back to plain markdown."""
    rep = parse_report(out.get("answer", ""))
    if rep is None or not out.get("sources"):
        return None
    names = {s["id"]: s.get("name", "") for s in out.get("sources", [])}
    _, label = answer_kind(out)
    exp = rep["experience"]
    exp_html = ""
    if exp and "none found" not in exp.lower():
        exp_html = f'<div class="cs-sec">Reported experience</div><div class="cs-body">{md_to_html(exp, names)}</div>'
    details = f'<div class="cs-sec">Details</div><div class="cs-body">{md_to_html(rep["details"], names)}</div>' if rep["details"] else ""
    disc = f'<div class="cs-disc">{esc(rep["disclaimer"])}</div>' if rep["disclaimer"] else ""
    return (
        '<div class="cs-report cs-reveal">'
        f'<div class="cs-report-head"><span class="cs-rtitle">{icon("file", 16)}{esc(title)}</span>'
        f'<span class="cs-pill ok">{esc(label)}</span></div>'
        f'<div class="cs-key"><div class="cs-key-label">Key answer</div><div class="cs-key-body">{md_to_html(rep["short"], names)}</div></div>'
        f'{details}{exp_html}{trust_html(out)}{disc}</div>')


def notice_for(out: dict) -> str | None:
    kind, _ = answer_kind(out)
    ans = (out.get("answer") or "").strip()
    if kind == "clarify":
        return alert_html("info", "One more detail needed", ans)
    if kind == "refusal":
        return alert_html("warn", "Outside what CivicStack can help with", ans.split("\n\n")[0])
    if kind == "limited":
        return alert_html("warn", "No supporting source found", ans.split("\n\n")[0])
    return None


def _link(url: str) -> str:
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return f'<a class="cs-slink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">Open source {icon("ext", 14)}</a>'
    return ""


def source_panel_html(s: dict, excerpt: str = "", extra: str = "", delay: int = 0, open_: bool = False) -> str:
    url = s.get("url", "") or ""
    where = esc(str(url).split("/")[-1]) if url and not str(url).startswith("http") else ""
    bits = [tier_badge(s.get("tier"))]
    for p in (f"Retrieved {esc(s.get('date'))}" if s.get("date") else "", esc(extra) if extra else "", where):
        if p:
            bits.append(f"<span>{p}</span>")
    body = (f'<div class="cs-excerpt">{esc(excerpt)}</div>' if excerpt else "") + _link(url)
    body_html = f'<div class="cs-sbody">{body}</div>' if body else ""
    return (f'<details class="cs-src" style="animation-delay:{delay * 0.06:.2f}s"{" open" if open_ else ""}><summary>'
            f'<span class="cs-sid">{esc(s.get("id"))}</span><div><div class="cs-sname">{esc(s.get("name"))}</div>'
            f'<div class="cs-smeta">{"".join(bits)}</div></div></summary>{body_html}</details>')


def sources_html(out: dict) -> str:
    cited, other = split_sources(out)
    if not cited and not other:
        return ""
    ex = context_excerpts(out.get("context", ""))
    h = ""
    if cited:
        h += (f'<div class="cs-srcs-title">{icon("layers", 18)}Sources cited '
              f'<span class="cs-pill">{len(cited)}</span></div>')
        h += "".join(source_panel_html(s, ex.get(s["id"], ""), delay=i) for i, s in enumerate(cited))
    if other:
        groups = grouped_other_sources(other)
        inner = "".join(
            source_panel_html({**g, "id": g["ids"][0]}, ex.get(g["ids"][0], ""),
                              extra=(f"{g['n']} passages ({', '.join(i for i in g['ids'] if i)})" if g["n"] > 1 else ""))
            for g in groups)
        h += (f'<details class="cs-src"><summary><span class="cs-sid">+{len(other)}</span><div><div class="cs-sname">'
              'Other passages retrieved</div><div class="cs-smeta"><span>Retrieved but not cited in the answer</span></div></div></summary>'
              f'<div class="cs-sbody">{inner}</div></details>')
    return h


def trace_chips_html(trace: dict) -> str:
    qu = (trace or {}).get("query_understanding") or {}
    items = []
    if qu.get("intent"):
        items.append(("Intent", str(qu["intent"]).replace("_", " ")))
    if qu.get("entity_types"):
        items.append(("Entity", ", ".join(qu["entity_types"])))
    if qu.get("missing_info"):
        items.append(("Missing info", ", ".join(m.replace("_", " ") for m in qu["missing_info"])))
    v = _verified(trace)
    if v:
        items.append(("Verifier", f"{v[0]} of {v[1]} claims supported"))
    if qu.get("rewritten_query"):
        items.append(("Search query", qu["rewritten_query"]))
    if not items:
        return ""
    return '<div class="cs-trace">' + "".join(f'<span class="cs-kv"><i>{esc(k)}</i>{esc(v)}</span>' for k, v in items) + "</div>"


def json_html(obj) -> str:
    import json
    try:
        s = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    return f'<pre class="cs-json">{esc(s)}</pre>'


def compare_strip_html(o1: dict, o4: dict) -> str:
    c1, c4 = len(split_sources(o1)[0]), len(split_sources(o4)[0])
    v = _verified(o4.get("trace", {}))
    cells = [
        ("Citations", f"{c1} → {c4}", "V1 → V4"),
        ("Verified claims", f"{v[0]}/{v[1]}" if v else "n/a", "V4 verifier pass"),
        ("Grounding", "None → Retrieval", "V1 → V4"),
    ]
    return '<div class="cs-delta">' + "".join(
        f'<div class="cs-stat cs-reveal cs-d{i}"><b>{esc(a)}</b><span>{esc(b)}</span><em>{esc(c)}</em></div>'
        for i, (b, a, c) in enumerate(cells, 1)) + "</div>"


# ----------------------------------------------------------------------------- evaluation dashboard
def results_dashboard_html(rows: list[dict]) -> str:
    n = len(rows)
    if not n:
        return ""
    v1t, ft = sum(r["v1"] for r in rows), sum(r["final"] for r in rows)
    passed = sum(1 for r in rows if r["passed"])
    top = 10 * n
    pct1, pctf, pctp = round(100 * v1t / top), round(100 * ft / top), round(100 * passed / n)
    hero = (
        '<div class="cs-dash"><div class="cs-card cs-reveal">'
        '<h4>Score uplift: no retrieval vs full pipeline</h4><p>Total score across all test questions, judged against Tier 1 ground truth.</p>'
        f'<div class="cs-barrow"><div class="cs-barlab"><span>V1 · model only</span><b>{v1t} / {top}</b></div><div class="cs-bar v1" style="--w:{pct1}%"><i></i></div></div>'
        f'<div class="cs-barrow"><div class="cs-barlab"><span>CivicStack · final</span><b>{ft} / {top}</b></div><div class="cs-bar" style="--w:{pctf}%"><i></i></div></div>'
        f'<span class="cs-pill ok">+{ft - v1t} points · {ft / max(v1t, 1):.1f}× the baseline</span></div>'
        f'<div class="cs-card cs-reveal cs-d2" style="text-align:center"><h4>Tests passed</h4>'
        f'<div class="cs-donut" style="--p:{pctp}"><div><span>{passed}/{n}<small>{pctp}% pass</small></span></div></div>'
        '<p>Pass = score of 7 or more with correct behaviour.</p></div></div>')
    cats: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        cats.setdefault(r.get("category") or "other", []).append(r)
    catrows = ""
    for c, rs in cats.items():
        a1 = sum(x["v1"] for x in rs) / (10 * len(rs)) * 100
        af = sum(x["final"] for x in rs) / (10 * len(rs)) * 100
        catrows += (f'<div class="cs-barrow"><div class="cs-barlab"><span>{esc(c.replace("_", " "))} · {len(rs)}</span><b>{a1:.0f}% → {af:.0f}%</b></div>'
                    f'<div class="cs-bar sm v1" style="--w:{a1:.0f}%"><i></i></div><div class="cs-bar sm" style="--w:{af:.0f}%; margin-top:4px"><i></i></div></div>')
    cat_card = f'<div class="cs-card cs-reveal cs-d3"><h4>By question category</h4><p>Grey: V1. Colour: final. Average score as % of maximum.</p>{catrows}</div>'
    body = ""
    for r in rows:
        body += (f'<tr><td class="qid">{esc(r["id"])}</td><td class="qtxt">{esc(r["question"])}</td>'
                 f'<td><span class="cs-chip">{esc((r.get("category") or "").replace("_", " "))}</span></td>'
                 f'<td style="min-width:110px"><div class="cs-barlab" style="margin:0 0 4px 0"><b>{r["v1"]}</b></div><div class="cs-bar sm v1" style="--w:{r["v1"] * 10}%"><i></i></div></td>'
                 f'<td style="min-width:110px"><div class="cs-barlab" style="margin:0 0 4px 0"><b>{r["final"]}</b></div><div class="cs-bar sm" style="--w:{r["final"] * 10}%"><i></i></div></td>'
                 f'<td><span class="cs-pass {"y" if r["passed"] else "n"}">{"✓ Pass" if r["passed"] else "✗ Fail"}</span></td></tr>')
    table = ('<div class="cs-scroll cs-reveal cs-d4"><table class="cs-tbl"><thead><tr><th>ID</th><th>Question</th><th>Category</th>'
             f'<th>V1 /10</th><th>Final /10</th><th>Result</th></tr></thead><tbody>{body}</tbody></table></div>')
    return hero + cat_card + table


# ----------------------------------------------------------------------------- about page
STEPS = [
    ("search", "Understand", "A first prompt classifies the question, spots the entity type (Pvt Ltd, LLP, OPC, Section 8) and rewrites it for search. Off-topic or advice-seeking questions stop here."),
    ("layers", "Retrieve", "Dense embeddings and BM25 run together, merged by reciprocal rank fusion and weighted by source tier, so official text outranks blogs."),
    ("file", "Answer", "A second prompt writes a short, cited answer using only the retrieved passages, and says so when the sources do not cover the question."),
    ("check", "Verify", "A third prompt checks every claim against its cited passage and removes or softens anything the sources do not support."),
]


def steps_html() -> str:
    cards = "".join(
        f'<div class="cs-card cs-reveal cs-d{i}"><span class="cs-step-n">STEP 0{i}</span><div class="cs-ci">{icon(ic, 20)}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></div>'
        for i, (ic, t, d) in enumerate(STEPS, 1))
    return f'<div class="cs-pipe">{cards}</div>'


def tiers_html(counts: dict | None = None) -> str:
    counts = counts or {}
    rows = [
        (1, "Official", "Acts, Rules and Gazette notifications. The ground truth, weighted highest."),
        (2, "Practitioner", "Guides from filing platforms. Useful process detail, weighted lower and flagged as unconfirmed unless Tier 1 backs it."),
        (3, "Reported experience", "Anonymised real filing experiences. The only source allowed to answer 'common issues' questions."),
    ]
    cards = ""
    for i, (t, name, desc) in enumerate(rows, 1):
        n = counts.get(t)
        num = f' <span class="cs-pill">{n} in index</span>' if n is not None else ""
        cards += f'<div class="cs-card cs-reveal cs-d{i}">{tier_badge(t)}{num}<h4 style="margin-top:12px !important">{esc(name)}</h4><p>{esc(desc)}</p></div>'
    return f'<div class="cs-grid">{cards}</div>'


def card_html(title: str, text_html: str, ic: str = "lock") -> str:
    return f'<div class="cs-card cs-reveal"><div class="cs-ci">{icon(ic, 20)}</div><h4>{esc(title)}</h4><p>{text_html}</p></div>'


def kb_counts(sources: list[dict]) -> dict:
    out: dict = {}
    for s in sources or []:
        if isinstance(s, dict) and s.get("enabled"):
            t = int(s.get("tier", 0) or 0)
            out[t] = out.get(t, 0) + 1
    return out

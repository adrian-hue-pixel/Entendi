"""Shared visual components for Entendi."""
import base64
from functools import cache
import html
from pathlib import Path
import random
from urllib.parse import quote

_ICONS = {
    "home": '<path d="M4 11l8-7 8 7v9H4zM10 20v-6h4v6"/>',
    "understand": '<rect x="4" y="6" width="16" height="13" rx="2"/><path d="M4 8l8 6 8-6"/>',
    "letters": '<path d="M7 5h12v15H7a2 2 0 010-4h12M7 16V5a2 2 0 00-2 2v11M10 9h6M10 12h4"/>',
    "deadlines": '<rect x="4" y="5" width="16" height="16" rx="3"/><path d="M4 10h16M9 3v4M15 3v4M9 15l2 2 4-4"/>',
    "benefits": '<path d="M12 22s7-4 7-10V5l-7-3-7 3v7c0 6 7 10 7 10zM9 12l2 2 4-4"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
}


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def icon(key: str) -> str:
    """Line icon (SF-Symbols style) that draws itself in when it appears."""
    body = _ICONS.get(key, _ICONS["home"])
    for tag in ("<path ", "<circle ", "<rect "):
        body = body.replace(tag, tag + 'pathLength="1" ')
    return (f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


# ---------------------------------------------------------------- colour tokens
_DARK = ("--bg:#0C0B18;--text:#F5F3FC;--muted:#B2ABC5;--card:rgba(255,255,255,.055);--card2:rgba(255,255,255,.085);"
         "--border:rgba(203,190,255,.16);--fborder:rgba(203,190,255,.26);--field:rgba(255,255,255,.07);--pop:#1B172A;"
         "--side:#100F1D;--nav-active:#201C32;--nav-border:#443A5E;--accent:#C3B2FF;--accent-soft:rgba(173,148,255,.18);--btn-text:#1C1437;"
         "--hero-gradient:linear-gradient(100deg,#ECE5FF 0%,#BEACFF 23%,#F2BCEF 48%,#BEACFF 71%,#ECE5FF 100%);"
         "--button-gradient:linear-gradient(115deg,#B8ABFF,#E0B4F2);--progress-start:#9380EE;"
         "--shadow:0 1px 0 rgba(255,255,255,.04) inset,0 12px 40px rgba(0,0,0,.45);--hover:rgba(255,255,255,.07);"
         "--warm:#F2B84B;--warm-soft:rgba(242,184,75,.15);--sky:#7FB8F0;--sky-soft:rgba(127,184,240,.15);"
         "--danger:#FF9A7A;--danger-soft:rgba(255,154,122,.14);--good:#C3B2FF;--good-soft:rgba(173,148,255,.16);"
         "--wx:linear-gradient(135deg,rgba(127,184,240,.16),rgba(173,148,255,.16));--head:linear-gradient(135deg,#FFFFFF0D,#B8ABFF17);")
_LIGHT = ("--bg:#F6F3FC;--text:#211B36;--muted:#59526E;--card:#FFFFFF;--card2:#FFFFFF;--border:#E2DBF0;--fborder:#CDC3E2;"
          "--field:#FFFFFF;--pop:#FFFFFF;--side:#FCFAFF;--nav-active:#F0EAFB;--nav-border:#D9CDEE;--accent:#5841B6;--accent-soft:rgba(88,65,182,.11);--btn-text:#FFFFFF;"
          "--hero-gradient:linear-gradient(100deg,#332374 0%,#5841B6 23%,#864597 48%,#5841B6 71%,#332374 100%);"
          "--button-gradient:linear-gradient(115deg,#4935A8,#783E91);--progress-start:#9276DF;"
          "--shadow:0 1px 2px rgba(41,27,79,.05),0 10px 28px rgba(41,27,79,.07);--hover:rgba(88,65,182,.07);"
          "--warm:#9A5B00;--warm-soft:#FFF3DA;--sky:#17619E;--sky-soft:#E7F1FB;--danger:#A8321A;--danger-soft:#FCEBE5;"
          "--good:#5841B6;--good-soft:#EDE6FC;"
          "--wx:linear-gradient(135deg,#E6F2FC 0%,#F2E7FC 100%);--head:linear-gradient(135deg,#FFFFFF 0%,#F0EAFC 100%);")

_FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"

_CSS = """
@property --n{syntax:"<integer>";inherits:false;initial-value:0}
.stApp,.stApp *{font-family:Inter,-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,"Noto Sans","Noto Sans Tamil","Noto Sans Devanagari",sans-serif;-webkit-font-smoothing:antialiased;}
[data-testid="stIconMaterial"],[data-testid="stIconMaterial"] *,.stApp span[class*="material-symbols"],.stApp span[class*="material-icons"]{font-family:"Material Symbols Rounded","Material Icons"!important;}
.stApp{background:var(--bg);color:var(--text);}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"],[data-testid="stBottom"]{background:transparent!important;}
footer{visibility:hidden;}
.block-container{position:relative;z-index:1;padding-top:2rem;padding-bottom:4rem;max-width:1080px;}
.element-container:has(.bg-fx),[data-testid="stElementContainer"]:has(.bg-fx){position:absolute;height:0;margin:0;overflow:visible;}
.stApp,.stApp p,.stApp li,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp span,.stApp summary,.stApp [data-testid="stMarkdownContainer"]{color:var(--text);}
.stApp small,.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] *{color:var(--muted);}
.stApp h2,.stApp h3{font-weight:700;letter-spacing:-.02em;}
.stApp hr{border-color:var(--border);}
.stApp a{color:var(--accent);}
.stApp code{color:var(--accent);background:var(--accent-soft);border-radius:6px;}
.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stWidgetLabel"] label{font-weight:600;font-size:.93rem;}
.stApp .gt{background:var(--hero-gradient);background-size:220% auto;-webkit-background-clip:text;background-clip:text;color:transparent!important;-webkit-text-fill-color:transparent;animation:shine 9s linear infinite;}
@keyframes shine{to{background-position:-220% center}}
@keyframes riseIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes blurIn{from{opacity:0;filter:blur(12px);transform:translateY(8px) scale(.98)}to{opacity:1;filter:none;transform:none}}
@keyframes pop{0%{opacity:0;transform:scale(.8)}100%{opacity:1;transform:scale(1)}}
@keyframes flipUp{from{opacity:0;transform:perspective(900px) rotateX(12deg) translateY(26px)}to{opacity:1;transform:none}}
@keyframes slideL{from{opacity:0;transform:translateX(-22px)}to{opacity:1;transform:none}}
@keyframes slideR{from{opacity:0;transform:translateX(22px)}to{opacity:1;transform:none}}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes count{from{--n:0}}
@keyframes breathe{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(1.14);opacity:.9}}
@keyframes grow{to{width:48px}}
@keyframes fillbar{from{width:0}}
/* ---------- ambient background ---------- */
.bg-fx{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden;contain:strict;}
.day-sky{background:linear-gradient(160deg,#fcfaff 0%,#f7f4fd 55%,#eeeaf9 100%);}
.day-sky::before{content:"";position:absolute;inset:-20%;
  background:radial-gradient(ellipse at 83% 24%,rgba(223,161,230,.34),transparent 33%),
    radial-gradient(ellipse at 18% 73%,rgba(160,147,230,.36),transparent 36%);
  opacity:.85;animation:day-drift 11s ease-in-out -3s infinite alternate;}
@keyframes day-drift{from{transform:translate(-8%,5%);opacity:.76}to{transform:translate(8%,-5%);opacity:1}}
.day-mote{position:absolute;left:var(--left);top:var(--top);width:var(--size);height:var(--size);border-radius:50%;
  background:radial-gradient(circle,var(--tint) 12%,transparent 72%);opacity:.58;
  animation:day-mote-rise var(--period) ease-in-out var(--phase) infinite alternate;}
@keyframes day-mote-rise{
  from{transform:translate(0,14px) scale(.82);opacity:.3}
  to{transform:translate(var(--drift),-42px) scale(1.12);opacity:.8}
}
.night-sky{background:
  radial-gradient(ellipse at 82% 24%,rgba(54,78,130,.23),transparent 42%),
  linear-gradient(151deg,transparent 22%,rgba(55,69,112,.16) 48%,transparent 69%),
  linear-gradient(180deg,#050815 0%,#090e1d 64%,#111b30 100%);}
.sky-star{position:absolute;width:var(--size);height:var(--size);border-radius:50%;background:var(--tint);
  opacity:var(--dim);animation:sky-twinkle var(--period) ease-in-out var(--phase) infinite;}
.sky-star.bright{box-shadow:0 0 5px 1px var(--tint);}
@keyframes sky-twinkle{0%,100%{opacity:var(--dim)}32%{opacity:var(--peak)}64%{opacity:var(--dim)}78%{opacity:var(--mid)}}
.sky-meteor{position:absolute;top:var(--top);left:var(--left);width:clamp(58px,11vw,168px);height:2px;
  background:linear-gradient(90deg,transparent,#91b6ff66 61%,#eaf5ff);border-radius:50%;opacity:0;
  animation:sky-meteor 42s linear var(--delay) infinite;}
.sky-meteor::after{content:"";position:absolute;right:0;width:2px;height:2px;border-radius:50%;background:#fff;box-shadow:0 0 7px 2px #b8d7ff;}
@keyframes sky-meteor{
  0%{opacity:0;transform:rotate(var(--angle)) translateX(0)}
  .6%{opacity:1}
  3.6%,100%{opacity:0;transform:rotate(var(--angle)) translateX(min(52vw,650px))}
}
@media (prefers-reduced-motion:reduce){.day-sky::before,.day-mote,.sky-star,.sky-meteor{animation:none!important;}}
/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--side)!important;backdrop-filter:saturate(180%) blur(28px);-webkit-backdrop-filter:saturate(180%) blur(28px);border-right:1px solid var(--border);}
[data-testid="stSidebar"]>div:first-child{background:transparent!important;}
.brand{display:flex;align-items:center;gap:.6rem;padding:.2rem 0 .8rem;animation:slideL .7s both;}
.brand b{font-size:1.25rem;font-weight:700;letter-spacing:-.025em;}
.st-key-page label:has(input[type="radio"]){box-sizing:border-box;display:flex;align-items:center;gap:.68rem;width:100%;
  min-height:2.55rem;margin:0;padding:.42rem .68rem;border:1px solid transparent;border-radius:11px;cursor:pointer;
  transition:background-color .18s,border-color .18s;}
.st-key-page [role="radiogroup"],.st-key-page [role="radiogroup"]>div{row-gap:.12rem;}
.st-key-page label[data-testid="stRadioOption"]>div>div:first-child:not([data-testid]),
.st-key-page label[data-baseweb="radio"]:not([data-testid="stRadioOption"])>div:first-child{display:none;}
.st-key-page label:has(input[type="radio"])::before{content:"";flex:0 0 1.15rem;width:1.15rem;height:1.15rem;
  background:var(--muted);mask:var(--nav-icon) center/contain no-repeat;}
.st-key-page label:has(input[type="radio"]) [data-testid="stMarkdownContainer"] p{margin:0;line-height:1.3;}
.st-key-page label:has(input[type="radio"]):hover{background:var(--hover);}
.st-key-page label:has(input:checked){background:var(--nav-active);border-color:var(--nav-border);}
.st-key-page label:has(input:checked)::before{background:var(--accent);}
.st-key-page label:has(input:checked) [data-testid="stMarkdownContainer"] p{font-weight:650;}
.st-key-page label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:-2px;}
.navlabel{font-size:.7rem;font-weight:750;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding:.2rem .68rem 0;}
.stApp [data-testid="stTooltipHoverTarget"] button[aria-label^="Help for"]{display:grid;place-items:center;padding:0;
  min-height:1.4rem;width:1.4rem;background:transparent;border:0;color:var(--muted);}
.stApp [data-testid="stTooltipHoverTarget"] button[aria-label^="Help for"]:hover{color:var(--accent);}
.stApp [data-testid="stTooltipHoverTarget"] button[aria-label^="Help for"] svg{color:inherit;stroke:currentColor;}
/* ---------- hero + headers ---------- */
.hero{position:relative;text-align:center;padding:1.2rem 0 1.4rem;display:flex;flex-direction:column;align-items:center;}
.hero .mwrap{position:relative;margin-bottom:.8rem;}
.halo{position:absolute;left:50%;top:58%;width:230px;height:230px;margin:-115px 0 0 -115px;border-radius:50%;background:radial-gradient(circle,var(--accent-soft),transparent 68%);animation:breathe 5s ease-in-out infinite;z-index:-1;}
.stApp .eyebrow{font-size:.78rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);animation:fade 1s .2s both;display:inline-block;}
.hero-title{font-size:clamp(2.3rem,6vw,4.2rem);line-height:1.04;font-weight:800;margin:.6rem 0 1rem;letter-spacing:-.04em;animation:blurIn 1.1s .25s cubic-bezier(.2,.8,.2,1) both;}
.hero p{margin:0 auto;color:var(--muted);font-size:1.15rem;line-height:1.55;max-width:36rem;animation:riseIn .9s .5s both;}
.chips{display:flex;flex-wrap:wrap;justify-content:center;gap:.45rem;margin-top:1.4rem;}
.chips span{padding:.32rem .9rem;border-radius:999px;background:var(--card);border:1px solid var(--border);font-size:.83rem;font-weight:500;color:var(--muted);box-shadow:0 1px 2px rgba(41,27,79,.04);animation:pop .6s cubic-bezier(.34,1.56,.64,1) both;}
.chips span:nth-child(1){animation-delay:.7s}.chips span:nth-child(2){animation-delay:.8s}.chips span:nth-child(3){animation-delay:.9s}.chips span:nth-child(4){animation-delay:1s}.chips span:nth-child(5){animation-delay:1.1s}
.pagehead{position:relative;display:flex;align-items:center;justify-content:space-between;gap:1.5rem;padding:1.3rem 1.8rem;margin-bottom:1.3rem;background:var(--head);border:1px solid var(--border);border-radius:26px;box-shadow:var(--shadow);animation:riseIn .8s cubic-bezier(.2,.8,.2,1) both;}
.pagehead .ptitle{display:flex;align-items:center;gap:1rem;}
.pagehead .ptile{flex:0 0 auto;width:56px;height:56px;border-radius:17px;display:flex;align-items:center;justify-content:center;color:var(--accent);background:var(--accent-soft);animation:pop .7s .2s cubic-bezier(.34,1.56,.64,1) both;}
.pagehead h1{font-size:clamp(1.5rem,3vw,2.05rem);margin:.1rem 0 0;font-weight:800;letter-spacing:-.03em;padding:0;line-height:1.1;animation:blurIn .8s .15s both;}
.pagehead p{margin:.3rem 0 0;color:var(--muted);font-size:1rem;line-height:1.45;max-width:34rem;animation:riseIn .8s .3s both;}
.mwrap{display:flex;flex-direction:column;align-items:center;flex-shrink:0;}
[class*="st-key-owl_message_"]{position:relative;background:var(--card);border-color:var(--border)!important;border-radius:18px;overflow:visible;}
[class*="st-key-owl_message_"]::before{content:"";position:absolute;top:-7px;right:3rem;width:12px;height:12px;
  transform:rotate(45deg);background:var(--pop);border-top:1px solid var(--border);border-left:1px solid var(--border);pointer-events:none;}
.owl-line{font-size:.93rem;margin:0;}
.bubble{position:relative;max-width:210px;text-align:center;padding:.5rem .9rem;margin-bottom:.6rem;border-radius:14px;background:var(--card2);border:1px solid var(--border);font-size:.8rem;color:var(--muted);box-shadow:0 1px 2px rgba(41,27,79,.05);animation:pop .7s .6s cubic-bezier(.34,1.56,.64,1) both;}
.bubble::after{content:"";position:absolute;bottom:-5px;left:50%;margin-left:-5px;width:9px;height:9px;background:var(--card2);border-right:1px solid var(--border);border-bottom:1px solid var(--border);transform:rotate(45deg);}
/* ---------- mascot ---------- */
.entendi-mascot{position:relative;display:inline-block;flex:none;vertical-align:middle;overflow:visible;transition:transform .5s cubic-bezier(.34,1.56,.64,1);}
.entendi-mascot:hover{transform:scale(1.08) rotate(-3deg);}
.owl-body{position:absolute;inset:3% 6% 9%;background:var(--owl-image) center bottom/contain no-repeat;
  transform-origin:50% 90%;animation:owl-float 4.5s ease-in-out infinite;}
.owl-shadow{position:absolute;bottom:4%;left:25%;width:50%;height:6%;border-radius:50%;background:var(--accent);
  opacity:.18;animation:owl-shadow 4.5s ease-in-out infinite;}
.owl-spark{position:absolute;width:9%;height:9%;display:grid;place-items:center;color:var(--accent);
  opacity:.65;animation:owl-sparkle 3s ease-in-out infinite;}
.owl-spark::before{content:"";width:70%;aspect-ratio:1;background:currentColor;
  clip-path:polygon(50% 0,60% 40%,100% 50%,60% 60%,50% 100%,40% 60%,0 50%,40% 40%);}
.owl-spark.left{top:26%;left:0;animation-delay:-1.5s;}
.owl-spark.right{top:15%;right:0;}
@keyframes owl-float{0%,100%{transform:none}50%{transform:translateY(-5%) rotate(2.5deg)}}
@keyframes owl-shadow{0%,100%{transform:scale(1);opacity:.2}50%{transform:scale(.84);opacity:.11}}
@keyframes owl-sparkle{0%,100%{opacity:.3;transform:scale(.75)}50%{opacity:.85;transform:scale(1.12)}}
/* ---------- cards ---------- */
[class*="fcard_"]{position:relative;overflow:hidden;background:var(--card);border:1px solid var(--border);border-radius:22px;padding:1.3rem 1.3rem .9rem;box-shadow:var(--shadow);transition:transform .45s cubic-bezier(.2,.8,.2,1),border-color .3s,box-shadow .3s;animation:flipUp .9s cubic-bezier(.2,.8,.2,1) both;}
[class*="fcard_"]::after{content:"";position:absolute;inset:0;background:radial-gradient(420px circle at 80% -10%,var(--accent-soft),transparent 60%);opacity:0;transition:opacity .4s;pointer-events:none;}
[class*="fcard_"]:hover{transform:translateY(-4px);border-color:var(--accent);}
[class*="fcard_"]:hover::after{opacity:1;}
.ficon{display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:14px;color:var(--accent);background:var(--accent-soft);transition:transform .5s cubic-bezier(.34,1.56,.64,1);}
[class*="fcard_"]:hover .ficon{transform:scale(1.1) rotate(-6deg);}
.ico{width:26px;height:26px;}
.ico *{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.3s .35s cubic-bezier(.4,0,.2,1) forwards;}
.ftitle{font-weight:700;font-size:1.05rem;margin:.85rem 0 .25rem;letter-spacing:-.015em;}
.ftag{color:var(--muted);font-size:.9rem;line-height:1.45;min-height:2.6rem;}
.stat{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:1.1rem 1rem;text-align:center;box-shadow:var(--shadow);animation:pop .8s cubic-bezier(.34,1.56,.64,1) both;}
.stat b{display:block;font-size:2.1rem;font-weight:800;letter-spacing:-.04em;}
.cnt{counter-reset:n var(--n);animation:count 1.6s .3s cubic-bezier(.2,.8,.2,1) both;}
.cnt::after{content:counter(n);}
.stat span{color:var(--muted);font-size:.84rem;font-weight:500;}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1.2rem;margin:2rem 0 2rem;}
.step{padding:1rem 0 0;border-top:1px solid var(--border);position:relative;animation:riseIn .9s both;}
.step::before{content:"";position:absolute;top:-1px;left:0;height:2px;width:0;background:var(--accent);animation:grow 1.2s .5s cubic-bezier(.2,.8,.2,1) forwards;}
.step:nth-child(2){animation-delay:.15s}.step:nth-child(3){animation-delay:.3s}
.step i{display:block;font-style:normal;font-size:.76rem;font-weight:700;letter-spacing:.09em;color:var(--accent);margin-bottom:.35rem;}
.step b{display:block;font-weight:700;letter-spacing:-.01em;font-size:1.05rem;}.step span{color:var(--muted);font-size:.92rem;}
.h2{font-size:1.55rem;font-weight:800;letter-spacing:-.03em;margin:1.4rem 0 .8rem;animation:slideL .8s both;}
.sec-title{font-size:.78rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin-bottom:.5rem;}
[class*="st-key-sec_"]{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:1.1rem 1.4rem;margin-bottom:.8rem;box-shadow:var(--shadow);animation:slideL .8s cubic-bezier(.2,.8,.2,1) both;}
.st-key-aside{position:sticky;top:3.5rem;align-self:flex-start;background:var(--card);border:1px solid var(--border);border-radius:22px;padding:1.2rem 1.3rem;box-shadow:var(--shadow);animation:slideR .9s .2s cubic-bezier(.2,.8,.2,1) both;}
.aside h4{margin:0 0 .6rem;font-size:1rem;font-weight:700;letter-spacing:-.01em;}
.aside li{color:var(--muted);font-size:.9rem;line-height:1.5;margin-bottom:.45rem;animation:fade .8s both;}
.aside ul{padding-left:1.1rem;margin:0;}
.loader{display:flex;flex-direction:column;align-items:center;padding:1.6rem;margin:1rem 0;border-radius:22px;background:var(--card);border:1px solid var(--border);box-shadow:var(--shadow);animation:pop .5s both;}
.bar{width:160px;height:4px;border-radius:4px;background:var(--accent-soft);overflow:hidden;margin-top:.6rem;}
.bar::after{content:"";display:block;width:40%;height:100%;border-radius:4px;background:var(--accent);animation:slide 1.4s ease-in-out infinite;}
@keyframes slide{0%{transform:translateX(-100%)}100%{transform:translateX(260%)}}
.lmsg{position:relative;height:1.4rem;width:100%;text-align:center;font-size:.9rem;color:var(--muted);margin-top:.7rem;}
.lmsg span{position:absolute;left:0;right:0;opacity:0;animation:lmsg 9s infinite;}
.lmsg span:nth-child(2){animation-delay:3s}.lmsg span:nth-child(3){animation-delay:6s}
@keyframes lmsg{0%{opacity:0}6%,30%{opacity:1}36%,100%{opacity:0}}
/* ---------- letter details ---------- */
.letter-loading{display:grid;justify-items:center;gap:.8rem;padding:2rem;color:var(--accent);}
.letter-summary{font-size:clamp(1.15rem,2.1vw,1.65rem);line-height:1.5;font-weight:650;}
.letter-badges{display:flex;gap:.45rem;flex-wrap:wrap;margin:.3rem 0 .65rem;}
.letter-fact{background:var(--card);border:1px solid var(--border);border-radius:17px;padding:.8rem 1rem;
  min-height:6.4rem;display:grid;align-content:start;gap:.25rem;box-shadow:var(--shadow);overflow-wrap:anywhere;}
.letter-fact span{color:var(--muted);font-size:.8rem;font-weight:650;}
.letter-fact b{font-size:1.02rem;color:var(--text);}
.letter-fact small{color:var(--muted);}
[class*="st-key-confirm_"]{border-color:var(--accent)!important;background:var(--accent-soft)!important;}
.badge{display:inline-block;padding:.18rem .65rem;border-radius:999px;font-size:.76rem;font-weight:700;background:var(--accent-soft);color:var(--accent);}
.badge.warn{background:var(--warm-soft);color:var(--warm);}.badge.bad{background:var(--danger-soft);color:var(--danger);}.badge.sky{background:var(--sky-soft);color:var(--sky);}
.group-h{font-size:.78rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;margin:1.1rem 0 .4rem;color:var(--muted);}
.group-h.bad{color:var(--danger);}.group-h.today{color:var(--accent);}
.empty{text-align:center;padding:1.6rem 1rem;border:2px dashed var(--fborder);border-radius:20px;color:var(--muted);background:var(--card);}
.empty b{display:block;color:var(--text);font-size:1.02rem;margin-bottom:.2rem;}
.callout{padding:.9rem 1.1rem;border-radius:16px;background:var(--warm-soft);color:var(--text);font-size:.92rem;border:1px solid var(--border);}
/* ---------- native widgets ---------- */
[data-testid="stForm"]{background:var(--card);border:1px solid var(--border);border-radius:22px;padding:1.4rem 1.5rem;box-shadow:var(--shadow);animation:riseIn .9s .1s cubic-bezier(.2,.8,.2,1) both;}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{background:var(--field)!important;border-color:var(--fborder)!important;border-radius:12px!important;transition:box-shadow .25s,border-color .25s;}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within,[data-baseweb="select"]:focus-within>div{border-color:var(--accent)!important;box-shadow:0 0 0 4px var(--accent-soft)!important;}
.stApp input,.stApp textarea,.stApp [data-baseweb="select"] *{color:var(--text)!important;-webkit-text-fill-color:var(--text);}
.stApp ::placeholder{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important;opacity:.85;}
.stApp [data-baseweb="select"] svg{fill:var(--muted);}
[data-baseweb="tag"]{background:var(--accent-soft)!important;border-radius:999px!important;}
[data-baseweb="tag"] *{color:var(--accent)!important;}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"] ul{background:var(--pop)!important;border:1px solid var(--border);border-radius:14px;}
[data-baseweb="popover"] li,[data-baseweb="popover"] li *{color:var(--text)!important;}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{background:var(--accent-soft)!important;}
.stApp button{position:relative;overflow:hidden;border-radius:999px;font-weight:600;min-height:2.7rem;border:1px solid var(--fborder);background:var(--card2);transition:background .2s,transform .25s cubic-bezier(.34,1.56,.64,1),box-shadow .25s,border-color .2s;}
.stApp button *{color:var(--text);}
.stApp button[data-testid^="stBaseButton-primary"],.stApp button[data-testid="stBaseButton-primaryFormSubmit"]{background:var(--button-gradient)!important;border:0!important;color:var(--btn-text)!important;box-shadow:0 6px 16px var(--accent-soft);}
.stApp button[data-testid^="stBaseButton-primary"] *{color:var(--btn-text)!important;}
.stApp button[data-testid^="stBaseButton-primary"]::after{content:"";position:absolute;top:0;left:-70%;width:50%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.35),transparent);transform:skewX(-20deg);transition:left .7s;}
.stApp button[data-testid^="stBaseButton-primary"]:hover::after{left:130%;}
.stApp button[data-testid^="stBaseButton"]:hover{transform:translateY(-2px);border-color:var(--accent);}
.stApp button[data-testid^="stBaseButton"]:active{transform:scale(.97);}
.stApp button:focus-visible,.stApp a:focus-visible,.stApp input:focus-visible{outline:3px solid var(--accent);outline-offset:2px;}
.st-key-cta_dash,.st-key-cta_lab{display:flex;animation:riseIn .8s 1.2s both;}.st-key-cta_dash{justify-content:flex-end;}.st-key-cta_lab{justify-content:flex-start;animation-delay:1.3s;}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--border)!important;border-radius:13px;}
[data-testid="stExpander"] details{background:transparent!important;border:0!important;}
[data-testid="stExpander"] summary{background:transparent!important;color:var(--muted)!important;border-radius:12px;}
[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] summary [data-testid="stIconMaterial"]{color:inherit!important;}
[data-testid="stExpander"] summary:hover,[data-testid="stExpander"] details[open]>summary{
  background:var(--hover)!important;color:var(--text)!important;}
[data-testid="stExpander"] summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;}
[data-testid="stCode"] pre,[data-testid="stCode"] code{background:var(--accent-soft)!important;border-radius:12px;}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--border)!important;border-radius:18px;background:var(--card);}
[data-testid="stFileUploaderDropzone"],[data-testid="stAudioInput"],[data-testid="stCameraInput"]{background:var(--field)!important;border:1.5px dashed var(--fborder)!important;border-radius:16px!important;}
[data-testid="stFileUploaderDropzone"] *,[data-testid="stAudioInput"] *{color:var(--text);}
[data-testid="stTabs"] [role="tablist"]{gap:.3rem;border-bottom:1px solid var(--border);}
[data-testid="stTabs"] button[role="tab"]{border-radius:12px 12px 0 0;border:0;background:transparent;min-height:2.6rem;font-weight:600;}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *{color:var(--accent);}
[data-testid="stMetric"]{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:.7rem 1rem;box-shadow:var(--shadow);}
[data-testid="stProgress"] > div > div{background:var(--accent-soft)!important;}
[data-testid="stImage"] img{border-radius:14px;}
::-webkit-scrollbar{width:8px;height:8px;}::-webkit-scrollbar-thumb{background:var(--fborder);border-radius:8px;}
@media (max-width:700px){.block-container{padding-left:1rem;padding-right:1rem;}.pagehead{flex-direction:column;text-align:center;padding:1.1rem;}.pagehead .ptitle{flex-direction:column;}.st-key-aside{position:static;}}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;animation-iteration-count:1!important;animation-delay:0s!important;}}
"""

# Style the native inner alert surface because it carries Streamlit's light-theme background.
_DARK_ONLY = """
[data-testid="stAlertContainer"]{--alert-text:var(--sky);--alert-bg:var(--sky-soft);background:var(--alert-bg)!important;
  border:1px solid var(--border);border-radius:12px;color:var(--alert-text)!important;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]){--alert-text:var(--good);--alert-bg:var(--good-soft);}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]){--alert-text:var(--warm);--alert-bg:var(--warm-soft);}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]){--alert-text:var(--danger);--alert-bg:var(--danger-soft);}
[data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] *{color:var(--text)!important;}
[data-testid="stAlertContainer"] [data-testid="stIconMaterial"]{color:var(--alert-text)!important;}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{filter:invert(.9) hue-rotate(180deg);border-radius:12px;}
"""
_LIGHT_ONLY = """
[data-testid="stAlert"]{border-radius:16px;animation:riseIn .6s both;}
"""
_LARGE = (".stApp{font-size:1.18rem;}.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp [data-baseweb=\"select\"] *,"
          ".stApp button,.stApp [data-testid=\"stMarkdownContainer\"] p{font-size:1.18rem!important;}"
          ".stApp [data-testid=\"stWidgetLabel\"] p{font-size:1.1rem!important;}.stApp button{min-height:3.2rem;}")
_LOW_DATA = ("*,*::before,*::after{animation:none!important;transition:none!important;}.ico *{stroke-dashoffset:0!important;}"
             ".cnt{counter-reset:none;}.stApp *{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;}"
             "[class*=\"fcard_\"],[class*=\"st-key-sec_\"],.pagehead{opacity:1!important;}.gt{animation:none!important;}")


def _min(s: str) -> str:
    """Collapse whitespace so Streamlit's Markdown parser never mistakes our HTML for a code block."""
    return " ".join(s.split())


@cache
def _owl_image() -> str:
    asset = Path(__file__).with_name("assets") / "amethyst-owl.webp"
    return base64.b64encode(asset.read_bytes()).decode("ascii")


@cache
def _navigation_css(pages: tuple[str, ...]) -> str:
    rules = []
    for index, page in enumerate(pages):
        svg = icon(page).replace('class="ico"', 'xmlns="http://www.w3.org/2000/svg"')
        rules.append(f'.st-key-page label:has(input[value="{index}"])'
                     f'{{--nav-icon:url("data:image/svg+xml,{quote(svg, safe="")}")}}')
    return "".join(rules)


def global_css(dark: bool = False, large_text: bool = False, low_data: bool = False,
               *, navigation: tuple[str, ...] = ()) -> str:
    extra = [f'[class*="st-key-sec_{i}"]{{animation-delay:{i * .12:.2f}s;}}' for i in range(5)]
    extra.append(_navigation_css(navigation))
    extra.append(_DARK_ONLY if dark else _LIGHT_ONLY)
    if large_text:
        extra.append(_LARGE)
    if low_data:
        extra.append(_LOW_DATA)
    root = (f".stApp{{{_DARK if dark else _LIGHT}color-scheme:{'dark' if dark else 'light'};"
            f'--owl-image:url("data:image/webp;base64,{_owl_image()}");}}')
    font = "" if low_data else _FONT_IMPORT   # low-data mode downloads no web font
    return f"<style>{_min(font + root + _CSS + ''.join(extra))}</style>"


def _day_background() -> str:
    motes = (
        (8, 21, 16, 8, 2, 22), (16, 36, 10, 9, 5, -18), (7, 58, 22, 11, 6, 26),
        (22, 68, 13, 7, 3, -21), (13, 87, 24, 10, 8, 31), (28, 18, 12, 8, 6, 20),
        (86, 24, 20, 10, 5, -25), (95, 42, 14, 7, 2, -23), (81, 51, 10, 9, 7, 19),
        (90, 66, 22, 11, 3, -32), (78, 82, 15, 8, 5, 24), (94, 91, 16, 10, 7, -26),
    )
    parts = ['<div class="bg-fx day-sky" aria-hidden="true">']
    for left, top, size, period, phase, drift in motes:
        tint = "rgba(107,78,189,.52)" if left < 50 else "rgba(167,88,173,.52)"
        parts.append(f'<i class="day-mote" style="--left:{left}%;--top:{top}%;--size:{size}px;'
                     f'--period:{period}s;--phase:-{phase}s;--drift:{drift}px;--tint:{tint}"></i>')
    return "".join(parts) + "</div>"


def background_fx(dark: bool = False, seed: int = 7, low_data: bool = False) -> str:
    """Render the decorative background for the current appearance."""
    if low_data:
        return ""
    if not dark:
        return _day_background()

    rnd = random.Random(seed)
    parts = ['<div class="bg-fx night-sky" aria-hidden="true">']
    tints = ("#fff8e8", "#d5e5ff", "#f0f5ff")
    # Faint points follow the diagonal glow, with larger stars spread across the sky.
    for index in range(136):
        x = rnd.uniform(0, 100)
        y = rnd.uniform(0, 100) if index < 108 else max(0, min(100, 77 - .56 * x + rnd.gauss(0, 9)))
        size = rnd.choices((.8, 1, 1.5, 2.2), weights=(38, 37, 20, 5))[0]
        peak = rnd.uniform(.49, .83) if size > 1 else rnd.uniform(.24, .61)
        dim = rnd.uniform(.09, .2)
        period = rnd.uniform(3.5, 9)
        glow = " bright" if size > 2 else ""
        parts.append(f'<i class="sky-star{glow}" style="left:{x:.1f}%;top:{y:.1f}%;--size:{size}px;'
                     f'--tint:{rnd.choice(tints)};--dim:{dim:.2f};--mid:{(dim + peak) / 2:.2f};'
                     f'--peak:{peak:.2f};--period:{period:.1f}s;--phase:-{rnd.uniform(0, period):.1f}s"></i>')
    for top, left, angle, delay in ((20, 18, 25, 4), (38, 66, 151, 18), (11, 43, 32, 32)):
        parts.append(f'<i class="sky-meteor" style="--top:{top}%;--left:{left}%;--angle:{angle}deg;--delay:{delay}s"></i>')
    parts.append("</div>")
    return "".join(parts)


def mascot(size: int = 120) -> str:
    """Display the amethyst owl in the existing mascot space."""
    sparks = '<i class="owl-spark left"></i><i class="owl-spark right"></i>' if size >= 72 else ""
    return (f'<span class="entendi-mascot" role="img" aria-label="Amethyst owl mascot" '
            f'style="width:{size}px;height:{round(size * 130 / 120)}px">'
            f'<i class="owl-shadow"></i><i class="owl-body"></i>{sparks}</span>')


def hero_html(headline: str = "Understand any official letter,", alternate: str = "in your language.",
              description: str = "See what the letter is about, what to do next, and when it’s due.") -> str:
    return _min(f'''<div class="hero"><div class="mwrap"><div class="halo"></div>{mascot(120)}</div>
<span class="eyebrow">Entendi</span>
<h1 class="hero-title">{esc(headline)}<br><span class="gt">{esc(alternate)}</span></h1>
<p>{esc(description)}</p></div>''')


def page_header(page: str, title: str, tagline: str) -> str:
    return _min(f'''<div class="pagehead"><div class="ptitle"><div class="ptile">{icon(page)}</div><div><span class="eyebrow">Entendi</span>
<h1>{esc(title)}</h1><p>{esc(tagline)}</p></div></div><div class="mwrap">{mascot(72)}</div></div>''')


def steps_html(translate=lambda value: value) -> str:
    steps = (("Photo", "Upload a letter or take a clear photo."),
             ("Read", "Get a plain-language explanation and see the original wording."),
             ("Act", "Follow the checklist and add important dates to your calendar."))
    cards = "".join(f"<div class='step'><i>{n:02}</i><b>{esc(translate(title))}</b><span>{esc(translate(detail))}</span></div>"
                    for n, (title, detail) in enumerate(steps, 1))
    return _min(f'<div class="steps">{cards}</div>')


def feature_card_html(key: str, title: str, tagline: str) -> str:
    return _min(f"<div class='ficon'>{icon(key)}</div><div class='ftitle'>{esc(title)}</div><div class='ftag'>{esc(tagline)}</div>")


def nav_label(text: str) -> str:
    return f"<div class='navlabel'>{esc(text)}</div>"


def sidebar_brand() -> str:
    return _min(f"<div class='brand'>{mascot(38)}<b>Entendi</b></div>")


def group_heading(text: str, kind: str = "") -> str:
    return f"<div class='group-h {esc(kind)}'>{esc(text)}</div>"


def badge_html(text: str, kind: str = "") -> str:
    return f"<span class='badge {esc(kind)}'>{esc(text)}</span>"


def empty_html(title: str, text: str) -> str:
    return _min(f"<div class='empty'><b>{esc(title)}</b>{esc(text)}</div>")


def fact_html(label: str, value: str, footnote: str = "") -> str:
    return (f'<div class="letter-fact"><span>{esc(label)}</span><b>{esc(value)}</b>'
            f'<small>{esc(footnote)}</small></div>')


def callout_html(text: str) -> str:
    return f"<div class='callout'>{esc(text)}</div>"

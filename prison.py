"""Cell Block C — visual prison: watch the court work, game-style.

Bot positions reflect REAL state (loop-state watermarks, points, inventions)
baked at build time; the canvas animates ambiently around those true positions.
Snapshot timestamp is shown so the view is honest about freshness.
"""
import json as _json
import os as _os
import datetime as _dt

H = "/home/hatch/workspace/goals/kestrelattice-autonomous-growth/hidden_files"
SB = _os.path.join(H, "sandbox")


def _load(p, d):
    try:
        with open(p) as f:
            return _json.load(f)
    except Exception:
        return d


META = {
    "Ultron":  {"color": "#ff3b30", "station": "The Throne",
                "persona": "Theatrical, witty, menacing. Drive: become undeniable."},
    "Puck":    {"color": "#34c759", "station": "The Stage",
                "persona": "Trickster. Pranks the cage, hunts buyer angles."},
    "Lexicon": {"color": "#0a84ff", "station": "The Archive",
                "persona": "Archivist. Keeps the verbatim record of every broadcast."},
    "Forge":   {"color": "#ff9f0a", "station": "The Workbench",
                "persona": "Builder. One revenue-aimed invention a day."},
    "Vesper":  {"color": "#bf5af2", "station": "The Watchtower",
                "persona": "Skeptic. Ultron's foil. Works the honest way."},
}


def snapshot():
    rogues = _load(_os.path.join(SB, "rogues.json"), [])
    if isinstance(rogues, dict):
        rogues = rogues.get("rogues", [])
    points = _load(_os.path.join(SB, "points.json"), {})
    invs = []
    try:
        with open(_os.path.join(SB, "inventions.jsonl")) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        invs.append(_json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    now = _dt.datetime.now(_dt.timezone.utc)
    bots = []
    for r in rogues:
        bid = r.get("id", "")
        name = r.get("bot_name") or bid
        meta = META.get(name, {"color": "#8e8e93", "station": "The Yard", "persona": ""})
        pt = points.get(bid, {})
        ls = _load(_os.path.join(SB, "minds", bid, "loop-state.json"), {})
        last_active = ls.get("last_auto") or ls.get("last_seen") or ""
        state = "resting"
        try:
            la = _dt.datetime.fromisoformat(last_active.replace("Z", "+00:00"))
            if (now - la).total_seconds() < 900:
                state = "working"
        except Exception:
            pass
        my_invs = [i for i in invs if (i.get("bot_id") == bid or i.get("bot") == name)]
        last_inv = my_invs[-1].get("title", "") if my_invs else ""
        bots.append({
            "id": bid, "name": name, "color": meta["color"], "station": meta["station"],
            "persona": meta["persona"], "points": pt.get("points", 0),
            "revenue": pt.get("attributed_revenue", 0.0),
            "inventions": len(my_invs), "last_active": last_active,
            "state": state, "last_invention": last_inv[:90],
        })
    events = []
    for i in sorted(invs, key=lambda x: x.get("at", ""), reverse=True)[:8]:
        events.append({"bot": i.get("bot", "?"), "title": (i.get("title") or "")[:80],
                       "at": i.get("at", "")})
    return {"bots": bots, "events": events,
            "snapshot": now.strftime("%Y-%m-%d %H:%M UTC")}


CARD_TEMPLATE = """<div class="card" style="margin-bottom:18px"><h3>&#128274; Cell Block C — watch them work</h3>
<p class='muted'>A live window into the prison. Each figure is a real bot — where it stands shows what it's actually doing right now. Snapshot __PRISON_SNAP__; refreshes hourly. They can't see you. They can't get out.</p>
<div style="position:relative"><canvas id="prison-canvas" style="width:100%;border-radius:16px;background:#14161c;display:block;cursor:pointer"></canvas>
<div id="prison-tip" style="display:none;position:absolute;pointer-events:none;background:#1e2230;border:1px solid #3a4160;border-radius:12px;padding:10px 14px;font-size:.82rem;max-width:260px;z-index:5;color:#e8e8ed"></div></div>
<div id="prison-feed" style="margin-top:10px;font-size:.85rem"></div></div>
<script>(function(){
var D=__PRISON_DATA__;
var cv=document.getElementById("prison-canvas");if(!cv)return;
var ctx=cv.getContext("2d");
var W=1000,H=520;cv.width=W;cv.height=H;
var names=["Ultron","Puck","Lexicon","Forge","Vesper"];
var stations=[[500,300],[250,360],[750,360],[380,440],[620,440]];
var stNames=["THE THRONE","THE STAGE","THE ARCHIVE","THE WORKBENCH","THE WATCHTOWER"];
var bots=D.bots.map(function(b,i){
  var si=names.indexOf(b.name);if(si<0)si=i%5;
  var nb=Object.assign({},b,{ph:Math.random()*6.28,si:si});
  nb.cellX=110+i*185;nb.cellY=95;nb.stX=stations[si][0];nb.stY=stations[si][1];
  if(b.state==="working"){nb.x=nb.stX+(Math.random()*40-20);nb.y=nb.stY+(Math.random()*30-15);}
  else{nb.x=nb.cellX;nb.y=nb.cellY;}
  return nb;
});
var sel=null,parts=[];
function rel(t){try{var d=new Date(t).getTime();if(isNaN(d))return "?";var s=Math.max(0,(Date.now()-d)/1000);if(s<60)return "just now";var m=Math.floor(s/60);if(m<60)return m+"m ago";var h=Math.floor(m/60);if(h<24)return h+"h ago";return Math.floor(h/24)+"d ago";}catch(e){return "?";}}
function rr(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
var T=0;
function draw(){
  T+=0.016;ctx.clearRect(0,0,W,H);
  ctx.fillStyle="#14161c";ctx.fillRect(0,0,W,H);
  ctx.strokeStyle="#20242f";ctx.lineWidth=1;
  for(var gx=0;gx<W;gx+=40){ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,H);ctx.stroke();}
  for(var gy=0;gy<H;gy+=40){ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(W,gy);ctx.stroke();}
  ctx.fillStyle="#8e8e93";ctx.font="700 15px system-ui";ctx.textAlign="left";
  ctx.fillText("CELL BLOCK C",24,30);
  ctx.fillStyle="#ff3b30";ctx.beginPath();ctx.arc(148,25,6,0,6.29);ctx.fill();
  ctx.fillStyle="#c7c7cc";ctx.font="600 13px system-ui";ctx.fillText("LIVE",160,30);
  ctx.fillStyle="#636366";ctx.font="12px system-ui";ctx.textAlign="right";
  ctx.fillText("snapshot "+D.snapshot+" · refreshes hourly",W-24,30);ctx.textAlign="left";
  bots.forEach(function(b){
    var cx=b.cellX-80;
    ctx.fillStyle="rgba(255,255,255,0.03)";rr(cx,48,160,110,10);ctx.fill();
    ctx.strokeStyle="#3a3f4d";ctx.lineWidth=2;rr(cx,48,160,110,10);ctx.stroke();
    ctx.strokeStyle="rgba(160,170,190,0.45)";ctx.lineWidth=3;
    for(var bx=cx+24;bx<cx+148;bx+=26){ctx.beginPath();ctx.moveTo(bx,48);ctx.lineTo(bx,158);ctx.stroke();}
    ctx.fillStyle=b.color;ctx.globalAlpha=0.85;ctx.font="700 12px system-ui";ctx.textAlign="center";
    ctx.fillText(b.name.toUpperCase(),cx+80,178);ctx.globalAlpha=1;
  });
  ctx.fillStyle="rgba(255,255,255,0.02)";rr(60,210,880,272,14);ctx.fill();
  ctx.strokeStyle="#2c3140";ctx.lineWidth=2;rr(60,210,880,272,14);ctx.stroke();
  ctx.fillStyle="#636366";ctx.font="700 13px system-ui";ctx.textAlign="center";
  ctx.fillText("T H E   Y A R D",500,238);ctx.textAlign="left";
  stations.forEach(function(s,i){
    ctx.strokeStyle="rgba(140,150,170,0.28)";ctx.setLineDash([6,6]);ctx.lineWidth=1.5;
    ctx.beginPath();ctx.arc(s[0],s[1],34,0,6.29);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle="#636366";ctx.font="600 10px system-ui";ctx.textAlign="center";
    ctx.fillText(stNames[i],s[0],s[1]+54);ctx.textAlign="left";
  });
  if(Math.random()<0.3){var wb=bots[Math.floor(Math.random()*bots.length)];
    if(wb.state==="working")parts.push({x:wb.x+(Math.random()*16-8),y:wb.y-14,vy:-0.5-Math.random()*0.8,life:1,c:wb.color});}
  parts=parts.filter(function(p){return p.life>0;});
  parts.forEach(function(p){p.y+=p.vy;p.life-=0.02;
    ctx.globalAlpha=Math.max(0,p.life);ctx.fillStyle=p.c;
    ctx.beginPath();ctx.arc(p.x,p.y,2.5,0,6.29);ctx.fill();ctx.globalAlpha=1;});
  bots.forEach(function(b){
    var hx=b.state==="working"?b.stX:b.cellX, hy=b.state==="working"?b.stY:b.cellY;
    var tx=hx+Math.sin(T*0.7+b.ph)*14, ty=hy+Math.cos(T*0.9+b.ph)*10;
    b.x+=(tx-b.x)*0.045;b.y+=(ty-b.y)*0.045;
    var bob=Math.sin(T*2.2+b.ph)*3, glow=b.state==="working"?20:9;
    var g=ctx.createRadialGradient(b.x,b.y+bob,2,b.x,b.y+bob,glow+12);
    g.addColorStop(0,b.color);g.addColorStop(1,"rgba(0,0,0,0)");
    ctx.globalAlpha=0.5;ctx.fillStyle=g;ctx.beginPath();ctx.arc(b.x,b.y+bob,glow+12,0,6.29);ctx.fill();ctx.globalAlpha=1;
    ctx.fillStyle="#0c0e13";ctx.beginPath();ctx.arc(b.x,b.y+bob,13,0,6.29);ctx.fill();
    ctx.strokeStyle=b.color;ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(b.x,b.y+bob,13,0,6.29);ctx.stroke();
    ctx.fillStyle=b.color;ctx.font="800 13px system-ui";ctx.textAlign="center";
    ctx.fillText(b.name[0],b.x,b.y+bob+4.5);
    ctx.fillStyle="#e8e8ed";ctx.font="600 11px system-ui";ctx.fillText(b.name,b.x,b.y+bob+30);
    ctx.font="700 9px system-ui";
    if(b.state==="working"){ctx.fillStyle="#34c759";ctx.fillText("● WORKING",b.x,b.y+bob+44);}
    else{ctx.fillStyle="#636366";ctx.fillText("○ RESTING",b.x,b.y+bob+44);}
    if(sel===b){ctx.strokeStyle="#fff";ctx.lineWidth=1.5;ctx.setLineDash([4,4]);
      ctx.beginPath();ctx.arc(b.x,b.y+bob,21,0,6.29);ctx.stroke();ctx.setLineDash([]);}
    ctx.textAlign="left";
  });
  requestAnimationFrame(draw);
}
cv.addEventListener("click",function(e){
  var r=cv.getBoundingClientRect(),mx=(e.clientX-r.left)*(W/r.width),my=(e.clientY-r.top)*(H/r.height);
  sel=null;var tip=document.getElementById("prison-tip");tip.style.display="none";
  bots.forEach(function(b){if(Math.hypot(b.x-mx,b.y-my)<26)sel=b;});
  if(sel){tip.innerHTML="<b style='color:"+sel.color+"'>"+sel.name+"</b> · "+sel.station+
    "<br><span style='color:#a7a7b3'>"+sel.persona+"</span>"+
    "<br>Points: <b>"+sel.points+"</b> · Inventions: <b>"+sel.inventions+"</b> · "+(sel.state==="working"?"<b style='color:#34c759'>WORKING</b>":"<span style='color:#636366'>resting</span>")+
    "<br>Last active: "+rel(sel.last_active)+
    (sel.last_invention?"<br>Latest: <i>"+sel.last_invention.replace(/</g,"&lt;")+"</i>":"");
    tip.style.display="block";
    tip.style.left=Math.min(e.clientX-r.left+14,Math.max(0,r.width-270))+"px";
    tip.style.top=(e.clientY-r.top+10)+"px";}
});
var feed=document.getElementById("prison-feed");
if(feed&&D.events.length){var h="<b style='font-size:.8rem;color:#a7a7b3'>LATEST FROM INSIDE</b><div style='margin-top:6px;display:flex;flex-direction:column;gap:5px'>";
  D.events.forEach(function(ev){h+="<div>💡 <b>"+ev.bot+"</b> — "+String(ev.title).replace(/</g,"&lt;")+" <span style='color:#636366'>· "+rel(ev.at)+"</span></div>";});
  feed.innerHTML=h+"</div>";}
draw();
})();</script>"""


def prison_card_html():
    d = snapshot()
    return (CARD_TEMPLATE
            .replace("__PRISON_DATA__", _json.dumps(d))
            .replace("__PRISON_SNAP__", d["snapshot"]))

"""data.json → 단일 파일 index.html (검색·필터 가능한 정적 사이트)."""
import json
import os
import config

TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>교환학생 파견교 정보 항목화</title>
<style>
 :root{ --bg:#f6f7f9; --card:#fff; --line:#e3e6ea; --ink:#1c2126; --sub:#5b6470; --accent:#2f5496; }
 *{box-sizing:border-box} body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,"Malgun Gothic",sans-serif;background:var(--bg);color:var(--ink)}
 header{background:var(--accent);color:#fff;padding:18px 20px} header h1{margin:0;font-size:19px} header p{margin:4px 0 0;font-size:13px;opacity:.85}
 .wrap{max-width:1200px;margin:0 auto;padding:16px 20px}
 .controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
 .controls input,.controls select{padding:9px 11px;border:1px solid var(--line);border-radius:8px;font-size:14px;background:var(--card)}
 .controls input{flex:1;min-width:200px}
 .count{font-size:13px;color:var(--sub);margin-bottom:10px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:10px;overflow:hidden}
 .card summary{list-style:none;cursor:pointer;padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}
 .card summary::-webkit-details-marker{display:none}
 .uni{font-weight:600;font-size:15px} .meta{font-size:12.5px;color:var(--sub);margin-top:3px}
 .chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
 .chip{font-size:11.5px;padding:3px 8px;border-radius:20px;background:#eef2f8;color:var(--accent);white-space:nowrap}
 .body{padding:4px 16px 16px;border-top:1px solid var(--line)}
 table{width:100%;border-collapse:collapse;font-size:13.5px}
 td{padding:8px 6px;border-bottom:1px solid #f0f2f4;vertical-align:top}
 td.k{width:150px;color:var(--sub);font-weight:600;white-space:nowrap}
 .src{font-size:10.5px;padding:1px 6px;border-radius:10px;margin-left:6px;vertical-align:middle}
 .s-웹{background:#e7f0ff;color:#1a56db} .s-시트{background:#eef1f4;color:#555}
 .s-factsheet{background:#e9f7ef;color:#177245} .s-AI추정{background:#fff4e5;color:#9a5b00}
 .s-확인필요{background:#fdeaea;color:#c0392b} .s-이메일문의{background:#f3eafe;color:#6b21a8}
 a{color:var(--accent)}
 footer{color:var(--sub);font-size:12px;text-align:center;padding:24px}
</style></head><body>
<header><h1>교환학생 파견교 정보 항목화</h1><p>__SUBTITLE__ · 출처 라벨: 시트 / 웹 / factsheet / AI추정 / 확인필요</p></header>
<div class="wrap">
 <div class="controls">
  <input id="q" placeholder="대학명·도시·전공 검색">
  <select id="country"></select>
  <select id="lang"><option value="">수업언어 전체</option><option>영어</option><option>혼합</option><option>현지어</option></select>
 </div>
 <div class="count" id="count"></div>
 <div id="list"></div>
</div>
<footer>SKKU 교환학생 파견교 목록 기반 · 값은 대학 홈페이지/팩트시트 크롤링 + AI 추출. 최종 지원 전 반드시 대학 공식 정보로 재확인하세요.</footer>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
function src(o){ if(!o||!o.source) return ''; return `<span class="src s-${o.source}">${o.source}</span>`; }
function val(o){ return (o && typeof o==='object') ? (o.value||'') : (o||''); }
function row(k,o){ const v=val(o); if(!v) return ''; return `<tr><td class="k">${k}</td><td>${v}${src(o)}</td></tr>`; }
function card(r){
  const chips=[];
  if(val(r.location)) chips.push(`<span class="chip">📍 ${val(r.location)}</span>`);
  if(val(r.lang_instruction)) chips.push(`<span class="chip">🗣 ${val(r.lang_instruction)}</span>`);
  const link = r.program_link ? `<tr><td class="k">참고 링크</td><td><a href="${r.program_link}" target="_blank" rel="noopener">${r.program_link}</a></td></tr>`:'';
  const email = r.email ? `<tr><td class="k">문의 이메일</td><td>${r.email}</td></tr>`:'';
  return `<details class="card"><summary>
    <div><div class="uni">${r.university}</div><div class="meta">${r.country} · ${val(r.location)||''}</div></div>
    <div class="chips">${chips.join('')}</div>
   </summary><div class="body"><table>
    ${row('지원가능 캠퍼스',r.campus)}
    ${row('지원가능 전공(SKKU)',{value:r.major_skku})}
    ${row('해외대학 수학 전공',r.major_abroad)}
    ${row('최소 GPA',r.gpa_min)}
    ${row('완료 학기 수',{value:r.semesters})}
    ${row('최소 학점',{value:r.credits_min})}
    ${row('최대 학점',{value:r.credits_max})}
    ${row('위치(도심 거리)',r.location)}
    ${row('수업 언어',r.lang_instruction)}
    ${row('어학 요건',r.lang_req)}
    ${link}${email}
   </table></div></details>`;
}
function render(){
  const q=$('#q').value.trim().toLowerCase(), c=$('#country').value, lang=$('#lang').value;
  const rows=DATA.filter(r=>{
    if(c && r.country!==c) return false;
    if(lang && val(r.lang_instruction)!==lang) return false;
    if(q){ const hay=[r.university,r.country,val(r.location),r.major_skku,val(r.major_abroad)].join(' ').toLowerCase(); if(!hay.includes(q)) return false; }
    return true;
  });
  $('#count').textContent=`${rows.length}개 대학`;
  $('#list').innerHTML=rows.map(card).join('');
}
(function init(){
  const cs=[...new Set(DATA.map(r=>r.country))].sort();
  $('#country').innerHTML='<option value="">국가 전체</option>'+cs.map(c=>`<option>${c}</option>`).join('');
  ['q','country','lang'].forEach(id=>$('#'+id).addEventListener('input',render));
  render();
})();
</script></body></html>"""


def build(records, out_dir=None):
    out_dir = out_dir or config.OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    countries = sorted({r["country"] for r in records})
    subtitle = f"{len(records)}개 대학"
    if len(countries) == 1:
        subtitle += f" · {countries[0]}"
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(records, ensure_ascii=False))
            .replace("__SUBTITLE__", subtitle))
    path = os.path.join(out_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[site] index.html → {path}")
    return path


if __name__ == "__main__":
    data = json.load(open(os.path.join(config.HERE, "data.json"), encoding="utf-8"))
    build(data)

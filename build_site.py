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
 .match{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-bottom:14px}
 .match summary{cursor:pointer;font-weight:600;font-size:14.5px}
 .mrow{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;align-items:center}
 .mrow label{font-size:13px;color:var(--sub);display:flex;align-items:center;gap:6px}
 .mrow input[type=number]{padding:7px 9px;border:1px solid var(--line);border-radius:8px;font-size:13.5px;width:90px}
 .mrow select{padding:7px 9px;border:1px solid var(--line);border-radius:8px;font-size:13.5px}
 .mbtn{padding:8px 16px;border:0;border-radius:8px;background:var(--accent);color:#fff;font-size:13.5px;cursor:pointer}
 .mbtn.ghost{background:#eef2f8;color:var(--accent)}
 .badge{font-size:11px;padding:2px 7px;border-radius:10px;margin-right:4px;white-space:nowrap}
 .b-ok{background:#e9f7ef;color:#177245} .b-warn{background:#fff4e5;color:#9a5b00}
 .mnote{font-size:11.5px;color:var(--sub);margin-top:10px;line-height:1.5}
 footer{color:var(--sub);font-size:12px;text-align:center;padding:24px}
</style></head><body>
<header><h1>교환학생 파견교 정보 항목화</h1><p>__SUBTITLE__ · 출처 라벨: 시트 / 웹 / factsheet / AI추정 / 확인필요</p></header>
<div class="wrap">
 <details class="match" id="matchbox">
  <summary>🎯 맞춤 검색 — 내 조건에 맞는 학교 찾기</summary>
  <div class="mrow">
   <label>내 GPA (4.5 만점) <input id="m_gpa" type="number" step="0.01" min="0" max="4.5" placeholder="예: 3.8"></label>
   <label>완료 학기 수 <input id="m_sem" type="number" step="1" min="0" max="12" placeholder="예: 4"></label>
   <label>소속(전공) <select id="m_major"><option value="">무관</option></select></label>
   <label>선호 위치 <select id="m_tier"><option value="">무관</option><option>도시</option><option>준도시</option><option>도시 외곽</option></select></label>
  </div>
  <div class="mrow">
   <label>TOEFL iBT <input id="m_toefl" type="number" min="0" max="120" placeholder="점수"></label>
   <label>IELTS <input id="m_ielts" type="number" step="0.5" min="0" max="9" placeholder="점수"></label>
   <label><input type="checkbox" id="m_nolang"> 공인 어학성적 없음</label>
   <button class="mbtn" id="m_apply">적용</button>
   <button class="mbtn ghost" id="m_reset">초기화</button>
  </div>
  <div class="mnote">국가·수업언어는 아래 필터를 함께 사용하세요. 조건 미달 학교는 숨겨지고, 값이 "이메일 문의"·"학과별 상이" 등이라 판단할 수 없는 항목은 ⚠️로 표시됩니다(직접 확인 필요).
  GPA는 만점 비율로 환산(4.5→각교 만점)한 근사치이고, CEFR 요건은 TOEFL/IELTS 통상 환산(B2≈iBT 72·IELTS 5.5, C1≈95·7.0)을 사용합니다. 최종 지원 전 반드시 공식 요강을 확인하세요.</div>
 </details>
 <div class="controls">
  <input id="q" placeholder="대학명·도시·전공 검색">
  <select id="country"></select>
  <select id="lang"><option value="">수업언어 전체</option></select>
  <select id="tier"><option value="">위치 전체</option></select>
 </div>
 <div class="count" id="count"></div>
 <div id="list"></div>
</div>
<footer>SKKU 교환학생 파견교 목록 기반 · 값은 대학 홈페이지/팩트시트 크롤링 + AI 추출. 최종 지원 전 반드시 대학 공식 정보로 재확인하세요.<br>
※ 어학요건의 "TOEFL iBT N점 (신척도)"는 2026년 1월 21일 도입된 1~6점 체계 기준이며, 그 외 TOEFL 점수는 기존 0~120점 체계입니다.</footer>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
function src(o){ if(!o||!o.source) return ''; return `<span class="src s-${o.source}">${o.source}</span>`; }
function val(o){ return (o && typeof o==='object') ? (o.value||'') : (o||''); }
function row(k,o){ const v=val(o); if(!v) return ''; return `<tr><td class="k">${k}</td><td>${v}${src(o)}</td></tr>`; }

/* ── 맞춤 검색(자격 매칭) ─────────────────────────────
   판정: 'ok' 충족 · 'fail' 미달(숨김) · 'warn' 판단불가(⚠️ 표시) · 'skip' 입력 안 함 */
let M=null; // {g,s,mj,t,i,none}
const CEFR={A1:[0,0],A2:[0,0],B1:[42,4.0],B2:[72,5.5],C1:[95,7.0],C2:[110,8.5]};
function chkGpa(r,g){ if(g==null) return 'skip';
  const v=val(r.gpa_min); if(!v||v==='담당자 이메일 문의'||v.startsWith('확인필요')) return 'warn';
  if(/^(제한 없음|명시 없음|Good standing|홈교 기준|프로그램별 상이)/.test(v)) return 'ok';
  const m=v.match(/(\d+(?:\.\d+)?)(?:~\d+(?:\.\d+)?)?\/(\d+(?:\.\d+)?)/);
  if(!m) return 'warn';
  return (g/4.5+1e-9>=parseFloat(m[1])/parseFloat(m[2]))?'ok':'fail'; }
function chkSem(r,s){ if(s==null) return 'skip';
  const v=val(r.semesters); if(!v) return 'warn';
  if(/^(제한 없음|명시 없음|홈교 기준)/.test(v)) return 'ok';
  const m=v.match(/^(\d)(?:~\d)?학기 이상/); if(!m) return 'warn';
  return s>=parseInt(m[1])?'ok':'fail'; }
// SKKU 공식 주관학부(대학) 목록 (킹고인포 기준, 2026-07)
const MAJORS=['경영대학','경제대학','동아시아학술원','문과대학','법과대학','사범대학','사회과학대학',
  '삼성융합의과학원','생명공학대학','성균나노과학기술원','성균융합원','소프트웨어대학','소프트웨어융합대학',
  '스포츠과학대학','약학대학','예술대학','유학대학','의과대학','자연과학대학','정보통신대학','학부대학'];
// 단과대학 → 데이터에 학과 단위로 제한된 경우 (선택 시 본인 학과인지 확인 필요 → ⚠️)
const MAJOR_DEPTS={'경영대학':['글로벌경영학과'],'경제대학':['글로벌경제학과'],
  '문과대학':['문헌정보학과','러시아어문학과'],'사회과학대학':['미디어커뮤니케이션학과'],'예술대학':['디자인학과']};
function chkMajor(r,mj){ if(!mj) return 'skip';
  const v=r.major_skku||''; if(!v) return 'warn';
  if(v.includes('모든 전공')||v.includes(mj)) return 'ok';
  if((MAJOR_DEPTS[mj]||[]).some(d=>v.includes(d))) return 'warn'; // 학과 제한 — 본인 학과 여부 확인
  return 'fail'; }
function chkLang(r,t,i,none){ const v=val(r.lang_req); if(!v) return 'warn';
  if(/(공인성적 불요|SKKU|확인서|^명시 없음)/.test(v)) return 'ok';
  if(v==='담당자 이메일 문의'||v.startsWith('확인필요')||/상이/.test(v)) return 'warn';
  if(!t&&!i&&!none) return 'skip';
  if(none) return 'fail'; // 점수형 요건인데 성적 없음
  let known=false;
  const mt=v.match(/TOEFL(?![- ]?(?:PBT|ITP|CBT))[- ]?(?:iBT ?)?(\d+(?:\.\d+)?)점/i);
  if(mt){ const req=parseFloat(mt[1]);
    if(req>=10){ known=true; if(t&&t>=req) return 'ok'; } }
  const mi=v.match(/IELTS[^0-9]{0,15}(\d(?:\.\d)?)점/i);
  if(mi){ known=true; if(i&&i>=parseFloat(mi[1])) return 'ok'; }
  const mc=v.match(/CEFR ([ABC][12])/);
  if(mc && /영어|English/.test(v)){ known=true;
    const lv=CEFR[mc[1]]||[999,99]; if((t&&t>=lv[0])||(i&&i>=lv[1])) return 'ok'; }
  if(!known) return 'warn'; // 현지어 요건·신척도 전용 등 → 직접 확인
  return 'fail'; }
function chkTier(r,tier){ if(!tier) return 'skip';
  const t=(r.location||{}).tier; if(!t) return 'warn';
  return t===tier?'ok':'fail'; }
function matchInfo(r){ if(!M) return null;
  const res={GPA:chkGpa(r,M.g),학기:chkSem(r,M.s),전공:chkMajor(r,M.mj),어학:chkLang(r,M.t,M.i,M.none),위치:chkTier(r,M.tier)};
  const vals=Object.values(res);
  return {res, fail:vals.includes('fail'), warn:vals.includes('warn')}; }
function badges(mi){ if(!mi) return '';
  const parts=[];
  for(const [k,st] of Object.entries(mi.res)){
    if(st==='ok') parts.push(`<span class="badge b-ok">✓ ${k}</span>`);
    else if(st==='warn') parts.push(`<span class="badge b-warn">⚠ ${k} 확인</span>`); }
  return parts.length?`<div style="margin-top:5px">${parts.join('')}</div>`:''; }
function card(r,mi){
  const chips=[];
  if(val(r.location)) chips.push(`<span class="chip">📍 ${val(r.location)}</span>`);
  if(val(r.lang_instruction)) chips.push(`<span class="chip">🗣 ${val(r.lang_instruction)}</span>`);
  const link = r.program_link ? `<tr><td class="k">참고 링크</td><td><a href="${r.program_link}" target="_blank" rel="noopener">${r.program_link}</a></td></tr>`:'';
  const email = r.email ? `<tr><td class="k">문의 이메일</td><td>${r.email}</td></tr>`:'';
  return `<details class="card"><summary>
    <div><div class="uni">${r.university}</div><div class="meta">${r.country} · ${val(r.location)||''}</div>${badges(mi)}</div>
    <div class="chips">${chips.join('')}</div>
   </summary><div class="body"><table>
    ${row('지원가능 전공(SKKU)',{value:r.major_skku})}
    ${row('해외대학 수학 전공',r.major_abroad)}
    ${row('최소 GPA',r.gpa_min)}
    ${row('완료 학기 수',r.semesters)}
    ${row('최소 학점',r.credits_min)}
    ${row('최대 학점',r.credits_max)}
    ${row('위치(도심 거리)',r.location)}
    ${row('수업 언어',r.lang_instruction)}
    ${row('어학 요건',r.lang_req)}
    ${row('특징',{value:(r.features||[]).map(f=>f.text).join(' · ')})}
    ${link}${email}
   </table></div></details>`;
}
function render(){
  const q=$('#q').value.trim().toLowerCase(), c=$('#country').value, lang=$('#lang').value, tier=$('#tier').value;
  let pairs=DATA.filter(r=>{
    if(c && r.country!==c) return false;
    if(lang && !val(r.lang_instruction).split(', ').includes(lang)) return false;
    if(tier && (r.location||{}).tier!==tier) return false;
    if(q){ const hay=[r.university,r.country,val(r.location),r.major_skku,val(r.major_abroad)].join(' ').toLowerCase(); if(!hay.includes(q)) return false; }
    return true;
  }).map(r=>[r, matchInfo(r)]);
  if(M){
    pairs=pairs.filter(([r,mi])=>!mi.fail);
    pairs.sort((a,b)=>(a[1].warn?1:0)-(b[1].warn?1:0)); // 전부 충족 먼저
    const nOk=pairs.filter(([r,mi])=>!mi.warn).length;
    $('#count').textContent=`내 조건에 맞는 대학 ${pairs.length}곳 (✓ 전부 충족 ${nOk} · ⚠ 일부 확인 필요 ${pairs.length-nOk})`;
  } else {
    $('#count').textContent=`${pairs.length}개 대학`;
  }
  $('#list').innerHTML=pairs.map(([r,mi])=>card(r,mi)).join('');
}
(function init(){
  const cs=[...new Set(DATA.map(r=>r.country))].sort();
  $('#country').innerHTML='<option value="">국가 전체</option>'+cs.map(c=>`<option>${c}</option>`).join('');
  // 수업언어 옵션: 값을 언어 단위로 분해해 빈도순 정렬 (예: "일본어, 영어" → 일본어/영어)
  const lc={};
  DATA.forEach(r=>val(r.lang_instruction).split(', ').filter(Boolean).forEach(l=>lc[l]=(lc[l]||0)+1));
  const ls=Object.keys(lc).filter(l=>l!=='확인필요').sort((a,b)=>lc[b]-lc[a]);
  $('#lang').innerHTML='<option value="">수업언어 전체</option>'+ls.map(l=>`<option value="${l}">${l} (${lc[l]})</option>`).join('');
  const tc={};
  DATA.forEach(r=>{const t=(r.location||{}).tier; if(t) tc[t]=(tc[t]||0)+1;});
  $('#tier').innerHTML='<option value="">위치 전체</option>'+['도시','준도시','도시 외곽'].filter(t=>tc[t]).map(t=>`<option value="${t}">${t} (${tc[t]})</option>`).join('');
  // 맞춤 검색: 소속(전공) 옵션 — SKKU 공식 주관학부(대학) 목록
  $('#m_major').innerHTML='<option value="">무관</option>'+MAJORS.map(m=>`<option value="${m}">${m}</option>`).join('');
  $('#m_apply').addEventListener('click',()=>{
    const num=id=>{const x=$('#'+id).value.trim(); return x===''?null:parseFloat(x);};
    M={g:num('m_gpa'), s:num('m_sem'), mj:$('#m_major').value, tier:$('#m_tier').value,
       t:num('m_toefl'), i:num('m_ielts'), none:$('#m_nolang').checked};
    if(M.g==null&&M.s==null&&!M.mj&&!M.tier&&M.t==null&&M.i==null&&!M.none) M=null;
    render();
  });
  $('#m_reset').addEventListener('click',()=>{
    ['m_gpa','m_sem','m_toefl','m_ielts'].forEach(id=>$('#'+id).value='');
    $('#m_major').value=''; $('#m_tier').value=''; $('#m_nolang').checked=false; M=null; render();
  });
  ['q','country','lang','tier'].forEach(id=>$('#'+id).addEventListener('input',render));
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

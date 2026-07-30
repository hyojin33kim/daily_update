(function(){
const D=window.MARKET_DATA;if(!D)return;
const fmt=(v,d=1)=>v==null?'N/A':Number(v).toLocaleString('ko-KR',{maximumFractionDigits:d});
const card=label=>[...document.querySelectorAll('.kpi-card')].find(x=>x.querySelector('.kpi-label')?.textContent.trim()===label);
const kpi=(label,value,sub)=>{const x=card(label);if(x){x.querySelector('.kpi-value').textContent=value;x.querySelector('.kpi-sub').textContent=sub;}};
const k=D.kospi,sign=k.change_pct>=0?'▲':'▼',gap=k.high_gap.at(-1).value;
document.getElementById('ts').textContent=`${k.as_of} 종가 · ${D.generated_at.slice(0,16).replace('T',' ')} KST 갱신`;
const alert=document.querySelector('.alert-dot + span');if(alert)alert.innerHTML=`KOSPI ${k.as_of}: <strong>${fmt(k.close,2)}</strong> (${sign}${Math.abs(k.change_pct).toFixed(2)}%) · VIX <strong>${fmt(D.vix.value,2)}</strong> · CNN F&amp;G <strong>${fmt(D.fear_greed.value,1)}</strong>`;
kpi('KOSPI 현재가',fmt(k.close,2),`${sign}${Math.abs(k.change_pct).toFixed(2)}% · ${k.as_of}`);
kpi('KOSPI Breadth',fmt(gap,1)+'%','실제 지수의 52주 고점 대비 이격');
kpi('Fear & Greed',fmt(D.fear_greed.value,1),`${D.fear_greed.rating} · ${D.fear_greed.as_of.slice(0,10)}`);
kpi('VIX 변동성',fmt(D.vix.value,2),`${D.vix.as_of} 종가`);kpi('P/C Ratio',fmt(D.put_call.value,2),`Equity P/C · ${D.put_call.as_of}`);
document.querySelectorAll('.ig-focus-card').forEach(x=>{const t=x.querySelector('.ig-fc-title'),v=x.querySelector('.ig-fc-val');if(!t||!v)return;if(t.textContent.trim()==='KOSPI Breadth'){t.textContent='KOSPI 52주 고점 이격';v.textContent=fmt(gap,1)+'%';}if(t.textContent.trim()==='50일 이격도')v.textContent=fmt(k.disparity_50,1)+'%';if(t.textContent.trim()==='VIX + P/C')v.textContent='VIX '+fmt(D.vix.value,2);if(t.textContent.trim()==='Fear & Greed')v.textContent=fmt(D.fear_greed.value,1)+'/100';});
const focus=[...document.querySelectorAll('.ig-focus-card')];
const focusData=[
 ['KOSPI 52주 고점 이격',fmt(gap,1)+'%',`${k.as_of} 종가 기준. 52주 고점과의 실제 가격 이격입니다.`],
 ['50일 이격도',fmt(k.disparity_50,1)+'%',`실제 KOSPI 종가와 50거래일 이동평균으로 계산했습니다.`],
 ['데이터 상태','검증 완료',`공개 원자료의 기준일과 범위를 검사한 뒤 게시합니다.`],
 ['VIX',''+fmt(D.vix.value,2),`${D.vix.as_of} Cboe VIX 종가입니다.`],
 ['CNN Fear & Greed',fmt(D.fear_greed.value,1)+'/100',`${D.fear_greed.as_of.slice(0,10)} · ${D.fear_greed.rating}`]
];
focus.forEach((x,i)=>{if(!focusData[i])return;x.querySelector('.ig-fc-title').textContent=focusData[i][0];x.querySelector('.ig-fc-val').textContent=focusData[i][1];x.querySelector('.ig-fc-desc').textContent=focusData[i][2];});
document.querySelectorAll('.ig-panel').forEach((panel,i)=>{if(i===0)return;panel.innerHTML=`<div class="ig-insight"><div class="ig-ins-tag">실제 데이터 기준</div><div class="ig-ins-body">KOSPI ${fmt(k.close,2)} (${k.as_of}) · 50일 이격도 ${fmt(k.disparity_50,1)}% · VIX ${fmt(D.vix.value,2)} · CNN Fear &amp; Greed ${fmt(D.fear_greed.value,1)}. 고정 전망과 검증되지 않은 역사 수치는 제거했습니다.</div></div>`;});
const s=document.querySelectorAll('.sent-card');if(s[0])s[0].querySelector('.sent-desc').innerHTML=`CNN F&amp;G <strong>${fmt(D.fear_greed.value,1)}/100</strong> · ${D.fear_greed.as_of.slice(0,10)}`;if(s[1])s[1].querySelector('.sent-desc').innerHTML=`현재 <strong>${fmt(D.vix.value,2)}</strong> · ${D.vix.as_of} 종가`;if(s[2])s[2].querySelector('.sent-desc').innerHTML=`Equity P/C <strong>${fmt(D.put_call.value,2)}</strong> · ${D.put_call.as_of}`;if(s[3])s[3].querySelector('.sent-desc').textContent=D.aaii.note;
const gauge=document.getElementById('fgGauge');if(gauge){const valueText=gauge.querySelector('text[font-size="20"]');if(valueText)valueText.textContent=fmt(D.fear_greed.value,1);const needle=gauge.querySelector('line');if(needle){const a=(D.fear_greed.value/100*180-180)*Math.PI/180;needle.setAttribute('x2',80+58*Math.cos(a));needle.setAttribute('y2',80+58*Math.sin(a));}const bar=document.querySelector('.bar-fg');if(bar)bar.style.width=Math.max(0,Math.min(100,D.fear_greed.value))+'%';}
const maPanel=[...document.querySelectorAll('.panel')].find(x=>x.querySelector('.panel-title')?.textContent.includes('KOSPI 이동평균선'));
if(maPanel){const summary=maPanel.querySelector(':scope > div[style*="display:flex"]');if(summary)summary.innerHTML=`<div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:10px 16px"><strong>50일 이격도 ${fmt(k.disparity_50,1)}%</strong><br><span style="font-size:11px">${k.as_of} 실제 종가 ${fmt(k.close,2)} 기준</span></div>`;}
const f=document.querySelector('.footer');if(f)f.innerHTML=`기준일 ${k.as_of} · <a href="${k.source}">KOSPI</a> · <a href="${D.vix.source}">VIX</a> · <a href="${D.put_call.source}">Cboe Equity Put/Call</a> · <a href="${D.fear_greed.source}">CNN Fear &amp; Greed</a> · N/A는 검증 가능한 무료 최신 자료가 없는 항목입니다.`;
const charts=(id,labels,values,color)=>{const old=Chart.getChart(id);if(old)old.destroy();return new Chart(document.getElementById(id),{type:'line',data:{labels,datasets:[{data:values,borderColor:color,backgroundColor:color,pointRadius:2,tension:.25}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'}}}}});};
charts('breadthChart',D.sp500.high_gap.map(x=>x.date.slice(2)),D.sp500.high_gap.map(x=>x.value),'#64748b');
charts('kospiBreathChart',k.high_gap.map(x=>x.date.slice(2)),k.high_gap.map(x=>x.value),'#7c3aed');
const bPanel=[...document.querySelectorAll('.panel')].find(x=>x.querySelector('.panel-title')?.textContent.includes('시장 쏠림'));
if(bPanel){bPanel.querySelector('.panel-title').childNodes[0].textContent='52주 고점 대비 실제 가격 이격: S&P 500 vs KOSPI ';const row=bPanel.querySelector('.breadth-kpi-row');if(row)row.innerHTML=`<div class="b-kpi"><div class="b-kpi-label">S&P 500 현재</div><div class="b-kpi-val">${fmt(D.sp500.high_gap.at(-1).value,1)}%</div><div class="b-kpi-sub">${D.sp500.as_of}</div></div><div class="b-kpi"><div class="b-kpi-label">KOSPI 현재</div><div class="b-kpi-val">${fmt(gap,1)}%</div><div class="b-kpi-sub">${k.as_of}</div></div>`;}
const vixOld=Chart.getChart('vixChart');if(vixOld)vixOld.destroy();new Chart(document.getElementById('vixChart'),{type:'line',data:{labels:D.vix.daily.map(x=>x.date.slice(5)),datasets:[{data:D.vix.daily.map(x=>x.value),borderColor:'#0078d4',pointRadius:2,tension:.2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:8}}}}});
const pcOld=Chart.getChart('pcChart');if(pcOld)pcOld.destroy();new Chart(document.getElementById('pcChart'),{type:'line',data:{labels:D.put_call.daily.map(x=>x.date.slice(5)),datasets:[{data:D.put_call.daily.map(x=>x.value),borderColor:'#f97316',pointRadius:3,tension:.2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:8}}}}});
const aaiiOld=Chart.getChart('aaiiChart');if(aaiiOld)aaiiOld.destroy();
})();

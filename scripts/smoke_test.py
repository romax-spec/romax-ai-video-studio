import requests,sys,time,os
base=os.getenv("ROMAX_API","http://localhost:8000")
r=requests.get(base+"/api/health",timeout=10);r.raise_for_status();print("health",r.json())
print("Upload/render smoke test requires a sample video path as argv[1].")
if len(sys.argv)<2: sys.exit(0)
with open(sys.argv[1],"rb") as f: p=requests.post(base+"/api/projects",files={"file":f},data={"title":"Smoke test"});p.raise_for_status()
project=p.json();print("uploaded",project["id"])
j=requests.post(base+f"/api/projects/{project['id']}/analyze").json()["jobId"]
while True:
 s=requests.get(base+f"/api/jobs/{j}").json();print(s)
 if s["status"] in ("completed","failed"):break
 time.sleep(1)
if s["status"]!="completed":raise SystemExit(s["message"])
r=requests.post(base+f"/api/projects/{project['id']}/render",json={"project":project["project"]});r.raise_for_status();j=r.json()["jobId"]
while True:
 s=requests.get(base+f"/api/jobs/{j}").json();print(s)
 if s["status"] in ("completed","failed"):break
 time.sleep(1)
if s["status"]!="completed":raise SystemExit(s["message"])
r=requests.get(base+f"/api/projects/{project['id']}/download");r.raise_for_status()
open("romax-smoke-export.mp4","wb").write(r.content);print("exported",len(r.content))

const fs=require("fs");const d=require("docx");
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,ImageRun,WidthType,ShadingType,AlignmentType,HeadingLevel,BorderStyle,PageBreak}=d;
const S=JSON.parse(fs.readFileSync("results/summary.json"));
const F="Calibri";
const t=(x,o={})=>new TextRun({text:x,font:F,size:21,...o});
const p=(x,o={})=>new Paragraph({children:Array.isArray(x)?x:[t(x)],spacing:{after:110,line:276},...o});
const h1=x=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun({text:x,font:F,size:30,bold:true,color:"1F3A5F"})],spacing:{before:260,after:120}});
const h2=x=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun({text:x,font:F,size:24,bold:true,color:"2A6F97"})],spacing:{before:180,after:80}});
const b=x=>new Paragraph({children:Array.isArray(x)?x:[t(x)],bullet:{level:0},spacing:{after:60}});
const B=x=>t(x,{bold:true});
const code=s=>new Paragraph({children:s.split("\n").flatMap((l,i)=>[...(i?[new TextRun({break:1})]:[]),new TextRun({text:l,font:"Consolas",size:17})]),shading:{type:ShadingType.CLEAR,fill:"F3F3F3"},spacing:{before:60,after:140}});
const eq=x=>new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:x,font:"Cambria Math",size:22,italics:true})],spacing:{before:60,after:120}});
const fig=(f,w,h,cap)=>[new Paragraph({alignment:AlignmentType.CENTER,children:[new ImageRun({type:"png",data:fs.readFileSync(f),transformation:{width:w,height:h},altText:{title:cap,description:cap,name:f}})],spacing:{before:80,after:40},keepNext:true}),
 new Paragraph({alignment:AlignmentType.CENTER,children:[t(cap,{italics:true,size:18,color:"555555"})],spacing:{after:140}})];
const bd={style:BorderStyle.SINGLE,size:4,color:"BBBBBB"};const bds={top:bd,bottom:bd,left:bd,right:bd};
function table(head,rows,widths){const tot=widths.reduce((a,c)=>a+c,0);
 const cell=(x,i,hd)=>new TableCell({borders:bds,width:{size:widths[i],type:WidthType.DXA},shading:hd?{type:ShadingType.CLEAR,fill:"1F3A5F"}:undefined,margins:{top:50,bottom:50,left:80,right:80},
  children:[new Paragraph({alignment:i?AlignmentType.CENTER:AlignmentType.LEFT,children:[new TextRun({text:String(x),font:F,size:18,bold:hd,color:hd?"FFFFFF":undefined})]})]});
 return new Table({width:{size:tot,type:WidthType.DXA},columnWidths:widths,rows:[new TableRow({tableHeader:true,children:head.map((x,i)=>cell(x,i,true))}),...rows.map(r=>new TableRow({cantSplit:true,children:r.map((x,i)=>cell(x,i,false))}))]});}
const ms=x=>(x*1e3).toFixed(1);
const kb=s=>s>=1e6?(s/1e6)+" MB":(s/1e3)+" kB";
const names=Object.keys(S.par6).sort((a,c)=>S.par6[a].size-S.par6[c].size);
const rnames=Object.keys(S.real.par6).sort();
const full=(key,src,nm)=>(nm||names).map(n=>{const v=src[key][n];return [n.replace("_v1","").replace(".txt",""),kb(v.size),ms(v.up.avg),ms(v.up.median),ms(v.up.min),ms(v.up.max),ms(v.down.avg),ms(v.down.median),ms(v.down.min),ms(v.down.max)]});
const H=["File","Size","Up avg","Up med","Up min","Up max","Down avg","Down med","Down min","Down max"];
const W=[1500,900,900,900,900,900,1000,1000,1000,1000];
const P=S.pooled;const MR=(c,R,f)=>S.model_vs_meas.find(r=>r.cfg===c&&r.R===R&&r.file===f);const BIG="s10000k_v1.txt";const big="s10000k_v1.txt";
const cmp=[["par6","N=6, parallel"],["par12","N=12, parallel"],["par24","N=24, parallel"],["seq6","N=6, sequential"]].map(([k,l])=>{const v=P[k];return [l,v.n,ms(v.up.avg),ms(v.up.median),ms(v.up.min),ms(v.up.max),ms(v.down.avg),ms(v.down.median),ms(v.down.min),ms(v.down.max)]});
const swp=names.map(n=>{const v=S.sweep.par6[n];return [kb(v.size),ms(v.up.avg),ms(v.up.median),ms(v.up.min),ms(v.up.max),ms(v.down.avg),ms(v.down.median),ms(v.down.min),ms(v.down.max)]});
const fit=k=>S.fits[k];
const model=S.model_vs_meas.map(r=>[({par6:"parallel, N=6",seq6:"sequential, N=6",par24:"parallel, N=24"})[r.cfg]+", R="+r.R,kb(r.size),r.tx_ms.toFixed(0),r.up_model.toFixed(0),r.up_meas.toFixed(0),r.down_model.toFixed(0),r.down_meas.toFixed(0)]);
const loss=S.loss.filter(l=>l.F>=3).map(l=>[l.N,l.F,(l.p1*100).toFixed(2)+" %",(l.rand50*100).toFixed(1)+" %",(l.rand1000*100).toFixed(1)+" %",(l.groups*100).toFixed(1)+" %"]);
const c=[];
c.push(new Paragraph({children:[new TextRun({text:"Mini-Project 2026 – Task 1: Replication",font:F,size:44,bold:true,color:"1F3A5F"})],spacing:{after:60}}));
c.push(new Paragraph({children:[t("A replicated, versioned file store with 3 full copies on N = 6, 12, 24 nodes (Flask REST, lead node, SQLite metadata)",{size:24,color:"555555"})],spacing:{after:200}}));
c.push(new Paragraph({shading:{type:ShadingType.CLEAR,fill:"E8F3EA"},border:{left:{style:BorderStyle.SINGLE,size:24,color:"2F9E44"}},spacing:{after:200},children:[B("Dataset. "),t("All results use the course dataset: 50 ASCII files (10 fruit names × versions _v1–_v5), exactly 10,000,000 bytes each (500 MB in total). Every file's SHA-256 was verified against manifest.json before use (50/50 match). Each version is built from its predecessor by deleting 1,000 random 1,000-byte paragraphs and inserting 1,000 new ones (10 % change). Because all real files have the same size, the dependence on file size is studied with an additional size sweep made of prefixes of apple_v1.txt (0.1, 0.5, 1, 2, 5 and 10 MB); this is stated wherever it is used.")]}));
c.push(h1("1. Summary"));
c.push(b([B("What was built: "),t("a lead node (REST API) that receives a file, detects its version, chooses 3 different storage nodes out of N and sends the file to each of them directly; N independent storage-node processes; store, retrieve-latest and retrieve-specific-version are all implemented.")]));
c.push(b([B("Correctness: "),t("13 automatic tests pass on the real dataset, including byte-exact retrieval of all 50 files (500 MB), exactly 3 distinct copies per file (150 blobs, 1.5 GB on disk = 3× storage), and successful reads after two nodes are killed.")]));
c.push(b([B("Performance: "),t(`with ≥100 repetitions per file, a 10 MB file uploads in ≈${ms(S.sweep.par6[big].up.avg)} ms (N=6) and downloads in ≈${ms(S.sweep.par6[big].down.avg)} ms. Times grow linearly with file size and do not depend on N (6, 12 or 24), as predicted by the model: a store is one transfer in plus three parallel transfers out.`)]));
c.push(b([B("Model check: "),t("with the link rate emulated at R = 400 Mbit/s, measured times follow the predicted formulas within 5–19 % (within ~10 % of the pure network formulas at 100 Mbit/s), and sequential fan-out is about 1.9× slower than parallel fan-out for the 10 MB file (predicted ≈2×).")]));

c.push(h1("2. System design"));
c.push(h2("2.1 Architecture"));
c.push(p("Three kinds of processes, all on one machine (loopback), each reachable over HTTP exactly as they would be on separate machines (Lecture 1: client/server over TCP/IP, HTTP request/response):"));
c.push(b([B("Client "),t("– sends HTTP PUT /files/<name> and GET /files/<name>[?version=N].")]));
c.push(b([B("Lead node (lead.py) "),t("– the only component that clients talk to. It keeps the metadata table files(base, version, size, sha256, nodes) in SQLite, decides placement, and sends data to the storage nodes.")]));
c.push(b([B("Storage nodes (node.py) "),t("– N separate OS processes on ports 8001…8000+N, each a very simple blob store (PUT/GET/DELETE /blob/<key>) writing to its own directory.")]));
c.push(code("client --PUT /files/report_v3.txt--> lead --+--PUT /blob/report.txt__v3--> node 2\n                                              +--PUT /blob/report.txt__v3--> node 5\n                                              +--PUT /blob/report.txt__v3--> node 9\n(3 distinct nodes out of N, chosen at random)"));
c.push(h2("2.2 Write path (store)"));
c.push(p("1) The lead receives the whole file. 2) It parses the name with the regular expression ^(.*?)(?:_v(\\d+))?(\\.[^.]*)?$ : report_v3.txt becomes base report.txt, version 3; a name without _vN gets the next free version number. A version that already exists is rejected with HTTP 409. 3) It picks 3 distinct nodes with random.sample (random replication, as in HDFS, Lecture 8). 4) It sends the file directly to each of the three nodes – in parallel threads by default, or one after the other in 'sequential' mode, used for comparison. 5) Each node writes to a temporary file, calls fsync, checks the SHA-256 sent by the lead, renames the file into place and only then answers 201. 6) Only after all three acknowledgements does the lead commit the metadata row and answer the client. Consequently a file is never visible unless all 3 replicas exist."));
c.push(h2("2.3 Read path (retrieve)"));
c.push(p("The lead looks up the latest (or requested) version, tries the three replicas in random order (this spreads read load, Lecture 3/4: reads can use any copy), verifies the SHA-256 of what it received and falls back to the next replica on a connection error, a missing blob or a corrupted blob. Only if all three fail does the client get HTTP 503."));
c.push(h2("2.4 REST interface"));
c.push(table(["Request","Meaning"],[["PUT/POST /files/<name>","store a file; version from _vN suffix or auto-assigned"],["GET /files/<name>","retrieve the latest version (header X-Version tells which)"],["GET /files/<name>?version=N or <stem>_vN.<ext>","retrieve a specific version (optional part of the brief)"],["GET /files/<name>/info","metadata: size, checksum, nodes holding the replicas"],["DELETE /files/<name>","remove all versions (benchmark clean-up)"]],[4200,5800]));
c.push(h2("2.5 Link to the lectures"));
c.push(table(["Lecture","Idea used in this project"],[
["1 – Introduction / networks","client–server over HTTP/TCP; bandwidth R and file size B determine transfer time 8B/R"],
["3 – Redundancy: replication","3 full copies = 200 % storage overhead; survives the loss of any 2 copies; any copy can serve a read"],
["4 – RAID","replication = RAID-1 style mirroring generalised to 3 copies: space efficiency 1/3, write cost = all copies written, read can use one of several copies"],
["8 – HDFS / replica placement","3-fold random replication; lead writes to all replicas (direct fan-out, instead of the HDFS write pipeline); random vs copyset-style placement and the data-loss probability C(F,3)/C(N,3)"]],[2600,7400]));

c.push(h1("3. Analysis (Task 1 questions)"));
c.push(h2("3.1 Upload time"));
c.push(p("Let B be the file size in bytes and R the bandwidth of every link in bit/s. The lead stores the file as soon as it is complete (store-and-forward), then sends it to the three nodes."));
c.push(eq("T_up(parallel) ≈ t0 + 8B/R  (client→lead)  +  8B/R  (lead→3 nodes at once)  =  t0 + 2·8B/R"));
c.push(eq("T_up(sequential, or one shared uplink) ≈ t0 + 8B/R + 3·8B/R = t0 + 4·8B/R"));
c.push(p("Here t0 is a fixed cost for HTTP set-up, the disk fsync and the metadata commit. The three copies leave the lead on three independent links, so with parallel fan-out the time for 3 replicas is almost the same as for 1. Because the lead only chooses which nodes receive the file, T_up does not depend on N: the number of nodes matters for capacity and fault tolerance, not for latency. If the lead had one single uplink of rate R shared by the three copies the term becomes 3·8B/R, which is what sequential mode emulates."));
c.push(h2("3.2 Download time"));
c.push(eq("T_down ≈ t_lookup + 8B/R (node→lead) + 8B/R (lead→client)  (store-and-forward),  ≈ t0 + 8B/R if the lead streams the data through"));
c.push(p("A read touches only one replica, so it costs about one transfer more than the raw network time; it is faster than an upload because no data is duplicated and no fsync is needed. With the three replicas on different nodes, concurrent readers are spread over 3 nodes (load balancing)."));
c.push(h2("3.3 Cost of the redundancy"));
c.push(b("Storage: 3B per file, i.e. 200 % overhead, efficiency 1/3 (Lecture 3). Confirmed by the test: 50 files → 150 blobs on disk."));
c.push(b("Tolerance: any 2 nodes may fail without losing data, since the 3 copies are on 3 different nodes (confirmed: after killing 2 nodes all files were still readable)."));
c.push(b("Beyond 2 failures it depends on placement. With random placement a file is lost when its three nodes are exactly the failed ones; the probability for one file with F failed nodes is C(F,3)/C(N,3). With many files almost every 3-subset is used by some file, so losing 3 random nodes loses data with high probability. Placing all copies in fixed groups of 3 nodes (MinCopysets idea, Lecture 8) trades this off: fewer different 3-sets, so data loss happens less often (but with more data lost when it does)."));
c.push(table(["N","failed F","P(one file lost)","P(≥1 of 50 lost) random","P(≥1 of 1000 lost) random","P(≥1 group lost) groups"],loss,[700,1000,1700,2200,2300,2100]));
c.push(p([t("Table 1 – data-loss probability (analytic; Monte-Carlo with 20 000 trials for the random scheme: "),t(`N=12,F=3: ${(S.mc["12,3"]*100).toFixed(1)} % (formula 20.4 %), N=12,F=4: ${(S.mc["12,4"]*100).toFixed(1)} % (60.0 %), N=24,F=4: ${(S.mc["24,4"]*100).toFixed(1)} % (9.4 %)).`)],{}));
c.push(...fig("figs/fig_loss.png",330,229,"Figure 1 – probability of losing at least one of 1000 files: random vs grouped placement"));

c.push(h1("4. Measurements"));
c.push(h2("4.1 Method"));
c.push(b("For every file (the ten v1 files, all 10 MB, plus six prefix files of 0.1–10 MB for the size sweep), 100 timed repetitions after 3 warm-up repetitions; each repetition uploads under a fresh name, downloads it back (byte-compared, outside the timed part) and deletes it, so every upload is a first store with random placement."));
c.push(b("Times are measured on the client with time.perf_counter(): upload = from sending the request to receiving the 201 reply (i.e. after all 3 replicas are fsynced); download = from the request to the last byte received."));
c.push(b("N = 6, 12, 24 storage-node processes; 'sequential' fan-out measured at N = 6 for comparison. Per-fruit results use the real 10 MB files; the dependence on file size uses the prefix sweep."));
c.push(b("Because everything runs on loopback, the network is effectively infinitely fast. To check the formulas of section 3 against a finite R, a second series throttles every link (client→lead, lead→node, lead→client) to R = 400 Mbit/s (and for one file size also 100 Mbit/s) with a rate-limited sender. The node→lead link on reads is not throttled, so the read model contains one transfer term."));
c.push(h2("4.2 Results without throttling (all times in ms)"));
c.push(p("Table 2 – N = 6, the ten real files of 10 MB (100 repetitions each)."));
c.push(table(H,full("par6",S.real,rnames),W));
c.push(p(""));
c.push(p("Table 3 – all ten real files pooled (1000 repetitions) for N = 6, 12, 24 and sequential fan-out."));
c.push(table(["Config","Reps",...H.slice(2)],cmp,[1900,700,900,900,900,900,1000,1000,1000,1000]));
c.push(p(""));
c.push(p("Table 4 – size sweep for N = 6 (prefixes of apple_v1.txt, 100 repetitions each)."));
c.push(table(["Size",...H.slice(2)],swp,[1100,1000,1000,1000,1000,1100,1100,1100,1100]));
c.push(p(""));
c.push(...fig("figs/fig_unthrottled.png",600,240,"Figure 2 – mean upload and download time against file size for N = 6, 12, 24 and sequential fan-out"));
c.push(p([B("Observations. "),t(`(i) Both times are linear in file size (R² ≥ 0.99): upload ≈ ${fit("par6_up").t0_ms.toFixed(0)} ms + ${fit("par6_up").ms_per_MB.toFixed(1)} ms/MB, download ≈ ${fit("par6_down").t0_ms.toFixed(0)} ms + ${fit("par6_down").ms_per_MB.toFixed(1)} ms/MB for N = 6. (ii) The lines for N = 6, 12 and 24 lie on top of each other (upload slopes ${fit("par6_up").ms_per_MB.toFixed(1)}, ${fit("par12_up").ms_per_MB.toFixed(1)}, ${fit("par24_up").ms_per_MB.toFixed(1)} ms/MB): N does not influence latency, as the model says. (iii) Sequential fan-out has a clearly steeper upload slope (${fit("seq6_up").ms_per_MB.toFixed(1)} ms/MB, ×${(fit("seq6_up").ms_per_MB/fit("par6_up").ms_per_MB).toFixed(2)}) but the same download slope. (iv) Uploads cost about twice as much as downloads for the reasons in 3.2.`)]));
c.push(...fig("figs/fig_box.png",330,216,"Figure 3 – spread of the 100 upload times of a real 10 MB file (apple_v1); the median is stable, rare outliers (max) are up to ~2× the median"));
c.push(p("The maximum column is consistently larger than the average, and the median is slightly lower: a few repetitions are delayed by scheduler jitter and disk flushes. The machine has only 2 CPU cores while up to 25 processes exist, so absolute values (and especially the max column) carry noise; the trends are robust. During the first N = 24 pass over the real files the host slowed down for the last two files (pineapple reached 4 s once); those two files were measured again immediately and the rerun replaced them (both raw files are in the code package)."));
c.push(h2("4.3 Validation of the model with emulated link rates"));
c.push(p("Model = unthrottled measurement + k·8B/R, with k = 2 (parallel upload), 4 (sequential upload), 1 (download); 8B/R is the time of one transfer (2 ms, 20 ms and 200 ms at 400 Mbit/s for 0.1, 1 and 10 MB; 800 ms for 10 MB at 100 Mbit/s)."));
c.push(table(["Config","Size","8B/R (ms)","Up model","Up measured","Down model","Down measured"],model,[2100,1500,1100,1300,1500,1300,1500]));
c.push(p(""));
c.push(...fig("figs/fig_model.png",600,240,"Figure 4 – measured means (bars) against the model (black marks) at R = 400 Mbit/s"));
{const a=MR("par6",400,BIG),q=MR("seq6",400,BIG),n=MR("par24",400,BIG),a1=MR("par6",100,BIG),q1=MR("seq6",100,BIG);
c.push(p(`The additive model is slightly pessimistic (up to ${(((a.up_model/a.up_meas)-1)*100).toFixed(0)} % too high for the 10 MB upload at 400 Mbit/s) because the throttled sending overlaps with CPU work that the model counts twice. The qualitative predictions hold: sequential upload of 10 MB took ${q.up_meas.toFixed(0)} ms versus ${a.up_meas.toFixed(0)} ms in parallel (×${(q.up_meas/a.up_meas).toFixed(2)}; predicted ×2 for the pure network terms), reads are identical in both modes, and N = 24 behaves like N = 6 (${n.up_meas.toFixed(0)} ms vs ${a.up_meas.toFixed(0)} ms). When the network dominates (R = 100 Mbit/s, 10 MB) the simple network-only formulas are close: parallel upload ${a1.up_meas.toFixed(0)} ms against 2·8B/R = 1600 ms (+${((a1.up_meas/1600-1)*100).toFixed(0)} %), sequential upload ${q1.up_meas.toFixed(0)} ms against 4·8B/R = 3200 ms (+${((q1.up_meas/3200-1)*100).toFixed(0)} %), download ${a1.down_meas.toFixed(0)} ms against 8B/R = 800 ms (+${((a1.down_meas/800-1)*100).toFixed(0)} %).`));}

c.push(h1("5. Discussion"));
c.push(b([B("Fan-out strategy. "),t("Sending the three copies in parallel from the lead is simple and keeps the write time ≈ 2 transfers; its cost is that the lead's network link must carry 3B of outgoing data per file. On a real network with a single 1 Gbit/s lead uplink that shared link becomes the bottleneck (the sequential/shared case, 4·8B/R). A chain (HDFS pipeline, Lecture 8) would instead take about (1 + 3)·8B/R too but spare the lead's uplink; we kept the direct fan-out as the brief requires.")]));
c.push(b([B("Durability vs speed. "),t("Waiting for fsync and the checksum on all three nodes makes writes slower than a fire-and-forget design, but a successful reply guarantees 3 durable copies.")]));
c.push(b([B("Placement. "),t("Random placement balances load and is trivial, but with many files nearly every 3-subset of nodes holds some file, so 3 simultaneous failures almost surely lose data (Table 1). Grouped placement lowers this probability by an order of magnitude at N = 24 at the cost of less even load; both are implemented (placement = random | groups).")]));
c.push(b([B("Lead node as single point of failure. "),t("The metadata lives only on the lead (SQLite). That is acceptable for the assignment; a production system would replicate it (cf. the HDFS name node, Lecture 8).")]));
c.push(h2("Limitations"));
c.push(b("All real files have the same size (10 MB), so the file-size dependence was measured with prefixes of apple_v1.txt (0.1–10 MB); content does not matter for Task 1, which only moves bytes. The version-to-version differences in the dataset (10 % edits) are irrelevant here and matter for Task 3 (delta encoding)."));
c.push(b("Loopback network on a 2-core machine: absolute numbers are not those of a real cluster, and timing noise is non-negligible; the R = 400 Mbit/s series is an emulation of the links, not a real network."));
c.push(b("Retrieval of specific versions is implemented and tested, but only 'store' and 'retrieve latest' were benchmarked."));
c.push(h1("6. How to reproduce"));
c.push(code("pip install flask requests waitress numpy matplotlib\npython test_correctness.py dataset_real # 13 functional tests (folder with the 50 real files)\n./run_all.sh dataset_real                 # all benchmarks → results/*.json\npython analysis.py                     # tables + figures"));
c.push(p("Files: common.py (version regex, throttle), node.py, lead.py, cluster.py, client.py, test_correctness.py, bench.py, run_all.sh, analysis.py."));
const doc=new Document({styles:{default:{document:{run:{font:F,size:21}}}},sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:1134,bottom:1134,left:1134,right:1134}}},children:c}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync("Task1_Report.docx",b));

// Lightweight DOM/canvas contract test. Does not replace a real browser test.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert');
const html=fs.readFileSync(process.argv[2]||'demo_export/XEM_MAU_3D.html','utf8');
assert(!html.includes('__GEOMETRY_JSON__'));
const queue=[];let fills=0;
const elements={};
function element(){return {children:[],dataset:{},listeners:{},append(...c){this.children.push(...c);},addEventListener(k,f){this.listeners[k]=f;}};}
for(const id of ['view','layers','reset','summary'])elements[id]=element();
const canvas=elements.view;
canvas.getBoundingClientRect=()=>({width:900,height:650});canvas.setPointerCapture=()=>{};
canvas.getContext=()=>({setTransform(){},clearRect(){},beginPath(){},moveTo(){},lineTo(){},closePath(){},fill(){fills++;}});
const context={document:{getElementById:id=>elements[id],createElement:element,createTextNode:t=>t},
 devicePixelRatio:1,requestAnimationFrame:f=>queue.push(f),ResizeObserver:class{constructor(f){this.f=f;}observe(){this.f();}}};
vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context,{timeout:10000});
function flush(){fills=0;while(queue.length)queue.shift()();return fills;}
const initial=flush();assert(initial>1000);assert.equal(canvas.dataset.rendered,'true');
const labels=elements.layers.children;assert.equal(labels.length,3);
labels[0].children[0].checked=false;labels[0].children[0].onchange();
const single=flush();assert(single>0&&single<initial);
labels[2].children[0].checked=true;labels[2].children[0].onchange();assert(flush()>single);
canvas.listeners.pointerdown({clientX:0,clientY:0,pointerId:1});canvas.listeners.pointermove({clientX:100,clientY:30});canvas.listeners.pointerup();assert(flush()>0);
canvas.listeners.wheel({deltaY:100,preventDefault(){}});assert(flush()>0);
elements.reset.onclick();assert(flush()>0);
console.log(JSON.stringify({initialTrianglesDrawn:initial,singlePieceTriangles:single,layerToggle:true,rotate:true,zoom:true,reset:true,realBrowserTested:false}));

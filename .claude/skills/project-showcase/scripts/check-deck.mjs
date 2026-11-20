import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const [input, output] = process.argv.slice(2);
if (!input || !output) throw Error('check-deck.mjs <index.html> <output>');
await mkdir(output, {recursive:true});
const options={headless:true};
if(process.env.CHROME_PATH) options.executablePath=process.env.CHROME_PATH;
else options.channel='chrome';
const browser=await chromium.launch(options);
const errors=[], shots=[];
try {
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('requestfailed',r=>errors.push(r.url()+': '+r.failure()?.errorText));
 await page.goto(pathToFileURL(path.resolve(input)).href);
 await page.evaluate(()=>document.fonts.ready);
 const inspect=()=>{
  const scene=[...document.querySelectorAll('.scene')].find(e=>getComputedStyle(e).display!=='none');
  const issues=[];const boundary=scene.getBoundingClientRect();
  const outside=(r,b)=>r.left<b.left-2||r.right>b.right+2||r.top<b.top-2||r.bottom>b.bottom+2;
  const textEls=[...scene.querySelectorAll('h1,.claim,.hero,.pill,.point,.big,.step,.tag,.note,.foot span,th,td,.state-tabs button')];
  const visible=textEls.filter(el=>el.getBoundingClientRect().width&&el.getBoundingClientRect().height);
  for(const el of visible){
   const range=document.createRange();range.selectNodeContents(el);
   const r=range.getBoundingClientRect();
   if(outside(r,boundary))issues.push('scene overflow: '+el.className+' '+el.textContent.slice(0,24));
   for(let a=el;a&&a!==scene.parentElement;a=a.parentElement){
    const css=getComputedStyle(a), ar=a.getBoundingClientRect();
    if(/hidden|clip|scroll|auto/.test(css.overflowX+' '+css.overflowY)&&outside(r,ar))issues.push('ancestor clipping: '+el.className+' in '+a.className);
   }
  }
  // Compare independent text blocks, excluding parent/child text pairs.
  for(let i=0;i<visible.length;i++)for(let j=i+1;j<visible.length;j++){
   const a=visible[i],b=visible[j];if(a.contains(b)||b.contains(a))continue;
   const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
   if(Math.min(ar.right,br.right)-Math.max(ar.left,br.left)>3&&Math.min(ar.bottom,br.bottom)-Math.max(ar.top,br.top)>3)issues.push('text overlap: '+a.className+' / '+b.className);
  }
  for(const img of scene.querySelectorAll('img'))if(!img.complete||!img.naturalWidth)issues.push('missing image');
  const h=scene.querySelector('h1').getBoundingClientRect(), l=scene.querySelector('.layout').getBoundingClientRect();
  if(l.bottom>boundary.bottom-130)issues.push('content enters footer/caption reserve');
  if(h.height>190)issues.push('title exceeds two lines');
  return {id:scene.id,issues:[...new Set(issues)]};
 };
 for(let i=0;i<8;i++) {
  await page.evaluate(i=>window.showSlide(i),i);
  const file=path.join(output,`slide-${i+1}.png`);await page.screenshot({path:file});shots.push({...await page.evaluate(inspect),file});
  const buttons=page.locator('.scene:visible [data-state]');
  for(let j=0;j<await buttons.count();j++){
   await buttons.nth(j).click();
   if(await buttons.nth(j).getAttribute('aria-pressed')!=='true')errors.push('state navigation failed');
   const file=path.join(output,`slide-${i+1}-state-${j+1}.png`);await page.screenshot({path:file});shots.push({...await page.evaluate(inspect),file});
  }
 }
 for(const [key,want] of [['ArrowLeft','7/8'],['Home','1/8'],['End','8/8'],['4','4/8']]){
  await page.keyboard.press(key);if(await page.locator('#counter').textContent()!==want)errors.push('keyboard navigation failed: '+key);
 }
 await page.keyboard.press('Home');if(!await page.locator('#prev').isDisabled())errors.push('first boundary button');
 await page.keyboard.press('End');if(!await page.locator('#next').isDisabled())errors.push('last boundary button');
 await page.keyboard.press('?');if(!await page.locator('#help').isVisible())errors.push('help failed');
 await page.keyboard.press('Escape');if(await page.locator('#help').isVisible())errors.push('help dismiss failed');
 await page.setViewportSize({width:1280,height:720});await page.screenshot({path:path.join(output,'projector-720p.png')});
 const navOverlap=await page.evaluate(()=>{
  const nav=document.querySelector('nav').getBoundingClientRect();
  return [...document.querySelectorAll('.scene')].filter(s=>getComputedStyle(s).display!=='none').some(s=>[...s.querySelectorAll('.foot span')].some(e=>{const r=e.getBoundingClientRect();return Math.min(r.right,nav.right)>Math.max(r.left,nav.left)&&Math.min(r.bottom,nav.bottom)>Math.max(r.top,nav.top);}));
 });
 if(navOverlap)errors.push('720p navigation overlaps footer');
 const report={ok:!errors.length&&shots.every(s=>!s.issues.length),samples:shots.length,errors,shots};
 await writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({ok:report.ok,samples:shots.length,errors,issues:shots.filter(s=>s.issues.length)}));
 if(!report.ok)process.exitCode=1;
} finally {await browser.close();}

// Exercise the file:// comparison UX without recording a selection.
import {chromium} from 'playwright';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {mkdir,writeFile} from 'node:fs/promises';
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('check-design.mjs <design/index.html> <output>');
const browser=await chromium.launch(process.env.CHROME_PATH?{headless:true,executablePath:process.env.CHROME_PATH}:{headless:true,channel:'chrome'});
const errors=[];const assert=(value,message)=>{if(!value)errors.push(message)};
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(Error('fixture clipboard unavailable'))}}));
 await page.goto(pathToFileURL(path.resolve(input)).href);await page.evaluate(async()=>{for(const i of document.images)i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))});
 assert(await page.locator('article').count()===4,'four directions');
 assert(await page.locator('.slides a:visible').count()===4,'initial covers only');
 await page.locator('.expand').first().click();assert(await page.locator('.slides a:visible').count()===6,'expand three slides');
 await page.locator('#grid-toggle').click();assert(await page.locator('.slides a:visible').count()===12,'twelve-slide view');
 await page.locator('.compare').nth(0).check();await page.locator('.compare').nth(1).check();await page.locator('.compare').nth(2).click();
 assert(!await page.locator('.compare').nth(2).isChecked(),'limit comparison to two');
 await page.locator('#pair-toggle').click();assert(await page.locator('article:visible').count()===2,'two-direction view');
 assert(await page.locator('#grid-toggle').getAttribute('aria-pressed')==='true','view toggle state');
 await page.locator('#reset').click();assert(await page.locator('article:visible').count()===4,'reset directions');
 await page.locator('.choose:enabled').first().click();assert(await page.locator('details').first().getAttribute('open')!==null,'clipboard fallback');
 assert((await page.locator('#feedback').textContent()).includes('직접 복사'),'copy is not a saved selection');
 const [popup]=await Promise.all([page.waitForEvent('popup'),page.locator('.slides a').nth(1).click()]);await popup.waitForLoadState('load');
 assert(await popup.locator('#counter').textContent()==='2/3','full-size slide link');await popup.close();
 await mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'comparison-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.locator('#pair-toggle').click();
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'mobile horizontal overflow');
 const rects=await page.locator('article:visible').evaluateAll(es=>es.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y})));
 assert(rects[0].x===rects[1].x&&rects[1].y>rects[0].y,'mobile stacked comparison');
 await page.screenshot({path:path.join(output,'comparison-mobile.png'),fullPage:true});
 await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))});
 assert(await page.locator('img').evaluateAll(es=>es.every(i=>i.complete&&i.naturalWidth>0)),'comparison images load');
 const report={ok:errors.length===0,errors,viewports:[1440,390],selection_written:false};await writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));if(!report.ok)process.exitCode=1;
}finally{await browser.close()}

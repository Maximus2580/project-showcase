import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const [input, output]=process.argv.slice(2);
const browser=await chromium.launch(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{channel:'chrome'});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.resolve(input)).href);await page.evaluate(()=>document.fonts.ready);
 const report=await page.evaluate(()=>{
  const cues=[...document.querySelectorAll('.caption')];const issues=[];
  for(const cue of cues){
   const span=cue.querySelector('span'),rect=span.getBoundingClientRect();
   const line=parseFloat(getComputedStyle(span).lineHeight);
   if(rect.height>line*2+25)issues.push({id:cue.id,code:'more_than_two_lines',text:span.textContent});
   if(rect.left<192||rect.right>1728||rect.top<780||rect.bottom>970)issues.push({id:cue.id,code:'caption_safe_area',text:span.textContent});
  }
  return {ok:cues.length>0&&!issues.length,samples:cues.length,issues};
 });
 await writeFile(output,JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(!report.ok)process.exitCode=1;
}finally{await browser.close()}

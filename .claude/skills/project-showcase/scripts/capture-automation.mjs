import { chromium } from 'playwright';
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../examples/automation-project');
const summary=JSON.parse(await readFile(path.join(root,'summary.json'),'utf8'));
if(summary.rows!==5||summary.by_status['완료']!==2||summary.by_status['지연']!==2||summary.by_status['진행']!==1)throw Error('unexpected computed result');
const browser=await chromium.launch(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{channel:'chrome'});
try{
 const page=await browser.newPage({viewport:{width:1400,height:900}});
 await page.goto(pathToFileURL(path.join(root,'report.html')).href);
 if(await page.locator('td').allTextContents().then(x=>x.join(','))!=='완료,2,지연,2,진행,1')throw Error('report differs from computed result');
 await mkdir(path.join(root,'input'),{recursive:true});
 await page.locator('main').screenshot({path:path.join(root,'input/report.png')});
}finally{await browser.close();}

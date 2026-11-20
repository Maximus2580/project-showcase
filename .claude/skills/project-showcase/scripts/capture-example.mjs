import {chromium} from 'playwright';import {mkdir} from 'node:fs/promises';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
const skill=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const out=path.resolve(process.argv[2]);await mkdir(out,{recursive:true});
const browser=await chromium.launch(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{channel:'chrome'});
try{const page=await browser.newPage({viewport:{width:1280,height:800}});await page.goto(pathToFileURL(path.join(skill,'examples/demo-project/index.html')).href);
await page.locator('main').screenshot({path:path.join(out,'input.png')});
for(const [input,expected,name] of [['배송이 언제 도착하나요?','배송 문의','delivery'],['환불해주세요','환불 문의','refund'],['안녕하세요','담당자 확인 필요','unknown']]){
await page.locator('#inquiry').fill(input);await page.locator('#classify').click();if(await page.locator('#result').textContent()!==expected)throw Error('fixture failure');await page.locator('main').screenshot({path:path.join(out,name+'.png')});}
console.log('배송/환불/미분류 실행 화면 3종 및 입력 화면 저장');}finally{await browser.close()}

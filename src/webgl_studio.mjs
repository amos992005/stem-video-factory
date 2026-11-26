/* Headless 3D scene renderer: SwiftShader WebGL frames -> FFmpeg, no flat art. */
import puppeteer from 'puppeteer-core';
import {spawn} from 'node:child_process';
import {readFileSync,existsSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import {once} from 'node:events';
const config=JSON.parse(readFileSync(process.argv[2],'utf8'));
const candidates=[process.env.CHROME_PATH,'/usr/bin/google-chrome-stable','/usr/bin/google-chrome','/usr/bin/chromium','/tmp/chromium'].filter(Boolean);
const executablePath=candidates.find(p=>existsSync(p));
if(!executablePath)throw new Error('No Chromium executable found; set CHROME_PATH');
console.log(`WebGL renderer using browser ${executablePath} at 360x640, final output 1080x1920`);
const browser=await puppeteer.launch({executablePath,headless:true,args:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--allow-file-access-from-files']});
try{
  const page=await browser.newPage();await page.setViewport({width:360,height:640,deviceScaleFactor:1});
  page.on('pageerror',e=>console.error('WebGL page error:',e.stack));
  page.on('console',m=>console.log('Browser:',m.text()));
  const html=path.join(path.dirname(fileURLToPath(import.meta.url)),'three_studio.html');
  await page.goto(pathToFileURL(html).href,{waitUntil:'load',timeout:30000});
  await page.waitForFunction('window.studioReady === true',{timeout:30000});
  const renderer=await page.evaluate(()=>{const c=document.createElement('canvas');const gl=c.getContext('webgl2');if(!gl)return 'unavailable';const ext=gl.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'WebGL2'});
  if(renderer==='unavailable')throw Error('WebGL2 unavailable in Chromium');
  console.log('WebGL device:',renderer);
  for(const beat of config.timeline){
    const dest=path.join(config.tmp,`beat_${beat.index}.mp4`);
    const vf=`scale=1080:1920:flags=bicubic,fade=t=in:st=0:d=0.2:color=white,setpts=PTS+${beat.start}/TB,ass='${config.ass}',setpts=PTS-${beat.start}/TB`;
    const args=['-v','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate','30','-i','pipe:0','-vf',vf,'-frames:v',String(beat.frames),'-r','30','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',dest];
    const ff=spawn('ffmpeg',args,{stdio:['pipe','ignore','inherit']});
    let writeError=null;ff.stdin.on('error',e=>{writeError=e});
    const exited=new Promise((resolve,reject)=>{ff.on('error',reject);ff.on('close',code=>code===0?resolve():reject(Error(`FFmpeg beat ${beat.index+1} exited ${code}`)))});
    const start=Date.now();
    for(let frame=0;frame<beat.frames;frame++){
      const global=beat.start+frame/30;const sample=config.rms[Math.min(config.rms.length-1,Math.floor(global*30))]||0;
      const jpeg=await page.evaluate(({i,t,a,l})=>window.renderFrame(i,t,a,l),{i:beat.index,t:global,a:sample,l:frame/30});
      if(writeError)throw writeError;
      if(!ff.stdin.write(Buffer.from(jpeg,'base64')))await once(ff.stdin,'drain');
    }
    ff.stdin.end();await exited;
    console.log(`Rendered 3D beat ${beat.index+1}: ${beat.frames} frames in ${((Date.now()-start)/1000).toFixed(1)}s`);
  }
}finally{await browser.close()}
